#!/bin/bash
# organize-output.sh — Move generated files to channel folders
# Usage: bash automation/organize-output.sh [channel] [topic]

CHANNEL="${1:-bible-explainer}"
TOPIC="${2:-}"

echo "=== Organize Output ==="

# Move images
if [ -d "img" ] && [ "$(ls -A img 2>/dev/null)" ]; then
  DEST="channels/${CHANNEL}/images/${TOPIC}"
  mkdir -p "$DEST"
  COUNT=$(ls img/*.jpeg 2>/dev/null | wc -l | tr -d ' ')
  if [ "$COUNT" -gt 0 ]; then
    cp img/*.jpeg "$DEST/" 2>/dev/null
    echo "Images: $COUNT files → $DEST/"
  fi
fi

# Move thumbnails
if [ -d "thumb" ] && [ "$(ls -A thumb 2>/dev/null)" ]; then
  DEST="channels/${CHANNEL}/thumbnails/${TOPIC}"
  mkdir -p "$DEST"
  COUNT=$(ls thumb/*.jpeg 2>/dev/null | wc -l | tr -d ' ')
  if [ "$COUNT" -gt 0 ]; then
    cp thumb/*.jpeg "$DEST/" 2>/dev/null
    echo "Thumbnails: $COUNT files → $DEST/"
  fi
fi

echo "=== Done ==="
echo "Original files in img/ and thumb/ preserved (not deleted)."
