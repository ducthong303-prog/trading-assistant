#!/usr/bin/env python3
"""
market_monitor.py  —  Smart Market Monitor (BTC/ETH)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gọi trade_engine.py để tính toàn bộ setup A+1/A+2/A1/A2/B1/B2 + confluence.
Telegram chỉ fires khi: setup detected (score≥3 + KZ), zone change, hoặc hard alert.
"""
import json, datetime, subprocess, sys, fcntl, time
from pathlib import Path

LOG_FILE = Path(__file__).parent / "trade_log.json"
TV_MCP_DIR    = Path(__file__).parent / "tradingview-mcp"
TV_COLLECT_JS = TV_MCP_DIR / "tv_collect.js"  # chạy với cwd=TV_MCP_DIR
TV_SNAPSHOT   = Path(__file__).parent / "tv_snapshot.json"
TRADING_MODE  = Path(__file__).parent / "trading_mode.json"

TOKEN   = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
CHAT_ID = "7850734762"
TG_URL  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

MONITOR_STATE = Path(__file__).parent / "monitor_state.json"
STATE_FILE    = Path(__file__).parent / "market_state.json"
LOCK_FILE     = Path(__file__).parent / "market_monitor.lock"

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

def send(text, silent=False):
    # silent=True → disable_notification (tinh tinh nhẹ cho setup/zone)
    # silent=False → âm thanh mặc định (hard alert)
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    if silent:
        payload["disable_notification"] = True
    data = json.dumps(payload).encode()
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

# ── Open trade tracking ───────────────────────────────────────────────────────

def get_price_for_pair(pair, state):
    """Map trade pair to a price from market_state.json."""
    p = pair.upper().replace("/", "")
    if "BTC" in p:
        return state["btc"]["price"]
    if "ETH" in p:
        return state["eth"]["price"]
    for sym, d in state.get("watchlist", {}).items():
        if d and sym in p or p.startswith(sym[:3]):
            return d["price"]
    return None


def generate_lesson(trade, result, exit_price):
    """Rule-based lesson — no AI needed."""
    entry = trade["entry"]
    sl    = trade["sl"]
    risk  = abs(entry - sl) or 1
    score = trade.get("entry_score") or trade.get("confluence_score")
    in_kz = trade.get("entry_in_kz")

    if result == "WIN":
        rr    = round(abs(exit_price - entry) / risk, 1)
        parts = [f"TP đạt +{rr}R ({exit_price:,.2f})."]
        if score and score >= 4:
            parts.append(f"Score {score}/5 xác nhận setup chất lượng.")
        if in_kz is False:
            parts.append("Lưu ý: vào ngoài KZ — rủi ro cao hơn bình thường.")
    else:
        parts = [f"SL hit tại {exit_price:,.2f}."]
        if score and score <= 2:
            parts.append(f"Score {score}/5 quá thấp — entry quá sớm.")
        zone = trade.get("entry_zone", "")
        if zone:
            parts.append(f"Vùng {zone} không giữ được.")
        if in_kz is False:
            parts.append("Vi phạm quy tắc KZ — đây là điểm cần cải thiện.")
    return " ".join(parts)


def check_open_trades(state):
    """Check open trades against current prices. Returns (updates, auto_closed)."""
    if not LOG_FILE.exists():
        return [], []
    try:
        log = json.load(open(LOG_FILE, encoding="utf-8"))
    except Exception:
        return [], []

    updates, closed, changed = [], [], False

    for trade in log.get("trades", []):
        if trade.get("status") != "OPEN":
            continue
        price = get_price_for_pair(trade.get("pair", ""), state)
        if price is None:
            continue

        entry = trade["entry"]
        sl    = trade["sl"]
        tp1   = trade.get("tp1")
        dirn  = trade.get("direction", "LONG").upper()
        risk  = abs(entry - sl) or 1
        pnl   = (price - entry) if dirn == "LONG" else (entry - price)
        rr    = round(pnl / risk, 2)

        sl_hit = (dirn == "LONG" and price <= sl) or (dirn == "SHORT" and price >= sl)
        tp_hit = bool(tp1 and ((dirn == "LONG" and price >= tp1) or
                               (dirn == "SHORT" and price <= tp1)))

        if sl_hit or tp_hit:
            result = "WIN" if tp_hit else "LOSS"
            lesson = generate_lesson(trade, result, price)
            trade.update({
                "status":     "CLOSED",
                "exit":       round(price, 2),
                "pnl_pts":    round(pnl, 2),
                "result":     result,
                "date_close": datetime.datetime.now().strftime("%Y-%m-%d"),
                "note":       lesson,
            })
            closed.append((trade, result, lesson))
            changed = True
        else:
            dist_sl  = abs(price - sl)
            dist_tp1 = abs(price - float(tp1)) if tp1 else None
            # 1:1 reached → must move SL to BE
            be_due = ((dirn == "LONG"  and price >= entry + risk) or
                      (dirn == "SHORT" and price <= entry - risk))
            # SL danger: within 30% of risk remaining
            sl_danger = dist_sl <= risk * 0.30
            updates.append({
                "trade_id": trade.get("trade_id", ""),
                "pair":     trade.get("pair", ""),
                "dirn":     dirn,
                "entry":    entry,
                "price":    price,
                "pnl":      round(pnl, 2),
                "rr":       rr,
                "sl":       sl,
                "tp1":      tp1,
                "risk":     risk,
                "dist_sl":  round(dist_sl, 1),
                "dist_tp1": round(dist_tp1, 1) if dist_tp1 is not None else None,
                "be_due":   be_due,
                "sl_danger": sl_danger,
                "score":    trade.get("entry_score"),
                "in_kz_entry": trade.get("entry_in_kz"),
            })

    if changed:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)

    return updates, closed


def check_fvg_retest(price, fvgs, buffer=20):
    """Return list of FVGs that price is currently inside or within buffer units."""
    return [f for f in fvgs
            if f["bottom"] - buffer <= price <= f["top"] + buffer]


# Buffer theo loại tài sản — mỗi nhóm có biên độ dao động khác nhau
_FVG_BUFFER = {
    "BTCUSDT": 20.0,   # Crypto BTC: buffer hẹp, tránh nhiễu M1
    "BTCUSD":  20.0,
    "ETHUSDT": 15.0,   # Crypto ETH: nhỏ hơn BTC, buffer càng hẹp
    "ETHUSD":  15.0,
    "XAUUSD":  15.0,   # Vàng: wick quét sâu, buffer vừa để bắt deep retest
    "XAGUSD":   0.15,  # Bạc: giá ~30, 0.15 ≈ 0.5%
    "USOIL":    0.3,   # Dầu: giá ~80, 0.3 ≈ 0.4%
    "USTEC":   40.0,   # Nasdaq (NQ): chỉ số chạy nhanh, buffer rộng hơn
}
_FOREX_BUFFER = 0.0002   # 2 pips cho tất cả Forex (EURUSD, GBPUSD, USDJPY...)
_FOREX_PAIRS  = {"EUR", "GBP", "AUD", "NZD", "CAD", "CHF", "JPY"}

# ── TV Auto-Scan (zero-token) ─────────────────────────────────────────────────

def get_trading_mode():
    """Đọc trading_mode.json. Trả về 'auto' hoặc 'monitor'."""
    try:
        d = json.loads(TRADING_MODE.read_text())
        return d.get("mode", "monitor"), d.get("symbol", "BTCUSD")
    except Exception:
        return "monitor", "BTCUSD"


def run_tv_collect(pair="BTCUSD", timeout=25):
    """
    Chạy tv_collect.js, pipe output vào tv_indicator_parser.py.
    Cập nhật tv_snapshot.json. Trả về True nếu thành công.
    """
    if not TV_COLLECT_JS.exists() or not TV_MCP_DIR.exists():
        print("[TV_SCAN] tv_collect.js not found — skip")
        return False

    # Kiểm tra snapshot còn fresh không (< 4 phút) — tránh collect liên tục
    try:
        snap_age = int(time.time()) - json.loads(TV_SNAPSHOT.read_text()).get("ts_unix", 0)
        if snap_age < 240:
            print(f"[TV_SCAN] Snapshot còn mới ({snap_age}s) — dùng cache, bỏ qua collect")
            return True
    except Exception:
        pass

    try:
        # Node.js collect — một process, 6 parallel CDP calls
        collect = subprocess.run(
            ["/usr/local/bin/node", str(TV_COLLECT_JS), pair],
            capture_output=True, text=True,
            timeout=timeout, cwd=str(TV_MCP_DIR)
        )
        if collect.returncode != 0 or not collect.stdout.strip():
            print(f"[TV_SCAN] tv_collect.js failed (exit {collect.returncode}): "
                  f"{collect.stderr[:200]}")
            return False

        raw = collect.stdout.strip()
        data = json.loads(raw)
        if "error" in data:
            print(f"[TV_SCAN] CDP error: {data.get('message','')}")
            return False

        # Pipe vào parser → ghi tv_snapshot.json
        parser = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "tv_indicator_parser.py")],
            input=raw, capture_output=True, text=True, timeout=10
        )
        if parser.returncode != 0:
            print(f"[TV_SCAN] parser error: {parser.stderr[:200]}")
            return False

        print(f"[TV_SCAN] snapshot updated — pair={pair}")
        return True

    except subprocess.TimeoutExpired:
        print(f"[TV_SCAN] timeout after {timeout}s")
        return False
    except Exception as e:
        print(f"[TV_SCAN] exception: {e}")
        return False


def get_tv_signal():
    """Đọc snapshot hiện tại, chạy signal engine. Trả về signal dict hoặc None."""
    try:
        from tv_signal_engine import check_signal
        return check_signal()
    except Exception as e:
        print(f"[TV_SCAN] signal engine error: {e}")
        return None


def get_dynamic_buffer(pair):
    """Return FVG retest buffer appropriate for the given pair/asset class."""
    p = pair.upper().replace("/", "")
    if p in _FVG_BUFFER:
        return _FVG_BUFFER[p]
    if any(fx in p for fx in _FOREX_PAIRS):
        return _FOREX_BUFFER
    return 20.0   # default: crypto-like


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # FIX #2: lockfile — ngăn zombie khi crontab spawn cycle mới trước cycle cũ xong
    _lock = open(LOCK_FILE, "w")
    try:
        fcntl.flock(_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        print("SKIP: tiến trình trước vẫn đang chạy")
        _lock.close()
        return
    # Lock giữ cho đến khi process thoát — OS tự giải phóng

    now_gmt7 = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    kz_now   = killzone()
    kz_str   = "✅ KILLZONE" if kz_now else "⏸ Ngoài KZ"

    # 1. Refresh checkpoint — trade_engine tính toàn bộ setup + confluence
    try:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / "trade_engine.py"), "--silent"],
            timeout=30
        )
        # FIX #1: kiểm tra exit code — crash không raise exception, chỉ trả returncode != 0
        if result.returncode != 0:
            print(f"ERROR trade_engine: exit code {result.returncode} — bỏ qua chu kỳ")
            return
    except Exception as e:
        print(f"ERROR trade_engine: {e}")
        return

    # 2. Đọc kết quả
    try:
        state = json.loads(STATE_FILE.read_text())
    except Exception:
        print("ERROR: không đọc được market_state.json")
        return

    # FIX #2: guard toàn bộ dict access — schema thay đổi hoặc partial write → KeyError thầm lặng
    try:
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
        struct    = state.get("last_structure", "unknown")
        klevels   = state.get("key_levels", [])
        watchlist = state.get("watchlist", {})
        btc_fvgs  = state["btc"].get("fvg_h1", []) + state["btc"].get("fvg_m5", [])
        eth_fvgs  = state["eth"].get("fvg_h1", []) + state["eth"].get("fvg_m5", [])
    except KeyError as e:
        print(f"ERROR: market_state.json thiếu key {e} — bỏ qua chu kỳ")
        return

    # 3. TV Auto-Scan — chỉ khi mode=auto, zero token
    tv_signal = None
    trading_mode, tv_pair = get_trading_mode()
    if trading_mode == "auto":
        tv_ok = run_tv_collect(tv_pair)
        if tv_ok:
            tv_signal = get_tv_signal()
            if tv_signal:
                print(f"[TV_SCAN] SIGNAL: {tv_signal['symbol']} {tv_signal['direction']} "
                      f"setup={tv_signal['setup']} score={tv_signal['effective_score']}/7")
            else:
                print("[TV_SCAN] Không có signal actionable")

    # 4. Hard alerts — luôn gửi bất kể KZ
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

    # FIX #3: kiểm tra freshness TRƯỚC khi quyết định gửi — không để tín hiệu sai đi ra
    is_fresh, data_age = check_data_freshness()
    if not is_fresh:
        # Hard alert vẫn gửi (cảnh báo ngưỡng giá quan trọng hơn freshness)
        # Zone change và setup dùng dữ liệu cũ → bỏ qua
        zone_changes = []
        setup_active = False
        if not hard_alerts:
            print(f"[DATA DELAYED — {data_age}m] Bỏ qua chu kỳ, không gửi Telegram")
            return
        print(f"[DATA DELAYED — {data_age}m] Chỉ gửi hard alert, bỏ qua setup/zone")

    # 6. Check open trades — cần state đã load ở bước 2
    open_updates, auto_closed = check_open_trades(state)

    # 7. FVG retest detection — dynamic buffer theo loại tài sản
    btc_buf       = get_dynamic_buffer("BTCUSDT")
    eth_buf       = get_dynamic_buffer("ETHUSDT")
    btc_retest    = check_fvg_retest(btc_p, btc_fvgs, btc_buf)
    eth_retest    = check_fvg_retest(eth_p, eth_fvgs, eth_buf)
    btc_retest_set = {(f["bottom"], f["top"]) for f in btc_retest}
    eth_retest_set = {(f["bottom"], f["top"]) for f in eth_retest}
    fvg_retest_alert = bool((btc_retest or eth_retest) and kz_now)  # chỉ alert trong KZ

    # Có lệnh đang mở → luôn gửi cập nhật 5 phút
    urgent_open = any(u.get("be_due") or u.get("sl_danger") for u in open_updates)
    should_send = bool(hard_alerts or zone_changes or setup_active
                       or open_updates or auto_closed or fvg_retest_alert
                       or tv_signal)

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

    # Market Radar — tách biến động mạnh (≥1%) khỏi grid thường
    if watchlist:
        prioritized, normal = [], []
        for sym, d in watchlist.items():
            if not d or d.get("price") is None:
                continue
            p   = d["price"]
            chg = d.get("change")
            chg_str = f"({chg:+.2f}%)" if chg is not None else ""
            if chg is not None and abs(chg) >= 1.0:
                prioritized.append(f"  🚨 <b>{sym} {p:,.4g} {chg_str}</b>")
            else:
                normal.append((sym, p, chg_str))

        radar_lines = ["", "📋 <b>MARKET RADAR</b>"]
        if prioritized:
            radar_lines += ["🔥 <b>Biến động mạnh:</b>"] + prioritized
        # Grid 2 cột cho phần còn lại
        if normal:
            radar_lines.append("📊 Watchlist:")
            for i in range(0, len(normal), 2):
                row = "  ".join(f"{s} {p:,.4g} {c}".strip()
                                for s, p, c in normal[i:i+2])
                radar_lines.append(f"  {row}")
        lines += radar_lines

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

    # FVG Zones — luôn hiển thị trong KZ hoặc khi có retest
    has_fvg = (btc_fvgs or eth_fvgs) and (kz_now or fvg_retest_alert)
    if has_fvg:
        lines += ["", f"🔍 <b>FVG Zones</b>  <i>(buf BTC {btc_buf:.0f}pt | ETH {eth_buf:.0f}pt)</i>"]
        if btc_fvgs:
            lines.append("<b>BTC</b>")
            for f in btc_fvgs[-4:]:
                icon = "🟩" if f["type"] == "BULLISH" else "🟥"
                tag  = "  🎯 <b>[RETESTING]</b>" if (f["bottom"], f["top"]) in btc_retest_set else ""
                lines.append(f"  {icon} {f['type']} {f['bottom']:,.0f}–{f['top']:,.0f}{tag}")
        if eth_fvgs:
            lines.append("<b>ETH</b>")
            for f in eth_fvgs[-4:]:
                icon = "🟩" if f["type"] == "BULLISH" else "🟥"
                tag  = "  🎯 <b>[RETESTING]</b>" if (f["bottom"], f["top"]) in eth_retest_set else ""
                lines.append(f"  {icon} {f['type']} {f['bottom']:.2f}–{f['top']:.2f}{tag}")

    # Setup block
    if setup_active:
        label = SETUP_LABELS.get(setup, setup)
        lines += ["", f"🎯 <b>SETUP: {label}</b>", f"  {s_note}"]
        # Trích Entry / SL / TP / Size từ signal
        for ln in signal.split("\n"):
            ln = ln.strip()
            if any(ln.startswith(k) for k in ("Entry:", "SL:", "TP:", "Size:")):
                lines.append(f"  {ln}")

    # TV Auto-Signal (zero-token)
    if tv_signal:
        lines += ["", "─" * 30, tv_signal["telegram_text"]]
        # TV signal có âm thanh riêng — không bị override bởi silent
        if tv_signal.get("reversal_warning"):
            lines.append("⚠️ <b>Kiểm tra lệnh đang mở!</b>")

    # Zone changes
    if zone_changes:
        lines += ["", "📍 <b>Zone Change</b>"] + zone_changes

    # Hard alerts
    if hard_alerts:
        lines += ["", "🚨 <b>HARD ALERT</b>"] + hard_alerts

    # Open trades — P&L + rule-based live advice
    if open_updates:
        lines += ["", "📊 <b>Lệnh đang theo dõi</b>"]
        for u in open_updates:
            p_icon = "📈" if u["rr"] >= 0 else "📉"
            lines.append(
                f"  {p_icon} <b>{u['pair']} {u['dirn']}</b>  ${u['price']:,.2f}"
                f"  P&L: {u['pnl']:+.0f}pts ({u['rr']:+.2f}R)"
            )
            # Price levels + distances
            if u["tp1"]:
                lines.append(
                    f"     Entry {u['entry']:,.0f} → SL {u['sl']:,.0f}"
                    f"  |  TP1 {u['tp1']:,.0f}"
                )
                lines.append(
                    f"     📏 Còn đến SL: {u['dist_sl']:,.0f}pts"
                    + (f"  |  Đến TP1: {u['dist_tp1']:,.0f}pts" if u['dist_tp1'] is not None else "")
                )
            else:
                lines.append(f"     SL {u['sl']:,.0f}  |  Còn {u['dist_sl']:,.0f}pts đến SL")

            # Rule-based advice
            if u.get("be_due"):
                lines.append("  🔔 <b>Dời SL về BE ngay</b> — giá đã đạt 1:1 RR")
            if u.get("sl_danger") and not u.get("be_due"):
                lines.append(f"  ⚠️ <b>SL nguy hiểm</b> — chỉ còn {u['dist_sl']:,.0f}pts (&lt;30% risk)")
            if u.get("in_kz_entry") is False:
                lines.append("  ⚠️ Lệnh vào ngoài KZ — theo dõi sát hơn bình thường")
            sc = u.get("score")
            if sc is not None and sc <= 2:
                lines.append(f"  ⚠️ Score {sc}/5 lúc vào — giữ SL chặt, không mở rộng risk")

    # Auto-closed trades
    if auto_closed:
        lines += ["", "🏁 <b>Lệnh vừa đóng tự động</b>"]
        for trade, result, lesson in auto_closed:
            icon = "✅ WIN" if result == "WIN" else "❌ LOSS"
            lines.append(f"  {icon}  {trade['pair']} {trade.get('direction','')}  "
                         f"Exit: {trade['exit']:,.2f}  ({trade['pnl_pts']:+.0f} pts)")
            lines.append(f"  📝 {lesson}")

    # Hard alert / TV signal / auto-close / FVG retest / BE due / SL danger → âm thanh; còn lại → silent
    send("\n".join(lines), silent=not bool(
        hard_alerts or tv_signal or auto_closed or fvg_retest_alert or urgent_open
    ))
    print(f"SENT: {now_gmt7.strftime('%H:%M')} "
          f"Setup={setup or '—'} Score={score} {verdict}")

    # Claude Deep Analysis — chạy sau khi đã gửi zero-token signal
    # Chỉ trigger khi signal đủ mạnh (effective_score >= 4) và không bị lock
    if tv_signal and tv_signal.get("effective_score", 0) >= 4:
        try:
            subprocess.Popen(
                ["python3", str(Path(__file__).parent / "tv_claude_analyzer.py"),
                 json.dumps(tv_signal)],
                cwd=str(Path(__file__).parent),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            print("[claude_analyzer] triggered in background"        )
        except Exception as _e:
            print(f"[claude_analyzer] could not start: {_e}")


if __name__ == "__main__":
    main()
