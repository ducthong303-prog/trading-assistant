# /new-video — Bắt Đầu Video Mới

Khởi động full production pipeline cho một video Bible Explainer mới.

## Flow

1. Hỏi user: **Topic** là gì? (VD: "Every Time God Said Fear Not")
2. Hỏi user: **Angle** là gì? (góc tiếp cận đặc biệt)
3. Hỏi user: **Mật độ ảnh** — Light (15-25) / Standard (30-50) / Dense (60-100)?
4. Chạy tuần tự:
   - **script-bible-explainer** → tạo kịch bản
   - **image-bible-explainer** → tạo prompt ảnh
   - **thumbnail-bible-explainer** → tạo thumbnail
5. Hiển thị **Publishing Checklist** sau khi hoàn tất.

## Output

```
output/
├── scripts/[Topic]_[Date].md
├── images/[Topic]/prompts.md
└── thumbnails/[Topic]/prompts.md
```

## Trigger

Gọi khi user nhắn: "video mới", "new video", "full production", "làm video mới"
