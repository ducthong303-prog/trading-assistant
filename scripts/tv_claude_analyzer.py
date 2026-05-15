#!/usr/bin/env python3
"""
tv_claude_analyzer.py — Trigger Claude deep analysis khi cron phát hiện signal.

Được gọi từ market_monitor.py (non-blocking Popen) khi effective_score >= 4.
Claude sẽ mở TradingView, phân tích D1→H4→H1→M5, rồi gửi báo cáo Telegram chi tiết.

Usage:
    python3 tv_claude_analyzer.py '<signal_json_string>'

Exit codes:
    0 = completed (Claude sent Telegram)
    1 = locked (another analysis running)
    2 = error (claude failed or timeout)
"""

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
WORK_DIR    = Path("/Users/ttcenter")
MCP_CONFIG  = WORK_DIR / ".claude" / ".mcp.json"
LOCK_FILE   = Path("/tmp/tv_claude_analysis.lock")
LOG_FILE    = WORK_DIR / "monitor.log"
MAX_BUDGET  = "1.5"      # USD cap per run
MODEL       = "sonnet"   # claude-sonnet-4-6
TIMEOUT_S   = 240        # 4 phút

TOKEN   = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
CHAT_ID = "7850734762"

# ── Helpers ───────────────────────────────────────────────────────────────────
def log(msg: str):
    ts   = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [claude_analyzer] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def is_locked() -> bool:
    if LOCK_FILE.exists():
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age < TIMEOUT_S + 60:
            return True
        LOCK_FILE.unlink(missing_ok=True)
    return False


def send_telegram(text: str):
    url  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id":    CHAT_ID,
        "parse_mode": "HTML",
        "text":       text,
    }).encode()
    try:
        urllib.request.urlopen(
            urllib.request.Request(url, data=data,
                                   headers={"Content-Type": "application/json"}),
            timeout=10
        )
    except Exception as e:
        log(f"Telegram send error: {e}")


# ── Prompt builder ────────────────────────────────────────────────────────────
def build_prompt(signal: dict) -> str:
    symbol    = signal.get("symbol", "BTCUSD")
    direction = signal.get("direction", "?")
    base      = signal.get("base_score", "?")
    eff       = signal.get("effective_score", "?")
    setup     = signal.get("setup", "?")
    lvl       = signal.get("levels", {})
    entry     = lvl.get("entry", "?")
    sl        = lvl.get("sl", "?")
    tp1       = lvl.get("tp1", "?")
    rr        = lvl.get("rr", "?")

    return f"""🔔 TV Scanner (zero-token) phát hiện signal:

Symbol:    {symbol}
Direction: {direction}
Score:     {base}/5 base + bonus = {eff}/7
Setup:     {setup}
Levels:    Entry {entry} | SL {sl} | TP1 {tp1} | RR {rr}

Signal đầy đủ:
{json.dumps(signal, indent=2, ensure_ascii=False)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nhiệm vụ: Xác nhận signal trên bằng phân tích sâu TradingView.
Thực hiện tuần tự — KHÔNG hỏi user, KHÔNG dừng giữa chừng.

Bước 1 — Set symbol:
  chart_set_symbol("{symbol}")

Bước 2 — D1 Bias:
  chart_set_timeframe("D")
  data_get_ohlcv(count=10, summary=true)
  → Xác định xu hướng D1: BULLISH / BEARISH / SIDEWAYS

Bước 3 — H4 Structure:
  chart_set_timeframe("240")
  data_get_ohlcv(count=16, summary=true)
  → CHoCH/BOS? Aligned với D1?

Bước 4 — H1 Momentum:
  chart_set_timeframe("60")
  data_get_study_values
  → RSI, MACD values

Bước 5 — M5 Entry:
  chart_set_timeframe("5")
  data_get_study_values
  capture_screenshot("chart")
  → FVG? Trigger rõ không?

Bước 6 — Tính §2 Confluence Score đầy đủ:
  (+1) HTF Bias:        D1+H4 cùng hướng?
  (+1) Killzone:        London 14-17h / NY 19-22h GMT+7?
  (+1) Volume:          Vol > SMA(20) xác nhận?
  (+1) Liquidity Sweep: Asia H/L hoặc PDH/PDL bị quét?
  (+1) DXY/SMT:         Divergence hoặc MACD khớp?
  TV Bonus (tối đa +2): RSI extreme / MACD direction / PO3 phase / SMC structure

Bước 7 — Gửi Telegram (BẮT BUỘC, dù score ra sao):
  Dùng Bash để gọi curl:

  TOKEN="{TOKEN}"
  CHAT_ID="{CHAT_ID}"

  Format message:
  - Header: 🔍 <b>DEEP ANALYSIS — {symbol} {direction}</b>
  - 📊 Confluence Score: X/5 + TV Bonus +Y = Z/7
  - Bảng §2 (mỗi bước: ✅ / ❌ + lý do ngắn)
  - Hành động: [Vào lệnh ngay / Đặt Limit / Đứng ngoài]
  - Entry / SL / TP1 / RR (nếu vào lệnh)
  - ⚠️ Pre-trade: Lý do lệnh có thể THUA?
  - Nếu score < 3: "Signal yếu sau deep analysis — đứng ngoài."

Chỉ phân tích và gửi Telegram. Không log lệnh. Không hỏi xác nhận.
"""


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        log("Usage: tv_claude_analyzer.py '<signal_json>'")
        sys.exit(1)

    try:
        signal = json.loads(sys.argv[1])
    except json.JSONDecodeError as e:
        log(f"Invalid signal JSON: {e}")
        sys.exit(1)

    if is_locked():
        log("Already running — skip this cycle")
        sys.exit(1)

    symbol = signal.get("symbol", "BTCUSD")
    score  = signal.get("effective_score", 0)
    log(f"Starting: {symbol} {signal.get('direction')} score={score}/7")

    LOCK_FILE.touch()
    prompt = build_prompt(signal)

    cmd = [
        "claude", "-p", prompt,
        "--mcp-config",              str(MCP_CONFIG),
        "--dangerously-skip-permissions",
        "--add-dir",                 str(WORK_DIR),
        "--max-budget-usd",          MAX_BUDGET,
        "--model",                   MODEL,
        "--output-format",           "text",
    ]

    try:
        log("Spawning claude -p...")
        result = subprocess.run(
            cmd,
            cwd=str(WORK_DIR),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
        )
        if result.returncode == 0:
            log("Deep analysis completed ✓")
        else:
            err = (result.stderr or "")[:300]
            log(f"Claude exited {result.returncode}: {err}")
            send_telegram(
                f"⚠️ <b>{symbol} deep analysis failed</b>\n"
                f"Score {score}/7 — kiểm tra thủ công.\n"
                f"Entry: {signal.get('levels',{}).get('entry','?')} | "
                f"SL: {signal.get('levels',{}).get('sl','?')}"
            )
            sys.exit(2)

    except subprocess.TimeoutExpired:
        log(f"Timeout after {TIMEOUT_S}s")
        lvl = signal.get("levels", {})
        send_telegram(
            f"⏱️ <b>{symbol} {signal.get('direction')} — Analysis timeout</b>\n"
            f"Score {score}/7. Kiểm tra thủ công.\n"
            f"Entry: {lvl.get('entry','?')} | SL: {lvl.get('sl','?')} | "
            f"TP1: {lvl.get('tp1','?')} | RR: {lvl.get('rr','?')}"
        )
        sys.exit(2)
    except Exception as e:
        log(f"Unexpected error: {e}")
        sys.exit(2)
    finally:
        LOCK_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
