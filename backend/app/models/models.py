import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False, default="user")
    email = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=True)
    source_url = Column(String(1024), nullable=True)
    duration = Column(Float, default=0.0)
    thumbnail_path = Column(String(512), nullable=True)
    status = Column(String(50), default="CREATED")  # CREATED, PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="projects")
    videos = relationship("Video", back_populates="project", cascade="all, delete-orphan")
    jobs = relationship("ProcessingJob", back_populates="project", cascade="all, delete-orphan")
    clips = relationship("Clip", back_populates="project", cascade="all, delete-orphan")

class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, default=0)
    duration = Column(Float, default=0.0)
    width = Column(Integer, default=0)
    height = Column(Integer, default=0)
    fps = Column(Float, default=0.0)
    format = Column(String(50), default="mp4")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="videos")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(64), primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    status = Column(String(50), default="QUEUED")  # QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED
    current_step = Column(String(100), default="queued")
    # Steps: queued, audio_extraction, transcribing, scene_detection, highlight_analysis, selecting_clips, rendering_clips, generating_subtitles, completed
    progress = Column(Float, default=0.0)  # 0 to 100
    error_message = Column(Text, nullable=True)
    
    # Configuration JSON or separate columns
    clip_duration = Column(Integer, default=30)
    requested_clips = Column(Integer, default=5)
    aspect_ratio = Column(String(20), default="9:16")
    language = Column(String(20), default="auto")
    caption_style = Column(String(50), default="Modern")
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="jobs")
    clips = relationship("Clip", back_populates="job", cascade="all, delete-orphan")

class Clip(Base):
    __tablename__ = "clips"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    job_id = Column(String(64), ForeignKey("processing_jobs.id"), nullable=True)
    clip_number = Column(Integer, default=1)
    title = Column(String(255), default="")
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    highlight_score = Column(Float, default=0.0)
    reasoning = Column(Text, nullable=True)
    transcript = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=False)
    thumbnail_path = Column(String(512), nullable=True)
    aspect_ratio = Column(String(20), default="9:16")
    width = Column(Integer, default=1080)
    height = Column(Integer, default=1920)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="clips")
    job = relationship("ProcessingJob", back_populates="clips")
    subtitles = relationship("Subtitle", back_populates="clip", cascade="all, delete-orphan")

class Subtitle(Base):
    __tablename__ = "subtitles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    clip_id = Column(Integer, ForeignKey("clips.id"), nullable=False)
    format = Column(String(20), default="srt")  # srt, vtt, ass
    file_path = Column(String(512), nullable=False)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    clip = relationship("Clip", back_populates="subtitles")
