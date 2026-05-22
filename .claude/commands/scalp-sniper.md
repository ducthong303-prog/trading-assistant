# /scalp-sniper — Phân Tích Scalp Sniper Đa Khung Thời Gian

Phân tích chuyên sâu cho scalp trading: H1 structure → M5 entry zone → M1 sniper trigger.
Tự đặt 3 câu hỏi nền tảng, đọc toàn bộ indicator, vẽ visual alerts, xuất kế hoạch giao dịch đa kịch bản.

---

## Cú pháp

```
/scalp-sniper [PAIR]
```

- `PAIR` mặc định: `XAUUSD` nếu không chỉ định
- Không log lệnh — analysis-only. Muốn log → `/open` hoặc `/auto-trade`

---

## Bước 0 — Kết nối + Snapshot Cache

1. Parse PAIR từ message (mặc định `XAUUSD`).
2. Kiểm tra TradingView:

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

- `OK` → tiếp tục
- khác → `bash /Users/ttcenter/launch_tradingview.sh` → đợi "✅ CDP sẵn sàng!"

3. Kiểm tra snapshot cache:

```bash
python3 -c "
import json, time
try:
    d = json.load(open('/Users/ttcenter/tv_snapshot.json'))
    age = int(time.time()) - d.get('ts_unix', 0)
    sym = d.get('symbol', 'XAUUSD')
    print(f'AGE={age} SYM={sym}')
except:
    print('AGE=9999 SYM=NONE')
"
```

**Nếu AGE < 180 và SYM khớp PAIR:** → SKIP Bước 1 & 2, nhảy thẳng Bước 3.

---

## Bước 1 — H1 Structure (nếu snapshot stale)

```
mcp__tradingview__chart_set_symbol(PAIR)
mcp__tradingview__chart_set_timeframe("60")
```

Gọi **song song** (3 calls):

```
data_get_ohlcv(count=30, summary=true)
data_get_pine_labels(study_filter="Smart Money", max_labels=12)
data_get_study_values
```

Phân tích H1:
- CHoCH/BOS gần nhất? Vị trí so với giá?
- FVG H1 chưa fill? → "nam châm" giá
- Xu hướng H1: BULLISH / BEARISH / SIDEWAYS
- DOL (Direction of Liquidity): giá đang về BSL hay SSL?

---

## Bước 2 — M5 Full Snapshot (nếu snapshot stale)

```
mcp__tradingview__chart_set_timeframe("5")
```

Gọi **song song** (8 calls):

```
data_get_ohlcv(count=50)
data_get_study_values
data_get_pine_labels(study_filter="Smart Money", max_labels=12)
data_get_pine_labels(study_filter="HTF Power", max_labels=4)
data_get_pine_lines(study_filter="Volume Profile")
data_get_pine_labels(study_filter="Liquidity", max_labels=25)
data_get_pine_boxes(study_filter="FVG")
capture_screenshot("chart")
```

Pipe vào parser để ghi snapshot mới:

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

## Bước 3 — 3 Câu Hỏi Nền Tảng (Self-Ask)

Trước khi tiếp tục phân tích, **phải trả lời 3 câu hỏi**:

### Câu 1: Thanh khoản đã bị quét chưa?
- Đọc SMC labels — EQH/EQL nào bị sweep gần đây?
- Sweep BSL hay SSL? Volume lúc sweep?
- Sweep Internal (continuation) hay External (reversal)?
- Liquidity Swings: level nào có count cao (≥50) — đã bị lấy chưa?

### Câu 2: Xu hướng hiện tại là gì?
- H1: CHoCH/BOS hướng nào? DOL đang về đâu?
- M5: Cấu trúc ngắn hạn — BOS/CHoCH gần nhất?
- SMC labels từ snapshot: structure direction?
- Xác nhận: `htf_bias = BULLISH | BEARISH | SIDEWAYS`

### Câu 3: Nếu giá chạm hỗ trợ/kháng cự mạnh, xác suất đảo chiều?
- POI nào gần giá nhất? (H1 OB, H1 FVG, VP HVN/LVN)
- FVG/iFVG boxes: zone nào active?
- RSI: oversold (<35) hay overbought (>65)?
- MACD histogram: đang tăng hay giảm?
- Wyckoff phase: Spring? UTAD? Accumulation?
- → Trả lời: "Cao" nếu ≥3 yếu tố đảo chiều / "Trung bình" nếu 1-2 / "Thấp" nếu 0

---

## Bước 4 — Confluence Score §2 + TV Bonus

| Bước | Điều kiện | Điểm |
|------|-----------|------|
| 1 — HTF Bias | SMC (D1/H4 embedded) + H1 cùng hướng | 0/1 |
| 2 — Killzone | Giờ VN: 14–17h (London) hoặc 19–22h (NY) | 0/1 |
| 3 — Volume | Vol H1 nến BOS/CHoCH > SMA(20) | 0/1 |
| 4 — Liquidity Sweep | EQH/EQL hoặc PDH/PDL bị quét + displacement | 0/1 |
| 5 — DXY/SMT | RSI divergence + MACD direction từ snapshot | 0/1 |

**TV Bonus (tối đa +2):**

| Điều kiện | Bonus |
|-----------|-------|
| RSI < 35 (oversold) hoặc > 65 (overbought) tại POI | +1 |
| MACD histogram khớp hướng trade | +1 |
| PO3 phase: accumulation (LONG) / distribution (SHORT) | +1 |
| SMC CHoCH/BOS khớp hướng trade | +1 |

→ `effective = base (0–5) + bonus (0–2)` — tối đa 7

**Ngưỡng:**
- base ≤ 2 → "Thị trường chưa sẵn sàng." — dừng
- base = 3 + bonus = 0 → Đứng ngoài
- base = 3 + bonus ≥ 1 → Actionable (xác nhận thêm)
- base ≥ 4 → Actionable

---

## Bước 5 — M1 Sniper Precision

```
mcp__tradingview__chart_set_timeframe("1")
data_get_ohlcv(count=20)
capture_screenshot("chart")
```

Tìm M1 trigger:
- **3A Engulfing:** Body ≥ 50%, volume > SMA×1.2
- **3B Wick Rejection:** Wick ≥ 50%, volume > SMA×1.5, close trong 30% đối diện
- **3C Sniper FVG:** Giá trong FVG M5 + M1 rejection + volume > SMA×1.2
- **3E Delta Flip:** (nếu có OF indicator) Flip ≠ 0 + vol ≥ 1.5×SMA

---

## Bước 6 — Kế Hoạch Giao Dịch Đa Kịch Bản

Xác định **3–4 kịch bản** (không chỉ 1):

### Kịch bản A — Primary (xác suất cao nhất)
- Setup: [A+1/A+2/A+3/A1/A2/B1/B2/C1]
- Điều kiện: [mô tả cụ thể]
- Entry / SL / TP1 / TP2 / RR / Size

### Kịch bản B — Backup (nếu giá đi sâu hơn)
- Entry zone xa hơn, RR tốt hơn
- Điều kiện kích hoạt

### Kịch bản C — Counter-DOL (chỉ nếu có tín hiệu đảo chiều rõ)
- Điều kiện: CHoCH + volume spike + close ngoài vùng
- Half size, SL chặt

### Kịch bản D — Đứng ngoài
- Điều kiện khiến tất cả setup mất hiệu lực

---

## Bước 7 — Vẽ Visual Alerts

Dùng `draw_shape` vẽ **5–6 horizontal lines** tại key levels:

| Level | Màu | Ý nghĩa |
|-------|------|---------|
| Entry zone chính | `#00ff00` (xanh lá) | "LONG/SHORT ENTRY — [lý do]" |
| Entry zone backup | `#00cc00` (xanh nhạt) | "BACKUP — [lý do]" |
| SL level | `#ff0000` (đỏ) | "SL — [mức] — Invalid nếu phá" |
| Resistance gần nhất | `#ff9900` (cam) | "Resistance — [tên level]" |
| Support gần nhất | `#ff9900` (cam) | "Support — [tên level]" |
| BSL/SSL target | `#3399ff` (xanh dương) | "BSL/SSL — [volume]" |

Mỗi line kèm text mô tả ngắn gọn.

---

## Bước 8 — Output §7 Signal Format

**Khôi phục timeframe về M5** trước khi output.

```
⚡ SCALP SNIPER — [PAIR] @ [giá hiện tại]

━━━ 3 CÂU HỎI NỀN TẢNG ━━━
Q1 — Thanh khoản đã quét?
  [trả lời chi tiết: SSL/BSL nào? Volume? Internal/External?]

Q2 — Xu hướng?
  H1: [BULL/BEAR/SIDE] — CHoCH/BOS tại [giá] — DOL về [BSL/SSL]
  M5: [structure ngắn hạn]

Q3 — Đảo chiều tại S/R mạnh?
  POI gần nhất: [tên POI] tại [giá]
  RSI: [giá trị] — MACD: [histogram]
  Wyckoff: [phase nếu rõ]
  → Xác suất đảo chiều: [Cao / Trung bình / Thấp]

━━━ CONFLUENCE SCORE ━━━
Phân loại:  [setup code + tên]
Trạng thái: [Reversal / Continuation / Sideway]

Confluence: x/5 base + y TV bonus = z/7
  (+1) HTF Bias        — [✅/❌] [lý do]
  (+1) Killzone        — [✅/❌] [session + giờ]
  (+1) Volume          — [✅/❌] [vol vs SMA]
  (+1) Liquidity Sweep — [✅/❌] [level bị quét]
  (+1) DXY/SMT         — [✅/❌/N/A] [lý do]
  TV Bonus:
  (+?) [RSI/MACD/PO3/SMC] — [lý do cụ thể]

Hành động: [Vào ngay / Đặt Limit / Đợi xác nhận / Đứng ngoài]

━━━ KẾ HOẠCH ĐA KỊCH BẢN ━━━
🅰 Primary:
  Entry: ...  SL: ...  TP1: ...  TP2: ...  RR: x:1  Size: ...%
  Trigger: [điều kiện cụ thể]

🅱 Backup:
  Entry: ...  SL: ...  TP1: ...  RR: x:1  Size: ...%
  Kích hoạt khi: [điều kiện]

🅲 Counter-DOL: (nếu applicable)
  Entry: ...  SL: ...  TP1: ...  RR: x:1  Size: 50%

🅳 Đứng ngoài nếu: [điều kiện invalid]

━━━ FVG & KEY LEVELS ━━━
FVG M5 active:  [top–bottom] — [số lượng boxes]
iFVG:           [top–bottom nếu có]
VP POC:         [giá] — giá đang [trên/dưới] = [premium/discount]
Key S/R:        R: [giá] ([tên]) | S: [giá] ([tên])
Liquidity:      BSL: [giá] ([volume]) | SSL: [giá] ([volume])

━━━ RỦI RO ━━━
Tại sao lệnh này có thể THUA?
  1. [lý do 1]
  2. [lý do 2]
  3. [lý do 3]

📊 Chart: [screenshot path]
📍 Visual alerts đã vẽ: [số lượng] đường tại [các mức]
```

---

## Bước 9 — Cleanup

- Khôi phục timeframe về M5
- Nhắc user: *"Khi giá chạm bất kỳ đường nào trên chart, gọi tôi phân tích ngay."*

---

## Quy tắc bắt buộc

- **Không log lệnh** — analysis-only. Muốn log → `/open` hoặc `/auto-trade`
- **Luôn tự hỏi 3 câu hỏi** trước khi đưa ra kết luận
- **Luôn đưa 3–4 kịch bản** — không chỉ 1 "best case"
- **Luôn vẽ visual alerts** — 5–6 đường ngang tại key levels
- **Luôn chụp 2 screenshots** — M5 overview + M1 sniper
- Score ≤ 2 → **"Thị trường chưa sẵn sàng."** + lý do, không output §7
- **Không tự động download/cài đặt công cụ** — chỉ dùng MCP tools có sẵn
- **Không dùng `ui_evaluate`** để chạy JS trên TradingView
- Nếu `alert_create` fail → fallback sang `draw_shape` horizontal lines
- Giữ timeframe M5 khi kết thúc

## Token Budget

| Trường hợp | MCP calls | Token ~ước lượng |
|-----------|-----------|-----------------|
| Snapshot fresh (< 3 phút) | 5–7 | ~2,500 |
| Snapshot stale | 14–16 | ~6,000 |
| TV không chạy + stale | 14–16 + launch | ~7,000 |
