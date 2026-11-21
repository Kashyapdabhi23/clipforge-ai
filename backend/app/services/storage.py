import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
import aiofiles
from fastapi import UploadFile

from app.core.config import UPLOADS_DIR, TEMP_DIR, CLIPS_DIR, THUMBNAILS_DIR, STORAGE_DIR, ALLOWED_EXTENSIONS, RAPIDAPI_KEY
from app.core.logging import logger

async def save_upload_file(upload_file: UploadFile) -> Tuple[str, str, int]:
    """
    Streams uploaded file chunk-by-chunk to disk to prevent RAM bloat on 8GB RAM machines.
    Returns: (saved_file_path, original_filename, file_size_bytes)
    """
    ext = Path(upload_file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file format '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    unique_filename = f"{uuid.uuid4().hex[:12]}_{upload_file.filename}"
    destination_path = UPLOADS_DIR / unique_filename

    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB stream buffer

    async with aiofiles.open(destination_path, "wb") as out_file:
        while content := await upload_file.read(chunk_size):
            total_bytes += len(content)
            await out_file.write(content)

    logger.info(f"Saved uploaded file: {destination_path} ({total_bytes / (1024*1024):.2f} MB)")
    return str(destination_path), upload_file.filename, total_bytes

def download_direct_stream(url: str) -> Tuple[str, str, int]:
    """
    Downloads direct video link (.mp4, .mov, .webm) via chunked streaming with requests.
    """
    import requests
    unique_id = uuid.uuid4().hex[:12]
    ext = ".mp4"
    for e in [".mp4", ".mov", ".mkv", ".webm"]:
        if e in url.lower():
            ext = e
            break

    dest = UPLOADS_DIR / f"{unique_id}_stream{ext}"
    logger.info(f"Downloading direct video stream: {url}")
    total_bytes = 0
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "Mozilla/5.0"}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)

    title = Path(url.split("?")[0]).stem or "Online Video"
    return str(dest), title, total_bytes

def download_authorized_url(url: str, rapidapi_key: Optional[str] = None) -> Tuple[str, str, int]:
    """
    Ingests an authorized video URL (direct MP4/web video or terms-compliant public link).
    """
    # If direct video link, download via HTTP streaming directly
    clean_url = url.split("?")[0].lower()
    if clean_url.endswith((".mp4", ".mov", ".mkv", ".webm")):
        return download_direct_stream(url)

    # Check if RapidAPI key is provided via param or config
    api_key = rapidapi_key or RAPIDAPI_KEY or os.getenv("RAPIDAPI_KEY")
    if api_key and ("youtube.com" in url or "youtu.be" in url):
        import requests
        import re
        # Extract YouTube Video ID
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", url)
        if match:
            video_id = match.group(1)
            logger.info(f"Fetching video {video_id} via RapidAPI downloader...")
            try:
                rapid_url = "https://youtube-media-downloader.p.rapidapi.com/v2/video/details"
                headers = {
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "youtube-media-downloader.p.rapidapi.com"
                }
                res = requests.get(rapid_url, headers=headers, params={"videoId": video_id}, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    title = data.get("title", "YouTube Video")
                    streams = data.get("videos", {}).get("items", [])
                    if streams:
                        download_url = streams[0].get("url")
                        return download_direct_stream(download_url)
            except Exception as e:
                logger.warning(f"RapidAPI endpoint 1 failed: {e}")

            try:
                # Fallback to yt-api RapidAPI
                yt_api_url = "https://yt-api.p.rapidapi.com/dl"
                headers2 = {
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "yt-api.p.rapidapi.com"
                }
                res2 = requests.get(yt_api_url, headers=headers2, params={"id": video_id}, timeout=15)
                if res2.status_code == 200:
                    d2 = res2.json()
                    title = d2.get("title", "YouTube Video")
                    formats = d2.get("formats", [])
                    if formats:
                        return download_direct_stream(formats[0].get("url"))
            except Exception as e:
                logger.warning(f"RapidAPI endpoint 2 failed: {e}")

    import yt_dlp

    unique_id = uuid.uuid4().hex[:12]
    out_tmpl = str(UPLOADS_DIR / f"{unique_id}_%(title).50s.%(ext)s")

    ydl_opts = {
        "outtmpl": out_tmpl,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": 10 * 1024 * 1024 * 1024,  # 10 GB limit
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "ios", "mweb"],
                "player_skip": ["webpage", "configs"]
            }
        },
        "http_headers": {
            "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 14; en_US; Pixel 8 Pro Build/UQ1A.240205.004) gzip"
        }
    }

    logger.info(f"Downloading authorized URL: {url}")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # In case extension changed
        if not os.path.exists(filename):
            base_p = str(Path(filename).with_suffix(""))
            for ext in [".mp4", ".mkv", ".webm"]:
                if os.path.exists(base_p + ext):
                    filename = base_p + ext
                    break

        file_size = os.path.getsize(filename)
        title = info.get("title", "Online Video")
        return filename, title, file_size

def get_storage_stats() -> float:
    """
    Returns total storage usage in MB across the storage directory.
    """
    total_bytes = 0
    for root, _, files in os.walk(STORAGE_DIR):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(fp)
            except OSError:
                pass
    return round(total_bytes / (1024 * 1024), 2)

def cleanup_temp_files(file_paths: list):
    """
    Removes temporary audio/ass/intermediate files after rendering.
    """
    for fp in file_paths:
        try:
            if fp and os.path.exists(fp):
                os.remove(fp)
                logger.debug(f"Cleaned up temp file: {fp}")
        except Exception as e:
            logger.warning(f"Failed to delete temp file {fp}: {e}")
