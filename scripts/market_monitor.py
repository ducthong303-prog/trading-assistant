#!/usr/bin/env python3
"""
market_monitor.py  —  Price Alert Monitor (chỉ gửi khi giá chạm alert của Claude)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Đọc alert_levels.json (do Claude ghi sau khi vẽ trên TV), fetch giá Binance,
gửi Telegram 1 lần duy nhất khi giá chạm level.
Dùng 24hr ticker để bắt wick (high/low), không chỉ last price.
"""
import json
import datetime
import fcntl
import subprocess
from pathlib import Path

LOCK_FILE    = Path(__file__).parent / "market_monitor.lock"
ALERT_FILE   = Path(__file__).parent / "alert_levels.json"
STATE_FILE   = Path(__file__).parent / "monitor_state.json"

TOKEN   = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
CHAT_ID = "7850734762"
TG_URL  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


def send_telegram(text):
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    data = json.dumps(payload)
    subprocess.run(["curl", "-s", "-X", "POST", TG_URL,
                   "-H", "Content-Type: application/json",
                   "-d", data, "--connect-timeout", "10", "--retry", "2"],
                   timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def fetch_prices():
    """Fetch BTC & ETH 24hr ticker (last + high + low). Fallback api1 → api."""
    prices = {}
    for symbol in ("BTCUSDT", "ETHUSDT"):
        ok = False
        for base in ("https://api.binance.com", "https://api1.binance.com"):
            if ok:
                break
            try:
                url = f"{base}/api/v3/ticker/24hr?symbol={symbol}"
                r = subprocess.run(["curl", "-s", "--connect-timeout", "10", "--retry", "1", url],
                                  capture_output=True, text=True, timeout=15)
                if r.returncode == 0 and r.stdout.strip():
                    d = json.loads(r.stdout)
                    prices[symbol] = {
                        "last": float(d["lastPrice"]),
                        "high": float(d["highPrice"]),
                        "low":  float(d["lowPrice"]),
                    }
                    ok = True
            except Exception:
                continue
    return prices


def load_alerts():
    try:
        return json.loads(ALERT_FILE.read_text())
    except Exception:
        return {"alerts": []}


def save_alerts(data):
    ALERT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_state():
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(s):
    STATE_FILE.write_text(json.dumps(s))


def main():
    _lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("SKIP: tiến trình trước vẫn đang chạy")
        _lock.close()
        return

    now_gmt7 = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=7)
    time_str = now_gmt7.strftime("%H:%M")

    # 1. Fetch
    prices = fetch_prices()
    btc = prices.get("BTCUSDT", {})
    eth = prices.get("ETHUSDT", {})

    if not btc and not eth:
        print(f"SILENT: {time_str} — Không fetch được giá, bỏ qua chu kỳ")
        return

    btc_last = btc.get("last", 0)
    btc_high = btc.get("high", 0)
    btc_low  = btc.get("low", 0)
    eth_last = eth.get("last", 0)
    eth_high = eth.get("high", 0)
    eth_low  = eth.get("low", 0)

    # 2. State — track high/low từ lần check trước (chỉ bắt wick mới)
    prev_state = load_state()
    prev_btc_high = prev_state.get("btc_high", btc_high)
    prev_btc_low  = prev_state.get("btc_low", btc_low)
    prev_eth_high = prev_state.get("eth_high", eth_high)
    prev_eth_low  = prev_state.get("eth_low", eth_low)

    # Save state NGAY để lần sau dùng
    save_state({
        "btc_high": btc_high,
        "btc_low":  btc_low,
        "eth_high": eth_high,
        "eth_low":  eth_low,
    })

    # 3. Alerts
    data = load_alerts()
    alerts = data.get("alerts", [])

    if not alerts:
        print(f"SILENT: {time_str} BTC ${btc_last:,.1f} ETH ${eth_last:,.2f} — 0 alerts")
        return

    # 4. Check — last price + high/low mới (không dùng high/low cũ)
    any_triggered = False
    active_count = 0

    for a in alerts:
        if a.get("status") != "active":
            continue
        active_count += 1

        lvl = a["level"]
        dirn = a.get("direction", "above")
        pair = a.get("pair", "BTCUSD").upper()

        if "ETH" in pair:
            last, high, low = eth_last, eth_high, eth_low
            prev_high, prev_low = prev_eth_high, prev_eth_low
            price_label = f"${last:,.2f}"
        else:
            last, high, low = btc_last, btc_high, btc_low
            prev_high, prev_low = prev_btc_high, prev_btc_low
            price_label = f"${last:,.1f}"

        hit = False
        trigger_price = last

        if dirn == "above":
            if last >= lvl:
                hit, trigger_price = True, last
            elif high >= lvl > prev_high:
                # Wick mới: high hiện tại > lvl nhưng high trước đó < lvl
                hit, trigger_price = True, high
        else:  # below
            if last <= lvl:
                hit, trigger_price = True, last
            elif low <= lvl < prev_low:
                # Wick mới: low hiện tại < lvl nhưng low trước đó > lvl
                hit, trigger_price = True, low

        if not hit:
            continue

        # Telegram
        note = a.get("note", "")
        dir_label = "vượt lên" if dirn == "above" else "rơi xuống"

        msg = (
            f"🚨 <b>GIÁ CHẠM ALERT</b>\n"
            f"<b>{pair}</b> {dir_label} <b>{lvl:,.2f}</b>\n"
            f"\n"
            f"⏰ {time_str} GMT+7  |  Giá hiện tại: {price_label}\n"
            f"📝 {note}"
        )
        send_telegram(msg)
        print(f"TRIGGERED: {time_str} {pair} {dir_label} {lvl:,.2f} → Telegram sent")

        a["status"] = "triggered"
        a["triggered_at"] = now_gmt7.strftime("%Y-%m-%dT%H:%M:%S")
        a["triggered_price"] = round(trigger_price, 2)
        any_triggered = True

    if any_triggered:
        save_alerts(data)

    triggered_count = sum(1 for a in alerts if a.get("status") == "triggered")
    print(f"SILENT: {time_str} BTC ${btc_last:,.1f} ETH ${eth_last:,.2f} — "
          f"{active_count} active, {triggered_count} triggered")


if __name__ == "__main__":
    main()
