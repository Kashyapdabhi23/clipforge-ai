import os
from pathlib import Path
from typing import List, Dict, Any

def format_timestamp_srt(seconds: float) -> str:
    millis = int((seconds % 1) * 1000)
    secs = int(seconds)
    hours = secs // 3600
    mins = (secs % 3600) // 60
    secs = secs % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    millis = int((seconds % 1) * 1000)
    secs = int(seconds)
    hours = secs // 3600
    mins = (secs % 3600) // 60
    secs = secs % 60
    return f"{hours:02d}:{mins:02d}:{secs:02d}.{millis:03d}"

def format_timestamp_ass(seconds: float) -> str:
    centis = int((seconds % 1) * 100)
    secs = int(seconds)
    hours = secs // 3600
    mins = (secs % 3600) // 60
    secs = secs % 60
    return f"{hours:01d}:{mins:02d}:{secs:02d}.{centis:02d}"

def generate_srt(segments: List[Dict[str, Any]], offset_start: float = 0.0) -> str:
    """
    Generates standard SRT subtitle text from whisper segments.
    offset_start: subtracted from timestamps so subtitle is relative to clip start.
    """
    lines = []
    idx = 1
    for seg in segments:
        s = max(0.0, seg["start"] - offset_start)
        e = max(s + 0.5, seg["end"] - offset_start)
        text = seg["text"].strip()
        if not text:
            continue
        lines.append(str(idx))
        lines.append(f"{format_timestamp_srt(s)} --> {format_timestamp_srt(e)}")
        lines.append(text)
        lines.append("")
        idx += 1
    return "\n".join(lines)

def generate_vtt(segments: List[Dict[str, Any]], offset_start: float = 0.0) -> str:
    lines = ["WEBVTT", ""]
    for seg in segments:
        s = max(0.0, seg["start"] - offset_start)
        e = max(s + 0.5, seg["end"] - offset_start)
        text = seg["text"].strip()
        if not text:
            continue
        lines.append(f"{format_timestamp_vtt(s)} --> {format_timestamp_vtt(e)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)

def generate_ass(segments: List[Dict[str, Any]], offset_start: float = 0.0, style_name: str = "Modern", video_width: int = 1080, video_height: int = 1920) -> str:
    """
    Generates Advanced SubStation Alpha (.ass) format with custom styling.
    Styles: Modern, Bold, Minimal, Gaming, Podcast
    """
    # Color format in ASS: &HAABBGGRR (Hex)
    if style_name == "Bold":
        # Bright yellow with thick black outline
        primary_color = "&H0000FFFF"  # Yellow in BGR
        outline_color = "&H00000000"  # Black
        font_size = 56
        bold = 1
        outline_size = 4
        shadow_size = 2
    elif style_name == "Gaming":
        # Neon cyan with dark border and green shadow
        primary_color = "&H00FFFF00"  # Cyan in BGR
        outline_color = "&H00101010"
        font_size = 54
        bold = 1
        outline_size = 4
        shadow_size = 3
    elif style_name == "Minimal":
        # Crisp white with thin clean outline
        primary_color = "&H00FFFFFF"
        outline_color = "&H00202020"
        font_size = 48
        bold = 0
        outline_size = 2
        shadow_size = 1
    elif style_name == "Podcast":
        # Soft cream text with subtle backing
        primary_color = "&H00E0F0FF"
        outline_color = "&H001A1A1A"
        font_size = 50
        bold = 1
        outline_size = 3
        shadow_size = 2
    else:  # Modern (Default)
        # Clean vibrant white with purple/dark glow outline
        primary_color = "&H00FFFFFF"
        outline_color = "&H002A1A10"
        font_size = 52
        bold = 1
        outline_size = 3
        shadow_size = 2

    # ASS Header
    ass_content = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,100,100,1,0,1,{outline_size},{shadow_size},2,40,40,280,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for seg in segments:
        s = max(0.0, seg["start"] - offset_start)
        e = max(s + 0.4, seg["end"] - offset_start)
        text = seg["text"].strip().replace("\n", " ")
        if not text:
            continue
        # Split very long sentences into 2 lines for 9:16 vertical readability
        words = text.split()
        if len(words) > 7:
            mid = len(words) // 2
            text = " ".join(words[:mid]) + "\\N" + " ".join(words[mid:])
        events.append(f"Dialogue: 0,{format_timestamp_ass(s)},{format_timestamp_ass(e)},Default,,0,0,0,,{text}")

    return ass_content + "\n".join(events) + "\n"
