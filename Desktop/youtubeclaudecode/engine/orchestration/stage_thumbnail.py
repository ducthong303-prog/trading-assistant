#!/usr/bin/env python3
"""Stage: Thumbnail Generation via KieAI.

Usage: python -m engine.orchestration.stage_thumbnail <project_id>

Reads thumbnail prompts, generates 3 variants (A/B/C) for A/B testing.
Updates manifest.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.manifest.manager import ManifestManager
from engine.providers.kieai import KieAIClient
from engine.utils.logger import Logger


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m engine.orchestration.stage_thumbnail <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    log = Logger()
    mgr = ManifestManager(project_id)
    kieai = KieAIClient(logger=log)

    manifest = mgr.load_or_create()
    stage = manifest["stages"]["thumbnail"]

    if stage["status"] == "done":
        log.info(f"[{project_id}] Thumbnail stage already done — skipping")
        print("✅ Thumbnails already done")
        return

    # Load thumbnail prompts
    thumb_dir = ROOT / "channels" / manifest["project"]["channel"] / "thumbnails" / project_id
    prompts_file = thumb_dir / "thumbnail_prompts.md"
    if not prompts_file.exists():
        log.warn(f"No thumbnail prompts found: {prompts_file}")
        stage["status"] = "failed"
        mgr.save(manifest)
        return

    prompts_text = prompts_file.read_text()
    variants = _parse_thumbnail_prompts(prompts_text)

    if not variants:
        log.error("Could not parse thumbnail prompts")
        stage["status"] = "failed"
        mgr.save(manifest)
        return

    stage["status"] = "processing"
    stage["variants"] = [v["variant"] for v in variants]
    stage["assets"] = []
    mgr.save(manifest)

    # Generate thumbnails
    output_dir = thumb_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    for v in variants:
        result = kieai.generate_and_save(
            prompt=v["prompt"],
            output_path=output_dir / f"thumb_{v['variant']}.jpeg",
            negative_prompt=v.get("negative"),
            aspect_ratio="16:9",
        )
        stage["assets"].append({
            "id": f"thumb_{v['variant']}",
            "status": "done" if result["success"] else "failed",
            "file": result.get("path"),
            "checksum": result.get("checksum"),
            "error": result.get("error"),
        })

    mgr.increment_cost(manifest, "kieai", calls=len(variants))

    all_done = all(a["status"] == "done" for a in stage["assets"])
    if all_done:
        mgr.stage_done(manifest, "thumbnail")
        print(f"\n✅ Thumbnails: {len(variants)} variants generated")
    else:
        failed = [a for a in stage["assets"] if a["status"] == "failed"]
        mgr.save(manifest)
        print(f"\n⚠️  Thumbnails: {len(failed)}/{len(variants)} failed")


def _parse_thumbnail_prompts(text: str) -> list[dict]:
    """Parse thumbnail_prompts.md into list of variant dicts."""
    import re
    variants = []
    # Look for Concept A/B/C prompts
    concept_pattern = r"(?:Concept|CONCEPT)\s+([A-C]).*?(?:Prompt|PROMPT):\s*\n(.*?)(?=\n\n(?:Concept|CONCEPT|\#)|\Z)"
    matches = list(re.finditer(concept_pattern, text, re.DOTALL | re.IGNORECASE))
    if matches:
        for m in matches:
            v = m.group(1).upper()
            prompt = m.group(2).strip()
            variants.append({"variant": f"concept_{v.lower()}", "prompt": prompt, "negative": None})
    return variants


if __name__ == "__main__":
    main()
