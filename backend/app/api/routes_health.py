import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Project, Clip, ProcessingJob
from app.services.storage import get_storage_stats
from app.core.config import FFMPEG_PATH, WHISPER_MODEL_NAME

router = APIRouter(prefix="/api", tags=["Health & Stats"])

@router.get("/health")
async def health_check():
    """
    Validates backend API health and subsystem readiness.
    """
    ffmpeg_ok = os.path.exists(FFMPEG_PATH) if FFMPEG_PATH else False
    return {
        "status": "online",
        "app": "ClipForge AI",
        "version": "1.0.0",
        "ffmpeg_path": FFMPEG_PATH,
        "ffmpeg_ready": ffmpeg_ok,
        "whisper_model": WHISPER_MODEL_NAME,
        "device": "cpu",
        "quantization": "int8"
    }

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns aggregated metrics for the SaaS dashboard:
    - total_projects
    - total_clips
    - processing_jobs
    - completed_jobs
    - storage_used_mb
    """
    total_projects = db.query(Project).count()
    total_clips = db.query(Clip).count()
    processing_jobs = db.query(ProcessingJob).filter(ProcessingJob.status.in_(["QUEUED", "PROCESSING"])).count()
    completed_jobs = db.query(ProcessingJob).filter(ProcessingJob.status == "COMPLETED").count()
    storage_mb = get_storage_stats()

    recent_projects_query = db.query(Project).order_by(Project.created_at.desc()).limit(5).all()
    recent_projects = []
    for p in recent_projects_query:
        recent_projects.append({
            "id": p.id,
            "title": p.title,
            "duration": p.duration,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "thumbnail_url": f"/static/thumbnails/{os.path.basename(p.thumbnail_path)}" if p.thumbnail_path else None,
            "clip_count": len(p.clips)
        })

    return {
        "total_projects": total_projects,
        "total_clips": total_clips,
        "processing_jobs": processing_jobs,
        "completed_jobs": completed_jobs,
        "storage_used_mb": storage_mb,
        "recent_projects": recent_projects
    }
