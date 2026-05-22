# AUTOMATION_PLAN.md — Automation Roadmap

> **Version:** v1.0.0
> **Status:** Phase 1 implemented, Phase 2-3 planned

---

## Phase 1: Implemented (Current)

### Script automation (`automation/new-video.sh`)
Scaffold new video project structure:
```bash
bash automation/new-video.sh "Every Time God Said Fear Not"
# Creates: channels/bible-explainer/{scripts,images,thumbnails}/fear-not/
```

### Output organizer (`automation/organize-output.sh`)
Organize generated images/thumbnails into channel folders:
```bash
bash automation/organize-output.sh
# Moves: img/* → channels/bible-explainer/images/[latest]/
#        thumb/* → channels/bible-explainer/thumbnails/[latest]/
```

### Pre-publish checklist (`automation/publish-checklist.sh`)
Verify all assets ready before upload:
```bash
bash automation/publish-checklist.sh "fear-not"
# Checks: script exists, images exist, thumbnails ready, audio ready
```

---

## Phase 2: Planned (Short-term)

### TTS Auto-generation
Script to auto-send clean script to ElevenLabs API:
```bash
bash automation/generate-tts.sh channels/bible-explainer/scripts/fear-not.md
# → channels/bible-explainer/audio/fear-not.mp3
```

### Thumbnail A/B Test Tracker
Script to log YouTube A/B test results:
```bash
bash automation/track-ab-test.sh "fear-not"
# Reads YouTube Analytics API → logs CTR per thumbnail → picks winner
```

### Competitor Monitor
Weekly competitor channel scan:
```bash
bash automation/competitor-scan.sh
# Checks Deep Made Simple, Bible Made Simple, Plain Truth
# Flags new uploads, thumbnail changes, viral hits
```

---

## Phase 3: Future (Long-term)

### Multi-Channel Manager
Manage multiple YouTube channels from one workspace:
```bash
bash automation/channel-new.sh "christian-history"
# Creates channels/christian-history/ with all subdirs
# Registers in configs/channels.json
```

### Batch Image Generation Queue
Queue-based image generation for large projects:
```bash
bash automation/batch-generate.sh channels/bible-explainer/images/fear-not/
# Reads prompts.md → splits into batches → generates via Flow API
```

### Analytics Dashboard
Aggregate CTR, retention, and growth metrics:
```bash
bash automation/analytics.sh
# Pulls YouTube Analytics → generates weekly report
```

### Video Assembly Automation
Auto-sync audio + images using FFmpeg:
```bash
bash automation/auto-assemble.sh "fear-not"
# Reads script timestamps → syncs images → generates rough cut
```

---

## Cron Jobs (via Claude Code Scheduler)

```
# Weekly competitor scan — Monday 9am
/loop 7d "chạy competitor scan"

# Monthly retro — 1st of month
/loop monthly "chạy monthly retro analysis"

# Daily A/B test check for active videos
/loop 1d "check A/B test results"
```

---

## Integration Points

| Tool | Integration Type | Priority |
|------|-----------------|----------|
| ElevenLabs API | TTS auto-generation | Phase 2 |
| YouTube Analytics API | A/B test tracking | Phase 2 |
| Google Flow | Batch image generation | Phase 3 |
| FFmpeg | Video assembly | Phase 3 |
| Canva API | Thumbnail post-production | Phase 3 |
