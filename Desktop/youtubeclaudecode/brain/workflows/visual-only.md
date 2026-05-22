# Visual-Only Fast Path

> **Trigger:** "tạo visual", "images + thumbnail", "visual only"
> **Duration:** ~30 min
> **Skills:** image-bible-explainer + thumbnail-bible-explainer

---

## Flow

1. Hỏi: Script file location?
2. Chạy image-bible-explainer (4 config questions → 5 phases)
3. Chạy thumbnail-bible-explainer (2 inputs → 4 phases)
4. Output:
   - Images → `channels/bible-explainer/images/[topic]/`
   - Thumbnails → `channels/bible-explainer/thumbnails/[topic]/`

---

## Use When

- Script đã có sẵn
- Chỉ cần generate visuals
- Update visuals cho video cũ
