import os
from typing import List, Dict, Any, Optional
from faster_whisper import WhisperModel

from app.core.config import WHISPER_MODEL_NAME, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, WHISPER_CPU_THREADS
from app.core.logging import logger

_model_instance: Optional[WhisperModel] = None

def get_whisper_model() -> WhisperModel:
    """
    Lazy-loads Whisper model instance with INT8 CPU quantization.
    Memory footprint for 'tiny' model is ~75 MB RAM.
    """
    global _model_instance
    if _model_instance is None:
        logger.info(f"Loading faster-whisper '{WHISPER_MODEL_NAME}' on {WHISPER_DEVICE} ({WHISPER_COMPUTE_TYPE})...")
        _model_instance = WhisperModel(
            model_size_or_path=WHISPER_MODEL_NAME,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
            cpu_threads=WHISPER_CPU_THREADS,
            num_workers=1
        )
        logger.info("faster-whisper model successfully initialized.")
    return _model_instance

def transcribe_audio(audio_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribes audio file using faster-whisper.
    Returns:
        {
            "language": detected_language,
            "language_probability": prob,
            "duration": total_audio_duration,
            "segments": [
                {
                    "id": int,
                    "start": float,
                    "end": float,
                    "text": str,
                    "words": [{"word": str, "start": float, "end": float, "probability": float}]
                }
            ],
            "full_text": str
        }
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = get_whisper_model()
    lang_param = None if language in (None, "auto", "") else language

    logger.info(f"Transcribing audio '{audio_path}' (target language: {lang_param or 'auto'})...")

    segments_generator, info = model.transcribe(
        audio_path,
        language=lang_param,
        beam_size=1,  # Greedy search for fastest CPU execution
        word_timestamps=True,
        vad_filter=True,  # Filter out silence
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    segments_list = []
    full_text_parts = []

    for seg in segments_generator:
        words_data = []
        if seg.words:
            for w in seg.words:
                words_data.append({
                    "word": w.word,
                    "start": w.start,
                    "end": w.end,
                    "probability": w.probability
                })

        segments_list.append({
            "id": seg.id,
            "start": float(seg.start),
            "end": float(seg.end),
            "text": seg.text.strip(),
            "words": words_data
        })
        full_text_parts.append(seg.text.strip())

    logger.info(f"Transcription complete: {len(segments_list)} segments found. Detected language: {info.language} ({info.language_probability:.2f})")

    return {
        "language": info.language,
        "language_probability": float(info.language_probability),
        "duration": float(info.duration),
        "segments": segments_list,
        "full_text": " ".join(full_text_parts)
    }
