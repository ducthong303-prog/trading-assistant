# Workflow: Full Video Production

> **Trigger:** "video mới", "new video", "full production", "làm video mới"
> **Duration:** Multi-session (thường 2-3 sessions)
> **Skills used:** script-bible-explainer → image-bible-explainer → thumbnail-bible-explainer

---

## SESSION 1: SCRIPT (~45-60 min)

### Phase 1: Config
1. Hỏi user: **Topic** (VD: "Every Time God Said Fear Not")
2. Hỏi user: **Góc tiếp cận** đặc biệt (nếu có)
3. Hỏi user: Có cần research sâu không? (WebSearch Kinh Thánh, lịch sử)

### Phase 2: Research Bank
- Thu thập scripture references
- Tìm Hebrew/Greek words
- Tìm 1+ non-Bible historical source
- Đọc competitor scripts nếu có

### Phase 3: Script Generation (script-bible-explainer)
- Load `modules-youtube/script-architecture.md`
- Load `modules-youtube/style-system.md`
- Generate theo 6-phase process
- Output: clean script in `output/scripts/[Topic]_[Date].md`

### Phase 4: Quality Check
- Word count: 3,500-4,000
- "You" count: 60+
- Zero brackets
- 3-Act structure verified
- TTS readability check

**User action needed:** Review script, suggest edits.

---

## SESSION 2: IMAGES (~30-45 min)

### Phase 1: Config
- Hỏi: Tổng số ảnh? (khuyến nghị: Standard 30-50)
- Hỏi: Phân bố? (khuyến nghị: AUTO)
- Hỏi: Loại scene ưu tiên? (khuyến nghị: MIXED)
- Hỏi: Text labels? (khuyến nghị: NO hoặc YES BIBLE VERSES)

### Phase 2: Prompt Generation (image-bible-explainer)
- Load script từ Session 1
- Scene inventory
- Generate prompts → `output/images/[Topic]/prompts.md`

### Phase 3: Image Generation (Google Flow)
- User tự generate trong Google Flow
- Image 1 → Subject Ingredient
- Images 2+ → dùng ingredient
- Downloads → `img/`

**User action needed:** Generate images trong Google Flow, review consistency.

---

## SESSION 3: THUMBNAIL + PUBLISH (~30 min)

### Phase 1: Thumbnail (thumbnail-bible-explainer)
- Input: Title + Script
- Auto-pick 3 patterns
- Generate 6 prompts → `output/thumbnails/[Topic]/prompts.md`

### Phase 2: Final Checklist
- Audio ready?
- Images ready?
- Thumbnails ready?
- Video assembled?
- YouTube upload checklist

**User action needed:** Generate thumbnails, assemble video, upload.

---

## OUTPUT STRUCTURE

```
output/
└── [Topic]_[Date]/
    ├── script.md           ← Final clean script
    ├── images_prompts.md   ← All image prompts
    ├── thumb_prompts.md    ← All thumbnail prompts
    └── publishing_log.md   ← Checklist status + A/B test results
```
