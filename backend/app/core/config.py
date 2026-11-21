import os
from pathlib import Path
import imageio_ffmpeg

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
CLIPS_DIR = STORAGE_DIR / "clips"
PROCESSED_DIR = STORAGE_DIR / "processed"
TEMP_DIR = STORAGE_DIR / "temp"
THUMBNAILS_DIR = STORAGE_DIR / "thumbnails"

for d in [STORAGE_DIR, UPLOADS_DIR, CLIPS_DIR, PROCESSED_DIR, TEMP_DIR, THUMBNAILS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DB_PATH = BASE_DIR / "clipforge.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

try:
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_PATH = "ffmpeg"

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm"}
MAX_UPLOAD_SIZE_MB = 10240  # 10 GB max video upload

# CPU Optimization for 8GB RAM / Core i5 7th Gen
WHISPER_MODEL_NAME = "tiny"
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"
WHISPER_CPU_THREADS = 4
FFMPEG_PRESET = "ultrafast"
FFMPEG_THREADS = 2
MAX_CONCURRENT_JOBS = 1

# Permanent RapidAPI Key for YouTube Downloader
RAPIDAPI_KEY = "87b03191b7msh0cb73dee47495ccp186ff6jsn2c0a2eed2f31"
