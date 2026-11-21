import os
import uuid
import zipfile
import io
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import ProcessingJob, Project, Video, Clip
from app.schemas.schemas import CreateJobRequest
from app.services.job_queue import execute_processing_pipeline
from app.core.logging import logger

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.post("")
async def create_job(
    payload: CreateJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Submits an AI video clipping job.
    Options:
    - clip_duration: 15, 30, 45, 60
    - requested_clips: 3, 5, 10, 15, 20
    - aspect_ratio: 9:16, 1:1, 16:9
    - language: auto, hi, en, gu
    - caption_style: Modern, Bold, Minimal, Gaming, Podcast
    """
    if not payload.project_id:
        raise HTTPException(status_code=400, detail="project_id is required.")

    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")

    video = db.query(Video).filter(Video.project_id == project.id).first()
    if not video or not os.path.exists(video.file_path):
        raise HTTPException(status_code=404, detail="Project source video file not found.")

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job = ProcessingJob(
        id=job_id,
        project_id=project.id,
        status="QUEUED",
        current_step="queued",
        progress=0.0,
        clip_duration=payload.clip_duration,
        requested_clips=payload.requested_clips,
        aspect_ratio=payload.aspect_ratio,
        language=payload.language,
        caption_style=payload.caption_style
    )
    db.add(job)
    project.status = "PROCESSING"
    db.commit()

    # Dispatch to background task worker
    background_tasks.add_task(execute_processing_pipeline, job_id)

    return {
        "success": True,
        "job_id": job.id,
        "project_id": project.id,
        "status": job.status,
        "message": "AI clipping job submitted to processing queue."
    }

@router.get("")
async def list_jobs(db: Session = Depends(get_db)):
    """
    Returns list of all processing jobs with their current status and progress.
    """
    jobs = db.query(ProcessingJob).order_by(ProcessingJob.created_at.desc()).all()
    results = []
    for j in jobs:
        results.append({
            "id": j.id,
            "project_id": j.project_id,
            "project_title": j.project.title if j.project else "Untitled",
            "status": j.status,
            "current_step": j.current_step,
            "progress": j.progress,
            "error_message": j.error_message,
            "clip_duration": j.clip_duration,
            "requested_clips": j.requested_clips,
            "aspect_ratio": j.aspect_ratio,
            "language": j.language,
            "caption_style": j.caption_style,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "started_at": j.started_at.isoformat() if j.started_at else None,
            "completed_at": j.completed_at.isoformat() if j.completed_at else None,
            "clips_count": len(j.clips)
        })
    return results

@router.get("/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """
    Returns detailed status, step progress, and generated clips for a specific job.
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    clips_data = []
    for c in job.clips:
        clips_data.append({
            "id": c.id,
            "clip_number": c.clip_number,
            "title": c.title,
            "start_time": c.start_time,
            "end_time": c.end_time,
            "duration": c.duration,
            "highlight_score": c.highlight_score,
            "reasoning": c.reasoning,
            "transcript": c.transcript,
            "aspect_ratio": c.aspect_ratio,
            "video_url": f"/static/clips/{os.path.basename(c.file_path)}",
            "thumbnail_url": f"/static/thumbnails/{os.path.basename(c.thumbnail_path)}" if c.thumbnail_path else None,
            "download_url": f"/api/clips/{c.id}/download",
            "subtitles": [
                {"id": s.id, "format": s.format, "url": f"/api/clips/{c.id}/subtitles?format={s.format}"}
                for s in c.subtitles
            ]
        })

    return {
        "id": job.id,
        "project_id": job.project_id,
        "project_title": job.project.title if job.project else "Untitled",
        "status": job.status,
        "current_step": job.current_step,
        "progress": job.progress,
        "error_message": job.error_message,
        "clip_duration": job.clip_duration,
        "requested_clips": job.requested_clips,
        "aspect_ratio": job.aspect_ratio,
        "language": job.language,
        "caption_style": job.caption_style,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "clips": clips_data
    }

@router.get("/{job_id}/download")
async def download_all_job_clips_zip(job_id: str, db: Session = Depends(get_db)):
    """
    Packages all generated clips and subtitles for a job into a single downloadable ZIP file.
    """
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    if not job.clips:
        raise HTTPException(status_code=400, detail="No clips available for download in this job.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for clip in job.clips:
            if os.path.exists(clip.file_path):
                zf.write(clip.file_path, arcname=f"clip_{clip.clip_number:02d}_{os.path.basename(clip.file_path)}")
            # Include subtitles
            for sub in clip.subtitles:
                if os.path.exists(sub.file_path):
                    zf.write(sub.file_path, arcname=f"subtitles/clip_{clip.clip_number:02d}.{sub.format}")

    zip_buffer.seek(0)
    filename = f"clipforge_{job.project.title[:30]}_{job_id[:8]}.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
