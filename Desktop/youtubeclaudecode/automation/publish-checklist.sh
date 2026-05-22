#!/bin/bash
# publish-checklist.sh — Verify all assets ready before YouTube upload
# Usage: bash automation/publish-checklist.sh [topic] [channel]

TOPIC="${1:-}"
CHANNEL="${2:-bible-explainer}"

if [ -z "$TOPIC" ]; then
  echo "Usage: bash automation/publish-checklist.sh [topic]"
  exit 1
fi

BASE="channels/${CHANNEL}"

echo "=== Pre-Publish Checklist: ${TOPIC} ==="
echo ""

# Check script
SCRIPT=$(find "${BASE}/scripts" -name "*${TOPIC}*" 2>/dev/null | head -1)
if [ -n "$SCRIPT" ]; then
  echo "✅ Script: $SCRIPT"
else
  echo "❌ Script: MISSING"
fi

# Check images
IMG_COUNT=$(find "${BASE}/images/${TOPIC}" -name "*.jpeg" 2>/dev/null | wc -l | tr -d ' ')
if [ "$IMG_COUNT" -gt 0 ]; then
  echo "✅ Images: ${IMG_COUNT} files"
else
  echo "⚠️  Images: none found (generate in Google Flow)"
fi

# Check thumbnails
THUMB_COUNT=$(find "${BASE}/thumbnails/${TOPIC}" -name "*.jpeg" 2>/dev/null | wc -l | tr -d ' ')
if [ "$THUMB_COUNT" -ge 3 ]; then
  echo "✅ Thumbnails: ${THUMB_COUNT} files (ready for A/B test)"
elif [ "$THUMB_COUNT" -gt 0 ]; then
  echo "⚠️  Thumbnails: ${THUMB_COUNT}/3 (need 3 for A/B test)"
else
  echo "❌ Thumbnails: MISSING"
fi

# Check audio
AUDIO=$(find "${BASE}/audio" -name "*${TOPIC}*" 2>/dev/null | head -1)
if [ -n "$AUDIO" ]; then
  echo "✅ Audio: $AUDIO"
else
  echo "⚠️  Audio: not yet generated (use ElevenLabs)"
fi

# Check video
VIDEO=$(find "${BASE}/video" -name "*${TOPIC}*" 2>/dev/null | head -1)
if [ -n "$VIDEO" ]; then
  echo "✅ Video: $VIDEO"
else
  echo "⚠️  Video: not yet assembled"
fi

echo ""
echo "=== Ready to publish when all ✅ ==="
