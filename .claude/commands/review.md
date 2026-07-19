# /review — Đánh Giá Hiệu Suất & Tâm Lý

Chạy lệnh sau để đọc dữ liệu:
```bash
python3 -c "
import json
from pathlib import Path
log = json.loads(Path('/Users/ttcenter/trade_log.json').read_text())
trades = log.get('trades', [])
closed = [t for t in trades if t.get('result') in ('WIN','LOSS','BE')]
print(json.dumps(closed[-20:], ensure_ascii=False))
"
```

Chỉ đọc 20 lệnh gần nhất để tiết kiệm token. Không đọc toàn bộ file.

---

## Tính toán & trình bày

Từ dữ liệu trả về, tính và trình bày theo đúng cấu trúc sau — không thêm bớt:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PERFORMANCE REVIEW  (N lệnh gần nhất)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Win / Loss / BE :  X / Y / Z
  Win Rate        :  XX%
  Avg Score       :  X.X/5  (nếu có confluence_score)

  Tâm lý → Kết quả:
    Kỷ luật  :  W thắng / L thua
    FOMO     :  W thắng / L thua
    Lo sợ   :  W thắng / L thua
    Trả thù  :  W thắng / L thua

  Setup hiệu quả nhất  :  [tên setup] (Win Rate XX%)
  Setup thua nhiều nhất:  [tên setup] (Win Rate XX%)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Bỏ qua hàng nào nếu không có dữ liệu (field null hoặc chưa có lệnh nào).

---

## Lời khuyên

Sau bảng thống kê, đưa ra **đúng 1 lời khuyên ngắn** dựa trên pattern nổi bật nhất:

- Nếu psychology dẫn đến thua nhiều nhất là **FOMO** → nhắc chờ trigger đóng nến trước khi entry.
- Nếu là **Lo sợ** → nhắc đặt SL đúng từ đầu và không dời.
- Nếu là **Trả thù** → nhắc quy tắc 2 thua liên tiếp = nghỉ 4 giờ.
- Nếu là **Kỷ luật** mà vẫn thua → kiểm tra lại setup có thực sự đủ điều kiện không (Score thấp?).
- Nếu Win Rate ≥ 60% và psychology chủ yếu là Kỷ luật → "Hệ thống đang hoạt động tốt. Giữ nguyên."
- Nếu không đủ dữ liệu (< 5 lệnh) → "Chưa đủ mẫu để kết luận. Tiếp tục ghi log."

Không đưa ra nhiều hơn 1 lời khuyên. Không liệt kê danh sách khuyến nghị.
