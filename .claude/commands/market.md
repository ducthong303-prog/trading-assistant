# /market — Quick Market Status

Run: `python3 /Users/ttcenter/trade_engine.py`

Read the output directly. Do NOT load or re-read CLAUDE.md — all §2/§4/§7 rules are already encoded inside trade_engine.py.

**Response rules:**
- If verdict is `STAND_ASIDE` → reply: "Thị trường chưa sẵn sàng." and stop.
- If verdict is `WAIT_CONFIRM` → show §7 signal block from output, note what confirmation is still needed.
- If verdict is `ACTIONABLE` → show full §7 signal block, remind to verify HTF Bias manually (marked MANUAL in output).

Keep response under 20 lines. Python đã tính hết — Claude chỉ đọc kết quả và ra quyết định.
