# /tv-connect — Đảm Bảo TradingView Đang Chạy

Skill nhỏ dùng nội bộ bởi `/tv-analyze` và `/auto-trade`.
Mục tiêu: đảm bảo CDP port 9222 sẵn sàng + có tab TradingView — tối đa 3 bước.

---

## Bước 1 — Kiểm tra nhanh bằng curl (không dùng MCP)

```bash
TV_STATUS=$(curl -s --max-time 2 http://localhost:9222/json 2>/dev/null | python3 -c "
import json, sys
try:
    tabs = json.load(sys.stdin)
    tv = [t for t in tabs if 'tradingview' in t.get('url','')]
    print('OK' if tv else 'NO_CHART')
except:
    print('DOWN')
")
echo "TV_STATUS=$TV_STATUS"
```

- `OK` → Dừng, tiếp tục ngay. **Không cần MCP health check.**
- `NO_CHART` hoặc `DOWN` → Chuyển sang Bước 2.

---

## Bước 2 — Launch TradingView

```bash
bash /Users/ttcenter/launch_tradingview.sh
```

Đợi output `✅ CDP sẵn sàng!`. Nếu timeout → báo user:
```
❌ Không thể kết nối TradingView. Kiểm tra: cat /tmp/tv_chromium.log
```

---

## Bước 3 — Điều hướng đến pair

```
mcp__tradingview__chart_set_symbol(PAIR)
```

Xác nhận bằng `mcp__tradingview__chart_get_state` **chỉ khi** cần verify (không gọi mặc định).

---

## Quy tắc

- **Không gọi `tv_health_check` trước** — tốn 1 MCP call không cần thiết; `curl` check nhanh hơn.
- Tổng số MCP calls tối đa: 2 (chart_set_symbol + chart_get_state nếu cần).
- Skill này không phân tích, không đọc data.
