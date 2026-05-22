#!/usr/bin/env python3
"""Render video with FFmpeg — Ken Burns + audio sync + transitions.

Reads editing blueprint timings, generates individual segments,
concats them, overlays audio, outputs final MP4.
"""
import subprocess
import sys
from pathlib import Path
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[2]
IMG_DIR = ROOT / "channels/bible-explainer/images/every-time-jesus-wept"
AUDIO_DIR = ROOT / "channels/bible-explainer/audio/every-time-jesus-wept"
OUTPUT_DIR = ROOT / "channels/bible-explainer/video/every-time-jesus-wept"
TEMP_DIR = OUTPUT_DIR / "temp_segments"

# ── Blueprint: ảnh → duration (giây) + Ken Burns type ──
SEGMENTS = [
    # Act 1 — THE MYSTERY (0:00–7:00)
    {"id": 1,  "file": "img_01_001.jpeg", "dur": 180, "motion": "slow_zoom_in",  "desc": "Two Words Tease"},
    {"id": 2,  "file": "img_01_002.jpeg", "dur": 180, "motion": "parallax",      "desc": "Mary collapsed, Martha at door"},
    {"id": 3,  "file": "img_01_003.jpeg", "dur": 60,  "motion": "slow_tilt_up",   "desc": "Jesus at tomb"},
    # Act 2 — THE WARNING (7:00–11:30)
    {"id": 4,  "file": "img_01_004.jpeg", "dur": 270, "motion": "slow_zoom_in",  "desc": "Jesus weeping over Jerusalem"},
    # Act 3 — THE BREAKING (11:30–17:00)
    {"id": 5,  "file": "img_02_001.jpeg", "dur": 90,  "motion": "pan_right",     "desc": "Gethsemane night"},
    {"id": 6,  "file": "img_02_002.jpeg", "dur": 60,  "motion": "slow_zoom_in",  "desc": "Jesus with disciples"},
    {"id": 7,  "file": "img_02_003.jpeg", "dur": 60,  "motion": "static",        "desc": "Jesus face-down in dirt"},
    {"id": 8,  "file": "img_02_004.jpeg", "dur": 60,  "motion": "slow_zoom_in",  "desc": "The cup + the scream"},
    {"id": 9,  "file": "img_02_005.jpeg", "dur": 45,  "motion": "extreme_slow_zoom", "desc": "Blood-sweat close-up"},
    {"id": 10, "file": "img_03_001.jpeg", "dur": 15,  "motion": "pan_left_right", "desc": "Torchlight approaching"},
    # Act 4 — THE COST (17:00–20:30)
    {"id": 11, "file": "img_03_002.jpeg", "dur": 30,  "motion": "slow_zoom_in",  "desc": "Kiss of betrayal"},
    {"id": 12, "file": "img_03_003.jpeg", "dur": 30,  "motion": "parallax",      "desc": "Peter in courtyard"},
    {"id": 13, "file": "img_03_004.jpeg", "dur": 30,  "motion": "slow_tilt_up",   "desc": "Before Caiaphas"},
    {"id": 14, "file": "img_03_005.jpeg", "dur": 30,  "motion": "slow_zoom_in",  "desc": "Rooster crows"},
    {"id": 15, "file": "img_04_001.jpeg", "dur": 30,  "motion": "slow_zoom_in",  "desc": "Before Pilate"},
    {"id": 16, "file": "img_04_002.jpeg", "dur": 30,  "motion": "zoom_out",      "desc": "Crowd demands crucifixion"},
    {"id": 17, "file": "img_04_003.jpeg", "dur": 10,  "motion": "static",        "desc": "Scourging"},
    {"id": 18, "file": "img_04_004.jpeg", "dur": 20,  "motion": "extreme_slow_zoom", "desc": "Crown of thorns"},
    # Act 5 — THE PEAK (20:30–22:30)
    {"id": 19, "file": "img_04_005.jpeg", "dur": 30,  "motion": "pan_right",     "desc": "Road to cross"},
    {"id": 20, "file": "img_05_001.jpeg", "dur": 30,  "motion": "zoom_out",      "desc": "Golgotha — three crosses"},
    {"id": 21, "file": "img_05_002.jpeg", "dur": 20,  "motion": "slow_zoom_in",  "desc": "Mary at cross"},
    {"id": 22, "file": "img_05_003.jpeg", "dur": 10,  "motion": "static",        "desc": "Darkness over land"},
    {"id": 23, "file": "img_05_004.jpeg", "dur": 15,  "motion": "extreme_slow_zoom", "desc": "Cry of abandonment"},
    {"id": 24, "file": "img_05_005.jpeg", "dur": 15,  "motion": "static",        "desc": "It is finished"},
    # Act 6 — THE RESOLUTION (22:30–24:00)
    {"id": 25, "file": "img_06_001.jpeg", "dur": 30,  "motion": "pan_left",      "desc": "Burial silence"},
    {"id": 26, "file": "img_06_002.jpeg", "dur": 20,  "motion": "zoom_out",      "desc": "Sealed stone waiting"},
    {"id": 27, "file": "img_06_003.jpeg", "dur": 20,  "motion": "slow_zoom_in",  "desc": "Empty tomb at dawn"},
    {"id": 28, "file": "img_06_004.jpeg", "dur": 20,  "motion": "static_zoom_out", "desc": "Every tear answered"},
]


def motion_filter(motion_type: str, duration: float, fps: int = 24) -> str:
    """Generate zoompan filter for Ken Burns effect."""
    total_frames = int(duration * fps)

    if motion_type == "static":
        # No motion at all
        return f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1"

    if motion_type == "slow_zoom_in":
        # Zoom from 1.0 to 1.08 over the full duration
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z='min(zoom+0.0004,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "extreme_slow_zoom":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z='min(zoom+0.0003,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "zoom_out":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z='max(zoom-0.0004,1.0)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "pan_right":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z=1.05:x='min(x+2,iw-iw/1.05)':y='ih/2-(ih/1.05/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "pan_left":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z=1.05:x='max(x-2,0)':y='ih/2-(ih/1.05/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "pan_left_right":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z=1.0:x='iw/2-(iw/2)+sin(on*0.02)*200+200':y='ih/2-(ih/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "parallax":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z='min(zoom+0.0003,1.05)':x='iw/2-(iw/zoom/2)+sin(on*0.015)*100':"
            f"y='ih/2-(ih/zoom/2)+cos(on*0.01)*50':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "slow_tilt_up":
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z=1.03:x='iw/2-(iw/1.03/2)':y='max(ih-ih/1.03-on*1.5,0)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    if motion_type == "static_zoom_out":
        # Static for first half, then slow zoom out
        return (
            f"scale=1920:1080:force_original_aspect_ratio=decrease,"
            f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
            f"zoompan=z='if(lte(on,{total_frames//2}),1.0,max(zoom-0.0006,0.92))':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
        )

    # Fallback: gentle zoom
    return (
        f"scale=1920:1080:force_original_aspect_ratio=decrease,"
        f"pad=2560:1440:(ow-iw)/2:(oh-ih)/2,"
        f"zoompan=z='min(zoom+0.0005,1.06)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1920x1080:fps={fps},setsar=1"
    )


def render_segment(seg: dict, output_path: Path, fps: int = 24) -> bool:
    """Render a single image segment with Ken Burns motion."""
    img_path = IMG_DIR / seg["file"]
    if not img_path.exists():
        print(f"  MISSING: {img_path}")
        return False

    dur = seg["dur"]
    vf = motion_filter(seg["motion"], dur, fps)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(dur), "-i", str(img_path),
        "-vf", vf,
        "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-an",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {result.stderr[-300:]}")
        return False
    return True


def concat_segments(segment_files: list[Path], output_path: Path) -> bool:
    """Concat all segments using concat demuxer."""
    concat_list = TEMP_DIR / "concat_list.txt"
    with open(concat_list, "w") as f:
        for sf in segment_files:
            f.write(f"file '{sf.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Concat failed: {result.stderr[-500:]}")
        return False
    return True


def concat_audio(audio_files: list[Path], output_path: Path) -> bool:
    """Concat audio files."""
    concat_list = TEMP_DIR / "audio_list.txt"
    with open(concat_list, "w") as f:
        for af in audio_files:
            f.write(f"file '{af.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "aac", "-b:a", "320k",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Audio concat failed: {result.stderr[-300:]}")
        return False
    return True


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    total_duration = sum(s["dur"] for s in SEGMENTS)
    print(f"╔══════════════════════════════════════╗")
    print(f"║  FFmpeg Render — Every Time Jesus Wept ║")
    print(f"║  {len(SEGMENTS)} ảnh | {total_duration}s (~{total_duration//60} phút) | 24fps ║")
    print(f"║  VideoToolbox HW Encode | {os.cpu_count()} cores ║")
    print(f"╚══════════════════════════════════════╝")
    print()

    # ── Phase 1: Render từng phân đoạn SONG SONG ─────
    print("─── Phase 1: Render 28 segments (parallel x4) ───")
    segment_files = []

    # Build job list
    jobs = []
    for seg in SEGMENTS:
        seg_path = TEMP_DIR / f"seg_{seg['id']:02d}.mp4"
        if seg_path.exists():
            segment_files.append((seg["id"], seg_path))
        else:
            jobs.append((seg, seg_path))

    # Already cached
    for sid, sp in segment_files:
        print(f"  [{sid:02d}/28] cached")
    todo_count = len(jobs)

    if jobs:
        max_workers = 4
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {pool.submit(render_segment, seg, sp): (seg, sp) for seg, sp in jobs}
            for future in as_completed(futures):
                seg, sp = futures[future]
                success = future.result()
                if success:
                    segment_files.append((seg["id"], sp))
                    remaining = len([f for f in futures if not f.done()])
                    print(f"  [{seg['id']:02d}/28] OK — {seg['desc']} ({remaining} remaining)")
                else:
                    print(f"  [{seg['id']:02d}/28] FAILED — {seg['desc']}")

    # Sort by ID
    segment_files.sort(key=lambda x: x[0])
    segment_paths = [sp for _, sp in segment_files]
    print(f"  → {len(segment_paths)}/28 segments ready")
    print()

    # ── Phase 2: Concat video ──────────────────────────
    print("─── Phase 2: Concat video ───")
    video_silent = TEMP_DIR / "video_silent.mp4"
    if concat_segments(segment_files, video_silent):
        print(f"  → {video_silent}")
    else:
        print("  → FAILED")
        sys.exit(1)
    print()

    # ── Phase 3: Concat audio ──────────────────────────
    print("─── Phase 3: Concat audio ───")
    audio_files = sorted(AUDIO_DIR.glob("tts_act*.mp3"))
    if not audio_files:
        print("  No audio files found!")
        sys.exit(1)
    audio_concat = TEMP_DIR / "audio_full.aac"
    if concat_audio(audio_files, audio_concat):
        print(f"  → {audio_concat}")
    else:
        print("  → FAILED")
        sys.exit(1)
    print()

    # ── Phase 4: Combine video + audio ─────────────────
    print("─── Phase 4: Combine video + audio ───")
    final_output = OUTPUT_DIR / "every-time-jesus-wept_v1.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_silent),
        "-i", str(audio_concat),
        "-c:v", "h264_videotoolbox", "-b:v", "8M", "-allow_sw", "1",
        "-c:a", "aac", "-b:a", "320k",
        "-shortest",
        "-movflags", "+faststart",
        str(final_output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        size_mb = final_output.stat().st_size / (1024 * 1024)
        print(f"  → {final_output}")
        print(f"  → {size_mb:.1f} MB")
        print()
        print(f"╔══════════════════════════════════════╗")
        print(f"║  ✅ RENDER COMPLETE                 ║")
        print(f"║  {final_output}")
        print(f"╚══════════════════════════════════════╝")
    else:
        print(f"  → FAILED: {result.stderr[-500:]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
