# /tv-analyze — Phân Tích Thị Trường Đầy Đủ Qua TradingView

Đọc chart M5 + H1 + 6 chỉ báo TradingView, tính Confluence Score §2 (+ TV bonus),
xuất §7 Signal Output. **Không log lệnh** — analysis-only.

---

## Cú pháp

```
/tv-analyze [PAIR]
```

- `PAIR` mặc định: `BTCUSD` nếu không chỉ định

---

## Bước 0 — Kết nối nhanh (không dùng MCP)

1. Parse PAIR từ message (mặc định `BTCUSD`).
2. Kiểm tra TradingView bằng curl:

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

- `OK` → tiếp tục Bước 0.5 (không cần gọi `tv_health_check`)
- `NO_CHART` hoặc `DOWN` → `bash /Users/ttcenter/launch_tradingview.sh` → đợi "✅ CDP sẵn sàng!" → tiếp tục

3. Nếu `TV_STATUS=OK`: **KHÔNG** gọi `chart_set_symbol` trước — đọc snapshot trước (Bước 0.5).

---

## Bước 0.5 — Kiểm tra Snapshot Cache

```bash
python3 -c "
import json, time, sys
try:
    d = json.load(open('/Users/ttcenter/tv_snapshot.json'))
    age = int(time.time()) - d.get('ts_unix', 0)
    sym = d.get('symbol', 'BTCUSD')
    print(f'AGE={age} SYM={sym}')
except:
    print('AGE=9999 SYM=NONE')
"
```

**Nếu AGE < 180 và SYM khớp PAIR:**
→ **SKIP Bước 1 và 2** — dùng snapshot đã có, nhảy thẳng đến Bước 3.
→ Thông báo: `"Dùng snapshot cache ({AGE}s cũ) — bỏ qua collect data."`

**Nếu AGE ≥ 180 hoặc SYM khác:**
→ Tiếp tục Bước 1.

---

## Bước 1 — M5 Snapshot (chỉ chạy khi snapshot stale)

Điều hướng chart:
```
mcp__tradingview__chart_set_symbol(PAIR)
mcp__tradingview__chart_set_timeframe("5")
```

Gọi **song song** (6 calls cùng lúc):

```
data_get_ohlcv(count=50)                                           → M5 bars
data_get_study_values                                              → RSI + MACD values
data_get_pine_labels(study_filter="Smart Money", max_labels=10)    → BOS/CHoCH/EQH/EQL
data_get_pine_labels(study_filter="HTF Power", max_labels=4)       → PO3 key levels
data_get_pine_lines(study_filter="Volume Profile")                 → VP levels → POC
data_get_pine_labels(study_filter="Liquidity", max_labels=20)      → swing levels + strength
```

Pipe vào parser (ghi snapshot mới):

```bash
echo '{
  "symbol": "PAIR",
  "price": CURRENT_PRICE,
  "study_values": STUDY_VALUES_JSON,
  "smc_labels":   SMC_LABELS_JSON,
  "po3_labels":   PO3_LABELS_JSON,
  "vp_lines":     VP_LINES_JSON,
  "liq_labels":   LIQ_LABELS_JSON
}' | python3 /Users/ttcenter/tv_indicator_parser.py
```

---

## Bước 2 — H1 Structure (chỉ chạy khi snapshot stale)

```
mcp__tradingview__chart_set_timeframe("60")
data_get_ohlcv(count=30, summary=true)
```

**Lưu ý:** Không cần D1/H4 OHLCV riêng — TV indicators (SMC, PO3) đã encode HTF bias.
Đọc H1 để: phát hiện CHoCH/BOS H1, tìm FVG H1, xác nhận trend direction.

→ `htf_bias = BULLISH | BEARISH | SIDEWAYS` (từ H1 structure + SMC labels snapshot)

---

## Bước 3 — Confluence Score §2

Dùng data từ snapshot (Bước 1) + H1 context (Bước 2, nếu chạy):

| Bước | Điều kiện | Điểm |
|------|-----------|------|
| 1 — HTF Bias | SMC labels (D1/H4 embedded) + H1 cùng hướng | 0/1 |
| 2 — Killzone | Giờ VN: 14–17h (London) hoặc 19–22h (NY) | 0/1 |
| 3 — Volume | Vol H1 nến BOS/CHoCH > SMA(20) | 0/1 |
| 4 — Liquidity Sweep | EQH/EQL hoặc PDH/PDL bị quét (từ SMC labels) | 0/1 |
| 5 — DXY/SMT | RSI divergence + MACD direction từ snapshot | 0/1 |

**TV Bonus** (từ snapshot, tối đa +2):

| Điều kiện | Bonus |
|-----------|-------|
| RSI < 35 (oversold) hoặc > 65 (overbought) tại POI | +1 |
| MACD histogram khớp hướng trade | +1 |
| PO3 phase: accumulation_zone (LONG) / distribution_zone (SHORT) | +1 |
| SMC CHoCH/BOS khớp hướng trade | +1 |

→ `effective_score = base (0–5) + bonus (0–2)`

**Ngưỡng quyết định:**
- base ≤ 2 → **"Thị trường chưa sẵn sàng."** — dừng
- base 3 + bonus 0 → Đứng ngoài
- base 3 + bonus ≥ 1 → Actionable
- base ≥ 4 → Actionable

---

## Bước 4 — M5 Entry Setup

```
mcp__tradingview__chart_set_timeframe("5")
data_get_ohlcv(count=50)
mcp__tradingview__capture_screenshot("chart")
```

Xác định:
1. **Setup** theo §4: A+1 / A+2 / A+3 / A1 / A2 / B1 / B2 / C1
2. **FVG** từ `data_get_pine_boxes(study_filter="FVG")` hoặc tính từ M5 bars
3. **Key levels** từ snapshot: EQH/EQL, Liquidity Swings, VP POC/HVN, PO3 boundaries
4. **Trigger** có chưa? 3A Engulfing / 3B Wick Rejection / 3C Sniper FVG

Tính RR:
```
entry  = FVG midpoint hoặc giá hiện tại
sl     = phía sau wick sweep + buffer 1–2 pts
tp1    = mức liquidity gần nhất (HVN hoặc EQH/EQL)
rr     = round(abs(tp1 - entry) / abs(entry - sl), 1)
```

**RR guard:** `rr < 1.5` → dừng ("RR thấp — setup chưa đủ điều kiện")

---

## Bước 5 — Pre-entry Check & Output §7

**Bắt buộc:** "Tại sao lệnh này có thể THUA?" — 3–5 lý do từ data.

**Xuất §7 Signal Output:**

```
Phân loại:  [setup code + tên]
Trạng thái: [Reversal / Continuation / Sideway]

Confluence Score: x/5 base + y TV bonus = z/7
  (+1) HTF Bias        — D1/H4 cùng hướng?        [✅ / ❌]
  (+1) Killzone        — London/NY đang active?    [✅ / ❌]
  (+1) Volume          — Vol > SMA(20) xác nhận?   [✅ / ❌]
  (+1) Liquidity Sweep — Đã quét đỉnh/đáy?         [✅ / ❌]
  (+1) DXY/SMT         — DXY tại S/D hoặc diverge? [✅ / ❌ / N/A]
  TV Bonus:
  (+?) MACD / RSI / PO3 / SMC                      [lý do cụ thể]

Hành động: [Vào ngay / Đặt Limit / Đợi xác nhận / Đứng ngoài]

  Entry: ...
  SL:    ...
  TP1:   ...  (RR: x:1)
  TP2:   ...  (nếu có)
  Size:  ...%

📋 Rủi ro:
  1. [lý do có thể thua 1]
  2. [lý do có thể thua 2]
  3. ...

📊 TV Snapshot (cache: {AGE}s cũ):
  SMC Structure : [bullish/bearish/mixed]
  PO3 Phase     : [accumulation/manipulation/distribution]
  VP POC        : [giá POC] — giá đang [trên/dưới] = [premium/discount]
  Key S/R       : R [resistance gần nhất] | S [support gần nhất]
  Reversal Warn : [YES / NO — lý do]
```

---

## Quy tắc bắt buộc

- **Không log lệnh** — analysis-only. Muốn log → dùng `/open` hoặc `/auto-trade`
- Score ≤ 2 → "Thị trường chưa sẵn sàng." + lý do ngắn, không output §7
- Luôn chụp screenshot M5 trước khi output §7
- Khôi phục timeframe về M5 sau khi hoàn tất
- **Snapshot cache được ưu tiên** — không collect lại nếu còn mới (< 3 phút)

## Token Budget

| Trường hợp | MCP calls | Token ~ước lượng |
|-----------|-----------|-----------------|
| Snapshot fresh (< 3 phút) | 2–3 | ~1,500 |
| Snapshot stale | 10–11 | ~5,000 |
| TV không chạy + stale | 10–11 + launch | ~6,000 |
