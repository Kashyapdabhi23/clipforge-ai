import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional
import av
import cv2

from app.core.config import FFMPEG_PATH, FFMPEG_PRESET, FFMPEG_THREADS
from app.core.logging import logger

def probe_video(video_path: str) -> Dict[str, Any]:
    """
    Probes video metadata using PyAV / OpenCV without external ffprobe dependency.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    file_size = os.path.getsize(video_path)
    metadata = {
        "duration": 0.0,
        "width": 0,
        "height": 0,
        "fps": 30.0,
        "has_audio": False,
        "file_size": file_size,
        "format": Path(video_path).suffix.lstrip(".").lower()
    }

    try:
        container = av.open(video_path)
        if container.duration is not None:
            metadata["duration"] = float(container.duration / av.time_base)

        video_streams = container.streams.video
        if video_streams:
            vs = video_streams[0]
            metadata["width"] = vs.width or 0
            metadata["height"] = vs.height or 0
            if vs.average_rate:
                metadata["fps"] = float(vs.average_rate)

        audio_streams = container.streams.audio
        if audio_streams and len(audio_streams) > 0:
            metadata["has_audio"] = True

        container.close()
    except Exception as e:
        logger.warning(f"PyAV probe failed, falling back to OpenCV: {e}")
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                metadata["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                metadata["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                metadata["fps"] = float(cap.get(cv2.CAP_PROP_FPS)) or 30.0
                frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                if metadata["fps"] > 0 and frame_count > 0:
                    metadata["duration"] = frame_count / metadata["fps"]
                cap.release()
        except Exception as e2:
            logger.error(f"OpenCV probe also failed: {e2}")

    return metadata

def extract_audio(video_path: str, output_audio_path: str, duration: float = 30.0) -> str:
    """
    Extracts 16kHz mono 16-bit PCM WAV audio for faster-whisper speech recognition.
    If the video has no audio track, generates a clean silent audio WAV so the AI pipeline continues safely.
    """
    os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        output_audio_path
    ]
    logger.info(f"Extracting audio: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.warning(f"No audio stream detected in source video. Generating silent track for processing: {result.stderr[-200:]}")
        # Generate silent audio track matching video duration or 60s
        silence_dur = max(1.0, min(duration, 300.0))
        silent_cmd = [
            FFMPEG_PATH,
            "-y",
            "-f", "lavfi",
            "-i", "anullsrc=r=16000:cl=mono",
            "-t", f"{silence_dur:.1f}",
            "-acodec", "pcm_s16le",
            output_audio_path
        ]
        sub_res = subprocess.run(silent_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if sub_res.returncode != 0:
            raise RuntimeError(f"Failed to generate fallback audio: {sub_res.stderr[-200:]}")

    return output_audio_path

def generate_thumbnail(video_path: str, output_thumb_path: str, timestamp: float = 1.0) -> str:
    """
    Generates a JPEG thumbnail from the video at the given timestamp.
    """
    os.makedirs(os.path.dirname(output_thumb_path), exist_ok=True)
    cmd = [
        FFMPEG_PATH,
        "-y",
        "-ss", str(max(0.0, timestamp)),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "3",
        output_thumb_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.warning(f"FFmpeg thumbnail generation failed at timestamp {timestamp}: {result.stderr}")
        cmd[2] = "0.0"
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return output_thumb_path

def build_crop_filter(aspect_ratio: str, width: int, height: int, subtitle_path: Optional[str] = None) -> str:
    """
    Builds FFmpeg video filter chain for intelligent cropping & subtitle burning.
    """
    filters = []

    if aspect_ratio == "9:16":
        in_ratio = (width / height) if height > 0 else (16 / 9)
        target_ratio = 9.0 / 16.0  # 0.5625

        if in_ratio > target_ratio:
            filters.append("crop=ih*(9/16):ih:(iw-ow)/2:0")
            filters.append("scale=1080:1920:flags=lanczos")
        else:
            filters.append("scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos")
            filters.append("crop=1080:1920")

        # Subtle unsharp filter for crisp facial and gaming detail on vertical reframing
        filters.append("unsharp=3:3:0.4:3:3:0.0")

    elif aspect_ratio == "1:1":
        filters.append("crop=min(iw\\,ih):min(iw\\,ih):(iw-ow)/2:(ih-oh)/2")
        filters.append("scale=1080:1080:flags=lanczos")
        filters.append("unsharp=3:3:0.4:3:3:0.0")

    elif aspect_ratio == "16:9":
        filters.append("scale=1920:1080:flags=lanczos")

    else:
        filters.append("scale=1080:1920:flags=lanczos")

    if subtitle_path and os.path.exists(subtitle_path):
        safe_sub_path = subtitle_path.replace("\\", "/").replace(":", "\\:")
        filters.append(f"subtitles='{safe_sub_path}'")

    return ",".join(filters)

def render_clip(
    input_video: str,
    start_time: float,
    duration: float,
    output_path: str,
    aspect_ratio: str = "9:16",
    subtitle_ass_path: Optional[str] = None,
    width: int = 1920,
    height: int = 1080
) -> str:
    """
    Renders vertical short video clip using FFmpeg with ultrafast preset.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    filter_chain = build_crop_filter(aspect_ratio, width, height, subtitle_ass_path)

    cmd = [
        FFMPEG_PATH,
        "-y",
        "-ss", f"{start_time:.3f}",
        "-t", f"{duration:.3f}",
        "-i", input_video,
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-preset", FFMPEG_PRESET,
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-threads", str(FFMPEG_THREADS),
        output_path
    ]

    logger.info(f"Rendering clip: start={start_time:.1f}s, duration={duration:.1f}s, out={output_path}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        logger.warning(f"Clip rendering with subtitles filter failed or no audio stream, trying fallback: {result.stderr[-300:]}")
        # Try without subtitle filter, or without audio if input had no audio
        clean_filter = build_crop_filter(aspect_ratio, width, height, None)
        cmd_fallback = [
            FFMPEG_PATH,
            "-y",
            "-ss", f"{start_time:.3f}",
            "-t", f"{duration:.3f}",
            "-i", input_video,
            "-vf", clean_filter,
            "-c:v", "libx264",
            "-preset", FFMPEG_PRESET,
            "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-threads", str(FFMPEG_THREADS),
            output_path
        ]
        res_fallback = subprocess.run(cmd_fallback, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_fallback.returncode != 0:
            raise RuntimeError(f"Rendering failed: {res_fallback.stderr[-300:]}")

    return output_path
