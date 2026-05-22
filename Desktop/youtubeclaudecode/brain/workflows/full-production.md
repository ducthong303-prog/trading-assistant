# Full Production Workflow — 9 Bước

> **Trigger:** "video mới", "new video", "full production"
> **Duration:** 2-3 sessions
> **Output:** Script + Images + Thumbnails → sẵn sàng publish

---

## PIPELINE OVERVIEW

```
IDEA → RESEARCH → SCRIPT → IMAGE PROMPTS → THUMBNAIL → TTS → VIDEO ASSEMBLY → EXPORT → UPLOAD
  1        2         3           4             5         6          7           8        9
```

---

## SESSION 1: CONTENT (~60 min)

### Step 1: IDEA
- [ ] Xác định topic (VD: "Every Time God Said Fear Not")
- [ ] Check competitor coverage (đã ai làm chưa?)
- [ ] Xác định unique angle
- [ ] Draft 3 title options
- [ ] Pick winning title

### Step 2: RESEARCH
- [ ] Thu thập 3+ scripture passages
- [ ] Tìm 2-4 Hebrew/Greek words + meanings
- [ ] Tìm 1+ non-Bible historical source
- [ ] List 5+ named characters
- [ ] Brainstorm open loop ideas
- [ ] Pick modern bridge type (A/B/C)

### Step 3: SCRIPT (script-bible-explainer)
- [ ] Phase 1: Topic confirmed
- [ ] Phase 2: Research bank gathered
- [ ] Phase 3: Outline approved
- [ ] Phase 4: 6 parts drafted
- [ ] Phase 5: Humanization done
- [ ] Phase 6: Final clean pass (zero brackets)
- [ ] Save → `channels/bible-explainer/scripts/[topic]_[date].md`

---

## SESSION 2: VISUALS (~45 min)

### Step 4: IMAGE PROMPTS (image-bible-explainer)
- [ ] 4 config questions answered
- [ ] Scene inventory done
- [ ] Prompts generated
- [ ] Save → `channels/bible-explainer/images/[topic]/prompts.md`
- [ ] Generate in Google Flow (Image 1 → Subject Ingredient → Images 2+)
- [ ] Save generated images → `channels/bible-explainer/images/[topic]/`

### Step 5: THUMBNAIL (thumbnail-bible-explainer)
- [ ] Title + Script input
- [ ] 3 patterns auto-selected
- [ ] 6 prompts generated (3 var × 2 ver)
- [ ] Save → `channels/bible-explainer/thumbnails/[topic]/prompts.md`
- [ ] Generate in Google Flow + Canva post-production

---

## SESSION 3: PRODUCTION (~60 min)

### Step 6: TTS / VOICEOVER
- [ ] Copy clean script to ElevenLabs
- [ ] Select voice (male, warm, narrative)
- [ ] Generate audio file
- [ ] Review Hebrew/Greek pronunciation
- [ ] Save → `channels/bible-explainer/audio/[topic].mp3`

### Step 7: VIDEO ASSEMBLY
- [ ] Import audio + images to editor (CapCut/Premiere)
- [ ] Sync image changes to script beats
- [ ] Add Ken Burns effect (subtle zoom/pan)
- [ ] Add lower thirds for Hebrew/Greek words
- [ ] Add scripture reference overlays
- [ ] Export 1080p/4K

### Step 8: EXPORT
- [ ] Final quality check (audio sync, visual consistency)
- [ ] Render in target format
- [ ] Save → `channels/bible-explainer/video/[topic]_final.mp4`

### Step 9: UPLOAD
- [ ] YouTube title (optimized format)
- [ ] Description (template + timestamps + scripture refs)
- [ ] Tags (15-20 relevant)
- [ ] Thumbnail (upload all 3 variants for A/B test)
- [ ] Playlist assignment
- [ ] Schedule or publish
- [ ] Log → `channels/bible-explainer/publishing/[topic]_log.md`

---

## POST-PUBLISH

### 24-Hour Check
- [ ] CTR >5%?
- [ ] Retention >50%?
- [ ] Comments positive?

### 7-Day Check
- [ ] Final CTR + watch time
- [ ] A/B test winner selected
- [ ] Document winning pattern → `brain/prompts/competitor-brief.md`

### Retro
- [ ] What worked? (keep)
- [ ] What didn't? (fix)
- [ ] What surprised? (investigate)
