import os
import asyncio
import datetime
import uuid
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.config import TEMP_DIR, CLIPS_DIR, THUMBNAILS_DIR
from app.core.logging import logger
from app.database.session import SessionLocal
from app.models.models import ProcessingJob, Project, Video, Clip, Subtitle
from app.video.ffmpeg_service import probe_video, extract_audio, generate_thumbnail, render_clip
from app.video.subtitles import generate_srt, generate_vtt, generate_ass
from app.ai.whisper_service import transcribe_audio
from app.ai.highlight_engine import detect_scenes, find_best_highlight_segments
from app.services.storage import cleanup_temp_files

# Concurrency semaphore: only 1 heavy video processing task runs concurrently
job_semaphore = asyncio.Semaphore(1)

def update_job_progress(job_id: str, step: str, progress: float, error_message: Optional[str] = None):
    db = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.current_step = step
            job.progress = min(100.0, max(0.0, progress))
            if error_message:
                job.error_message = error_message
                job.status = "FAILED"
            elif step == "completed":
                job.status = "COMPLETED"
                job.completed_at = datetime.datetime.utcnow()
            else:
                job.status = "PROCESSING"
            db.commit()
    except Exception as e:
        logger.error(f"Error updating job {job_id} in db: {e}")
    finally:
        db.close()

async def execute_processing_pipeline(job_id: str):
    """
    Executes the full end-to-end AI video clipping pipeline.
    Runs inside a semaphore to protect 8GB RAM PC from CPU exhaustion.
    """
    async with job_semaphore:
        logger.info(f"Starting execution of job {job_id}")
        db = SessionLocal()
        temp_files_to_clean = []

        try:
            job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found in database.")
                return

            job.status = "PROCESSING"
            job.started_at = datetime.datetime.utcnow()
            db.commit()

            project = db.query(Project).filter(Project.id == job.project_id).first()
            video = db.query(Video).filter(Video.project_id == project.id).first()
            if not video or not os.path.exists(video.file_path):
                raise FileNotFoundError(f"Source video file not found for project {project.id}")

            source_video_path = video.file_path
            clip_duration = float(job.clip_duration or 30)
            requested_clips = int(job.requested_clips or 5)
            aspect_ratio = job.aspect_ratio or "9:16"
            target_lang = job.language or "auto"
            caption_style = job.caption_style or "Modern"

            # ---------------------------------------------------------------
            # Step 1: Probe video & Extract Audio
            # ---------------------------------------------------------------
            update_job_progress(job_id, "extracting_audio", 10.0)
            temp_audio_path = str(TEMP_DIR / f"{job_id}_audio.wav")
            temp_files_to_clean.append(temp_audio_path)

            await asyncio.to_thread(extract_audio, source_video_path, temp_audio_path, video.duration)
            update_job_progress(job_id, "extracting_audio", 20.0)

            # ---------------------------------------------------------------
            # Step 2: Transcribe Audio using faster-whisper (tiny INT8 CPU)
            # ---------------------------------------------------------------
            update_job_progress(job_id, "transcribing", 25.0)
            transcription_result = await asyncio.to_thread(transcribe_audio, temp_audio_path, target_lang)
            transcript_segments = transcription_result.get("segments", [])
            update_job_progress(job_id, "transcribing", 40.0)

            # ---------------------------------------------------------------
            # Step 3: Detect Scenes using PySceneDetect
            # ---------------------------------------------------------------
            update_job_progress(job_id, "detecting_scenes", 45.0)
            scene_cuts = await asyncio.to_thread(detect_scenes, source_video_path)
            update_job_progress(job_id, "detecting_scenes", 55.0)

            # ---------------------------------------------------------------
            # Step 4 & 5: Analyze Highlights & Select Best Segments
            # ---------------------------------------------------------------
            update_job_progress(job_id, "analyzing_highlights", 60.0)
            selected_segments = await asyncio.to_thread(
                find_best_highlight_segments,
                video.duration,
                transcript_segments,
                scene_cuts,
                target_duration=clip_duration,
                max_clips=requested_clips
            )
            update_job_progress(job_id, "selecting_clips", 68.0)

            if not selected_segments:
                raise ValueError("No viable highlight segments could be identified from this video.")

            # ---------------------------------------------------------------
            # Step 6: Render each clip & Generate Subtitles
            # ---------------------------------------------------------------
            update_job_progress(job_id, "rendering_clips", 70.0)
            total_clips_to_render = len(selected_segments)
            rendered_clips_records = []

            for idx, seg in enumerate(selected_segments):
                clip_num = idx + 1
                clip_start = seg["start"]
                clip_end = seg["end"]
                clip_dur = seg["duration"]
                clip_score = seg["score"]
                clip_reasoning = seg["reasoning"]
                clip_text = seg["transcript"]
                sub_segs = seg.get("sub_segments", [])

                clip_uid = uuid.uuid4().hex[:8]
                clip_filename = f"clip_{project.id}_{clip_num}_{clip_uid}.mp4"
                clip_output_path = str(CLIPS_DIR / clip_filename)

                # Generate Subtitles
                srt_content = generate_srt(sub_segs, offset_start=clip_start)
                vtt_content = generate_vtt(sub_segs, offset_start=clip_start)
                ass_content = generate_ass(sub_segs, offset_start=clip_start, style_name=caption_style)

                ass_file_path = str(TEMP_DIR / f"{job_id}_clip_{clip_num}.ass")
                srt_file_path = str(CLIPS_DIR / f"clip_{project.id}_{clip_num}_{clip_uid}.srt")
                vtt_file_path = str(CLIPS_DIR / f"clip_{project.id}_{clip_num}_{clip_uid}.vtt")
                temp_files_to_clean.append(ass_file_path)

                with open(ass_file_path, "w", encoding="utf-8") as f:
                    f.write(ass_content)
                with open(srt_file_path, "w", encoding="utf-8") as f:
                    f.write(srt_content)
                with open(vtt_file_path, "w", encoding="utf-8") as f:
                    f.write(vtt_content)

                # Render Vertical Clip with Subtitles
                await asyncio.to_thread(
                    render_clip,
                    source_video_path,
                    clip_start,
                    clip_dur,
                    clip_output_path,
                    aspect_ratio=aspect_ratio,
                    subtitle_ass_path=ass_file_path,
                    width=video.width,
                    height=video.height
                )

                # Generate Thumbnail for Clip
                clip_thumb_filename = f"thumb_clip_{project.id}_{clip_num}_{clip_uid}.jpg"
                clip_thumb_path = str(THUMBNAILS_DIR / clip_thumb_filename)
                await asyncio.to_thread(generate_thumbnail, clip_output_path, clip_thumb_path, 0.5)

                # Title generation based on transcript snippet or highlight theme
                first_words = " ".join(clip_text.split()[:6]) if clip_text else f"Highlight Moment #{clip_num}"
                clip_title = f"Clip #{clip_num}: {first_words.strip()}"

                # Save Clip Record
                clip_record = Clip(
                    project_id=project.id,
                    job_id=job_id,
                    clip_number=clip_num,
                    title=clip_title,
                    start_time=clip_start,
                    end_time=clip_end,
                    duration=clip_dur,
                    highlight_score=clip_score,
                    reasoning=clip_reasoning,
                    transcript=clip_text,
                    file_path=clip_output_path,
                    thumbnail_path=clip_thumb_path,
                    aspect_ratio=aspect_ratio,
                    width=1080 if aspect_ratio == "9:16" else (1920 if aspect_ratio == "16:9" else 1080),
                    height=1920 if aspect_ratio == "9:16" else (1080 if aspect_ratio == "16:9" else 1080)
                )
                db.add(clip_record)
                db.flush()

                # Add Subtitle records
                sub_srt = Subtitle(clip_id=clip_record.id, format="srt", file_path=srt_file_path, content=srt_content)
                sub_vtt = Subtitle(clip_id=clip_record.id, format="vtt", file_path=vtt_file_path, content=vtt_content)
                db.add(sub_srt)
                db.add(sub_vtt)
                db.commit()

                # Update progress incrementally
                rendered_percent = 70.0 + ((idx + 1) / total_clips_to_render) * 25.0
                update_job_progress(job_id, "rendering_clips", rendered_percent)

            # Update project status
            project.status = "COMPLETED"
            db.commit()

            # Mark Completed
            update_job_progress(job_id, "completed", 100.0)
            logger.info(f"Job {job_id} successfully completed. Generated {total_clips_to_render} clips.")

        except Exception as e:
            logger.exception(f"Job {job_id} failed with error: {e}")
            update_job_progress(job_id, "failed", 0.0, error_message=str(e))
        finally:
            cleanup_temp_files(temp_files_to_clean)
            db.close()
