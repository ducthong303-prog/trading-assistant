# WORKFLOW.md — End-to-End Production Pipeline

> **Version:** v3.0.0
> **Last updated:** 2026-05-21

---

## Master Pipeline (9 Steps)

```
                          SESSION 1 (60 min)
  ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 1. IDEA  │───→│2. RESEARCH│───→│ 3. SCRIPT│
  └──────────┘    └──────────┘    └──────────┘
                                        │
                          SESSION 2 (45 min)
                                        ▼
  ┌──────────┐    ┌──────────┐
  │4. IMAGES │    │5.THUMBNAIL│
  └──────────┘    └──────────┘
        │               │
                          SESSION 3 (60 min)
        ▼               ▼
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │ 6. TTS   │───→│7. ASSEMBLY│───→│ 8. EXPORT│───→│ 9. UPLOAD│
  └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## Step Details

### Step 1: IDEA
**Input:** Nothing hoặc topic suggestion
**Output:** Title + Angle + Promise
**Tool:** Brainstorm với Claude
**Checklist:**
- [ ] Competitor check (đã ai làm chưa?)
- [ ] Unique angle identified
- [ ] 3 title options drafted

### Step 2: RESEARCH
**Input:** Topic từ Step 1
**Output:** Research bank (scripture, characters, Hebrew/Greek, history)
**Tool:** WebSearch + Bible resources
**Checklist:**
- [ ] 3+ scripture passages
- [ ] 2-4 Hebrew/Greek words
- [ ] 1+ non-Bible source
- [ ] 5+ named characters

### Step 3: SCRIPT
**Input:** Research bank
**Output:** Clean script 3,500-4,000 words → `channels/bible-explainer/scripts/`
**Skill:** script-bible-explainer (6 phases)
**Checklist:**
- [ ] 3-Act structure
- [ ] "You" count ≥60
- [ ] Zero brackets in final
- [ ] TTS readability verified

### Step 4: IMAGE PROMPTS
**Input:** Script từ Step 3
**Output:** [N] prompts → `channels/bible-explainer/images/`
**Skill:** image-bible-explainer (5 phases)
**Checklist:**
- [ ] 4 config questions answered
- [ ] All prompts in English
- [ ] Generated in Google Flow
- [ ] Character consistency verified

### Step 5: THUMBNAIL
**Input:** Title + Script
**Output:** 6 prompts → `channels/bible-explainer/thumbnails/`
**Skill:** thumbnail-bible-explainer (4 phases)
**Checklist:**
- [ ] 3 different patterns
- [ ] 2 versions each (with-text + no-text)
- [ ] Cinzel/Playfair typography
- [ ] Colors: #1E2A4A + #B25D29

### Step 6: TTS / VOICEOVER
**Input:** Clean script
**Output:** Audio file → `channels/bible-explainer/audio/`
**Tool:** ElevenLabs
**Checklist:**
- [ ] Voice selected (male, warm, narrative)
- [ ] Hebrew/Greek pronunciation reviewed
- [ ] Pacing appropriate

### Step 7: VIDEO ASSEMBLY
**Input:** Audio + Images
**Output:** Assembled video timeline
**Tool:** CapCut / Premiere Pro
**Checklist:**
- [ ] Images synced to script beats
- [ ] Ken Burns effect added
- [ ] Scripture reference overlays
- [ ] Lower thirds for Hebrew/Greek

### Step 8: EXPORT
**Input:** Assembled timeline
**Output:** Final video → `channels/bible-explainer/video/`
**Checklist:**
- [ ] 1080p or 4K
- [ ] Audio sync verified
- [ ] Visual consistency check

### Step 9: UPLOAD
**Input:** Final video + thumbnails
**Output:** Published YouTube video
**Tool:** YouTube Studio
**Checklist:**
- [ ] Optimized title
- [ ] Description with timestamps
- [ ] 15-20 tags
- [ ] 3 thumbnails for A/B test
- [ ] Playlist assigned
- [ ] Publishing log saved

---

## Fast Paths

| Path | Steps | Duration | Trigger |
|------|-------|----------|---------|
| **Full Production** | 1-9 | 3 sessions | "video mới" |
| **Script Only** | 1-3 | 60 min | "chỉ cần script" |
| **Visual Only** | 4-5 | 45 min | "tạo visual" |
| **Rapid Thumbnail** | 5 | 10 min | "thumbnail nhanh" |

---

## Post-Publish

### 24-Hour Check
- CTR >5%?
- Retention >50%?

### 7-Day Check
- A/B test winner selected
- Winning pattern documented
- Competitor brief updated

### Monthly Retro
- Top 3 videos analyzed
- Pattern effectiveness reviewed
- Style guide updated if needed
