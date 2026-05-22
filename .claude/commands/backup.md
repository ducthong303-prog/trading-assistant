# /backup — Tạo Stable Backup

Tạo snapshot toàn bộ code cốt lõi vào `stable_version/`.

## Cú pháp

```
/backup [label]
```

- `label` (tùy chọn): nhãn mô tả bản backup, ví dụ `before_refactor`
- Không có label → timestamp thuần: `backup_20260509_054016`
- Có label → `backup_20260509_054016_before_refactor`

## Bước thực hiện

1. Chạy:
```bash
bash /Users/ttcenter/backup_stable.sh [label]
```

2. Xác nhận output với user:
```
✅ Backup hoàn tất
   Vị trí : /Users/ttcenter/stable_version/backup_YYYYMMDD_HHMMSS
   Files   : 14 (8 core + 6 commands)
   Latest  : /Users/ttcenter/stable_version/latest → backup_YYYYMMDD_HHMMSS
```

## Để restore

```bash
./restore_stable.sh          # khôi phục bản latest
./restore_stable.sh list     # xem tất cả bản backup
./restore_stable.sh backup_20260509_054016   # khôi phục bản cụ thể
```
