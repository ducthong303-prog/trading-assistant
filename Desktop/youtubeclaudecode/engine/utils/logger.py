"""YouTube AI Factory v4.1 — Structured JSONL Logger"""
import json
import time
from pathlib import Path
from datetime import datetime, timezone


class Logger:
    def __init__(self, log_path: str = "logs/pipeline.log"):
        self.path = Path(log_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _emit(self, level: str, msg: str, data: dict = None):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "msg": msg,
        }
        if data:
            entry["data"] = data
        with open(self.path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def info(self, msg: str, data: dict = None):
        self._emit("INFO", msg, data)

    def warn(self, msg: str, data: dict = None):
        self._emit("WARN", msg, data)

    def error(self, msg: str, data: dict = None):
        self._emit("ERROR", msg, data)

    def stage_start(self, stage: str):
        self.info(f"Stage started: {stage}", {"stage": stage})

    def stage_done(self, stage: str, stats: dict = None):
        self.info(f"Stage done: {stage}", {"stage": stage, "stats": stats or {}})

    def asset_done(self, asset_id: str, provider: str, path: str, size: int):
        self.info(f"Asset done: {asset_id}", {"asset_id": asset_id, "provider": provider, "path": path, "size_bytes": size})

    def asset_failed(self, asset_id: str, provider: str, error: str, retries: int):
        self.warn(f"Asset failed: {asset_id}", {"asset_id": asset_id, "provider": provider, "error": error, "retries": retries})

    def checkpoint(self, stage: str, batch: int):
        self.info(f"Checkpoint: {stage} batch {batch}", {"stage": stage, "batch": batch})
