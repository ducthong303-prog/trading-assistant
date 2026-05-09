# /monitor-mode — Quay Lại Chế Độ Theo Dõi Tự Động

Tắt chế độ Auto Trading, quay về chế độ Monitor bình thường (cron-based).

---

## Cú pháp kích hoạt

- `"dừng auto trading"`
- `"quay lại chế độ theo dõi"`
- `"về monitor mode"`
- `"tắt auto"`
- `"thoát auto trading"`

---

## Bước thực hiện

### Bước 1 — Kiểm tra lệnh đang mở

Đọc `trade_log.json` xem có lệnh `status: OPEN` nào không.

- Nếu **có lệnh OPEN**: hiển thị danh sách + nhắc nhở:
  ```
  ⚠️ Còn [N] lệnh đang mở:
    • TS_XXXXXX_01  BTCUSD LONG  Entry: 80,420  P&L: ...
  Lệnh sẽ tiếp tục được theo dõi bởi cron market_monitor.py.
  Tôi sẽ không chủ động phân tích thêm cho đến khi bạn kích hoạt lại Auto Trading.
  ```
- Nếu **không có lệnh mở**: tiếp tục ngay

### Bước 2 — Ghi trạng thái

```bash
python3 -c "
import json, datetime
d = {'mode': 'monitor', 'deactivated_at': str(datetime.datetime.now())[:19]}
open('/Users/ttcenter/trading_mode.json','w').write(json.dumps(d, indent=2))
print('✅ Mode: MONITOR')
"
```

### Bước 3 — Xác nhận với user

```
✅ Đã chuyển về Monitor Mode.

Hệ thống:
  • Cron market_monitor.py tiếp tục chạy mỗi 5 phút
  • Telegram tự động báo: zone changes, setup signals, hard alerts
  • Lệnh đang mở được theo dõi và đóng tự động khi SL/TP chạm

Để phân tích thủ công: nhắn tên pair hoặc "phân tích thị trường"
Để bắt đầu lại Auto Trading: nhắn "bắt đầu auto trading [PAIR]"
```

---

## Sự khác biệt giữa 2 chế độ

| | Monitor Mode | Auto Trading Mode |
|---|---|---|
| Nguồn dữ liệu | Binance API (qua trade_engine.py) | TradingView MCP (chart trực tiếp) |
| Phân tích | Khi user hỏi | Chủ động theo chu kỳ |
| Log lệnh | User nhập cú pháp `/open` | Claude tự log khi score ≥ 4 |
| TradingView | Không cần mở | Phải mở + kết nối |
| Cron Telegram | ✅ Chạy | ✅ Vẫn chạy |
| Auto-close SL/TP | ✅ market_monitor.py | ✅ market_monitor.py |
