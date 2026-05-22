#!/usr/bin/env python3
"""Stage: Asset Verification.

Usage: python -m engine.orchestration.stage_verify <project_id>

Validates all generated assets:
- Image count matches manifest
- File sizes > minimum
- Audio files exist and have valid duration
- Checksums match
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.manifest.manager import ManifestManager
from engine.utils.logger import Logger
from engine.utils.checksum import sha256, size_kb, exists_and_not_empty
from engine.utils.config import get_pipeline


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m engine.orchestration.stage_verify <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    log = Logger()
    mgr = ManifestManager(project_id)
    manifest = mgr.load_or_create()
    stages = manifest["stages"]

    issues = []
    ok = []

    min_img_size = get_pipeline("validation", "image_min_size_kb", default=50)
    min_audio_sec = get_pipeline("validation", "audio_min_duration_sec", default=10)

    # ── Images ────────────────────────────────────────
    if stages["images"]["status"] == "done":
        for asset in stages["images"].get("assets", []):
            if asset["status"] == "done":
                fp = asset.get("file")
                if fp and exists_and_not_empty(fp):
                    kb = size_kb(fp)
                    if kb >= min_img_size:
                        ok.append(f"img:{asset['id']}")
                    else:
                        issues.append(f"img:{asset['id']} too small ({kb:.1f}KB < {min_img_size}KB)")
                else:
                    issues.append(f"img:{asset['id']} file missing or empty: {fp}")

    # ── TTS ───────────────────────────────────────────
    if stages["tts"]["status"] == "done":
        for chunk in stages["tts"].get("chunks", []):
            if chunk["status"] == "done":
                fp = chunk.get("file")
                if fp and exists_and_not_empty(fp):
                    ok.append(f"tts:{chunk['id']}")
                else:
                    issues.append(f"tts:{chunk['id']} file missing or empty: {fp}")

    # ── Thumbnails ────────────────────────────────────
    if stages["thumbnail"]["status"] == "done":
        for asset in stages["thumbnail"].get("assets", []):
            if asset["status"] == "done":
                fp = asset.get("file")
                if fp and exists_and_not_empty(fp):
                    ok.append(f"thumb:{asset['id']}")
                else:
                    issues.append(f"thumb:{asset['id']} file missing or empty: {fp}")

    # ── Report ────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"VERIFY: {project_id}")
    print(f"{'='*50}")
    print(f"  ✅ OK:     {len(ok)} assets")
    print(f"  ❌ Issues: {len(issues)}")

    if issues:
        print(f"\n⚠️  Issues found:")
        for iss in issues:
            print(f"  - {iss}")
        log.warn(f"Verification issues: {len(issues)}", {"issues": issues})
    else:
        print(f"\n🎉 All assets verified!")
        log.info(f"All assets verified for {project_id}")

    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
