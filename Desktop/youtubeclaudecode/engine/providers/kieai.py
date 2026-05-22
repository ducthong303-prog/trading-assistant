"""YouTube AI Factory v4.1 — KieAI Image Generation Client

REST API (sync): POST prompt → receive image bytes directly.
URL: $KIEAI_IMAGE_URL (default: https://kie.ai/nano-banana-pro)
"""
import time
import requests
from pathlib import Path
from typing import Union
from engine.utils.config import require_env, get_env, get_pipeline
from engine.utils.logger import Logger
from engine.utils.checksum import sha256, size_kb
from .base import AbstractProvider


class KieAIClient(AbstractProvider):
    def __init__(self, logger: Logger = None):
        super().__init__("kieai", logger)
        self.api_key = require_env("KIEAI_API_KEY")
        self.image_url = get_env("KIEAI_IMAGE_URL", "https://kie.ai/nano-banana-pro")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })
        self.timeout = get_pipeline("providers", "kieai", "timeout_seconds", default=300)

    def generate(self, prompt: str, negative_prompt: str = None,
                 aspect_ratio: str = "16:9", model: str = None) -> tuple:
        """Returns (image_bytes, None) on success, (None, error_str) on failure."""
        model = model or get_pipeline("providers", "kieai", "model", default="imagen-4")
        payload = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "model": model,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt

        def _call():
            resp = self.session.post(self.image_url, json=payload, timeout=self.timeout)
            resp.raise_for_status()
            return resp.content

        result, error = self.retry_with_backoff(
            _call,
            max_retries=get_pipeline("providers", "kieai", "max_retries", default=3),
            backoff_seconds=get_pipeline("providers", "kieai", "retry_backoff", default=[2, 4, 8]),
            label="generate",
        )
        return result, error

    def generate_and_save(self, prompt: str, output_path: Union[str, Path],
                          negative_prompt: str = None, aspect_ratio: str = "16:9",
                          model: str = None) -> dict:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        image_bytes, error = self.generate(prompt, negative_prompt, aspect_ratio, model)
        if error:
            return {"success": False, "path": None, "checksum": None, "size_kb": 0, "error": error}

        try:
            with open(output_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            return {"success": False, "path": None, "checksum": None, "size_kb": 0, "error": f"Write failed: {e}"}

        return {
            "success": True,
            "path": str(output_path),
            "checksum": sha256(output_path),
            "size_kb": size_kb(output_path),
            "error": None,
        }

    def generate_batch(self, compiled_prompts: list[dict], output_dir: Union[str, Path],
                       batch_delay: float = None) -> list[dict]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        batch_delay = batch_delay or get_pipeline("providers", "kieai", "batch_delay_seconds", default=3)

        results = []
        for i, item in enumerate(compiled_prompts):
            asset_id = item["id"]
            filepath = output_dir / f"{asset_id}.jpeg"

            self.log.info(f"KieAI: generating {asset_id} ({i+1}/{len(compiled_prompts)})")

            result = self.generate_and_save(
                prompt=item["prompt"],
                output_path=filepath,
                negative_prompt=item.get("negative"),
            )
            result["id"] = asset_id
            result["metadata"] = item.get("metadata", {})
            results.append(result)

            if i < len(compiled_prompts) - 1:
                time.sleep(1)

        return results
