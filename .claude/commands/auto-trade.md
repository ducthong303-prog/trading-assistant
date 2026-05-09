# /auto-trade — Chế Độ Phân Tích & Trading Tự Động

Khi user kích hoạt, Claude **chủ động mở TradingView, đọc đồ thị, phân tích theo CLAUDE.md §1–§5,
và log lệnh tự động nếu đủ điều kiện** — không cần user hỏi từng bước.

---

## Cú pháp kích hoạt

- `"bắt đầu auto trading [PAIR]"` — PAIR mặc định BTCUSD
- `"auto trade [PAIR]"`
- `"chế độ tự động [PAIR]"`
- `"tự động trading [PAIR]"`

---

## Bước 1 — Khởi động

1. Parse PAIR từ message (mặc định: `BTCUSD`).
2. Ghi file trạng thái:

```bash
python3 -c "
import json, datetime
d = {'mode': 'auto', 'symbol': 'BTCUSD_PAIR', 'activated_at': str(datetime.datetime.now())[:19]}
open('/Users/ttcenter/trading_mode.json','w').write(json.dumps(d, indent=2))
print('✅ Mode: AUTO')
"
```

_(thay `BTCUSD_PAIR` bằng pair thực tế)_

3. Chạy `mcp__tradingview__tv_health_check`:
   - Nếu OK → tiếp tục bước 4
   - Nếu FAIL → chạy launch script:
     ```bash
     bash /Users/ttcenter/launch_tradingview.sh
     ```
     Script tự mở Chromium + TradingView với CDP port 9222. Đợi output "✅ CDP sẵn sàng!" rồi `tv_health_check` lại.
   - Nếu vẫn FAIL → báo user kiểm tra log: `cat /tmp/tv_chromium.log`

4. `mcp__tradingview__chart_set_symbol(symbol)` → điều hướng đến pair.

---

## Bước 1.5 — Đọc Chỉ Báo TradingView

Gọi **song song** (không cần đợi nhau):

```
data_get_study_values                                          → RSI + MACD values
data_get_pine_labels(study_filter="Smart Money", max_labels=10) → BOS/CHoCH/EQH/EQL
data_get_pine_labels(study_filter="HTF Power")                 → PO3 key levels (4 labels)
data_get_pine_lines(study_filter="Volume Profile")             → VP levels → POC estimate
data_get_pine_labels(study_filter="Liquidity", max_labels=20)  → swing levels + strength
```

Sau khi có data, pipe vào parser để lấy structured snapshot:

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

Đọc output và ghi nhớ:
- **TV Bias**: BULLISH / BEARISH / MIXED
- **Reversal Warning**: có không? Direction?
- **TV Bonus**: +0/+1/+2 điểm Confluence bổ sung
- **Key levels**: EQH/EQL gần giá + resistance/support từ Liquidity Swings
- **PO3 Phase**: accumulation / manipulation / distribution zone
- **VP POC**: giá đang trên hay dưới POC?

> Nếu output có `⚠️ CẢNH BÁO ĐỔI CHIỀU` → **báo ngay cho user** + kiểm tra lệnh OPEN đang có.

---

## Bước 2 — HTF Bias (D1)

```
chart_set_timeframe("D")
data_get_ohlcv(count=20, summary=true)
```

Phân tích:
- Xu hướng: Trending up (HH/HL liên tiếp)? Trending down (LL/LH)? Sideway?
- BOS gần nhất: phá đỉnh hay phá đáy?
- Giai đoạn: Accumulation / Distribution / Mark-up / Mark-down?

→ Kết luận `htf_d1 = BULLISH | BEARISH | SIDEWAYS`

---

## Bước 3 — H4 Structure

```
chart_set_timeframe("240")
data_get_ohlcv(count=30)
data_get_study_values
```

Phân tích:
- CHoCH / BOS H4 rõ không?
- Giá đang retest OB/FVG H4 không?
- H4 cùng hướng D1? → **HTF score +1** nếu D1 và H4 cùng bias

→ Kết luận `htf_h4 = BULLISH | BEARISH | SIDEWAYS`
→ Chấm: `htf_score = 1` nếu D1 + H4 cùng hướng, `0` nếu không

---

## Bước 4 — H1 Confluence §2

```
chart_set_timeframe("60")
data_get_ohlcv(count=30)
data_get_study_values
```

Chấm §2 Confluence (5 bước gốc + TV bonus):

| Bước | Điều kiện | Điểm |
|------|-----------|------|
| 1 — HTF Bias | D1+H4 cùng hướng | `htf_score` (0/1) |
| 2 — Killzone | Giờ VN trong 14–17h (London) hoặc 19–22h (NY) | 0/1 |
| 3 — Volume | Vol H1 nến BOS/CHoCH > SMA(20)? Dùng `Volume` study | 0/1 |
| 4 — Liquidity Sweep | Asia H/L hoặc PDH/PDL bị quét? **Ưu tiên đọc từ SMC labels (EQH/EQL sweep)** | 0/1 |
| 5 — DXY/SMT | DXY Supply/Demand? **RSI Divergence Indicator + MACD MTF phân kỳ?** | 0/1 |

**TV Bonus từ Bước 1.5 (cộng thêm vào score, tối đa +2):**

| TV Indicator | Điều kiện | Bonus |
|-------------|-----------|-------|
| RSI Divergence | RSI < 35 (oversold) hoặc > 65 (overbought) tại POI | +1 |
| MACD MTF | Histogram đảo chiều phù hợp hướng trade | +1 |
| PO3 Phase | Price ở accumulation_zone (LONG) / distribution_zone (SHORT) | +1 |
| SMC Structure | CHoCH + BOS khớp hướng trade | +1 |

→ `confluence_score = §2 base (0–5) + TV bonus (0–2)` → **tối đa 7, ngưỡng hành động vẫn tính trên 5**

Áp dụng ngưỡng §7:
- base `≤ 2` → **"Thị trường chưa sẵn sàng."** — dừng toàn bộ, không phân tích tiếp
- base `3` + TV bonus `≥ 1` → nâng lên nhóm actionable (có thể auto-log nếu trigger rõ)
- base `≥ 4` → actionable (tiếp tục)
- base `3` + TV bonus `0` → wait confirm (hỏi user)

---

## Bước 5 — M5 Entry Trigger

```
chart_set_timeframe("5")
data_get_ohlcv(count=50)
data_get_study_values
capture_screenshot("chart")
```

Xác định:
1. **Setup** theo §4: A+1 / A+2 / A+3 / A1 / A2 / B1 / B2 / C1 (từ context H4+H1 + TV snapshot)
   - Ưu tiên kiểm tra **A+3** nếu Bước 1.5 có RSI divergence + SMC CHoCH gần giá
   - **B1** ưu tiên nếu đang trong Silver Bullet window (14–15h hoặc 21–22h VN)
   - **C1** nếu `tv_snapshot.json` detect được `BEARISH_BREAKER` / `BULLISH_BREAKER`
2. **FVG** — dùng `FVG/iFVG (Nephew_Sam_)` indicator trên chart (boxes) làm reference chính
   - Đọc từ `data_get_pine_boxes(study_filter="FVG")` nếu cần chính xác
   - Fallback: tính từ raw klines (hàm `find_micro_fvg()` trong trade_engine.py)
3. **Key levels** từ TV snapshot:
   - **EQH/EQL** (SMC labels) = liquidity sweep targets
   - **Liquidity Swings** levels = nearest S/R với strength count
   - **VP POC/HVN** = TP target lý tưởng (VP range extremes)
   - **PO3 low/high** = accumulation/distribution boundaries4. **Trigger** theo §3:
   - **3A Engulfing:** nến M5 engulf + body ≥ 50% + volume xác nhận
   - **3B Wick Rejection:** wick ≥ 50% tổng nến + volume > SMA×1.5
   - **3C Sniper FVG:** giá trong FVG M5 + M1 rejection + volume > SMA×1.2

4. Tính:
```
entry = FVG midpoint (nếu có FVG) hoặc giá hiện tại
sl    = phía sau wick sweep + buffer 1–2 pts
tp1   = mức liquidity gần nhất (Asia High/Low, PDH/PDL)
risk  = abs(entry - sl)
reward = abs(tp1 - entry)
rr    = round(reward / risk, 1)
```

5. **RR guard:** `rr < 1.5` → **từ chối, không log** ("RR thấp — bỏ qua lệnh này")

---

## Bước 6 — Quyết định & Log

### Score ≥ 4 + trigger rõ:
```bash
python3 /Users/ttcenter/trade_engine.py --open-trade '{"pair":"PAIR","direction":"LONG","entry":X,"sl":X,"tp1":X}'
```
→ Hiển thị rule scan output đầy đủ
→ Xác nhận: *"Đã log lệnh tự động. Hệ thống sẽ báo cáo qua Telegram mỗi 5 phút."*

### Score 3 + trigger:
→ Hiển thị §7 Signal output đầy đủ
→ Hỏi: *"Setup đạt 3/5 — bạn có muốn vào không? Trả lời 'có' để tôi log."*

### Score ≤ 2 hoặc không có trigger:
→ *"Thị trường chưa sẵn sàng."* — dừng, không log gì.

---

## Bước 7 — Theo dõi sau khi log

Sau khi lệnh đã log:
- Giữ chart trên pair đang trading
- Đọc giá thực time qua `mcp__tradingview__quote_get` khi cần
- Khi user hỏi tình hình lệnh → đọc `trade_log.json` + quote hiện tại → báo cáo P&L
- Khi user nói *"đã đóng lệnh tại [giá]"* → tự động chạy quy trình `/close`
- Khi user nói *"dừng auto trading"* → chạy `/monitor-mode`

---

## Quy tắc bắt buộc

- **Không bao giờ log lệnh khi score ≤ 2 hoặc RR < 1.5**
- **Không entry ngoài Killzone** (trừ B2 FTR — ghi chú rõ)
- **Pre-entry bắt buộc:** Trả lời *"Tại sao lệnh này có thể THUA?"* trước khi log
- **2 thua liên tiếp** → từ chối đề xuất mới, yêu cầu user post-mortem trước
- Luôn chụp screenshot chart trước khi log để làm bằng chứng phân tích
