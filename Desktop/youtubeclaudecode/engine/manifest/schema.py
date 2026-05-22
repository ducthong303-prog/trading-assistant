"""YouTube AI Factory v4.1 — Manifest Schema & Validation"""
from datetime import datetime, timezone
from typing import Literal

StageStatus = Literal["pending", "processing", "done", "failed"]
AssetStatus = Literal["pending", "processing", "done", "failed", "dead_letter"]


def create_project_manifest(
    project_id: str,
    channel: str = "bible-explainer",
    script_file: str = None,
    total_images: int = 28,
    tts_chunks: list[dict] = None,
    thumbnail_variants: list[str] = None,
) -> dict:
    """Factory for a new project manifest with all stages initialized."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "project": {
            "id": project_id,
            "channel": channel,
            "state": "script_done" if script_file else "new",
            "checkpoint": None,
        },
        "stages": {
            "script": {
                "status": "done" if script_file else "pending",
                "file": script_file,
                "model": "deepseek-v4",
                "word_count": None,
            },
            "images": {
                "status": "pending",
                "provider": "kieai",
                "total": total_images,
                "done": 0,
                "failed": 0,
                "batch_size": 5,
                "current_batch": 0,
                "style_lock_used": "jesus-portrait-v1",
                "assets": [],
            },
            "tts": {
                "status": "pending",
                "provider": "elevenlabs",
                "voice_id": None,
                "chunks": tts_chunks or [],
                "files": [],
            },
            "thumbnail": {
                "status": "pending",
                "provider": "kieai",
                "variants": thumbnail_variants or ["concept_a", "concept_b", "concept_c"],
                "assets": [],
            },
            "editing": {
                "status": "pending",
                "capcut_manifest": None,
                "ffmpeg_script": None,
            },
        },
        "checkpoints": [],
        "cost": {
            "kieai": {"calls": 0, "estimated_cost": 0},
            "elevenlabs": {"calls": 0, "estimated_cost": 0},
            "deepseek": {"tokens": 0, "estimated_cost": 0},
            "total_estimated": 0,
        },
        "meta": {
            "created": now,
            "updated": now,
            "version": "4.1",
        },
    }


def validate_manifest(manifest: dict) -> list[str]:
    """Validate manifest structure. Returns list of errors (empty = valid)."""
    errors = []
    required_keys = ["project", "stages", "checkpoints", "cost", "meta"]
    for k in required_keys:
        if k not in manifest:
            errors.append(f"Missing top-level key: {k}")

    required_stages = ["script", "images", "tts", "thumbnail", "editing"]
    if "stages" in manifest:
        for s in required_stages:
            if s not in manifest["stages"]:
                errors.append(f"Missing stage: {s}")

    return errors


def new_asset_entry(
    asset_id: str,
    stage: str,
    batch: int,
    prompt_file: str = None,
) -> dict:
    """Create a new asset tracking entry."""
    return {
        "id": asset_id,
        "status": "pending",
        "batch": batch,
        "file": None,
        "checksum": None,
        "size_bytes": None,
        "retries": 0,
        "error": None,
        "prompt_file": prompt_file,
        "validated": False,
        "created_at": None,
    }
