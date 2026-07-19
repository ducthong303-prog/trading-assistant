# /close — Đóng Giao Dịch & Ghi Nhật Ký

Thực hiện đúng thứ tự sau. Hỏi từng bước, chờ trả lời trước khi hỏi tiếp.

---

## Bước 1 — Thu thập kết quả

Hỏi lần lượt (không hỏi gộp):

1. **Cặp tiền:** "Lệnh vừa đóng là cặp gì? (ví dụ: BTCUSD, ETHUSD, XAUUSD)"
2. **Kết quả:** "Kết quả: Win / Loss / BE?"
3. **Lợi nhuận:** "Lãi/lỗ bao nhiêu R hoặc %? (ví dụ: +2R, -1R, +0.8%)"
4. **Setup:** "Setup nào? (A+1 Unicorn / A+2 PO3 / A1 Judas / A2 SMT / B1 Silver Bullet / B2 FTR)"
5. **Confluence Score:** "Confluence Score lúc vào lệnh là mấy? (0–5)"

---

## Bước 2 — Phỏng vấn tâm lý

Hỏi: "Trạng thái tâm lý chủ đạo khi thực hiện lệnh này là gì?"

Đưa ra 4 lựa chọn để người dùng chọn số:

```
1. Kỷ luật   — Vào/ra đúng kế hoạch, không bị cảm xúc chi phối
2. FOMO      — Vào lệnh vì sợ lỡ, không chờ đủ điều kiện
3. Lo sợ     — Chốt non hoặc dời SL sai quy tắc vì hoảng loạn
4. Trả thù   — Vào lệnh ngay sau thua để gỡ gạc
```

Sau khi người dùng chọn, hỏi thêm: "Một câu ghi chú ngắn về lệnh này? (hoặc gõ 'skip' để bỏ qua)"

---

## Bước 3 — Thực thi

Sau khi có đủ thông tin, map kết quả sang đúng schema rồi chạy:

```bash
python3 /Users/ttcenter/trade_engine.py --log-trade '<json>'
```

JSON phải đúng schema này:
```json
{
  "trade_id": "TS_YYYYMMDD_NN",
  "pair": "BTCUSD",
  "direction": "LONG hoặc SHORT — hỏi thêm nếu chưa có",
  "setup": "A1",
  "confluence_score": 4,
  "psychology": "Kỷ luật",
  "result": "WIN",
  "pnl_r": "+2R",
  "note": "nội dung ghi chú hoặc chuỗi rỗng nếu skip"
}
```

Quy tắc map:
- `trade_id`: format `TS_` + ngày hôm nay `YYYYMMDD` + `_NN` (NN = số thứ tự trong ngày, bắt đầu từ 01; đọc file để xác định NN chính xác nếu cần)
- `result`: "Win" → `"WIN"`, "Loss" → `"LOSS"`, "BE" → `"BE"`
- `psychology`: map từ số người dùng chọn → `"Kỷ luật"` / `"FOMO"` / `"Lo sợ"` / `"Trả thù"`
- `note`: nếu người dùng gõ "skip" → dùng chuỗi rỗng `""`
- Nếu chưa hỏi `direction` → hỏi thêm trước khi chạy lệnh

---

## Bước 4 — Xác nhận & phản hồi tâm lý

Sau khi lệnh chạy thành công:

1. In kết quả gọn:
```
✅ Nhật ký đã được hộp đen ghi lại.
   [PAIR] [DIRECTION] | [SETUP] | Score [X]/5 | [RESULT] [PNL_R]
```

2. Phản hồi tâm lý theo trạng thái đã chọn:
   - **Kỷ luật** → "Tốt. Kỷ luật tạo ra edge bền vững hơn bất kỳ setup nào."
   - **FOMO** → "Ghi nhận. FOMO là dấu hiệu chưa tin vào hệ thống — lần sau chờ trigger đóng nến."
   - **Lo sợ** → "Ghi nhận. Nếu SL đặt đúng từ đầu, không cần dời. Xem lại R:R trước khi vào lệnh tiếp."
   - **Trả thù** → "Dừng lại. Hãy nghỉ ít nhất 30 phút trước lệnh tiếp theo. Thị trường luôn có cơ hội mới."

3. Nếu kết quả là Loss hoặc psychology là Trả thù/Lo sợ → thêm dòng:
   "Hãy nghỉ ngơi nếu bạn cảm thấy mệt mỏi. Không có lệnh nào quan trọng hơn trạng thái tinh thần của bạn."
