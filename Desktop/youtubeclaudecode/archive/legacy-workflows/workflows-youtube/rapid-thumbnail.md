# Workflow: Rapid Thumbnail

> **Trigger:** "thumbnail nhanh", "rapid thumb", "chỉ cần thumb"
> **Duration:** ~10-15 min
> **Skills used:** thumbnail-bible-explainer

---

## Flow

### Phase 1: Input (2 fields)
1. **Title** của video
2. **Script file** hoặc paste script trực tiếp

### Phase 2: Pattern Selection
- AI đọc script → recommend 3 patterns từ 6 proven patterns
- User chọn 1-3 patterns (mặc định: auto-pick 3)

### Phase 3: Generate (thumbnail-bible-explainer)
- Load `modules-youtube/style-system.md` (typography specs)
- Generate 3 variations x 2 versions
- Output → `output/thumbnails/[Topic]/prompts.md`

### Phase 4: Post-Production Tips
- Nhắc user: font Cinzel Bold + Playfair từ Google Fonts
- Nhắc user: colors #1E2A4A + #B25D29
- Nhắc user: Canva template nếu cần

---

## Quick Reference: 6 Patterns

| Pattern | Best for |
|---------|----------|
| A — "Every X Explained" | Series videos, listicle topics |
| B — "Title Statement" | Single-topic deep dives |
| C — "Contrast/Comparison" | Two-sided topics (grace vs law) |
| D — "Character Grid" | Biographical videos |
| E — "Quote/Concept Block" | Theological concepts |
| F — "Icon Row with Labels" | Process/sequence topics |
