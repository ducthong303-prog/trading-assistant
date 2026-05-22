# /analyze — Full Session Analysis

Run in sequence:
1. `python3 /Users/ttcenter/session_analyzer.py`
2. `python3 /Users/ttcenter/trade_engine.py`

Read **trade_engine output only** for the final verdict (session_analyzer data is already fed into the checkpoint).

**Response rules:**
- Score ≤ 2 → "Thị trường chưa sẵn sàng." Stop. Do not force a setup.
- Score 3   → **DỪNG. Hỏi trước khi show §7.** Đặt câu hỏi này cho người dùng:
              > "ForexFactory có tin đỏ/cam nào trong 4h tới không? (trả lời Có/Không)"
              - Trả lời **Không** → show §7, label "Đợi xác nhận", size ≤ 0.5%.
              - Trả lời **Có** → "Thị trường chưa sẵn sàng — tin mạnh trong 4h tới. Đứng ngoài." Dừng.
              - Không trả lời → không show signal. Hỏi lại.
- Score ≥ 4 → Show full §7 signal. Remind: verify HTF Bias on D1/H4 chart (MANUAL field in output).

Do NOT re-read CLAUDE.md. All rules are encoded in trade_engine.py.
Tập trung vào: KZ còn mở không? Sweep đã xảy ra chưa? Setup có trigger chưa?
