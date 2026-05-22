# /tv-auto-scan — Bật/Tắt Chế Độ Theo Dõi TradingView Tự Động (Zero Token)

Kích hoạt hệ thống giám sát TradingView 24/7 mà **không tốn token Claude**.
Mỗi 5 phút, cron tự động thu thập data và gửi Telegram nếu phát hiện tín hiệu.

---

## Cú pháp

```
/tv-auto-scan on [PAIR]    — bật chế độ tự động cho PAIR (mặc định BTCUSD)
/tv-auto-scan off          — tắt, về monitor mode
/tv-auto-scan status       — kiểm tra trạng thái hiện tại
/tv-auto-scan test         — chạy thử 1 lần, xem có signal không
```

---

## Kiến trúc (Zero Token)

```
cron mỗi 5 phút → market_monitor.py
  ├── trade_engine.py --silent    (Binance data)
  ├── [mode=auto] tv_collect.js   (Node.js + CDP, 1 process)
  │     └── 6 parallel CDP calls → tv_snapshot.json
  ├── tv_signal_engine.py         (Python, §2 Confluence logic)
  │     └── check signal → score, direction, levels
  └── send Telegram               (nếu signal hoặc cần alert)
```

**Không cần Claude, không tốn token — toàn bộ chạy trong cron.**

---

## Bước thực hiện khi `/tv-auto-scan on [PAIR]`

### Bước 1 — Ghi trading_mode.json

```bash
python3 -c "
import json, datetime
d = {'mode': 'auto', 'symbol': 'PAIR', 'activated_at': str(datetime.datetime.now())[:19]}
open('/Users/ttcenter/trading_mode.json','w').write(json.dumps(d, indent=2))
print('✅ Mode: AUTO SCAN')
"
```

### Bước 2 — Kiểm tra TradingView

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
```

- `OK` → tiếp tục
- `DOWN/NO_CHART` → `bash /Users/ttcenter/launch_tradingview.sh`

### Bước 3 — Chạy thử 1 lần để xác nhận pipeline hoạt động

```bash
cd /Users/ttcenter/tradingview-mcp && node tv_collect.js PAIR 2>/tmp/tv_err.log | \
  python3 /Users/ttcenter/tv_indicator_parser.py
```

Kết quả thành công → in summary snapshot.

```bash
python3 /Users/ttcenter/tv_signal_engine.py
```

Kết quả: signal hoặc "Market chưa sẵn sàng".

### Bước 4 — Xác nhận với user

```
✅ TV Auto-Scan đã bật cho PAIR.

Hệ thống:
  • Cron chạy mỗi 5 phút — tv_collect.js → tv_signal_engine.py → Telegram
  • Không cần Claude — ZERO TOKEN
  • Telegram báo khi: signal actionable (score ≥ 4) hoặc Reversal Warning 3/3
  • tv_watchdog.sh giữ TradingView luôn chạy khi mode=auto

Signal threshold:
  • Score ≥ 4/5 base + bonus → ALERT có âm thanh
  • Score 3/5 + bonus ≥ 1   → ALERT silent
  • Score ≤ 2               → Im lặng (không gửi)

Để tắt: /tv-auto-scan off hoặc "dừng auto trading"
```

---

## Bước thực hiện khi `/tv-auto-scan off`

1. Ghi `trading_mode.json` → `{"mode": "monitor", ...}`
2. Báo user: "Đã tắt TV Auto-Scan. Cron vẫn chạy market_monitor.py (Binance only)."

---

## Bước thực hiện khi `/tv-auto-scan status`

```bash
cat /Users/ttcenter/trading_mode.json
python3 -c "
import json, time
s = json.load(open('/Users/ttcenter/tv_snapshot.json'))
age = int(time.time()) - s.get('ts_unix', 0)
print(f'Snapshot: {s[\"symbol\"]} @ {s[\"price\"]:,} | age={age}s | bias={s[\"tv_bias\"]}')
"
```

Output:
```
Mode    : AUTO (BTCUSD, activated 2026-05-09 19:00)
Snapshot: BTCUSD @ 80,239 | age=87s | bias=BULLISH
Cron    : chạy mỗi 5 phút
TV      : ✅ Chromium đang chạy
```

---

## Bước thực hiện khi `/tv-auto-scan test`

Chạy pipeline thủ công 1 lần:

```bash
cd /Users/ttcenter/tradingview-mcp
node tv_collect.js BTCUSD 2>/dev/null | python3 /Users/ttcenter/tv_indicator_parser.py
python3 /Users/ttcenter/tv_signal_engine.py
```

Báo cáo kết quả đầy đủ:
- Snapshot summary (bias, structure, RSI, MACD, PO3)
- Signal (nếu có): direction, setup, score, entry/SL/TP/RR
- Lý do không có signal (nếu không có)

---

## Files quan trọng

| File | Vai trò |
|------|---------|
| `tradingview-mcp/tv_collect.js` | Node.js CDP collector — 1 process, 6 parallel calls |
| `tv_indicator_parser.py` | Parse raw data → tv_snapshot.json |
| `tv_signal_engine.py` | §2 Confluence Score + signal detection |
| `market_monitor.py` | Cron runner — gọi TV pipeline khi mode=auto |
| `tv_watchdog.sh` | Giữ TradingView Chromium luôn chạy |
| `tv_snapshot.json` | Cache 5 phút — tránh collect liên tục |
| `trading_mode.json` | Switch mode: auto / monitor |

---

## Quy tắc

- **Không gửi signal khi score ≤ 2** — tránh noise
- **RR < 1.5 → reject** — không đề xuất entry rủi ro cao
- **Snapshot cache 4 phút** — nếu còn mới thì dùng, không collect lại
- **Graceful fallback**: nếu TV không chạy → market_monitor vẫn gửi Binance data bình thường
- **Skill này không log lệnh** — chỉ phát tín hiệu. Muốn log → `/open` hoặc `/auto-trade`
