import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Clip, Subtitle

router = APIRouter(prefix="/api/clips", tags=["Clips"])

@router.get("")
async def list_all_clips(db: Session = Depends(get_db)):
    """
    Returns all generated clips across all projects, sorted newest first.
    """
    clips = db.query(Clip).order_by(Clip.created_at.desc()).all()
    results = []
    for c in clips:
        results.append({
            "id": c.id,
            "project_id": c.project_id,
            "project_title": c.project.title if c.project else "Untitled",
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
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return results

@router.get("/{clip_id}")
async def get_clip(clip_id: int, db: Session = Depends(get_db)):
    """
    Returns single clip details with subtitle options.
    """
    c = db.query(Clip).filter(Clip.id == clip_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Clip not found.")

    return {
        "id": c.id,
        "project_id": c.project_id,
        "project_title": c.project.title if c.project else "Untitled",
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
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "subtitles": [
            {"id": s.id, "format": s.format, "url": f"/api/clips/{c.id}/subtitles?format={s.format}"}
            for s in c.subtitles
        ]
    }

@router.get("/{clip_id}/download")
async def download_clip_video(clip_id: int, db: Session = Depends(get_db)):
    """
    Downloads the MP4 video file of the clip.
    """
    c = db.query(Clip).filter(Clip.id == clip_id).first()
    if not c or not os.path.exists(c.file_path):
        raise HTTPException(status_code=404, detail="Clip video file not found on disk.")

    filename = f"clipforge_clip_{c.clip_number}_{os.path.basename(c.file_path)}"
    return FileResponse(
        c.file_path,
        media_type="video/mp4",
        filename=filename
    )

@router.get("/{clip_id}/subtitles")
async def download_clip_subtitles(clip_id: int, format: str = Query(default="srt"), db: Session = Depends(get_db)):
    """
    Downloads the standalone subtitle file (SRT or VTT) for the clip.
    """
    sub = db.query(Subtitle).filter(Subtitle.clip_id == clip_id, Subtitle.format == format.lower()).first()
    if not sub or not os.path.exists(sub.file_path):
        raise HTTPException(status_code=404, detail="Subtitle file not found.")

    return FileResponse(
        sub.file_path,
        media_type="text/plain",
        filename=f"clip_{clip_id}_subtitles.{format.lower()}"
    )

@router.delete("/{clip_id}")
async def delete_clip(clip_id: int, db: Session = Depends(get_db)):
    """
    Deletes the clip and its files from storage.
    """
    c = db.query(Clip).filter(Clip.id == clip_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Clip not found.")

    if c.file_path and os.path.exists(c.file_path):
        try:
            os.remove(c.file_path)
        except OSError:
            pass

    if c.thumbnail_path and os.path.exists(c.thumbnail_path):
        try:
            os.remove(c.thumbnail_path)
        except OSError:
            pass

    for s in c.subtitles:
        if s.file_path and os.path.exists(s.file_path):
            try:
                os.remove(s.file_path)
            except OSError:
                pass

    db.delete(c)
    db.commit()
    return {"success": True, "message": "Clip deleted successfully."}
