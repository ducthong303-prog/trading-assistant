#!/usr/bin/env bash
# ============================================================
# YouTube AI Factory v4.1 — MAIN PIPELINE DISPATCHER
# ============================================================
# Usage: bash engine/orchestration/pipeline.sh <project_id>
#
# Reads manifest → determines next stage → executes it.
# Safe: resumable, batch-oriented, checkpoint after each stage.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PROJECT_ID="${1:-}"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: bash engine/orchestration/pipeline.sh <project_id>"
    echo "  Example: bash engine/orchestration/pipeline.sh every-time-jesus-wept"
    exit 1
fi

cd "$ROOT"
export PYTHONPATH="$ROOT:$PYTHONPATH"

MANIFEST_FILE="engine/manifest/active/${PROJECT_ID}.json"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  YouTube AI Factory v4.1 — Pipeline Dispatcher      ║"
echo "║  Project: $PROJECT_ID"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Run a stage with error handling ──────────────────

run_stage() {
    local stage="$1"
    local cmd="$2"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "▶ STAGE: $stage"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if python3 -m "$cmd" "$PROJECT_ID" 2>&1; then
        echo "✅ $stage — done"
        return 0
    else
        echo "❌ $stage — FAILED (check logs/pipeline.log)"
        echo "   Resume: bash engine/orchestration/pipeline.sh $PROJECT_ID"
        return 1
    fi
}

# ── Determine current stage from manifest ─────────────

run_pipeline() {
    # If manifest exists, check state
    if [ -f "$MANIFEST_FILE" ]; then
        STATE=$(python3 -c "
import json
with open('$MANIFEST_FILE') as f:
    m = json.load(f)
print(m['project']['state'])
" 2>/dev/null || echo "new")

        echo "Current state: $STATE"
        echo ""

        case "$STATE" in
            complete|editing_done)
                echo "🎉 All stages complete!"
                echo "Run verify: python3 -m engine.orchestration.stage_verify $PROJECT_ID"
                return 0
                ;;
            editing_pending|thumbnail_done)
                run_stage "EDITING MANIFEST" "engine.orchestration.stage_editing_manifest" || return 1
                ;;
            thumbnail_pending|tts_done)
                run_stage "THUMBNAIL" "engine.orchestration.stage_thumbnail" || return 1
                run_pipeline  # Continue to next stage
                ;;
            tts_pending|images_done)
                run_stage "TTS" "engine.orchestration.stage_tts" || return 1
                run_pipeline
                ;;
            images_pending|script_done)
                run_stage "IMAGES" "engine.orchestration.stage_images" || return 1
                run_pipeline
                ;;
            *)
                echo "Unknown state: $STATE"
                echo "Starting from images stage..."
                run_stage "IMAGES" "engine.orchestration.stage_images" || return 1
                run_pipeline
                ;;
        esac
    else
        echo "No manifest found. Creating new project..."
        python3 -c "
from engine.manifest.schema import create_project_manifest
from engine.manifest.manager import ManifestManager
mgr = ManifestManager('$PROJECT_ID')
mgr.create()
print('Manifest created.')
"
        echo "Please set up script file in manifest before running pipeline."
        echo "  Edit: engine/manifest/active/$PROJECT_ID.json"
    fi
}

run_pipeline

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Pipeline run complete."
echo "Manifest: $MANIFEST_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
