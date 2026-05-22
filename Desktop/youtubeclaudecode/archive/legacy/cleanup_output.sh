#!/bin/bash
# cleanup_output.sh — Organize output files into project folders
# Usage: bash scripts/cleanup_output.sh [Topic]

TOPIC="${1:-Untitled}"

echo "=== YouTube AI Output Cleanup ==="
echo "Topic: $TOPIC"
echo ""

# Nothing to delete — just report what's in the output dirs
echo "Scripts:"
ls -la output/scripts/ 2>/dev/null || echo "  (empty)"

echo ""
echo "Images:"
ls -la img/ 2>/dev/null | head -5 || echo "  (empty)"

echo ""
echo "Thumbnails:"
ls -la thumb/ 2>/dev/null | head -5 || echo "  (empty)"

echo ""
echo "=== Done ==="
