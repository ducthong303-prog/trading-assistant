# channels/ — Multi-Channel Output

Mỗi kênh YouTube có thư mục riêng. Hiện tại có 1 kênh đang hoạt động.

## Cấu trúc mỗi kênh

```
channels/[channel-name]/
├── scripts/       ← Final scripts (.md)
├── images/        ← Image prompts + generated .jpeg
├── thumbnails/    ← Thumbnail prompts + generated .jpeg
├── audio/         ← TTS output (.mp3)
├── video/         ← Final rendered video (.mp4)
└── publishing/    ← Publishing logs + A/B test results
```

## Thêm kênh mới

```bash
mkdir -p channels/[new-channel]/{scripts,images,thumbnails,audio,video,publishing}
# Đăng ký trong configs/channels.json
```

## Kênh hiện tại

| Kênh | Trạng thái | Videos |
|------|-----------|--------|
| `bible-explainer` | Active | 1 (Fear Not, 2026-05-14) |
