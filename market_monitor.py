#!/usr/bin/env python3
"""
market_monitor.py  —  Smart Market Monitor (BTC/ETH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gọi trade_engine.py để tính toàn bộ setup A+1/A+2/A1/A2/B1/B2 + confluence.
Telegram chỉ fires khi: setup detected (score≥3 + KZ), zone change, hoặc hard alert.
"""
import json, datetime, subprocess, sys
from pathlib import Path

TOKEN   = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
CHAT_ID = "7850734762"
TG_URL  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

MONITOR_STATE = Path(__file__).parent / "monitor_state.json"
STATE_FILE    = Path(__file__).parent / "market_state.json"

# ── Key levels (hard alert thresholds) ────────────────────────────────────────
BTC_SL       = 79_500
BTC_BREAKOUT = 81_397
ETH_SL       = 2_278
ETH_BREAKOUT = 2_346

# ── Labels ────────────────────────────────────────────────────────────────────
ZONE_LABELS = {
    "DƯỚI_SL": "⛔ DƯỚI SL",
    "ZONE_B":  "🟢 ZONE B (79,500–80,044)",
    "ZONE_A":  "🟡 ZONE A (80,044–80,900)",
    "SILENT":  "⬜ SILENT (80,900–81,397)",
    "BREAKOUT":"🚀 BREAKOUT",
    "ENTRY":   "🟢 ENTRY ZONE (2,278–2,308)",
}
SETUP_LABELS = {
    "A+1": "⭐⭐ A+1 Unicorn",
    "A+2": "⭐⭐ A+2 Power of 3",
    "A1":  "⭐ A1 Judas Swing",
    "A2":  "⭐ A2 Symmetry SMT",
    "B1":  "🔹 B1 Silver Bullet",
    "B2":  "🔹 B2 FTR",
}
VERDICT_ICON = {"ACTIONABLE": "⚡", "WAIT_CONFIRM": "👀", "STAND_ASIDE": "⏸"}

# ── Helpers ───────────────────────────────────────────────────────────────────
import urllib.request

def send(text):
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req  = urllib.request.Request(TG_URL, data=data,
                                  headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)

def killzone():
    h = (datetime.datetime.utcnow().hour + 7) % 24
    return (14 <= h < 17) or (19 <= h < 22)

def load_prev_zones():
    try:
        return json.loads(MONITOR_STATE.read_text())
    except Exception:
        return {"btc": None, "eth": None}

def save_zones(btc_z, eth_z):
    MONITOR_STATE.write_text(json.dumps({"btc": btc_z, "eth": eth_z}))

def check_data_freshness():
    try:
        state   = json.loads(STATE_FILE.read_text())
        ts_str  = state.get("ts", "").replace(" GMT+7", "")
        ts_vn   = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M")
        now_vn  = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
        age_min = (now_vn - ts_vn).total_seconds() / 60
        return age_min <= 5, round(age_min, 1)
    except Exception:
        return False, -1

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    now_gmt7 = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    kz_now   = killzone()
    kz_str   = "✅ KILLZONE" if kz_now else "⏸ Ngoài KZ"

    # 1. Refresh checkpoint — trade_engine tính toàn bộ setup + confluence
    try:
        subprocess.run(
            [sys.executable, str(Path(__file__).parent / "trade_engine.py"), "--silent"],
            timeout=30
        )
    except Exception as e:
        print(f"ERROR trade_engine: {e}")
        return

    # 2. Đọc kết quả
    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception:
        print("ERROR: không đọc được market_state.json")
        return

    btc_p   = state["btc"]["price"]
    eth_p   = state["eth"]["price"]
    btc_z   = state["btc"]["zone"]
    eth_z   = state["eth"]["zone"]
    vr      = state["btc"].get("vol_ratio", 0)
    score   = state["confluence"]["score"]
    verdict = state["confluence"]["verdict"]
    bd      = state["confluence"]["breakdown"]
    setup   = state["setup"]["code"]
    s_note  = state["setup"]["note"]
    signal  = state["setup"].get("signal") or ""
    struct  = state.get("last_structure", "unknown")
    klevels = state.get("key_levels", [])

    # 3. Hard alerts — luôn gửi bất kể KZ
    hard_alerts = []
    if btc_p < BTC_SL:       hard_alerts.append("🔴 BTC PHÁ SL 79,500!")
    if eth_p < ETH_SL:       hard_alerts.append("🔴 ETH PHÁ SL 2,278!")
    if btc_p > BTC_BREAKOUT: hard_alerts.append("🟢 BTC BREAKOUT >81,397!")
    if eth_p > ETH_BREAKOUT: hard_alerts.append("🟢 ETH BREAKOUT >2,346!")

    # 4. Zone change — chỉ trong KZ
    prev = load_prev_zones()
    zone_changes = []
    if kz_now and prev["btc"] and prev["btc"] != btc_z:
        zone_changes.append(f"📍 BTC: {prev['btc']} → {btc_z}")
    if kz_now and prev["eth"] and prev["eth"] != eth_z:
        zone_changes.append(f"📍 ETH: {prev['eth']} → {eth_z}")
    save_zones(btc_z, eth_z)

    # 5. Setup alert — trong KZ + score≥3, hoặc B2 FTR (linh hoạt giờ)
    setup_active = bool(setup and score >= 3 and (kz_now or setup == "B2"))

    # 6. Quyết định gửi
    should_send = bool(hard_alerts or zone_changes or setup_active)

    if not should_send:
        print(f"SILENT: {now_gmt7.strftime('%H:%M')} "
              f"BTC ${btc_p:,.1f} [{btc_z}]  "
              f"ETH ${eth_p:,.2f} [{eth_z}]  "
              f"Score {score}/5  {kz_str}")
        return

    # 7. Build Telegram message
    v_icon = VERDICT_ICON.get(verdict, "")
    lines  = [
        f"📊 <b>MARKET MONITOR</b> — {now_gmt7.strftime('%H:%M')} GMT+7",
        f"⏰ {kz_str}  |  🏗 Structure: {struct.upper()}",
        "",
        f"<b>BTC</b>  ${btc_p:,.1f}  vol {vr}×",
        f"  {ZONE_LABELS.get(btc_z, btc_z)}",
        f"<b>ETH</b>  ${eth_p:,.2f}",
        f"  {ZONE_LABELS.get(eth_z, eth_z)}",
    ]

    # Key levels (3 gần nhất)
    if klevels:
        lvl_str = "  |  ".join(f"{l['label']} {l['price']:,.0f}" for l in klevels[:3])
        lines += ["", f"📌 {lvl_str}"]

    # Confluence
    sweep_note = bd["sweep"]["note"]
    lines += [
        "",
        f"<b>Score: {score}/5  {v_icon} {verdict}</b>",
        f"  KZ:{bd['kz']['score']} Vol:{bd['volume']['score']} "
        f"Sweep:{bd['sweep']['score']} DXY:{bd['corr']['score']} HTF:⚠️",
        f"  Sweep → {sweep_note}",
    ]

    # Setup block
    if setup_active:
        label = SETUP_LABELS.get(setup, setup)
        lines += ["", f"🎯 <b>SETUP: {label}</b>", f"  {s_note}"]
        # Trích Entry / SL / TP / Size từ signal
        for ln in signal.split("\n"):
            ln = ln.strip()
            if any(ln.startswith(k) for k in ("Entry:", "SL:", "TP:", "Size:")):
                lines.append(f"  {ln}")

    # Zone changes
    if zone_changes:
        lines += ["", "📍 <b>Zone Change</b>"] + zone_changes

    # Hard alerts
    if hard_alerts:
        lines += ["", "🚨 <b>HARD ALERT</b>"] + hard_alerts

    send("\n".join(lines))
    print(f"SENT: {now_gmt7.strftime('%H:%M')} "
          f"Setup={setup or '—'} Score={score} {verdict}")

    # Freshness check
    is_fresh, data_age = check_data_freshness()
    if not is_fresh:
        print(f"[DATA DELAYED — {data_age}m] checkpoint cũ, kiểm tra trade_engine")


if __name__ == "__main__":
    main()
