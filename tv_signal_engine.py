#!/usr/bin/env python3
"""
tv_signal_engine.py — Phát hiện tín hiệu giao dịch từ TV snapshot (không cần Claude)
══════════════════════════════════════════════════════════════════════════════════════
Đọc tv_snapshot.json, áp dụng §2 Confluence Score + §4 Setup Classification,
trả về signal dict hoặc None.

Không gửi Telegram — caller (market_monitor.py) xử lý việc gửi.

Usage:
  from tv_signal_engine import check_signal
  signal = check_signal()  # đọc tv_snapshot.json tự động
  if signal:
      print(signal["telegram_text"])
"""
import json, datetime, time
from pathlib import Path

TV_SNAPSHOT = Path(__file__).parent / "tv_snapshot.json"
MAX_SNAP_AGE = 300  # giây — snapshot > 5 phút coi là stale

# ── Thresholds ────────────────────────────────────────────────────────────────
RSI_OVERSOLD  = 35
RSI_OVERBOUGHT = 65
MIN_RR        = 1.5
SWEEP_RADIUS  = 0.015   # ±1.5% từ giá để coi là "gần đã sweep"
MIN_BASE_SCORE = 3      # base score tối thiểu để tính là actionable

# ── Setup labels ─────────────────────────────────────────────────────────────
SETUP_ICON = {
    "A+1": "⭐⭐⭐",
    "A+2": "⭐⭐⭐",
    "A+3": "⭐⭐⭐",
    "A1":  "⭐⭐",
    "A2":  "⭐⭐",
    "B1":  "⭐",
    "B2":  "⭐",
}


# ── Step 1: Đọc snapshot ──────────────────────────────────────────────────────

def load_snapshot():
    """Đọc và validate tv_snapshot.json. Trả về dict hoặc None nếu stale/missing."""
    try:
        snap = json.loads(TV_SNAPSHOT.read_text())
    except Exception:
        return None

    age = int(time.time()) - snap.get("ts_unix", 0)
    if age > MAX_SNAP_AGE:
        return None  # quá cũ

    # Cần có các key tối thiểu
    required = ("price", "smc", "po3", "vp", "liquidity", "rsi", "macd", "tv_bias")
    if not all(k in snap for k in required):
        return None

    return snap


# ── Step 2: Xác định direction ────────────────────────────────────────────────

def determine_direction(snap):
    """
    Trả về ("LONG"|"SHORT", confidence) hoặc (None, 0) nếu không rõ.
    Ưu tiên: reversal_warning.direction > tv_bias > po3 bias.
    """
    rev = snap.get("reversal_warning", {})
    if rev.get("warning"):
        # Nếu parser đã xác định direction rõ ràng → dùng trực tiếp
        rev_dir = rev.get("direction")
        if rev_dir in ("LONG", "SHORT"):
            return rev_dir, 3
        # Ngược lại xem số signals
        long_sig  = rev.get("long_signals", 0)
        short_sig = rev.get("short_signals", 0)
        if long_sig >= 2 and long_sig > short_sig:
            return "LONG", 2
        if short_sig >= 2 and short_sig > long_sig:
            return "SHORT", 2

    bias = snap.get("tv_bias", "MIXED")
    if bias == "BULLISH":
        return "LONG", 1
    if bias == "BEARISH":
        return "SHORT", 1

    po3_bias = snap.get("po3", {}).get("bias", "")
    if po3_bias in ("LONG", "SHORT"):
        return po3_bias, 0

    return None, 0


# ── Step 3: §2 Confluence Score ───────────────────────────────────────────────

def compute_confluence(snap, direction):
    """Tính 5-bước Confluence Score + TV bonus. Trả về dict chi tiết."""
    price = snap["price"]
    smc   = snap["smc"]
    rsi   = snap["rsi"]
    macd  = snap["macd"]
    po3   = snap["po3"]
    liq   = snap["liquidity"]
    bonus_data = snap.get("tv_bonus", {})

    score   = 0
    details = {}

    # Bước 1 — HTF Bias (SMC structure khớp direction)
    smc_str       = smc.get("structure", "")
    last_choch    = smc.get("last_choch_dir", "")
    # "at_reversal" = cấu trúc đang đảo chiều → xem last_choch_dir để quyết định
    at_rev_ok     = (smc_str == "at_reversal" and
                     ((direction == "LONG"  and "bull" in last_choch.lower()) or
                      (direction == "SHORT" and "bear" in last_choch.lower())))
    htf_ok        = (direction == "LONG"  and smc_str == "bullish") or \
                    (direction == "SHORT" and smc_str == "bearish") or \
                    at_rev_ok
    if htf_ok:
        score += 1
    details["htf_bias"] = htf_ok

    # Bước 2 — Killzone (giờ GMT+7: London 14–17h, NY 19–22h)
    h_vn   = (datetime.datetime.utcnow().hour + 7) % 24
    london = 14 <= h_vn < 17
    ny     = 19 <= h_vn < 22
    in_kz  = london or ny
    if in_kz:
        score += 1
    details["killzone"] = in_kz
    details["kz_name"]  = "London" if london else ("NY" if ny else "Ngoài KZ")
    details["hour_vn"]  = h_vn

    # Bước 3 — Volume (dùng RSI extreme / MACD recovering làm proxy)
    rsi_val  = rsi.get("rsi", 50)
    vol_ok   = (direction == "LONG"  and rsi_val <= RSI_OVERSOLD) or \
               (direction == "SHORT" and rsi_val >= RSI_OVERBOUGHT) or \
               macd.get("recovering", False)
    if vol_ok:
        score += 1
    details["volume"] = vol_ok

    # Bước 4 — Liquidity Sweep (EQH/EQL gần giá → đã/đang sweep)
    eqh = smc.get("eqh_near", [])
    eql = smc.get("eql_near", [])
    swept = False
    if direction == "LONG" and eql:
        near = min(eql, key=lambda x: abs(x - price))
        swept = abs(near - price) / price <= SWEEP_RADIUS
    elif direction == "SHORT" and eqh:
        near = min(eqh, key=lambda x: abs(x - price))
        swept = abs(near - price) / price <= SWEEP_RADIUS
    if swept:
        score += 1
    details["liquidity_sweep"] = swept

    # Bước 5 — DXY/SMT (RSI divergence)
    smt_ok = (direction == "LONG"  and rsi.get("bull_divergence", False)) or \
             (direction == "SHORT" and rsi.get("bear_divergence", False))
    if smt_ok:
        score += 1
    details["dxy_smt"] = smt_ok

    # TV Bonus (max +2)
    raw_bonus = bonus_data.get("bonus", 0)
    bonus     = min(raw_bonus, 2)
    bonus_signals = bonus_data.get("signals", [])
    bonus_notes   = bonus_data.get("notes", [])

    effective = score + bonus
    actionable = (effective >= 4) or (score >= MIN_BASE_SCORE and bonus >= 1)

    return {
        "base":       score,
        "bonus":      bonus,
        "effective":  effective,
        "actionable": actionable,
        "details":    details,
        "bonus_signals": bonus_signals,
        "bonus_notes":   bonus_notes,
    }


# ── Step 4: Classify setup ────────────────────────────────────────────────────

def classify_setup(snap, direction, conf):
    """
    Chọn setup phù hợp nhất dựa trên điều kiện thị trường.
    Trả về setup code string.
    """
    in_kz   = conf["details"]["killzone"]
    h_vn    = conf["details"]["hour_vn"]
    smc     = snap["smc"]
    po3     = snap["po3"]
    rsi     = snap["rsi"]
    macd    = snap["macd"]
    bonus_s = conf["bonus_signals"]

    # A+3: RSI divergence + CHoCH gần giá + score cao
    choch_price = smc.get("last_choch", {}).get("price", 0)
    price       = snap["price"]
    choch_near  = choch_price and abs(choch_price - price) / price < 0.005
    if in_kz and choch_near and (rsi.get("bull_divergence") or rsi.get("bear_divergence")) and conf["base"] >= 4:
        return "A+3"

    # A+2: PO3 accumulation/distribution rõ + London
    po3_phase = po3.get("phase", "")
    london    = 14 <= h_vn < 15  # đầu London
    if london and ((direction == "LONG"  and po3_phase == "accumulation_zone") or
                   (direction == "SHORT" and po3_phase == "distribution_zone")) and conf["base"] >= 3:
        return "A+2"

    # A1: Judas Swing — London + CHoCH rõ
    if in_kz and "London" in conf["details"]["kz_name"] and conf["base"] >= 3:
        return "A1"

    # B1: Silver Bullet — NY 21-22h
    if 21 <= h_vn < 22 and conf["base"] >= 2:
        return "B1"

    # B2: FTR — không cần KZ, MACD recovering + structure
    if macd.get("recovering") and conf["base"] >= 2:
        return "B2"

    # A2: SMT Symmetry — bất kỳ KZ + divergence
    if in_kz and (rsi.get("bull_divergence") or rsi.get("bear_divergence")):
        return "A2"

    return "B2"  # fallback thấp nhất


# ── Step 5: Tính Entry/SL/TP/RR ──────────────────────────────────────────────

def compute_levels(snap, direction, setup):
    """Tính Entry, SL, TP1, TP2, RR từ snapshot data."""
    price = snap["price"]
    vp    = snap["vp"]
    liq   = snap["liquidity"]
    po3   = snap["po3"]
    smc   = snap["smc"]

    entry = price

    # SL: phía sau swing gần nhất + buffer nhỏ
    if direction == "LONG":
        sup = liq.get("nearest_support", [])
        sl  = sup[0]["price"] * 0.999 if sup else entry * 0.992
        tp1 = vp.get("tp_target_high", entry * 1.015)
        tp2 = liq["nearest_resistance"][0]["price"] if liq.get("nearest_resistance") else None
        # Nếu tp2 < tp1 → không có ý nghĩa
        if tp2 and tp2 <= tp1:
            tp2 = None
    else:
        res = liq.get("nearest_resistance", [])
        sl  = res[0]["price"] * 1.001 if res else entry * 1.008
        tp1 = vp.get("tp_target_low", entry * 0.985)
        tp2 = liq["nearest_support"][0]["price"] if liq.get("nearest_support") else None
        if tp2 and tp2 >= tp1:
            tp2 = None

    risk   = abs(entry - sl)
    reward = abs(tp1 - entry)
    rr     = round(reward / risk, 1) if risk > 0 else 0

    # Size rule theo setup
    size_map = {"A+1": 2.0, "A+2": 1.0, "A+3": 1.5,
                "A1": 1.0, "A2": 1.0, "B1": 0.5, "B2": 0.5}
    size = size_map.get(setup, 0.5)

    return {
        "entry":  round(entry, 2),
        "sl":     round(sl, 2),
        "tp1":    round(tp1, 2),
        "tp2":    round(tp2, 2) if tp2 else None,
        "rr":     rr,
        "risk_pts": round(risk, 2),
        "size_pct": size,
    }


# ── Step 6: Format Telegram message ──────────────────────────────────────────

def format_telegram(snap, direction, conf, setup, levels, age_s):
    """Tạo Telegram message text (HTML)."""
    price  = snap["price"]
    symbol = snap.get("symbol", "BTCUSD")
    rsi    = snap["rsi"]
    macd   = snap["macd"]
    po3    = snap["po3"]
    vp     = snap["vp"]
    rev    = snap.get("reversal_warning", {})
    det    = conf["details"]
    icon   = SETUP_ICON.get(setup, "⭐")

    kz_icon  = "✅" if det["killzone"] else "❌"
    htf_icon = "✅" if det["htf_bias"]       else "❌"
    vol_icon = "✅" if det["volume"]          else "❌"
    liq_icon = "✅" if det["liquidity_sweep"] else "❌"
    smt_icon = "✅" if det["dxy_smt"]         else "❌"

    dir_icon = "📈" if direction == "LONG" else "📉"
    rev_warn = "⚠️ Reversal Warning ACTIVE" if rev.get("warning") else ""

    rr_flag  = "✅" if levels["rr"] >= MIN_RR else "❌"
    cache_str = f"snapshot {age_s}s cũ"

    lines = [
        f"📊 <b>TV AUTO-SIGNAL — {symbol} {direction}</b>  {dir_icon}",
        f"   {icon} Setup: <b>{setup}</b>  |  {cache_str}",
        "",
        f"<b>Confluence: {conf['base']}/5 base + {conf['bonus']} bonus = {conf['effective']}/7</b>",
        f"  {htf_icon} HTF Bias       — SMC {snap['smc']['structure']}",
        f"  {kz_icon} Killzone       — {det['kz_name']} ({det['hour_vn']:02d}h VN)",
        f"  {vol_icon} Volume/Momentum — RSI {rsi['rsi']:.1f}  MACD {'↑' if macd['direction']=='BULLISH' else '↓'}",
        f"  {liq_icon} Liquidity Sweep — EQH/EQL gần giá",
        f"  {smt_icon} DXY/SMT        — RSI divergence",
    ]

    if conf["bonus_notes"]:
        lines.append(f"  🎁 TV Bonus (+{conf['bonus']}): " + " · ".join(conf["bonus_notes"]))

    lines += [
        "",
        f"<b>Entry:</b>  ${levels['entry']:,.2f}",
        f"<b>SL:</b>     ${levels['sl']:,.2f}  (risk {levels['risk_pts']:,.0f} pts)",
        f"<b>TP1:</b>    ${levels['tp1']:,.2f}  {rr_flag} RR {levels['rr']}:1",
    ]
    if levels["tp2"]:
        lines.append(f"<b>TP2:</b>    ${levels['tp2']:,.2f}")
    lines.append(f"<b>Size:</b>   {levels['size_pct']}%")

    lines += [
        "",
        f"📋 PO3: {po3['phase']} ({po3['pct_from_low']:.0f}% từ đáy)",
        f"📋 VP POC: ${vp['poc']:,.0f}  |  giá {'trên' if price > vp['poc'] else 'dưới'} POC",
    ]

    if rev_warn:
        lines.append(f"⚠️ {rev_warn}")

    return "\n".join(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def check_signal(snapshot_path=None):
    """
    Entry point chính. Trả về dict signal hoặc None.

    Dict gồm:
      symbol, direction, setup, base_score, effective_score,
      actionable, levels, telegram_text, snap_age_s
    """
    path = Path(snapshot_path) if snapshot_path else TV_SNAPSHOT
    try:
        snap = json.loads(path.read_text())
    except Exception:
        return None

    age_s = int(time.time()) - snap.get("ts_unix", 0)
    if age_s > MAX_SNAP_AGE:
        return None

    required = ("price", "smc", "po3", "vp", "liquidity", "rsi", "macd", "tv_bias")
    if not all(k in snap for k in required):
        return None

    direction, confidence = determine_direction(snap)
    if direction is None:
        return None  # market unclear

    conf   = compute_confluence(snap, direction)
    if not conf["actionable"]:
        return None  # score quá thấp

    setup  = classify_setup(snap, direction, conf)
    levels = compute_levels(snap, direction, setup)

    if levels["rr"] < MIN_RR:
        return None  # RR không đủ

    tg_text = format_telegram(snap, direction, conf, setup, levels, age_s)

    return {
        "symbol":          snap.get("symbol", "BTCUSD"),
        "direction":       direction,
        "setup":           setup,
        "base_score":      conf["base"],
        "effective_score": conf["effective"],
        "actionable":      conf["actionable"],
        "levels":          levels,
        "telegram_text":   tg_text,
        "snap_age_s":      age_s,
        "in_kz":           conf["details"]["killzone"],
        "reversal_warning": snap.get("reversal_warning", {}).get("warning", False),
    }


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = check_signal()
    if result:
        print(f"✅ SIGNAL FOUND: {result['symbol']} {result['direction']} "
              f"Setup={result['setup']} Score={result['effective_score']}/7 "
              f"RR={result['levels']['rr']}")
        print()
        print(result["telegram_text"])
    else:
        snap = load_snapshot()
        if snap is None:
            print("❌ Snapshot missing hoặc stale")
        else:
            direction, _ = determine_direction(snap)
            if direction is None:
                print(f"⏸ Market MIXED — tv_bias={snap.get('tv_bias')} — không có signal")
            else:
                conf = compute_confluence(snap, direction)
                print(f"⏸ Score {conf['base']}/5 + {conf['bonus']} bonus = {conf['effective']}/7 "
                      f"— chưa đủ ngưỡng actionable")
