# archive/ — Project Archive

Dự án cũ, backups, và file legacy.

## Cấu trúc

```
archive/
├── 2026-05-14-fear-not/     ← Video project đầu tiên (ảnh + thumbnails gốc)
│   ├── images/              ← 24 ảnh watercolor
│   └── thumbnails/          ← 3 thumbnails
├── backups/                 ← ZIP backups của skill files (May 2026)
├── legacy/                  ← File hệ thống cũ (MIGRATION_PLAN.md, cleanup_output.sh)
├── legacy-modules/          ← Module cũ từ v2 (đã migrate sang brain/)
├── legacy-workflows/        ← Workflow cũ từ v2 (đã migrate sang brain/)
└── competitor-analysis.xlsx ← Phân tích đối thủ (từ file Excel gốc)
```

## Quy tắc

- Đặt dự án cũ vào thư mục `YYYY-MM-DD-[topic]/`
- Backup ZIP vào `backups/`
- File legacy vào `legacy/`
- **Không xoá** — mọi thứ có thể khôi phục
