"""YouTube AI Factory v4.1 — KieAI GPT-4o Image Client

Async via webhook callback:
1. POST https://api.kie.ai/api/v1/gpt4o-image/generate → taskId
2. Wait for callback at webhook URL
3. Download image from resultUrls
"""
import time
import requests
from pathlib import Path
from typing import Union
from engine.utils.config import require_env, get_pipeline
from engine.utils.logger import Logger
from engine.utils.checksum import sha256, size_kb
from .base import AbstractProvider


class KieAI4oClient(AbstractProvider):
    def __init__(self, logger: Logger = None):
        super().__init__("kieai-4o", logger)
        self.api_key = require_env("KIEAI_API_KEY")
        self.api_url = "https://api.kie.ai/api/v1/gpt4o-image/generate"
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        self.timeout = get_pipeline("providers", "kieai", "timeout_seconds", default=120)
        self.poll_interval = 5
        self.max_wait = 180

    def generate_and_save(self, prompt: str, output_path: Path,
                          size: str = "3:2") -> dict:
        """Generate via callback pattern and save."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create webhook
        webhook = self._create_webhook()
        if not webhook:
            return {"success": False, "error": "Cannot create webhook"}

        webhook_uuid, webhook_url = webhook

        # Submit job
        task_id, error = self._submit(prompt, size, webhook_url)
        if error:
            return {"success": False, "error": error}

        self.log.info(f"4o task: {task_id}")

        # Wait for callback
        result, error = self._wait_callback(webhook_uuid, task_id)
        if error:
            return {"success": False, "error": error}

        # Download
        img_url = result.get("resultUrls", [None])[0] if isinstance(result, dict) else None
        if not img_url:
            # Try other fields
            if isinstance(result, dict):
                img_url = result.get("url") or result.get("image_url")
        if not img_url:
            return {"success": False, "error": "No image URL in callback"}

        try:
            img_bytes = self.session.get(img_url, timeout=120).content
            with open(output_path, "wb") as f:
                f.write(img_bytes)
        except Exception as e:
            return {"success": False, "error": f"Download failed: {e}"}

        kb = size_kb(output_path)
        return {
            "success": True,
            "path": str(output_path),
            "checksum": sha256(output_path),
            "size_kb": kb,
            "error": None,
        }

    def generate_batch(self, items: list[dict], output_dir: Path, parallel: int = 5) -> list[dict]:
        """Generate batch: submit all → wait all → download all."""
        output_dir.mkdir(parents=True, exist_ok=True)
        log = self.log

        webhooks = {}  # uuid → url
        jobs = {}  # uuid → [task_ids]

        # Submit all jobs
        for item in items:
            wh = self._create_webhook()
            if not wh:
                continue
            uuid, url = wh
            webhooks[uuid] = url
            task_id, err = self._submit(item["prompt"], item.get("size", "3:2"), url)
            if err:
                log.warn(f"Submit failed for {item['id']}: {err}")
                continue
            jobs.setdefault(uuid, []).append({"task_id": task_id, "item": item})
            log.info(f"4o: {item['id']} → {task_id}")
            time.sleep(0.5)  # Rate limit

        # Wait for all callbacks
        results = {}
        start = time.time()
        while time.time() - start < self.max_wait:
            for uuid in list(jobs.keys()):
                pending = jobs.get(uuid)
                if not pending:
                    continue
                reqs = self._get_webhook_requests(uuid)
                for req in reqs:
                    data = req.get("content") or {}
                    cb_task_id = data.get("taskId") or data.get("data", {}).get("taskId", "")
                    # Find matching job
                    for j in pending[:]:
                        if j["task_id"] == cb_task_id:
                            result_urls = data.get("resultUrls") or data.get("data", {}).get("resultUrls", [])
                            results[j["item"]["id"]] = {"url": result_urls[0] if result_urls else None}
                            pending.remove(j)
                if not pending:
                    del jobs[uuid]
            if not jobs:
                break
            time.sleep(self.poll_interval)

        # Download
        output = []
        for item in items:
            aid = item["id"]
            if aid in results and results[aid]["url"]:
                fp = output_dir / f"{aid}.jpeg"
                try:
                    img_bytes = self.session.get(results[aid]["url"], timeout=120).content
                    with open(fp, "wb") as f:
                        f.write(img_bytes)
                    output.append({"id": aid, "success": True, "path": str(fp), "error": None})
                except Exception as e:
                    output.append({"id": aid, "success": False, "error": str(e)})
            else:
                output.append({"id": aid, "success": False, "error": "No result"})

        return output

    # ── Helpers ───────────────────────────────────────

    def _create_webhook(self) -> tuple:
        try:
            r = requests.post("https://webhook.site/token", headers={"Accept": "application/json"}, timeout=10)
            data = r.json()
            uuid = data.get("uuid")
            return (uuid, f"https://webhook.site/{uuid}") if uuid else None
        except Exception:
            return None

    def _submit(self, prompt: str, size: str, callback_url: str) -> tuple:
        payload = {"prompt": prompt, "size": size, "callBackUrl": callback_url}
        try:
            r = self.session.post(self.api_url, json=payload, timeout=self.timeout)
            r.raise_for_status()
            data = r.json()
            task_id = data.get("data", {}).get("taskId", "")
            return (task_id, None) if task_id else (None, "No taskId in response")
        except Exception as e:
            return None, str(e)

    def _get_webhook_requests(self, uuid: str) -> list:
        try:
            r = requests.get(
                f"https://webhook.site/token/{uuid}/requests?sorting=newest",
                headers={"Accept": "application/json"}, timeout=10,
            )
            data = r.json()
            raw_requests = data.get("data", [])
            parsed = []
            for req in raw_requests:
                content_str = req.get("content", "")
                if content_str:
                    try:
                        parsed.append({"content": __import__('json').loads(content_str)})
                    except Exception:
                        parsed.append({"content": content_str})
            return parsed
        except Exception:
            return []

    def _wait_callback(self, uuid: str, task_id: str) -> tuple:
        start = time.time()
        while time.time() - start < self.max_wait:
            reqs = self._get_webhook_requests(uuid)
            for req in reqs:
                data = req.get("content", {})
                cb_task_id = data.get("taskId") or data.get("data", {}).get("taskId", "")
                if cb_task_id == task_id:
                    result = data.get("resultJson") or data.get("data", {}).get("resultJson", "")
                    if result:
                        try:
                            return (__import__('json').loads(result), None)
                        except Exception:
                            return (result, None)
                    result_urls = data.get("resultUrls") or data.get("data", {}).get("resultUrls", [])
                    return ({"resultUrls": result_urls}, None)
            time.sleep(self.poll_interval)
        return None, f"Timeout waiting for callback: {task_id}"
