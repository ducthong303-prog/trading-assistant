# /generate-thumb — Tạo Prompt Thumbnail

Tạo prompt thumbnail YouTube từ title + script.

## Flow

1. Hỏi user: **Title** của video?
2. Hỏi user: **Script file**? (tự detect nếu có script mới nhất)
3. Auto-detect 3 pattern phù hợp nhất từ 6 proven patterns (A-F).
4. Chạy **thumbnail-bible-explainer** skill.
5. Output: 3 variations x 2 versions = 6 prompts.
6. Save vào `output/thumbnails/[Topic]/prompts.md`

## 6 Patterns Reference

| Pattern | Tên | Tỉ lệ viral |
|---------|-----|-------------|
| A | "Every X Explained" | 40% |
| B | "Title Statement" | 25% |
| C | "Contrast/Comparison" | 10% |
| D | "Character Grid" | 10% |
| E | "Quote/Concept Block" | 10% |
| F | "Icon Row with Labels" | 5% |

## Trigger

Gọi khi user nhắn: "thumbnail", "thumb Bible", "tạo thumb", "Bible thumbnail"
