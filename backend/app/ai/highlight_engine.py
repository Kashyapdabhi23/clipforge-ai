import re
from typing import List, Dict, Any, Tuple
from scenedetect import open_video, SceneManager, ContentDetector
from app.core.logging import logger

# Engaging vocabulary across English, Hindi, and Gujarati
HIGHLIGHT_PATTERNS = {
    "questions": [
        r"\?", r"\bwhy\b", r"\bhow\b", r"\bwhat\b", r"\bwho\b", r"\bwhere\b", r"\bwhen\b",
        r"\bkya\b", r"\bkyu\b", r"\bkaise\b", r"\bkaun\b", r"\bkem\b", r"\bshu\b", r"\bkyare\b"
    ],
    "surprise_and_reactions": [
        r"!", r"\bwow\b", r"\bomg\b", r"\boh my god\b", r"\bunbelievable\b", r"\binsane\b",
        r"\bcrazy\b", r"\bshocking\b", r"\bnever\b", r"\blook at\b", r"\bsecret\b", r"\bmistake\b",
        r"\barrey\b", r"\byaar\b", r"\bzabardast\b", r"\bbhai\b", r"\bdekho\b", r"\bsach me\b",
        r"\bhadd hai\b", r"\bvato\b", r"\bvicharo\b", r"\bkharekhar\b", r"\bkamal\b"
    ],
    "excitement_and_energy": [
        r"\bawesome\b", r"\bamazing\b", r"\blegendary\b", r"\bepic\b", r"\bhuge\b", r"\bwinner\b",
        r"\bvictory\b", r"\bclutch\b", r"\bheadshot\b", r"\bkill\b", r"\bgame\b", r"\bplay\b",
        r"\bscore\b", r"\bmast\b", r"\bdhamaka\b", r"\bbawal\b", r"\btoofan\b", r"\brock\b"
    ],
    "storytelling_and_info": [
        r"\bthe truth is\b", r"\blisten\b", r"\bimportant\b", r"\brule\b", r"\btip\b",
        r"\bhack\b", r"\bfirst\b", r"\bfinally\b", r"\bsuddenly\b", r"\breason\b",
        r"\byad rakhna\b", r"\bdhyan se\b", r"\bkahani\b", r"\bkhabar\b", r"\bmahatvapurna\b"
    ]
}

def detect_scenes(video_path: str, threshold: float = 27.0) -> List[Tuple[float, float]]:
    """
    Detects scene boundaries in seconds using PySceneDetect ContentDetector.
    """
    try:
        logger.info(f"Detecting scenes in '{video_path}'...")
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()

        scenes = []
        for scene in scene_list:
            start_sec = scene[0].get_seconds()
            end_sec = scene[1].get_seconds()
            scenes.append((start_sec, end_sec))

        logger.info(f"Detected {len(scenes)} visual scene cuts.")
        return scenes
    except Exception as e:
        logger.warning(f"PySceneDetect encountered error: {e}. Falling back to time-based boundaries.")
        return []

def score_transcript_segment(text: str) -> Tuple[float, List[str]]:
    """
    Scores the interest and virality potential of a text transcript segment.
    Returns (score: 0-100, reasoning_tags: List[str]).
    """
    if not text or len(text.strip()) < 10:
        return 0.0, ["Insufficient Speech"]

    score = 20.0  # Base score for speech presence
    tags = []
    text_lower = text.lower()

    # Question & Answer pattern
    q_matches = sum(1 for p in HIGHLIGHT_PATTERNS["questions"] if re.search(p, text_lower))
    if q_matches > 0:
        score += min(25.0, q_matches * 8.0)
        tags.append("Q&A / Curiosity Hook")

    # Reaction / Surprise
    reaction_matches = sum(1 for p in HIGHLIGHT_PATTERNS["surprise_and_reactions"] if re.search(p, text_lower))
    if reaction_matches > 0:
        score += min(25.0, reaction_matches * 9.0)
        tags.append("Strong Reaction / Surprise")

    # Excitement / Gaming
    excitement_matches = sum(1 for p in HIGHLIGHT_PATTERNS["excitement_and_energy"] if re.search(p, text_lower))
    if excitement_matches > 0:
        score += min(25.0, excitement_matches * 8.0)
        tags.append("High Energy Moment")

    # Storytelling / Key Info
    story_matches = sum(1 for p in HIGHLIGHT_PATTERNS["storytelling_and_info"] if re.search(p, text_lower))
    if story_matches > 0:
        score += min(20.0, story_matches * 6.0)
        tags.append("Key Takeaway / Storytelling")

    # Exclamation count bonus
    exclams = text.count("!")
    if exclams > 0:
        score += min(15.0, exclams * 4.0)

    # Question marks
    q_marks = text.count("?")
    if q_marks > 0:
        score += min(15.0, q_marks * 5.0)

    return min(100.0, score), tags

def find_best_highlight_segments(
    video_duration: float,
    transcript_segments: List[Dict[str, Any]],
    scene_cuts: List[Tuple[float, float]],
    target_duration: float = 30.0,
    max_clips: int = 5
) -> List[Dict[str, Any]]:
    """
    Identifies high-potential, non-overlapping candidate segments throughout the video.
    Aligns start and end times to natural sentence boundaries or scene cuts.
    """
    if video_duration <= 0:
        return []

    # If video is shorter than target duration, clip is the entire video
    if video_duration <= target_duration:
        full_text = " ".join(s["text"] for s in transcript_segments)
        base_score, tags = score_transcript_segment(full_text)
        return [{
            "start": 0.0,
            "end": video_duration,
            "duration": video_duration,
            "score": round(max(50.0, base_score), 1),
            "reasoning": ", ".join(tags) or "Complete Source Video",
            "transcript": full_text
        }]

    candidates = []
    step = 5.0  # Sliding window step
    current_time = 0.0

    while current_time + (target_duration * 0.7) <= video_duration:
        window_start = current_time
        window_end = min(video_duration, window_start + target_duration)
        clip_len = window_end - window_start

        # Collect whisper segments within this window
        window_sub_segments = [
            s for s in transcript_segments
            if (s["start"] >= window_start - 2.0 and s["end"] <= window_end + 2.0)
        ]

        # Snap start/end to nearest speech segment boundary to avoid cut-off mid-sentence
        snapped_start = window_start
        snapped_end = window_end

        if window_sub_segments:
            # First segment starting near window_start
            first_seg = window_sub_segments[0]
            if abs(first_seg["start"] - window_start) <= 3.0:
                snapped_start = max(0.0, first_seg["start"])

            # Last segment ending near window_end
            last_seg = window_sub_segments[-1]
            if abs(last_seg["end"] - window_end) <= 3.0:
                snapped_end = min(video_duration, last_seg["end"])

        # Re-verify clip length
        actual_len = snapped_end - snapped_start
        if actual_len < 10.0:
            current_time += step
            continue

        window_text = " ".join(s["text"] for s in window_sub_segments)
        word_count = len(window_text.split())

        # Speech rate: ideal shorts speech is ~2.0 to 3.8 words per second
        words_per_sec = word_count / actual_len if actual_len > 0 else 0
        speech_density_score = 0.0
        if 1.5 <= words_per_sec <= 4.0:
            speech_density_score = 25.0
        elif words_per_sec > 0.5:
            speech_density_score = 15.0
        else:
            # Penalize long silent sections
            speech_density_score = 2.0

        # Transcript content score
        content_score, tags = score_transcript_segment(window_text)

        # Scene cut dynamics: short clips benefit from 1-4 visual scene cuts
        scenes_in_window = [
            cut for cut in scene_cuts
            if snapped_start <= cut[0] <= snapped_end
        ]
        scene_score = min(20.0, len(scenes_in_window) * 6.0)

        # Total combined score
        total_score = (content_score * 0.55) + (speech_density_score * 0.25) + (scene_score * 0.20)

        # Bonus for good hook at start (first 5 seconds of clip)
        first_few_words = " ".join(window_text.split()[:12])
        if any(re.search(p, first_few_words.lower()) for p in HIGHLIGHT_PATTERNS["questions"] + HIGHLIGHT_PATTERNS["surprise_and_reactions"]):
            total_score += 8.0
            tags.append("Strong Opening Hook")

        final_score = min(99.0, max(25.0, total_score))

        reasoning_str = " | ".join(tags) if tags else "Balanced engagement & visual activity"

        candidates.append({
            "start": round(snapped_start, 2),
            "end": round(snapped_end, 2),
            "duration": round(actual_len, 2),
            "score": round(final_score, 1),
            "reasoning": reasoning_str,
            "transcript": window_text,
            "sub_segments": window_sub_segments
        })

        current_time += step

    # Sort candidates by highlight score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Greedily pick top non-overlapping clips
    selected_clips = []
    min_separation = target_duration * 0.6  # Allow slight overlap only if high quality, prefer diverse moments

    for cand in candidates:
        if len(selected_clips) >= max_clips:
            break

        # Check overlap with already chosen clips
        has_overlap = False
        for chosen in selected_clips:
            overlap_start = max(cand["start"], chosen["start"])
            overlap_end = min(cand["end"], chosen["end"])
            overlap_len = max(0.0, overlap_end - overlap_start)

            if overlap_len > (target_duration * 0.35):
                has_overlap = True
                break

        if not has_overlap:
            selected_clips.append(cand)

    # Sort selected clips chronologically by start time
    selected_clips.sort(key=lambda x: x["start"])

    # If the video has very little speech or activity, ensure at least 1-2 clips are generated
    if not selected_clips and video_duration > 5.0:
        chunk_len = min(video_duration, target_duration)
        selected_clips.append({
            "start": 0.0,
            "end": chunk_len,
            "duration": chunk_len,
            "score": 55.0,
            "reasoning": "Opening video highlight",
            "transcript": " ".join(s["text"] for s in transcript_segments[:5]),
            "sub_segments": transcript_segments[:5]
        })

    logger.info(f"Selected {len(selected_clips)} high-quality highlight clips from {len(candidates)} candidates.")
    return selected_clips
