#!/usr/bin/env python3
"""Stage: Image Generation via KieAI.

Usage: python -m engine.orchestration.stage_images <project_id>
       python -m engine.orchestration.stage_images every-time-jesus-wept

Reads manifest, finds pending image prompts, generates in batches of 5.
Updates manifest after each batch (checkpoint-safe).
On resume, skips already-done assets, continues from failed batch.
"""
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.manifest.manager import ManifestManager
from engine.manifest.recovery import get_next_batch_assets
from engine.providers.kieai import KieAIClient
from engine.utils.logger import Logger
from engine.utils.config import get_pipeline


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m engine.orchestration.stage_images <project_id>")
        sys.exit(1)

    project_id = sys.argv[1]
    log = Logger()
    mgr = ManifestManager(project_id)
    kieai = KieAIClient(logger=log)

    manifest = mgr.load_or_create()
    stage = manifest["stages"]["images"]

    if stage["status"] == "done":
        log.info(f"[{project_id}] Images stage already done — skipping")
        return

    # Find prompts directory
    prompts_dir = ROOT / "channels" / manifest["project"]["channel"] / "images" / project_id
    if not prompts_dir.exists():
        log.error(f"Prompts directory not found: {prompts_dir}")
        sys.exit(1)

    # Load existing prompt files (part1..part6)
    scene_prompts = _load_prompts_from_dir(prompts_dir)
    if not scene_prompts:
        log.error(f"No prompts found in {prompts_dir}")
        sys.exit(1)

    total = len(scene_prompts)
    stage["total"] = total
    batch_size = get_pipeline("providers", "kieai", "batch_size", default=5)
    stage["batch_size"] = batch_size
    stage["status"] = "processing"

    # Initialize asset tracking if empty
    if not stage.get("assets"):
        asset_ids = [s["id"] for s in scene_prompts]
        prompt_map = {s["id"]: s.get("prompt_source", "") for s in scene_prompts}
        mgr.init_asset_list(manifest, "images", asset_ids, batch_size, prompt_map)

    mgr.save(manifest)

    output_dir = prompts_dir  # Save images alongside prompts

    # Process batches
    while True:
        pending = get_next_batch_assets(manifest, "images")
        if not pending:
            break

        batch_num = pending[0].get("batch", "?")
        log.stage_start(f"images batch {batch_num} ({len(pending)} assets)")

        # Get compiled prompts for these assets
        compiled = []
        for asset in pending:
            scene = _find_scene(scene_prompts, asset["id"])
            if scene:
                compiled.append(scene)

        if not compiled:
            log.warn(f"No compiled prompts for batch {batch_num} — skipping")
            for asset in pending:
                mgr.mark_asset_done(manifest, "images", asset["id"], "skipped_no_prompt")
            mgr.save(manifest)
            continue

        # Generate batch
        results = kieai.generate_batch(compiled, output_dir)

        # Update manifest per result
        for result in results:
            aid = result["id"]
            if result["success"]:
                mgr.mark_asset_done(
                    manifest, "images", aid,
                    filepath=result["path"],
                    checksum=result.get("checksum"),
                    size_bytes=int(result.get("size_kb", 0) * 1024),
                )
            else:
                mgr.mark_asset_failed(manifest, "images", aid, result.get("error", "unknown"))

        mgr.increment_cost(manifest, "kieai", calls=len(compiled))
        log.checkpoint("images", batch_num)
        mgr.save(manifest)

        if len(pending) < batch_size:
            break  # Last (partial) batch done

        time.sleep(get_pipeline("providers", "kieai", "batch_delay_seconds", default=3))

    # Mark stage done if all assets done
    pending = get_next_batch_assets(manifest, "images")
    if not pending:
        mgr.stage_done(manifest, "images")
        log.stage_done("images", {"total": stage["total"], "done": stage["done"], "failed": stage["failed"]})
    else:
        mgr.save(manifest)

    print(f"\n✅ Images: {stage['done']}/{stage['total']} done, {stage['failed']} failed")
    if stage["failed"] > 0:
        print(f"⚠️  {stage['failed']} assets need attention (see manifest)")


def _load_prompts_from_dir(prompts_dir: Path) -> list[dict]:
    """Load all prompts from part files. Return list of compiled prompt dicts."""
    scenes = []
    for part_file in sorted(prompts_dir.glob("part*_prompts.md")):
        scenes.extend(_parse_part_file(part_file))
    return scenes


def _parse_part_file(filepath: Path) -> list[dict]:
    """Parse a part file into list of scene dicts for prompt_compiler.compile()."""
    import re
    content = filepath.read_text()
    scenes = []
    # Find all prompt blocks
    blocks = re.split(r'\n## Prompt \d+:', content)
    for i, block in enumerate(blocks[1:], 1):  # Skip text before first prompt
        # Extract the raw prompt text (everything until next section or end)
        prompt_text = block.strip().split('\n---')[0].strip()
        if prompt_text:
            # Generate an ID based on part filename + prompt number
            part_num = re.search(r'part(\d+)', filepath.stem)
            part = part_num.group(1) if part_num else "0"
            scene = {
                "id": f"img_{int(part):02d}_{i:03d}",
                "prompt": prompt_text,
                "negative": "",
                "metadata": {"source": str(filepath)},
            }
            scenes.append(scene)
    return scenes


def _find_scene(scenes: list[dict], asset_id: str) -> dict:
    for s in scenes:
        if s["id"] == asset_id:
            return s
    return None


if __name__ == "__main__":
    main()
