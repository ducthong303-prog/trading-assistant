# /generate-images — Tạo Prompt Ảnh Cho Script

Tạo prompt ảnh watercolor Bible illustration từ script có sẵn.

## Flow

1. Hỏi user: **Script file** nào? (tự detect nếu có script mới nhất trong output/scripts/)
2. 4 câu hỏi config bắt buộc (từ image-bible-explainer skill):
   - Q1: Tổng số ảnh (5-200)
   - Q2: Phân bố (AUTO/EVEN/CLIMAX-FOCUSED/CUSTOM)
   - Q3: Loại scene ưu tiên (NARRATIVE/EXPLAINER/EMOTIONAL/MIXED)
   - Q4: Text labels trong ảnh? (NO/YES BIBLE VERSES/YES CONCEPTS/YES CHARACTER NAMES/MIXED)
3. Chạy **image-bible-explainer** skill với config trên.
4. Save prompts vào `output/images/[Topic]/prompts.md`

## Output

File prompts.md chứa toàn bộ prompt tiếng Anh, sẵn sàng copy vào Google Flow.

## Trigger

Gọi khi user nhắn: "tạo ảnh", "generate images", "image prompts", "prompt cho script"
