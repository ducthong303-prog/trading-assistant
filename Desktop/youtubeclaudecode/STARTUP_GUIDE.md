# STARTUP_GUIDE.md — Quick Start

> **Cho:** Người mới vào project hoặc bắt đầu session mới.

---

## Lần đầu tiên

```bash
# 1. Vào thư mục project
cd ~/Desktop/youtubeclaudecode

# 2. Kiểm tra trạng thái
bash automation/workflow.sh status

# 3. Đọc tổng quan
#    - README.md — giới thiệu
#    - STYLE_GUIDE.md — visual style
#    - WORKSPACE_MAP.md — kiến trúc đầy đủ
```

---

## Session điển hình

### "Tôi muốn làm video mới" → Full Production

```
Bạn: "video mới"
     → Claude hỏi: Topic? Length? Tone?
     → Chạy 9-step pipeline
     → Output trong channels/bible-explainer/
```

### "Tôi chỉ cần script" → Script Only

```
Bạn: "viết script về [chủ đề]"
     → script-bible-explainer kích hoạt
     → 6 phases
     → Script sạch, TTS-ready
```

### "Script đã có, cần ảnh + thumb" → Visual Only

```
Bạn: "tạo ảnh"
     → image-bible-explainer: 4 config questions → prompts
Bạn: "thumbnail"
     → thumbnail-bible-explainer: Title + Script → 6 prompts
```

---

## Commands nhanh

| Command | Làm gì |
|---------|--------|
| `/new-video` | Full production pipeline |
| `/generate-images` | Tạo prompt ảnh |
| `/generate-thumb` | Tạo thumbnail |
| `/export-video` | Publishing checklist |
| `/competitor-check` | Phân tích kênh đối thủ |

---

## Script automation

```bash
# Scaffold project mới
bash automation/workflow.sh new "Every Miracle Jesus Performed"

# Kiểm tra assets trước upload
bash automation/workflow.sh check "every-miracle"

# Xem trạng thái
bash automation/workflow.sh status

# Gợi ý cleanup
bash automation/workflow.sh clean
```

---

## Thư mục quan trọng

| Thư mục | Để làm gì |
|---------|-----------|
| `channels/bible-explainer/scripts/` | Lưu script đã viết |
| `channels/bible-explainer/images/` | Lưu prompt + ảnh |
| `channels/bible-explainer/thumbnails/` | Lưu prompt + thumbnail |
| `brain/prompts/` | Style config (sửa style ở đây) |
| `brain/workflows/` | Workflow definitions |

---

## Checklist trước khi upload YouTube

```bash
bash automation/workflow.sh check "topic-name"
```

Phải thấy:
- ✅ Script
- ✅ Images (có thể chưa generate — làm trong Google Flow)
- ✅ Thumbnails (3 cái cho A/B test)
- ⚠️ Audio (làm trong ElevenLabs)
- ⚠️ Video (render trong CapCut/Premiere)

---

## Troubleshooting

| Vấn đề | Cách fix |
|--------|----------|
| "Không tìm thấy skill" | Đảm bảo đang ở `~/Desktop/youtubeclaudecode/` |
| "Style không đúng" | Kiểm tra `brain/prompts/style-signature.md` |
| "Màu không đồng nhất" | Chỉ dùng hex từ `brain/prompts/color-palette.md` |
| "Muốn quay lại style cũ" | Xem `archive/legacy-modules/` |
| "Lỡ xoá file" | Khôi phục từ `archive/backups/` |
