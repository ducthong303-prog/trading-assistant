# Publishing Pipeline — YouTube Bible Explainer

> **Authority:** Workflow chuẩn từ script đến published video.
> **Version:** v1.0.0

---

## PRE-PRODUCTION

### Step 1: Topic Validation
- [ ] Check competitor coverage (đã ai làm topic này chưa?)
- [ ] Identify unique angle (mình mang gì mới?)
- [ ] Estimate search volume (YouTube search suggestions)
- [ ] Draft 3 title options

### Step 2: Script Production
Tool: **script-bible-explainer** skill
- [ ] Research bank collected
- [ ] 3-Act outline approved
- [ ] 6 Parts drafted
- [ ] Humanization rewrite done
- [ ] Final clean pass (ZERO brackets)
- [ ] Word count: 3,500-4,000
- [ ] "You" count: 60+
- [ ] Save to `output/scripts/[Topic]_[Date].md`

### Step 3: Visual Planning
Tool: **image-bible-explainer** skill
- [ ] Scene inventory from script
- [ ] Density decided (Light/Standard/Dense/Premium)
- [ ] Scene types balanced (Narrative/Explainer/Emotional)
- [ ] Character consistency plan documented
- [ ] Prompts generated → `output/images/[Topic]/prompts.md`

---

## PRODUCTION

### Step 4: Voiceover
- [ ] Copy clean script to ElevenLabs
- [ ] Select voice (male, warm, narrative)
- [ ] Generate audio file
- [ ] Review for Hebrew/Greek pronunciation
- [ ] Edit timing/pacing if needed

### Step 5: Image Generation
- [ ] Open Google Flow
- [ ] Generate Image 1 (main character) → save as ingredient
- [ ] Generate Images 2+ using ingredient
- [ ] Download all images to `img/`
- [ ] Quality check: consistency, style, no AI artifacts
- [ ] Re-generate failures

### Step 6: Thumbnails
Tool: **thumbnail-bible-explainer** skill
- [ ] Generate 3 variations x 2 versions
- [ ] Generate in Google Flow
- [ ] Post-production in Canva (text layer if needed)
- [ ] Export all to `thumb/`
- [ ] A/B test plan: which 3 to upload?

---

## POST-PRODUCTION

### Step 7: Video Assembly
- [ ] Import audio + images to editor
- [ ] Sync image changes to script beats
- [ ] Add subtle motion/zoom (Ken Burns effect)
- [ ] Add lower thirds for Hebrew/Greek words
- [ ] Add scripture reference overlays
- [ ] Export 1080p or 4K

### Step 8: YouTube Upload
- [ ] Title: optimized format
- [ ] Description: template + timestamps
- [ ] Tags: 15-20 relevant tags
- [ ] Thumbnail: upload all 3 variants
- [ ] Playlist: add to series playlist
- [ ] Captions: auto-generate + review
- [ ] Schedule or publish

### Step 9: A/B Testing
- [ ] Upload 3 thumbnails
- [ ] Run 7-14 days
- [ ] Check CTR metrics
- [ ] Select winner
- [ ] Document winning pattern → `competitor-analysis.xlsx`

---

## POST-PUBLISH

### 24-Hour Check
- [ ] CTR above 5%?
- [ ] Retention above 50%?
- [ ] Comments positive?
- [ ] Any issues (audio sync, missing captions)?

### 7-Day Check
- [ ] Final CTR
- [ ] Watch time
- [ ] Subscriber gain
- [ ] Which thumbnail won A/B test?

### Retro
- [ ] What worked? (keep)
- [ ] What didn't? (fix)
- [ ] What surprised? (investigate)
- [ ] Update competitor benchmarks
- [ ] Update script templates if needed

---

## TOOLS INDEX

| Stage | Tool | Purpose |
|-------|------|---------|
| Script | Claude Code + script-bible-explainer | AI-assisted writing |
| Voiceover | ElevenLabs | TTS narration |
| Images | Google Flow + Imagen 4 | AI image generation |
| Post-production | Canva | Thumbnail text overlay |
| Video Editing | CapCut / Premiere Pro | Assembly + effects |
| Publishing | YouTube Studio | Upload + A/B test |
| Analytics | YouTube Analytics | CTR, retention, growth |
