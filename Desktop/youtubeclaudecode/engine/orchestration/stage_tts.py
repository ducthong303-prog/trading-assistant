#!/usr/bin/env python3
"""Stage: TTS Narration Generation via ElevenLabs.

Usage: python -m engine.orchestration.stage_tts <project_id>

Reads script → chunks by act → generates MP3 per act → updates manifest.
"""
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.manifest.manager import ManifestManager
from engine.providers.elevenlabs import ElevenLabsClient
from engine.utils.logger import Logger
from engine.utils.config import get_pipeline


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m engine.orchestration.stage_tts <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    log = Logger()
    mgr = ManifestManager(project_id)
    eleven = ElevenLabsClient(logger=log)

    manifest = mgr.load_or_create()
    stage = manifest["stages"]["tts"]

    if stage["status"] == "done":
        log.info(f"[{project_id}] TTS stage already done — skipping")
        print("✅ TTS already done")
        return

    # Load script
    script_file = manifest["stages"]["script"].get("file")
    if not script_file:
        log.error("No script file in manifest")
        sys.exit(1)

    script_path = ROOT / "channels" / manifest["project"]["channel"] / script_file
    if not script_path.exists():
        log.error(f"Script not found: {script_path}")
        sys.exit(1)

    script_text = script_path.read_text()

    # Split script into acts
    chunks = _split_into_acts(script_text)
    if not chunks:
        log.error("Could not split script into acts")
        sys.exit(1)

    # Init chunk tracking
    stage["status"] = "processing"
    stage["chunks"] = []
    for i, chunk in enumerate(chunks):
        stage["chunks"].append({
            "id": f"tts_act{i+1}",
            "text": chunk["text"][:100] + "...",  # Preview only
            "char_count": len(chunk["text"]),
            "status": "pending",
            "file": None,
        })
    stage["voice_id"] = eleven.default_voice_id
    mgr.save(manifest)

    # Generate audio
    output_dir = ROOT / "channels" / manifest["project"]["channel"] / "audio" / project_id
    output_dir.mkdir(parents=True, exist_ok=True)

    tts_chunks = [{"id": f"tts_act{i+1}", "text": c["text"]} for i, c in enumerate(chunks)]

    results = eleven.generate_narration_chunks(tts_chunks, output_dir)

    # Update manifest
    for result in results:
        cid = result["id"]
        for chunk_entry in stage["chunks"]:
            if chunk_entry["id"] == cid:
                if result["success"]:
                    chunk_entry["status"] = "done"
                    chunk_entry["file"] = result["path"]
                    chunk_entry["duration_sec"] = result.get("duration_sec")
                else:
                    chunk_entry["status"] = "failed"
                    chunk_entry["error"] = result.get("error")
                break

    mgr.increment_cost(manifest, "elevenlabs", calls=len(chunks))

    # Check if all done
    all_done = all(c["status"] == "done" for c in stage["chunks"])
    if all_done:
        mgr.stage_done(manifest, "tts")
        log.stage_done("tts", {"chunks": len(chunks)})
        print(f"\n✅ TTS: {len(chunks)} acts generated")
    else:
        failed = [c for c in stage["chunks"] if c["status"] == "failed"]
        mgr.save(manifest)
        print(f"\n⚠️  TTS: {len(failed)}/{len(chunks)} chunks failed")


def _split_into_acts(script_text: str) -> list[dict]:
    """Split script into ~6 chunks for TTS generation."""
    # Remove frontmatter (everything before first ---)
    parts = script_text.split("---\n", 1)
    text = parts[1] if len(parts) > 1 else script_text

    # Try ACT headers first
    parts = re.split(r'ACT\s+(\d+)', text)
    acts = []
    for i in range(1, len(parts), 2):
        act_num = parts[i]
        act_text = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if act_text:
            acts.append({"act": int(act_num), "text": act_text})

    if acts:
        return acts

    # No ACT headers — split by character count for ~5 min chunks each
    # ~4000 chars ≈ 5 min at 150 WPM with ElevenLabs
    CHARS_PER_CHUNK = 4000
    text = text.strip()
    total_chars = len(text)

    if total_chars <= CHARS_PER_CHUNK:
        return [{"act": 1, "text": text}]

    # Split evenly into ~6 chunks, but break at paragraph boundaries
    num_chunks = max(2, min(6, total_chars // CHARS_PER_CHUNK))
    chunk_size = total_chars // num_chunks

    acts = []
    cursor = 0
    for ci in range(num_chunks):
        end = min(cursor + chunk_size, total_chars) if ci < num_chunks - 1 else total_chars
        # Extend to nearest paragraph break
        if end < total_chars:
            next_break = text.find("\n\n", end)
            if next_break != -1 and next_break - end < 500:
                end = next_break
        chunk_text = text[cursor:end].strip()
        if chunk_text:
            acts.append({"act": ci + 1, "text": chunk_text})
        cursor = end

    return acts


if __name__ == "__main__":
    main()
