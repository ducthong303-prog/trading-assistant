"""YouTube AI Factory v4.1 — Manifest Manager (read/write/update)"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from .schema import create_project_manifest, validate_manifest, new_asset_entry

ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "engine" / "manifest" / "active"


class ManifestManager:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.path = MANIFEST_DIR / f"{project_id}.json"

    # ── CRUD ──────────────────────────────────────────

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> dict:
        if not self.exists():
            raise FileNotFoundError(f"Manifest not found: {self.path}")
        with open(self.path) as f:
            return json.load(f)

    def save(self, manifest: dict):
        manifest["meta"]["updated"] = datetime.now(timezone.utc).isoformat()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(manifest, f, indent=2, default=str, ensure_ascii=False)

    def create(self, **kwargs) -> dict:
        manifest = create_project_manifest(self.project_id, **kwargs)
        self.save(manifest)
        return manifest

    def load_or_create(self, **kwargs) -> dict:
        if self.exists():
            return self.load()
        return self.create(**kwargs)

    # ── Stage operations ──────────────────────────────

    def set_stage_status(self, manifest: dict, stage: str, status: str):
        manifest["stages"][stage]["status"] = status
        manifest["project"]["checkpoint"] = f"{stage}_{status}"

    def stage_done(self, manifest: dict, stage: str) -> dict:
        self.set_stage_status(manifest, stage, "done")
        manifest["checkpoints"].append({
            "stage": stage,
            "status": "done",
            "time": datetime.now(timezone.utc).isoformat(),
        })
        self._advance_project_state(manifest, stage)
        self.save(manifest)
        return manifest

    def _advance_project_state(self, manifest: dict, completed_stage: str):
        """Set project.state based on which stages are done."""
        stages = manifest["stages"]
        order = ["script", "images", "tts", "thumbnail", "editing"]
        for stage in order:
            if stages[stage]["status"] != "done":
                manifest["project"]["state"] = f"{stage}_pending"
                return
        manifest["project"]["state"] = "complete"

    # ── Asset operations ──────────────────────────────

    def init_asset_list(self, manifest: dict, stage: str, asset_ids: list[str],
                        batch_size: int = 5, prompt_map: dict[str, str] = None):
        """Initialize asset tracking for a stage. prompt_map maps asset_id -> prompt_file."""
        stage_data = manifest["stages"][stage]
        stage_data["batch_size"] = batch_size
        batch = 1
        for i, aid in enumerate(asset_ids):
            if i > 0 and i % batch_size == 0:
                batch += 1
            prompt_file = prompt_map.get(aid) if prompt_map else None
            stage_data["assets"].append(new_asset_entry(aid, stage, batch, prompt_file))

    def mark_asset_done(self, manifest: dict, stage: str, asset_id: str,
                        filepath: str, checksum: str = None, size_bytes: int = None):
        asset = self._find_asset(manifest, stage, asset_id)
        if not asset:
            return
        asset["status"] = "done"
        asset["file"] = filepath
        asset["checksum"] = checksum
        asset["size_bytes"] = size_bytes
        asset["validated"] = True
        asset["created_at"] = datetime.now(timezone.utc).isoformat()
        manifest["stages"][stage]["done"] += 1

    def mark_asset_failed(self, manifest: dict, stage: str, asset_id: str, error: str):
        asset = self._find_asset(manifest, stage, asset_id)
        if not asset:
            return
        asset["retries"] += 1
        asset["error"] = error
        if asset["retries"] >= 3:
            asset["status"] = "dead_letter"
        else:
            asset["status"] = "failed"
        manifest["stages"][stage]["failed"] += 1

    def _find_asset(self, manifest: dict, stage: str, asset_id: str):
        for a in manifest["stages"][stage]["assets"]:
            if a["id"] == asset_id:
                return a
        return None

    def get_pending_assets(self, manifest: dict, stage: str) -> list[dict]:
        """Return assets that are pending or failed (retriable)."""
        return [
            a for a in manifest["stages"][stage]["assets"]
            if a["status"] in ("pending", "failed") and a["status"] != "dead_letter"
        ]

    def increment_cost(self, manifest: dict, provider: str, calls: int = 1):
        if provider in manifest["cost"]:
            manifest["cost"][provider]["calls"] += calls
