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

3. **Kiểm tra TradingView bằng curl** (không dùng MCP):

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

- `OK` → tiếp tục Bước 1.5
- `NO_CHART` hoặc `DOWN` → `bash /Users/ttcenter/launch_tradingview.sh` → đợi "✅ CDP sẵn sàng!"
- Vẫn FAIL → báo user: `cat /tmp/tv_chromium.log`

---

## Bước 1.5 — Kiểm tra Snapshot Cache

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
→ **SKIP Bước 2, 3, 4** — nhảy thẳng đến Bước 5.
→ `mcp__tradingview__chart_set_symbol(PAIR)` nếu symbol chưa đúng.
→ Thông báo: `"Dùng snapshot cache ({AGE}s cũ) — bỏ qua data collect."`

**Nếu AGE ≥ 180 hoặc SYM khác:** → Tiếp tục Bước 2.

---

## Bước 2 — Kết nối & M5 Snapshot (chỉ khi snapshot stale)

```
mcp__tradingview__chart_set_symbol(PAIR)
mcp__tradingview__chart_set_timeframe("5")
```

Gọi **song song** (6 calls):

```
data_get_ohlcv(count=50)
data_get_study_values
data_get_pine_labels(study_filter="Smart Money", max_labels=10)
data_get_pine_labels(study_filter="HTF Power", max_labels=4)
data_get_pine_lines(study_filter="Volume Profile")
data_get_pine_labels(study_filter="Liquidity", max_labels=20)
```

Pipe vào parser:

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

Ghi nhớ từ output: **TV Bias**, **Reversal Warning**, **TV Bonus**, **Key levels**, **PO3 Phase**, **VP POC**.

> Nếu output có `⚠️ CẢNH BÁO ĐỔI CHIỀU` → **báo ngay cho user** + kiểm tra lệnh OPEN.

---

## Bước 3 — H1 Structure (chỉ khi snapshot stale)

```
mcp__tradingview__chart_set_timeframe("60")
data_get_ohlcv(count=30, summary=true)
```

Phân tích: CHoCH/BOS H1 rõ không? FVG H1 tồn tại không? → `htf_h1 = BULLISH | BEARISH | SIDEWAYS`

**Lưu ý:** Không cần D1/H4 OHLCV riêng — SMC labels và PO3 từ snapshot đã encode HTF bias đầy đủ.

---

## Bước 4 — H1 Confluence §2 (chỉ khi snapshot stale)

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
mcp__tradingview__chart_set_timeframe("5")
data_get_ohlcv(count=50)
mcp__tradingview__capture_screenshot("chart")
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
