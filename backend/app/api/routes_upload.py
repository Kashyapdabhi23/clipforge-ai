import os
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.session import get_db
from app.models.models import Project, Video
from app.services.storage import save_upload_file, download_authorized_url
from app.video.ffmpeg_service import probe_video, generate_thumbnail
from app.core.config import THUMBNAILS_DIR
from app.core.logging import logger

router = APIRouter(prefix="/api", tags=["Upload"])

class UrlUploadRequest(BaseModel):
    url: str
    rapidapi_key: Optional[str] = None

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts video file upload, streams it to disk, probes metadata,
    creates Project & Video records and generates an initial thumbnail.
    """
    try:
        saved_path, original_filename, file_size = await save_upload_file(file)
        metadata = probe_video(saved_path)

        # Generate thumbnail
        thumb_name = f"thumb_{Path(saved_path).stem}.jpg"
        thumb_path = str(THUMBNAILS_DIR / thumb_name)
        generate_thumbnail(saved_path, thumb_path, min(2.0, metadata["duration"] * 0.2))

        # Create Project
        project = Project(
            title=Path(original_filename).stem,
            original_filename=original_filename,
            duration=metadata["duration"],
            thumbnail_path=thumb_path,
            status="CREATED"
        )
        db.add(project)
        db.flush()

        # Create Video record
        video_record = Video(
            project_id=project.id,
            filename=os.path.basename(saved_path),
            file_path=saved_path,
            file_size_bytes=file_size,
            duration=metadata["duration"],
            width=metadata["width"],
            height=metadata["height"],
            fps=metadata["fps"],
            format=metadata["format"]
        )
        db.add(video_record)
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "project_id": project.id,
            "video_id": video_record.id,
            "title": project.title,
            "filename": original_filename,
            "duration": metadata["duration"],
            "width": metadata["width"],
            "height": metadata["height"],
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "thumbnail_url": f"/static/thumbnails/{thumb_name}"
        }

    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload/url")
async def upload_video_url(
    payload: UrlUploadRequest,
    db: Session = Depends(get_db)
):
    """
    Ingests video from an authorized URL using terms-compliant public video ingestion.
    """
    url = payload.url.strip()
    if not url or not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL provided.")

    try:
        saved_path, title, file_size = download_authorized_url(url, payload.rapidapi_key)
        metadata = probe_video(saved_path)

        thumb_name = f"thumb_{Path(saved_path).stem}.jpg"
        thumb_path = str(THUMBNAILS_DIR / thumb_name)
        generate_thumbnail(saved_path, thumb_path, min(2.0, metadata["duration"] * 0.2))

        project = Project(
            title=title[:200],
            source_url=url,
            original_filename=os.path.basename(saved_path),
            duration=metadata["duration"],
            thumbnail_path=thumb_path,
            status="CREATED"
        )
        db.add(project)
        db.flush()

        video_record = Video(
            project_id=project.id,
            filename=os.path.basename(saved_path),
            file_path=saved_path,
            file_size_bytes=file_size,
            duration=metadata["duration"],
            width=metadata["width"],
            height=metadata["height"],
            fps=metadata["fps"],
            format=metadata["format"]
        )
        db.add(video_record)
        db.commit()
        db.refresh(project)

        return {
            "success": True,
            "project_id": project.id,
            "video_id": video_record.id,
            "title": project.title,
            "filename": os.path.basename(saved_path),
            "duration": metadata["duration"],
            "width": metadata["width"],
            "height": metadata["height"],
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "thumbnail_url": f"/static/thumbnails/{thumb_name}"
        }

    except Exception as e:
        logger.error(f"URL ingestion failed: {e}")
        err_str = str(e)
        if "10054" in err_str or "forcibly closed" in err_str or "youtube" in url.lower() or "youtu.be" in url.lower():
            friendly_msg = (
                "YouTube blocked automated download access (Connection Reset / Bot Gate). "
                "YouTube terms and security systems restrict automated scrapers from downloading directly. "
                "Please switch to the 'Upload Video File' tab to upload the video file directly from your computer for 100% reliable AI clipping."
            )
            raise HTTPException(status_code=400, detail=friendly_msg)
        raise HTTPException(status_code=400, detail=f"Failed to fetch video from URL: {err_str}")
