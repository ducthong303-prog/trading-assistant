#!/usr/bin/env python3
"""Stage: Build Editing Manifest (CapCut JSON + FFmpeg script).

Usage: python -m engine.orchestration.stage_editing_manifest <project_id>

Reads project manifest + editing blueprint → produces:
1. CapCut import JSON (for manual fine-tuning)
2. FFmpeg assembly script (for auto rough-cut)
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.manifest.manager import ManifestManager
from engine.utils.logger import Logger
from engine.utils.config import get_pipeline


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m engine.orchestration.stage_editing_manifest <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    log = Logger()
    mgr = ManifestManager(project_id)
    manifest = mgr.load_or_create()

    stage = manifest["stages"]["editing"]
    stage["status"] = "processing"
    mgr.save(manifest)

    channel = manifest["project"]["channel"]
    channel_dir = ROOT / "channels" / channel

    # Collect assets
    images = _collect_image_assets(manifest, channel_dir)
    audio = _collect_audio_assets(manifest, channel_dir)

    if not images:
        log.warn("No images found — generating placeholder editing manifest")

    # Build editing manifests
    fps = get_pipeline("editing", "fps", default=24)
    resolution = get_pipeline("editing", "resolution", default=[1920, 1080])

    # 1. CapCut JSON
    capcut_path = channel_dir / "video" / project_id / "capcut_import.json"
    capcut_path.parent.mkdir(parents=True, exist_ok=True)
    capcut_manifest = _build_capcut_json(project_id, images, audio, fps, resolution)
    with open(capcut_path, "w") as f:
        json.dump(capcut_manifest, f, indent=2)
    stage["capcut_manifest"] = str(capcut_path)
    log.info(f"CapCut manifest: {capcut_path}")

    # 2. FFmpeg script
    ffmpeg_path = channel_dir / "video" / project_id / "ffmpeg_assemble.sh"
    ffmpeg_path.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg_script = _build_ffmpeg_script(project_id, images, audio, fps, resolution, ffmpeg_path.parent)
    with open(ffmpeg_path, "w") as f:
        f.write(ffmpeg_script)
    ffmpeg_path.chmod(0o755)
    stage["ffmpeg_script"] = str(ffmpeg_path)
    log.info(f"FFmpeg script: {ffmpeg_path}")

    mgr.stage_done(manifest, "editing")
    print(f"\n✅ Editing Manifest:")
    print(f"   CapCut: {capcut_path}")
    print(f"   FFmpeg: {ffmpeg_path}")
    print(f"\n▶ To assemble rough-cut: bash {ffmpeg_path}")


def _collect_image_assets(manifest: dict, channel_dir: Path) -> list[dict]:
    """Collect all generated images from manifest."""
    images = []
    for asset in manifest["stages"]["images"].get("assets", []):
        if asset["status"] == "done" and asset.get("file"):
            images.append({
                "id": asset["id"],
                "path": asset["file"],
                "duration_sec": 8.0,  # default
            })
    return images


def _collect_audio_assets(manifest: dict, channel_dir: Path) -> list[dict]:
    """Collect all TTS audio files from manifest."""
    audio = []
    for chunk in manifest["stages"]["tts"].get("chunks", []):
        if chunk["status"] == "done" and chunk.get("file"):
            audio.append({
                "id": chunk["id"],
                "path": chunk["file"],
                "duration_sec": chunk.get("duration_sec", 0),
            })
    return audio


def _build_capcut_json(project_id: str, images: list[dict], audio: list[dict],
                       fps: int, resolution: list) -> dict:
    """Build CapCut-compatible import JSON."""
    timeline = []
    time_cursor = 0.0

    for img in images:
        dur = img.get("duration_sec", 8.0)
        entry = {
            "asset": Path(img["path"]).name if img.get("path") else f"{img['id']}.jpeg",
            "source": img.get("path", ""),
            "start": round(time_cursor, 1),
            "duration": dur,
            "motion": {
                "type": "ken_burns_slow_zoom_in",
                "start_scale": 1.0,
                "end_scale": 1.08,
            },
            "transition_in": "crossfade_2s" if time_cursor > 0 else "none",
        }
        timeline.append(entry)
        time_cursor += dur

    total_duration = time_cursor

    return {
        "project": {
            "name": project_id,
            "fps": fps,
            "resolution": resolution,
            "total_duration_sec": round(total_duration, 1),
        },
        "timeline": timeline,
        "audio": {
            "files": [
                {"id": a["id"], "source": a.get("path", "")}
                for a in audio
            ],
        },
    }


def _build_ffmpeg_script(project_id: str, images: list[dict], audio: list[dict],
                         fps: int, resolution: list, output_dir: Path) -> str:
    """Generate FFmpeg assembly shell script."""
    lines = [
        "#!/usr/bin/env bash",
        f"# Auto-generated FFmpeg assembly: {project_id}",
        f"# Generated by YouTube AI Factory v4.1",
        "set -euo pipefail",
        "",
        f"OUTPUT=\"{output_dir / f'{project_id}_rough_v1.mp4'}\"",
        "",
    ]

    # Build input list
    inputs = []
    filters = []
    for i, img in enumerate(images):
        p = img.get("path", f"{img['id']}.jpeg")
        dur = img.get("duration_sec", 8.0)
        inputs.append(f'-loop 1 -t {dur} -i "{p}"')
        filters.append(
            f"[{i}:v]fade=t=in:d=2:alpha=1,setpts=PTS+{_sum_dur(images, i)}/TB[v{i}]"
        )

    lines.append("# Inputs")
    lines.append("ffmpeg \\")
    for inp in inputs:
        lines.append(f"  {inp} \\")

    # Audio input
    audio_concat = ""
    if audio:
        for a in audio:
            p = a.get("path", "")
            if p:
                lines.append(f'  -i "{p}" \\')
        # Audio concat: all audio files
        audio_count = len([a for a in audio if a.get("path")])

    total_dur = sum(img.get("duration_sec", 8.0) for img in images)

    lines.append(f'  -filter_complex "')
    lines.append(f"    {' '.join(filters)};")
    if audio:
        if len([a for a in audio if a.get("path")]) > 1:
            audio_inputs = " ".join(f"[{len(images)+j}:a]" for j in range(len([a for a in audio if a.get("path")])))
            lines.append(f"    {audio_inputs}concat=n={audio_count}:v=0:a=1[a];")
            audio_map = "[a]"
        else:
            audio_map = f"[{len(images)}:a]"
    else:
        audio_map = "anullsrc=r=44100:cl=stereo"
    lines.append(f'    [v0][v1][v2][v3][v4][v5][v6][v7][v8][v9]concat=n={len(images)}:v=1:a=0[v]')
    lines.append(f'  " \\')
    lines.append(f'  -map "[v]" -map "{audio_map}" \\')
    lines.append(f'  -c:v libx264 -preset medium -crf 18 \\')
    lines.append(f'  -c:a aac -b:a 320k \\')
    lines.append(f'  -t {total_dur} \\')
    lines.append(f'  "$OUTPUT"')
    lines.append("")
    lines.append(f'echo "Done: $OUTPUT"')

    return "\n".join(lines)


def _sum_dur(images: list[dict], until_idx: int) -> float:
    return sum(img.get("duration_sec", 8.0) for img in images[:until_idx])


if __name__ == "__main__":
    main()
