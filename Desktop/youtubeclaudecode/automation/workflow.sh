#!/bin/bash
# workflow.sh — Central workflow dispatcher
# Usage: bash automation/workflow.sh [command] [args...]
#
# Commands:
#   new [topic] [channel]     — Scaffold new video project
#   organize [channel]        — Move files from legacy to channels/
#   check [topic] [channel]   — Pre-publish checklist
#   status                    — Show project status
#   clean                     — Show cleanup recommendations

set -e

COMMAND="${1:-status}"
shift 2>/dev/null || true

case "$COMMAND" in
  new)
    bash "$(dirname "$0")/new-video.sh" "$@"
    ;;
  organize)
    bash "$(dirname "$0")/organize-output.sh" "$@"
    ;;
  check)
    bash "$(dirname "$0")/publish-checklist.sh" "$@"
    ;;
  status)
    echo "=== YouTube AI Factory Status ==="
    echo ""
    echo "Channels:"
    ls -d channels/*/ 2>/dev/null | while read ch; do
      name=$(basename "$ch")
      scripts=$(find "channels/$name/scripts" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
      images=$(find "channels/$name/images" -name "*.jpeg" 2>/dev/null | wc -l | tr -d ' ')
      thumbs=$(find "channels/$name/thumbnails" -name "*.jpeg" 2>/dev/null | wc -l | tr -d ' ')
      echo "  $name: $scripts scripts, $images images, $thumbs thumbnails"
    done
    echo ""
    echo "Archive: $(find archive -type f 2>/dev/null | wc -l | tr -d ' ') files"
    echo "Skills: 3 (script, image, thumbnail)"
    echo ""
    echo "Run 'bash automation/workflow.sh new \"Topic\"' to start."
    ;;
  clean)
    echo "=== Cleanup Recommendations ==="
    echo ""
    echo "Safe to delete (already archived):"
    echo "  server.log — trading system log"
    echo ""
    echo "Run 'bash automation/workflow.sh status' for project overview."
    ;;
  *)
    echo "Usage: bash automation/workflow.sh [new|organize|check|status|clean]"
    ;;
esac
