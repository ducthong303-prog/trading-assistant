# configs/ — Central Configuration

## Files

| File | Mô tả |
|------|--------|
| `channels.json` | Channel registry — danh sách kênh, trạng thái, target |

## Cấu trúc channels.json

```json
{
  "channels": [
    {
      "name": "channel-slug",
      "display_name": "Channel Name",
      "status": "active|inactive|planned",
      "niche": "mô tả",
      "style": "watercolor-bible-illustration",
      "competitors": ["Competitor 1", "Competitor 2"],
      "created": "YYYY-MM-DD",
      "videos_published": 0,
      "target_subs": 100000,
      "upload_schedule": "weekly"
    }
  ]
}
```

## Thêm kênh mới

1. Tạo thư mục: `mkdir -p channels/[slug]/{scripts,images,thumbnails,audio,video,publishing}`
2. Đăng ký trong `channels.json`
3. Tạo README.md cho kênh
