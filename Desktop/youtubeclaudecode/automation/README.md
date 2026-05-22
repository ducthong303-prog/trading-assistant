# automation/ — Utility Scripts

Scripts tự động hoá các tác vụ lặp lại.

## Scripts

| Script | Usage | Chức năng |
|--------|-------|-----------|
| `new-video.sh` | `bash automation/new-video.sh "Topic"` | Scaffold project structure mới |
| `organize-output.sh` | `bash automation/organize-output.sh` | Chuyển file từ img/thumb/ vào channels/ |
| `publish-checklist.sh` | `bash automation/publish-checklist.sh "topic"` | Kiểm tra mọi assets sẵn sàng trước upload |

## Thêm script mới

```bash
touch automation/new-script.sh
chmod +x automation/new-script.sh
```

Tất cả scripts phải:
- Có comment header giải thích usage
- Chấp nhận tham số (không hardcode)
- In trạng thái rõ ràng (✅/❌/⚠️)
