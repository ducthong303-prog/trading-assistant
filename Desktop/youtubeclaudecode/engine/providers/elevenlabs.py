"""YouTube AI Factory v4.1 — ElevenLabs TTS Client (Direct API)

Sync API: POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
Auth: xi-api-key header
Returns: audio/mpeg bytes directly
"""
import time
import requests
from pathlib import Path
from typing import Union
from engine.utils.config import require_env, get_pipeline
from engine.utils.logger import Logger
from engine.utils.checksum import sha256, size_kb
from .base import AbstractProvider


ELEVENLABS_API = "https://api.elevenlabs.io/v1"


class ElevenLabsClient(AbstractProvider):
    def __init__(self, logger: Logger = None):
        super().__init__("elevenlabs", logger)
        self.api_key = require_env("ELEVENLABS_API_KEY")
        self.default_voice_id = require_env("ELEVENLABS_VOICE_ID")
        self.session = requests.Session()
        self.session.headers.update({
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
        })
        self.timeout = get_pipeline("providers", "elevenlabs", "timeout_seconds", default=300)

    def generate_speech(self, text: str, voice_id: str = None,
                        stability: float = None, clarity: float = None) -> tuple:
        voice_id = voice_id or self.default_voice_id
        stability = stability if stability is not None else get_pipeline("providers", "elevenlabs", "stability", default=0.5)
        clarity = clarity if clarity is not None else get_pipeline("providers", "elevenlabs", "clarity", default=0.75)
        output_format = get_pipeline("providers", "elevenlabs", "output_format", default="mp3_44100_128")

        url = f"{ELEVENLABS_API}/text-to-speech/{voice_id}"
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": clarity,
            },
        }

        def _call():
            resp = self.session.post(url, json=payload, timeout=self.timeout,
                                     params={"output_format": output_format})
            resp.raise_for_status()
            return resp.content

        return self.retry_with_backoff(
            _call,
            max_retries=get_pipeline("providers", "elevenlabs", "max_retries", default=3),
            backoff_seconds=get_pipeline("providers", "elevenlabs", "retry_backoff", default=[1, 3, 5]),
            label="generate_speech",
        )

    def generate_and_save(self, text: str, output_path: Union[str, Path],
                          voice_id: str = None, stability: float = None,
                          clarity: float = None) -> dict:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        audio_bytes, error = self.generate_speech(text, voice_id, stability, clarity)
        if error:
            return {"success": False, "path": None, "checksum": None, "size_kb": 0, "duration_sec": 0, "error": error}

        try:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
        except Exception as e:
            return {"success": False, "path": None, "checksum": None, "size_kb": 0, "duration_sec": 0, "error": f"Write: {e}"}

        kb = size_kb(output_path)
        self.log.asset_done(asset_id=output_path.stem, provider="elevenlabs",
                            path=str(output_path), size=int(kb * 1024))
        return {
            "success": True, "path": str(output_path), "checksum": sha256(output_path),
            "size_kb": kb, "duration_sec": round(kb / 16.0, 1), "error": None,
        }

    def generate_narration_chunks(self, chunks: list[dict], output_dir: Union[str, Path],
                                  voice_id: str = None) -> list[dict]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for chunk in chunks:
            cid = chunk["id"]
            fp = output_dir / f"{cid}.mp3"
            self.log.info(f"ElevenLabs: {cid} ({len(chunk['text'])} chars)")
            r = self.generate_and_save(text=chunk["text"], output_path=fp, voice_id=voice_id)
            r["id"] = cid
            results.append(r)
            if r["success"]:
                time.sleep(get_pipeline("providers", "elevenlabs", "batch_delay_seconds", default=2))
        return results
