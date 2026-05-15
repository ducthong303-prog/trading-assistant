#!/usr/bin/env python3
"""
Daily Market Setup Scanner
Phân tích các cặp tiền và gửi báo cáo lên Telegram
"""

import requests
import json
import time
import math
from datetime import datetime, timezone, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
TELEGRAM_CHAT_ID = "7850734762"
DEEPSEEK_API_KEY = "sk-023a034cc4834353bbe61bbbd2cc41ca"
DEEPSEEK_MODEL = "deepseek-chat"          # deepseek-v4-pro → alias thực tế
DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"

TIMEOUT = 30  # seconds per API call

CRYPTO_PAIRS = ["BTCUSDT", "ETHUSDT"]
YAHOO_PAIRS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "GBPNZD": "GBPNZD=X",
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "USOIL":  "CL=F",
    "USTEC":  "NQ=F",
}

VN_TZ = timezone(timedelta(hours=7))

# ── Helpers ──────────────────────────────────────────────────────────────────

def safe_get(url, params=None, headers=None):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  [GET error] {url}: {e}")
        return None


def send_telegram(text, parse_mode="HTML"):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT)
        data = r.json()
        if data.get("ok"):
            print("  [Telegram] Gửi thành công")
            return True
        else:
            print(f"  [Telegram] Lỗi: {data}")
            return False
    except Exception as e:
        print(f"  [Telegram] Exception: {e}")
        return False


# ── Data Fetching ─────────────────────────────────────────────────────────────

def fetch_binance(symbol, interval="1h", limit=50):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    data = safe_get(url, params=params)
    if not data:
        return None
    candles = []
    for k in data:
        candles.append({
            "t": k[0], "o": float(k[1]), "h": float(k[2]),
            "l": float(k[3]), "c": float(k[4]), "v": float(k[5]),
        })
    return candles


def fetch_yahoo(symbol, interval="1h", range_="5d"):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    params = {"interval": interval, "range": range_}
    headers = {"User-Agent": "Mozilla/5.0"}
    data = safe_get(url, params=params, headers=headers)
    if not data:
        return None
    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        q = result["indicators"]["quote"][0]
        opens = q["open"]
        highs = q["high"]
        lows  = q["low"]
        closes = q["close"]
        vols  = q.get("volume", [0] * len(closes))
        candles = []
        for i in range(len(timestamps)):
            if closes[i] is None:
                continue
            candles.append({
                "t": timestamps[i] * 1000,
                "o": opens[i] or closes[i],
                "h": highs[i] or closes[i],
                "l": lows[i] or closes[i],
                "c": closes[i],
                "v": vols[i] or 0,
            })
        return candles
    except (KeyError, IndexError, TypeError) as e:
        print(f"  [Yahoo parse error] {symbol}: {e}")
        return None


# ── Technical Indicators ──────────────────────────────────────────────────────

def calc_rsi(closes, period=14):
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i-1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


def calc_atr(candles, period=14):
    if len(candles) < period + 1:
        return None
    trs = []
    for i in range(1, len(candles)):
        h = candles[i]["h"]
        l = candles[i]["l"]
        pc = candles[i-1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    atr = sum(trs[:period]) / period
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
    return round(atr, 6)


def detect_trend(candles):
    """Simple swing high/low trend detection."""
    if len(candles) < 10:
        return "unknown"
    closes = [c["c"] for c in candles]
    highs  = [c["h"] for c in candles]
    lows   = [c["l"] for c in candles]

    # Find recent swing highs / lows (local extrema with 2-bar lookback)
    swing_h, swing_l = [], []
    for i in range(2, len(candles) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            swing_h.append(highs[i])
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            swing_l.append(lows[i])

    if len(swing_h) >= 2 and len(swing_l) >= 2:
        hh = swing_h[-1] > swing_h[-2]
        hl = swing_l[-1] > swing_l[-2]
        lh = swing_h[-1] < swing_h[-2]
        ll = swing_l[-1] < swing_l[-2]
        if hh and hl:
            return "bullish"
        if lh and ll:
            return "bearish"
    # Fallback: MA slope
    ma20 = sum(closes[-20:]) / 20
    ma5  = sum(closes[-5:]) / 5
    if ma5 > ma20 * 1.001:
        return "bullish"
    if ma5 < ma20 * 0.999:
        return "bearish"
    return "ranging"


def summarize_candles(candles, n=20):
    """Return a compact OHLCV summary string for last n candles."""
    subset = candles[-n:]
    lines = []
    for c in subset:
        lines.append(f"O:{c['o']:.4f} H:{c['h']:.4f} L:{c['l']:.4f} C:{c['c']:.4f} V:{c['v']:.0f}")
    return "\n".join(lines)


# ── DeepSeek Analysis ─────────────────────────────────────────────────────────

def call_deepseek(pair_name, h1_summary, rsi_h1, atr_h1, trend_h1,
                  current_price, price_24h_ago):
    change_pct = ((current_price - price_24h_ago) / price_24h_ago * 100) if price_24h_ago else 0

    prompt = f"""Bạn là chuyên gia phân tích kỹ thuật SMC (Smart Money Concepts).
Dữ liệu cặp {pair_name}:
- Giá hiện tại: {current_price:.4f}
- Thay đổi 24h: {change_pct:+.2f}%
- RSI(14) H1: {rsi_h1}
- ATR(14) H1: {atr_h1}
- Xu hướng H1: {trend_h1}

OHLCV H1 (20 nến gần nhất):
{h1_summary}

Hãy trả lời 3 câu hỏi bắt buộc theo phân tích SMC:

CÂU HỎI 1: Thanh khoản nằm ở đâu?
- Xác định BSL (Buy-Side Liquidity) tại vùng giá nào?
- Xác định SSL (Sell-Side Liquidity) tại vùng giá nào?

CÂU HỎI 2: Giá đã có tín hiệu đảo chiều chưa?
- Có BOS (Break of Structure) không? Ở đâu?
- Có CHoCH (Change of Character) không?
- Có sweep thanh khoản BSL/SSL không?

CÂU HỎI 3: Entry vào lệnh có hợp lý không?
- Có OB (Order Block) hoặc FVG (Fair Value Gap) để entry không?
- RR (Risk:Reward) ước tính?
- Hành động đề xuất: LONG, SHORT, hay CHỜ?

Sau đó, cho Confluence Score từ 1-5:
1 = Không có gì rõ ràng
2 = Có 1-2 tín hiệu yếu
3 = Có cấu trúc nhưng chưa đủ trigger
4 = Setup rõ, có entry zone
5 = Setup A+ đầy đủ điều kiện

Trả lời NGẮN GỌN theo format JSON:
{{
  "q1_bsl": "...",
  "q1_ssl": "...",
  "q2_reversal": "...",
  "q3_entry": "...",
  "direction": "LONG|SHORT|CHỜ",
  "entry": "...",
  "sl": "...",
  "tp": "...",
  "rr": "...",
  "score": <số 1-5>,
  "reason": "lý do ngắn gọn score"
}}"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 800,
        "response_format": {"type": "json_object"},
    }
    try:
        r = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=TIMEOUT)
        data = r.json()
        if "choices" not in data:
            print(f"  [DeepSeek] Unexpected response: {data}")
            return None
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  [DeepSeek] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  [DeepSeek] Error: {e}")
        return None


# ── Main Analysis Pipeline ─────────────────────────────────────────────────────

def analyze_pair(pair_name, fetch_fn):
    print(f"\n── Analyzing {pair_name} ──")
    candles_h1 = fetch_fn()
    if not candles_h1 or len(candles_h1) < 20:
        print(f"  [SKIP] Không đủ dữ liệu H1 cho {pair_name}")
        return None

    closes_h1 = [c["c"] for c in candles_h1]
    rsi  = calc_rsi(closes_h1)
    atr  = calc_atr(candles_h1)
    trend = detect_trend(candles_h1)
    current_price = closes_h1[-1]
    price_24h_ago = closes_h1[-25] if len(closes_h1) >= 25 else closes_h1[0]
    h1_summary = summarize_candles(candles_h1, n=20)

    print(f"  Price={current_price:.4f} RSI={rsi} ATR={atr} Trend={trend}")

    result = call_deepseek(
        pair_name, h1_summary, rsi, atr, trend, current_price, price_24h_ago
    )
    if not result:
        return None

    score = result.get("score", 0)
    print(f"  DeepSeek Score={score}/5  Direction={result.get('direction','?')}")
    return {
        "pair": pair_name,
        "price": current_price,
        "rsi": rsi,
        "atr": atr,
        "trend": trend,
        "score": score,
        "analysis": result,
    }


def run_all_pairs():
    results = []

    # Crypto via Binance
    for symbol in CRYPTO_PAIRS:
        def make_fetch(sym):
            return lambda: fetch_binance(sym, interval="1h", limit=50)
        res = analyze_pair(symbol, make_fetch(symbol))
        if res:
            results.append(res)
        time.sleep(0.5)

    # Forex/Commodities via Yahoo Finance
    for display_name, yahoo_sym in YAHOO_PAIRS.items():
        def make_fetch_y(sym):
            return lambda: fetch_yahoo(sym, interval="1h", range_="5d")
        res = analyze_pair(display_name, make_fetch_y(yahoo_sym))
        if res:
            results.append(res)
        time.sleep(0.5)

    return results


# ── Format & Send ─────────────────────────────────────────────────────────────

def build_telegram_summary(results):
    now_vn = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M VN")

    ready    = [r for r in results if r["score"] >= 3]
    not_ready = [r for r in results if r["score"] < 3]

    ready.sort(key=lambda x: x["score"], reverse=True)

    lines = [f"🔍 <b>DAILY SETUP SCAN — {now_vn}</b>\n"]

    if ready:
        lines.append("🏆 <b>TOP SETUPS HÔM NAY:</b>\n")
        for r in ready:
            a = r["analysis"]
            score_bar = "⭐" * r["score"]
            direction_emoji = {"LONG": "🟢", "SHORT": "🔴", "CHỜ": "🟡"}.get(a.get("direction", "CHỜ"), "⚪")
            lines.append(
                f"{direction_emoji} <b>{r['pair']}</b>  Score {r['score']}/5  {score_bar}\n"
                f"  ❓ Thanh khoản: {a.get('q1_bsl','?')} / {a.get('q1_ssl','?')}\n"
                f"  ❓ Đảo chiều: {a.get('q2_reversal','?')}\n"
                f"  ❓ Entry hợp lí: {a.get('q3_entry','?')}\n"
                f"  → {a.get('direction','CHỜ')} | Entry: {a.get('entry','?')} | SL: {a.get('sl','?')} | TP: {a.get('tp','?')} | RR: {a.get('rr','?')}\n"
                f"  📌 {a.get('reason','')}\n"
            )
    else:
        lines.append("⚠️ <i>Không có setup nào đạt score ≥ 3 hôm nay.</i>\n")

    if not_ready:
        pairs_str = ", ".join(r["pair"] for r in not_ready)
        lines.append(f"\n❌ <b>Chưa sẵn sàng ({len(not_ready)} pairs):</b> {pairs_str}")

    return "\n".join(lines)


def build_best_detail(best):
    a = best["analysis"]
    now_vn = datetime.now(VN_TZ).strftime("%d/%m/%Y %H:%M VN")
    direction_emoji = {"LONG": "🟢", "SHORT": "🔴", "CHỜ": "🟡"}.get(a.get("direction", "CHỜ"), "⚪")
    return (
        f"🌟 <b>BEST SETUP — {best['pair']} — {now_vn}</b>\n\n"
        f"{direction_emoji} <b>Direction:</b> {a.get('direction','?')}\n"
        f"📊 <b>Score:</b> {best['score']}/5\n"
        f"💰 <b>Price:</b> {best['price']:.4f}\n"
        f"📈 <b>RSI:</b> {best['rsi']}  |  ATR: {best['atr']}  |  Trend: {best['trend']}\n\n"
        f"❓ <b>Câu 1 — Thanh khoản:</b>\n"
        f"  BSL: {a.get('q1_bsl','?')}\n"
        f"  SSL: {a.get('q1_ssl','?')}\n\n"
        f"❓ <b>Câu 2 — Đảo chiều:</b>\n"
        f"  {a.get('q2_reversal','?')}\n\n"
        f"❓ <b>Câu 3 — Entry:</b>\n"
        f"  {a.get('q3_entry','?')}\n\n"
        f"🎯 <b>Entry:</b> {a.get('entry','?')}\n"
        f"🛑 <b>SL:</b> {a.get('sl','?')}\n"
        f"✅ <b>TP:</b> {a.get('tp','?')}\n"
        f"📐 <b>RR:</b> {a.get('rr','?')}\n\n"
        f"💬 <i>{a.get('reason','')}</i>"
    )


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("DAILY MARKET SETUP SCANNER")
    print(f"Thời gian: {datetime.now(VN_TZ).strftime('%d/%m/%Y %H:%M VN')}")
    print("=" * 60)

    results = run_all_pairs()

    print("\n── Kết quả tổng hợp ──")
    for r in sorted(results, key=lambda x: x["score"], reverse=True):
        print(f"  {r['pair']:10s} Score={r['score']}/5  {r['analysis'].get('direction','?'):5s}  "
              f"Price={r['price']:.4f}  RSI={r['rsi']}")

    # Build & send summary
    summary_text = build_telegram_summary(results)
    print("\n── Gửi tin Telegram tổng hợp ──")
    send_telegram(summary_text)

    # Send detail for best pair (score >= 4)
    top_results = [r for r in results if r["score"] >= 4]
    if top_results:
        best = max(top_results, key=lambda x: x["score"])
        print(f"\n── Gửi tin chi tiết cho {best['pair']} ──")
        detail_text = build_best_detail(best)
        time.sleep(1)
        send_telegram(detail_text)
    else:
        print("\n[INFO] Không có pair nào score >= 4, không gửi tin chi tiết.")

    print("\n✅ Hoàn thành!")


if __name__ == "__main__":
    main()
