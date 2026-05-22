#!/bin/bash
# new-video.sh — Scaffold new video project
# Usage: bash automation/new-video.sh "Topic Name"

TOPIC="${1:-Untitled}"
SAFE_NAME=$(echo "$TOPIC" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
CHANNEL="${2:-bible-explainer}"
BASE="channels/${CHANNEL}"

echo "=== New Video Scaffold ==="
echo "Topic: $TOPIC"
echo "Safe name: $SAFE_NAME"
echo "Channel: $CHANNEL"
echo ""

mkdir -p "${BASE}/scripts" "${BASE}/images/${SAFE_NAME}" "${BASE}/thumbnails/${SAFE_NAME}" "${BASE}/audio" "${BASE}/video" "${BASE}/publishing"

echo "Created:"
echo "  ${BASE}/scripts/        ← Put script here"
echo "  ${BASE}/images/${SAFE_NAME}/   ← Image prompts + .jpeg"
echo "  ${BASE}/thumbnails/${SAFE_NAME}/ ← Thumbnail prompts + .jpeg"
echo "  ${BASE}/audio/          ← TTS output"
echo "  ${BASE}/video/          ← Final video"
echo "  ${BASE}/publishing/     ← Publishing log"
echo ""
echo "Next: Nói 'viết script về ${TOPIC}' để bắt đầu."
