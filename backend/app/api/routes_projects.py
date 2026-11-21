import os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.models import Project, Video, Clip

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("")
async def list_projects(db: Session = Depends(get_db)):
    """
    Returns list of all projects with clip count, duration, thumbnail, and status.
    """
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        results.append({
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "original_filename": p.original_filename,
            "source_url": p.source_url,
            "duration": p.duration,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "thumbnail_url": f"/static/thumbnails/{os.path.basename(p.thumbnail_path)}" if p.thumbnail_path else None,
            "clip_count": len(p.clips)
        })
    return results

@router.get("/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """
    Returns a single project with all its generated clips.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    clips_data = []
    for c in p.clips:
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
        "id": p.id,
        "title": p.title,
        "description": p.description,
        "original_filename": p.original_filename,
        "source_url": p.source_url,
        "duration": p.duration,
        "status": p.status,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "thumbnail_url": f"/static/thumbnails/{os.path.basename(p.thumbnail_path)}" if p.thumbnail_path else None,
        "clip_count": len(clips_data),
        "clips": clips_data
    }

@router.delete("/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    Deletes project, all associated clips, and cleans up video files from storage.
    """
    p = db.query(Project).filter(Project.id == project_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found.")

    # Remove files
    for v in p.videos:
        if v.file_path and os.path.exists(v.file_path):
            try:
                os.remove(v.file_path)
            except OSError:
                pass

    for c in p.clips:
        if c.file_path and os.path.exists(c.file_path):
            try:
                os.remove(c.file_path)
            except OSError:
                pass
        for s in c.subtitles:
            if s.file_path and os.path.exists(s.file_path):
                try:
                    os.remove(s.file_path)
                except OSError:
                    pass

    db.delete(p)
    db.commit()
    return {"success": True, "message": "Project and associated clips deleted successfully."}
