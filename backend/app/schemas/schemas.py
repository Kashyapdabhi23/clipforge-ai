from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# Request Schemas
class CreateJobRequest(BaseModel):
    project_id: Optional[int] = None
    video_id: Optional[int] = None
    source_url: Optional[str] = None
    clip_duration: int = Field(default=30, ge=10, le=90)
    requested_clips: int = Field(default=5, ge=1, le=30)
    aspect_ratio: str = Field(default="9:16")  # 9:16, 1:1, 16:9
    language: str = Field(default="auto")  # auto, hi, en, gu
    caption_style: str = Field(default="Modern")  # Modern, Bold, Minimal, Gaming, Podcast

class SubtitleItem(BaseModel):
    id: int
    format: str
    file_path: str

    class Config:
        from_attributes = True

class ClipResponse(BaseModel):
    id: int
    project_id: int
    job_id: Optional[str]
    clip_number: int
    title: str
    start_time: float
    end_time: float
    duration: float
    highlight_score: float
    reasoning: Optional[str] = None
    transcript: Optional[str] = None
    file_path: str
    thumbnail_path: Optional[str] = None
    aspect_ratio: str
    width: int
    height: int
    created_at: datetime
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    subtitles: List[SubtitleItem] = []

    class Config:
        from_attributes = True

class ProcessingJobResponse(BaseModel):
    id: str
    project_id: int
    status: str
    current_step: str
    progress: float
    error_message: Optional[str] = None
    clip_duration: int
    requested_clips: int
    aspect_ratio: str
    language: str
    caption_style: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    clips: List[ClipResponse] = []

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    original_filename: Optional[str] = None
    source_url: Optional[str] = None
    duration: float
    thumbnail_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    clip_count: int = 0
    clips: List[ClipResponse] = []

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_projects: int
    total_clips: int
    processing_jobs: int
    completed_jobs: int
    storage_used_mb: float

class HealthResponse(BaseModel):
    status: str
    ffmpeg_available: bool
    whisper_available: bool
    version: str
