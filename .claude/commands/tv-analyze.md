# /tv-analyze — Phân Tích Thị Trường Đầy Đủ Qua TradingView

Đọc toàn bộ chart D1→H4→H1→M5 + 6 chỉ báo TradingView, tính Confluence Score §2 (+ TV bonus),
xuất §7 Signal Output. **Không log lệnh** — analysis-only.

---

## Cú pháp

```
/tv-analyze [PAIR]
```

- `PAIR` mặc định: `BTCUSD` nếu không chỉ định
- Ví dụ: `/tv-analyze ETHUSD`, `/tv-analyze XAUUSD`

---

## Bước 0 — Khởi động & kiểm tra

1. Parse PAIR từ message (mặc định `BTCUSD`).
2. `mcp__tradingview__tv_health_check` — nếu FAIL → `bash /Users/ttcenter/launch_tradingview.sh`
3. `mcp__tradingview__chart_set_symbol(PAIR)` → điều hướng đến pair.
4. `mcp__tradingview__chart_get_state` → xác nhận symbol + liệt kê indicators đang active.

---

## Bước 1 — M5 Snapshot (gọi song song)

```
data_get_ohlcv(count=50)                                           → M5 bars
data_get_study_values                                              → RSI + MACD values
data_get_pine_labels(study_filter="Smart Money", max_labels=10)    → BOS/CHoCH/EQH/EQL
data_get_pine_labels(study_filter="HTF Power", max_labels=4)       → PO3 key levels
data_get_pine_lines(study_filter="Volume Profile")                 → VP levels → POC estimate
data_get_pine_labels(study_filter="Liquidity", max_labels=20)      → swing levels + strength
```

Pipe tất cả vào parser để lấy TV snapshot:

```bash
echo '{
  "price": CURRENT_PRICE,
  "study_values": STUDY_VALUES_JSON,
  "smc_labels":   SMC_LABELS_JSON,
  "po3_labels":   PO3_LABELS_JSON,
  "vp_lines":     VP_LINES_JSON,
  "liq_labels":   LIQ_LABELS_JSON
}' | python3 /Users/ttcenter/tv_indicator_parser.py
```

Ghi nhớ từ output:
- **TV Bias**: BULLISH / BEARISH / MIXED
- **Reversal Warning**: có không? Direction? (nếu có → **báo ngay**)
- **TV Bonus**: +0/+1/+2
- **Key levels**: EQH/EQL, nearest S/R, PO3 low/high, VP POC/HVN

---

## Bước 2 — HTF Bias D1

```
chart_set_timeframe("D")
data_get_ohlcv(count=20, summary=true)
```

Phân tích:
- Trend (HH/HL liên tiếp hay LL/LH)?
- BOS gần nhất phá đỉnh hay đáy?
- Pha: Accumulation / Distribution / Mark-up / Mark-down?

→ `htf_d1 = BULLISH | BEARISH | SIDEWAYS`

---

## Bước 3 — H4 Structure

```
chart_set_timeframe("240")
data_get_ohlcv(count=30, summary=true)
```

Phân tích:
- CHoCH / BOS H4 rõ không?
- Giá đang retest OB/FVG H4 không?
- Cùng hướng D1? → `htf_score = 1` nếu đồng thuận, `0` nếu xung đột

→ `htf_h4 = BULLISH | BEARISH | SIDEWAYS`

---

## Bước 4 — H1 Confluence Score §2

```
chart_set_timeframe("60")
data_get_ohlcv(count=30)
```

Chấm §2 (5 bước gốc):

| Bước | Điều kiện | Điểm |
|------|-----------|------|
| 1 — HTF Bias | D1+H4 cùng hướng | 0/1 |
| 2 — Killzone | Giờ VN: 14–17h (London) hoặc 19–22h (NY) | 0/1 |
| 3 — Volume | Vol H1 nến BOS/CHoCH > SMA(20) | 0/1 |
| 4 — Liquidity Sweep | Asia H/L hoặc PDH/PDL bị quét + displacement | 0/1 |
| 5 — DXY/SMT | DXY Supply/Demand hoặc RSI divergence + MACD MTF | 0/1 |

**TV Bonus** (từ Bước 1):

| Điều kiện | Bonus |
|-----------|-------|
| RSI < 35 hoặc > 65 tại POI | +1 |
| MACD histogram khớp hướng trade | +1 |
| PO3 phase: accumulation (LONG) / distribution (SHORT) | +1 |
| SMC CHoCH/BOS khớp hướng trade | +1 |

→ Tối đa +2 bonus. `effective_score = base + bonus`

**Ngưỡng quyết định:**
- base ≤ 2 → **"Thị trường chưa sẵn sàng."** — dừng phân tích
- base 3 + bonus 0 → Đứng ngoài / chờ xác nhận thêm
- base 3 + bonus ≥ 1 → Actionable (coi như 4)
- base ≥ 4 → Actionable

---

## Bước 5 — M5 Entry Setup

```
chart_set_timeframe("5")
data_get_ohlcv(count=50)
capture_screenshot("chart")
```

Xác định:
1. **Setup** theo §4: A+1 / A+2 / A+3 / A1 / A2 / B1 / B2 / C1
   - A+3 ưu tiên nếu RSI divergence + SMC CHoCH gần giá
   - B1 nếu đang trong Silver Bullet window (14–15h hoặc 21–22h VN)
   - C1 nếu phát hiện Breaker Block qua TV snapshot
2. **FVG** — đọc từ `data_get_pine_boxes(study_filter="FVG")` nếu có, hoặc tính từ M5 bars
3. **Key levels** từ TV snapshot: EQH/EQL, Liquidity Swings, VP POC/HVN, PO3 boundaries
4. **Trigger** có chưa? 3A Engulfing / 3B Wick Rejection / 3C Sniper FVG

Tính RR:
```
entry  = FVG midpoint hoặc giá hiện tại
sl     = phía sau wick sweep + buffer 1–2 pts
tp1    = mức liquidity gần nhất (EQH/EQL hoặc VP HVN)
risk   = abs(entry - sl)
reward = abs(tp1 - entry)
rr     = round(reward / risk, 1)
```

**RR guard:** `rr < 1.5` → không đề xuất entry ("RR thấp — setup chưa đủ điều kiện")

---

## Bước 6 — Pre-entry Check & Output §7

**Bắt buộc trả lời trước khi output signal:**
> "Tại sao lệnh này có thể THUA?"
> (Liệt kê 3–5 lý do cụ thể từ data, không bịa)

**Xuất §7 Signal Output** theo format chuẩn:

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

📊 TV Snapshot:
  SMC Structure : [bullish/bearish/mixed]
  PO3 Phase     : [accumulation/manipulation/distribution]
  VP POC        : [giá POC] — giá đang [trên/dưới] = [premium/discount]
  Key S/R       : R [resistance gần nhất] | S [support gần nhất]
  Reversal Warn : [YES / NO — lý do]
```

---

## Quy tắc bắt buộc

- **Không log lệnh** — skill này chỉ phân tích, user quyết định entry
- Nếu muốn log → dùng `/open` hoặc `/auto-trade`
- Score ≤ 2 → chỉ nói "Thị trường chưa sẵn sàng." + lý do ngắn gọn, không output signal
- Luôn chụp screenshot M5 trước khi output §7
- Khôi phục timeframe về M5 sau khi hoàn tất
