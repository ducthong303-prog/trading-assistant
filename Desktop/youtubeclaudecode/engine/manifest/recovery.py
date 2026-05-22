"""YouTube AI Factory v4.1 — Checkpoint Recovery & Resume Logic"""
from .manager import ManifestManager


def find_resume_point(manifest: dict) -> dict:
    """
    Analyse manifest to determine where to resume.
    Returns: { "stage": str, "action": str, "details": str }
      stage:  which stage to resume (images/tts/thumbnail/editing)
      action: "start" (begin stage) | "resume_batch" (continue from batch)
              | "skip" (stage already done)
    """
    stages = manifest["stages"]
    orders = ["script", "images", "tts", "thumbnail", "editing"]

    for stage in orders:
        status = stages[stage]["status"]
        if status == "done":
            continue
        if status == "processing":
            # Find the first unfinished batch
            assets = stages[stage].get("assets", [])
            pending = [a for a in assets if a["status"] in ("pending", "failed")]
            if not pending:
                return {"stage": stage, "action": "start", "details": "No assets in progress, starting fresh"}
            first_batch = pending[0].get("batch", 1)
            return {
                "stage": stage,
                "action": "resume_batch",
                "details": f"Resuming from batch {first_batch}, {len(pending)} assets remaining",
                "batch": first_batch,
                "remaining": len(pending),
            }
        if status == "pending":
            return {"stage": stage, "action": "start", "details": f"Starting {stage}"}
        if status == "failed":
            return {"stage": stage, "action": "start", "details": f"Retrying failed stage: {stage}"}

    return {"stage": "editing", "action": "done", "details": "All stages complete"}


def get_next_batch_assets(manifest: dict, stage: str, batch_size: int = None) -> list[dict]:
    """Get assets in the next uncompleted batch."""
    stage_data = manifest["stages"][stage]
    bs = batch_size or stage_data.get("batch_size", 5)
    assets = stage_data.get("assets", [])

    # Group by batch
    batches = {}
    for a in assets:
        b = a.get("batch", 1)
        batches.setdefault(b, []).append(a)

    for batch_num in sorted(batches.keys()):
        batch_assets = batches[batch_num]
        # If any asset in this batch is not done, this is our target
        if any(a["status"] != "done" for a in batch_assets):
            return [a for a in batch_assets if a["status"] != "done" and a["status"] != "dead_letter"]

    return []
