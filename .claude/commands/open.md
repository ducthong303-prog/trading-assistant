# /open — Log Lệnh Mới (OPEN)

Parse cú pháp từ user và ghi lệnh mới vào `trade_log.json` với status `OPEN`.

## Cú pháp nhận vào

```
PAIR | DIRECTION | Entry: X | SL: X | TP1: X | TP2: X
```

- `TP2: X` hoặc bỏ trống → `null`
- DIRECTION: `LONG` hoặc `SHORT`

## Bước thực hiện

1. Parse các field từ cú pháp trên (case-insensitive, bỏ khoảng trắng thừa).
2. Validate:
   - LONG: SL < Entry < TP1
   - SHORT: TP1 < Entry < SL
   - Nếu sai → báo lỗi rõ ràng, **không log**, hỏi lại user.
3. Build JSON:
```json
{
  "pair": "BTCUSD",
  "direction": "LONG",
  "entry": 80120,
  "sl": 79970,
  "tp1": 81000,
  "tp2": null
}
```
4. Chạy lệnh:
```bash
python3 /Users/ttcenter/trade_engine.py --open-trade '<JSON>'
```
5. Xác nhận với user: Trade ID, pair, direction, entry/SL/TP1, RR.

## Tính RR để hiển thị

```
risk = abs(entry - sl)
reward = abs(tp1 - entry)
rr = round(reward / risk, 1)
```

Hiển thị: `RR: X.X:1` — nếu RR < 1.5 → cảnh báo "RR thấp, cân nhắc lại".

## Output mẫu

```
✅ Đã log lệnh:
  ID     : TS_20260509_01
  ETHUSD SHORT  Entry: 2,305  SL: 2,330  TP1: 2,250
  RR     : 2.2:1
  Monitor: tự động báo cáo mỗi 5 phút qua Telegram
```

## Hiển thị kết quả rule scan

Sau khi chạy lệnh `--open-trade`, đọc toàn bộ stdout và hiển thị với user:

1. Thông tin lệnh (Trade ID, pair, entry/SL/TP1, RR)
2. **Kết quả kiểm tra quy tắc** — đọc phần sau dấu `──` trong output:
   - ✅ Confirmations (quy tắc đạt)
   - ⚠️ Advice (cần lưu ý)
   - ❌ Issues (vi phạm)
3. Nếu có issues → hiển thị rõ: *"Lệnh có vi phạm quy tắc — bạn có chắc muốn tiếp tục không?"*
4. Nếu hợp lệ → xác nhận: *"Lệnh đã log. Hệ thống sẽ báo cáo qua Telegram mỗi 5 phút."*
