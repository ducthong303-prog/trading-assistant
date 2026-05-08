#!/usr/bin/env python3
"""
market_monitor.py  —  Silent Market Monitor (BTC/ETH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Silent mode: Telegram only fires on hard alerts, pattern + KZ, or zone changes.
Routine "nothing happened" cycles → write checkpoint only, no Telegram noise.
"""
import urllib.request, json, datetime, subprocess, sys
from pathlib import Path

TOKEN   = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
CHAT_ID = "7850734762"
TG_URL  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

MONITOR_STATE = Path(__file__).parent / "monitor_state.json"

# ── Key levels ─────────────────────────────────────────────────────────────────
BTC_LEVELS = {
    "sl":        79_500,
    "zone_b_lo": 79_500,  "zone_b_hi": 80_044,
    "zone_a_lo": 80_044,  "zone_a_hi": 80_900,
    "silent_lo": 80_900,  "silent_hi": 81_397,
    "breakout":  81_397,
}
ETH_LEVELS = {
    "sl":        2_278,
    "entry_lo":  2_278,  "entry_hi": 2_308,
    "silent_lo": 2_308,  "silent_hi": 2_346,
    "breakout":  2_346,
}

# ── Helpers ────────────────────────────────────────────────────────────────────
def fetch(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return json.loads(r.read())

def send(text):
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req  = urllib.request.Request(TG_URL, data=data,
                                  headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)

def price(symbol):
    return float(fetch(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")["price"])

def klines(symbol, interval="1h", limit=4):
    data = fetch(
        f"https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )
    return [{"o": float(k[1]), "h": float(k[2]), "l": float(k[3]),
             "c": float(k[4]), "v": float(k[5])} for k in data]

def killzone():
    h = (datetime.datetime.utcnow().hour + 7) % 24
    return (14 <= h < 17) or (19 <= h < 22)

def engulfing(bars):
    if len(bars) < 3: return None
    p, c = bars[-3], bars[-2]
    if p["c"] < p["o"] and c["c"] > p["o"] and c["o"] < p["c"] and c["c"] > c["o"]:
        return "BULLISH ENGULFING"
    if p["c"] > p["o"] and c["c"] < p["o"] and c["o"] > p["c"] and c["c"] < c["o"]:
        return "BEARISH ENGULFING"
    return None

def vol_ok(bars):
    vols = [b["v"] for b in bars]
    if len(vols) < 2: return False
    avg = sum(vols[:-1]) / len(vols[:-1])
    return vols[-2] > avg * 1.2

def btc_zone(p):
    if p < BTC_LEVELS["sl"]:         return "DƯỚI_SL"
    if p <= BTC_LEVELS["zone_b_hi"]: return "ZONE_B"
    if p <= BTC_LEVELS["zone_a_hi"]: return "ZONE_A"
    if p <= BTC_LEVELS["silent_hi"]: return "SILENT"
    return "BREAKOUT"

def eth_zone(p):
    if p < ETH_LEVELS["sl"]:         return "DƯỚI_SL"
    if p <= ETH_LEVELS["entry_hi"]:  return "ENTRY"
    if p <= ETH_LEVELS["silent_hi"]: return "SILENT"
    return "BREAKOUT"

ZONE_LABELS = {
    "DƯỚI_SL": "⛔ DƯỚI SL",
    "ZONE_B":  "🟢 ZONE B (79,500–80,044)",
    "ZONE_A":  "🟡 ZONE A (80,044–80,900)",
    "SILENT":  "⬜ SILENT (80,900–81,397)",
    "BREAKOUT":"🚀 BREAKOUT",
    "ENTRY":   "🟢 ENTRY ZONE (2,278–2,308)",
}

# ── Zone state tracking ────────────────────────────────────────────────────────

def load_prev_zones():
    try:
        return json.loads(MONITOR_STATE.read_text())
    except Exception:
        return {"btc": None, "eth": None}

def save_zones(btc_z, eth_z):
    MONITOR_STATE.write_text(json.dumps({"btc": btc_z, "eth": eth_z}))

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    now_gmt7 = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    kz       = killzone()
    kz_str   = "✅ KILLZONE" if kz else "⏸ Ngoài KZ"

    btc_p  = price("BTCUSDT")
    eth_p  = price("ETHUSDT")
    btc_h1 = klines("BTCUSDT", "1h", 4)
    eth_h1 = klines("ETHUSDT", "1h", 4)

    btc_eng  = engulfing(btc_h1)
    eth_eng  = engulfing(eth_h1)
    btc_vol  = vol_ok(btc_h1)
    eth_vol  = vol_ok(eth_h1)
    btc_z    = btc_zone(btc_p)
    eth_z    = eth_zone(eth_p)

    # Hard alerts (always send regardless of KZ)
    hard_alerts = []
    if btc_p < BTC_LEVELS["sl"]:       hard_alerts.append("🔴 BTC PHÁ SL 79,500!")
    if eth_p < ETH_LEVELS["sl"]:       hard_alerts.append("🔴 ETH PHÁ SL 2,278!")
    if btc_p > BTC_LEVELS["breakout"]: hard_alerts.append("🟢 BTC BREAKOUT >81,397!")
    if eth_p > ETH_LEVELS["breakout"]: hard_alerts.append("🟢 ETH BREAKOUT >2,346!")

    # Soft triggers (only in KZ)
    soft_triggers = []
    if kz and btc_eng:
        sig = "⚡" if btc_vol else "👀"
        vol_tag = "✅ vol ok" if btc_vol else "⚠️ vol thấp"
        soft_triggers.append(f"{sig} BTC {btc_eng} ({vol_tag})")
    if kz and eth_eng:
        sig = "⚡" if eth_vol else "👀"
        vol_tag = "✅ vol ok" if eth_vol else "⚠️ vol thấp"
        soft_triggers.append(f"{sig} ETH {eth_eng} ({vol_tag})")

    # Zone change detection
    prev = load_prev_zones()
    zone_changes = []
    if kz and prev["btc"] and prev["btc"] != btc_z:
        zone_changes.append(f"📍 BTC zone: {prev['btc']} → {btc_z}")
    if kz and prev["eth"] and prev["eth"] != eth_z:
        zone_changes.append(f"📍 ETH zone: {prev['eth']} → {eth_z}")

    save_zones(btc_z, eth_z)

    # Decide whether to send Telegram
    should_send = bool(hard_alerts or soft_triggers or zone_changes)

    if should_send:
        lines = [
            f"📊 <b>MARKET MONITOR</b> — {now_gmt7.strftime('%H:%M')} GMT+7",
            f"⏰ {kz_str}",
            "",
            f"<b>BTC</b>  ${btc_p:,.1f}",
            f"  {ZONE_LABELS.get(btc_z, btc_z)}",
            "",
            f"<b>ETH</b>  ${eth_p:,.2f}",
            f"  {ZONE_LABELS.get(eth_z, eth_z)}",
        ]
        if zone_changes:
            lines += ["", "📍 <b>Zone Changes</b>"] + zone_changes
        if soft_triggers:
            lines += ["", "🎯 <b>Pattern Detected</b>"] + soft_triggers
        if hard_alerts:
            lines += ["", "🚨 <b>HARD ALERT</b>"] + hard_alerts

        send("\n".join(lines))
        print("SENT:", "\n".join(lines))
    else:
        # Silent — update checkpoint only
        print(f"SILENT: {now_gmt7.strftime('%H:%M')} BTC ${btc_p:,.1f} [{btc_z}]"
              f"  ETH ${eth_p:,.2f} [{eth_z}]  {kz_str}")

    # Always update trade_engine checkpoint
    try:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "trade_engine.py"), "--silent"],
            timeout=30
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
