# /close — Đóng Lệnh & Phân Tích Tự Động

Khi user nhắn "đã đóng", "thoát lệnh", "close lệnh" kèm exit price — thực hiện **toàn bộ quy trình dưới đây không hỏi thêm bất kỳ câu nào**.

---

## Bước 1 — Parse thông tin từ message

Trích xuất từ message của user:
- **Pair**: BTCUSD / ETHUSD / XAUUSD / v.v. — nếu không rõ, đọc `trade_log.json` tìm lệnh OPEN duy nhất
- **Exit price**: số giá thoát lệnh

Nếu có nhiều lệnh OPEN và không rõ pair → hỏi DUY NHẤT 1 câu: "Bạn đóng lệnh nào? [liệt kê các lệnh OPEN]"

---

## Bước 2 — Đóng lệnh trong log

Chạy:
```bash
python3 /Users/ttcenter/trade_engine.py --close-trade PAIR EXIT_PRICE
```

Output là JSON của trade vừa đóng. Parse toàn bộ để phân tích bước tiếp.

---

## Bước 3 — Phân tích tự động (từ dữ liệu đã lưu)

Dùng các field sau từ JSON trade để tự động sinh phân tích — **không hỏi thêm**:

| Field | Ý nghĩa |
|-------|---------|
| `entry`, `exit`, `sl`, `tp1` | Giá entry/exit/SL/TP |
| `direction` | LONG / SHORT |
| `pnl_pts` | Lãi/lỗ (điểm) |
| `rr_achieved` | R:R thực tế |
| `entry_score` | Confluence score lúc vào (0–5) |
| `entry_in_kz` | Có trong Killzone không |
| `entry_zone` | Zone lúc entry (ZONE_A / ZONE_B / ENTRY...) |
| `entry_setup` | Setup code lúc vào (A1 / B2 / v.v.) |

### Phân tích WIN:
- `rr_achieved >= 2` → "Thoát đúng vùng RR mục tiêu ({rr}R)"
- `entry_score >= 4` → "Setup chất lượng cao (score {n}/5) — edge tốt"
- `entry_in_kz == True` → "Vào đúng Killzone — rule được tuân thủ"
- `entry_in_kz == False` → "⚠️ Thắng ngoài KZ — cần cẩn thận, không lặp lại"
- exit >= tp1 (LONG) / exit <= tp1 (SHORT) → "TP1 đạt — thoát theo kế hoạch"
- exit < tp1 (LONG) → "Thoát sớm trước TP1 — hợp lý nếu có tín hiệu đảo chiều"

### Phân tích LOSS:
- `entry_score <= 2` → "Entry quá sớm — score {n}/5 dưới ngưỡng tối thiểu (cần ≥ 3)"
- `entry_in_kz == False` → "Vi phạm KZ rule — đây là lỗi có hệ thống, cần loại bỏ"
- SL hit sát entry → "SL quá chật so với ATR vùng — xem lại sizing"
- `entry_zone` không phải demand/support zone → "Vào sai vùng giá — {zone} không phải POI mạnh"
- pnl loss lớn hơn 1R → "Lỗ vượt 1R — kiểm tra lại SL có đặt đúng không"

### Phân tích BE:
- Thoát hoà — ghi nhận bảo toàn vốn, đánh giá lý do không đến TP

**Luôn kết thúc phân tích bằng 1 dòng hành động cụ thể cho lần sau** (ví dụ: "Lần sau: chỉ entry khi score ≥ 3 và trong KZ").

---

## Bước 4 — Cập nhật tổng kết tuần

```bash
python3 /Users/ttcenter/trade_engine.py --update-weekly
```

---

## Bước 5 — Hiển thị kết quả

```
[ICON] [PAIR] [DIRECTION] — [RESULT]
  Entry   : X,XXX  →  Exit: X,XXX
  P&L     : +/−XXX pts  |  R:R thực tế: X.XX R
  Setup   : [code]  |  Score: X/5  |  KZ: ✅/❌

📋 Phân tích:
  [bullet points từ Bước 3]

📊 Tuần này: X lệnh | W/L: X/X | Net: +/−XXX pts | Win rate: XX%
```

Icon: ✅ WIN | ❌ LOSS | ➖ BE

---

## Quy tắc bắt buộc

- **Không hỏi setup, score, psychology** — tất cả đã được lưu lúc `/open`
- Nếu field bị `null` (vào lệnh thủ công không qua `/open`) → bỏ qua dòng đó, không đặt câu hỏi
- Chạy `--update-weekly` luôn luôn, kể cả khi phân tích ngắn
