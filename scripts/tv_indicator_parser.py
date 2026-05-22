#!/usr/bin/env python3
"""
tv_indicator_parser.py — TradingView Indicator Parser
══════════════════════════════════════════════════════
Parses raw MCP indicator data into structured trading signals.

Usage:
  echo '{"price":80221,"study_values":[...],"smc_labels":[...],...}' | python3 tv_indicator_parser.py
  python3 tv_indicator_parser.py --file /tmp/tv_raw.json
  python3 tv_indicator_parser.py --demo   # test with current market_state.json

Output: tv_snapshot.json + compact summary to stdout
"""
import json, sys, datetime
from pathlib import Path

TV_SNAPSHOT = Path(__file__).parent / "tv_snapshot.json"
MARKET_STATE = Path(__file__).parent / "market_state.json"


# ── SMC [LuxAlgo] parser ───────────────────────────────────────────────────

def parse_smc(labels, current_price, n=10):
    """Parse Smart Money Concepts labels (BOS/CHoCH/EQH/EQL).
    Labels come newest-first from MCP tool.
    Returns: structure direction, key levels, nearest events.
    """
    recent = labels[:n]

    choch = [l for l in recent if l.get("text") == "CHoCH"]
    bos   = [l for l in recent if l.get("text") == "BOS"]
    eqh   = [l for l in recent if l.get("text") == "EQH"]
    eql   = [l for l in recent if l.get("text") == "EQL"]

    # Determine structure: last CHoCH direction
    # CHoCH above current price → price fell from there → bearish
    # CHoCH below current price → price rose from there → bullish
    structure = "unknown"
    last_choch_dir = None
    if choch:
        last_choch_price = choch[0]["price"]
        if last_choch_price > current_price * 1.003:
            structure = "bearish"
            last_choch_dir = "bearish"
        elif last_choch_price < current_price * 0.997:
            structure = "bullish"
            last_choch_dir = "bullish"
        else:
            structure = "at_reversal"
            last_choch_dir = "reversal_zone"

    # Find CHoCH / BOS nearest to current price (potential re-test zones)
    def nearest(events, price):
        return sorted(events, key=lambda e: abs(e["price"] - price))[:3]

    nearest_choch = nearest(choch, current_price)
    nearest_bos   = nearest(bos,   current_price)

    # EQH/EQL within 1.5% of current price = active liquidity targets
    pct = 0.015
    eqh_near = [e["price"] for e in eqh if e["price"] < current_price * (1 + pct)]
    eql_near = [e["price"] for e in eql if e["price"] > current_price * (1 - pct)]

    # BOS above and below → nearest S/R
    bos_above = sorted([b["price"] for b in bos if b["price"] > current_price])[:3]
    bos_below = sorted([b["price"] for b in bos if b["price"] < current_price], reverse=True)[:3]

    return {
        "structure":       structure,
        "last_choch_dir":  last_choch_dir,
        "last_choch":      choch[0] if choch else None,
        "last_bos":        bos[0]   if bos   else None,
        "nearest_choch":   nearest_choch,
        "nearest_bos":     nearest_bos,
        "eqh_near":        sorted(eqh_near, reverse=True)[:3],
        "eql_near":        sorted(eql_near)[:3],
        "bos_resistance":  bos_above,
        "bos_support":     bos_below,
        "reversal_at_price": choch[0]["price"] if choch else None,
    }


# ── HTF Power of Three parser ─────────────────────────────────────────────

def parse_po3(labels, current_price):
    """Parse HTF Power of Three° labels → PO3 zone classification.
    Returns price position: accumulation / manipulation / distribution.
    """
    prices = sorted(set(l["price"] for l in labels))
    if len(prices) < 2:
        return {"levels": prices, "position": "unknown", "phase": "unknown",
                "poc": None, "range": 0, "pct_from_low": 0, "pct_from_high": 0,
                "low": None, "high": None, "mid": None, "range_pts": 0, "bias": "UNKNOWN"}

    low, high = min(prices), max(prices)
    rng       = high - low
    mid       = (low + high) / 2

    # PO3 quadrants
    q1 = low + rng * 0.25   # bottom of accumulation zone
    q3 = high - rng * 0.25  # top of distribution zone

    if current_price <= q1:
        phase = "accumulation_zone"
        bias  = "LONG"
    elif current_price >= q3:
        phase = "distribution_zone"
        bias  = "SHORT"
    elif current_price < mid:
        phase = "discount_mid"
        bias  = "LONG_WATCH"
    else:
        phase = "premium_mid"
        bias  = "SHORT_WATCH"

    pct_from_low  = round((current_price - low)  / rng * 100, 1)
    pct_from_high = round((high - current_price) / rng * 100, 1)

    return {
        "levels":        prices,
        "low":           low,
        "high":          high,
        "mid":           round(mid, 2),
        "range_pts":     round(rng, 2),
        "phase":         phase,
        "bias":          bias,
        "pct_from_low":  pct_from_low,
        "pct_from_high": pct_from_high,
        "position":      "discount" if current_price < mid else "premium",
    }


# ── Volume Profile parser ──────────────────────────────────────────────────

def parse_vp(lines, current_price):
    """Estimate POC, HVN, LVN from Volume Profile horizontal lines.
    Lines are evenly spaced → POC ≈ midpoint, extremes = HVN.
    """
    if not lines:
        return {"poc": None, "vah": None, "val": None, "position": "unknown"}

    levels = sorted(lines)
    low, high = levels[0], levels[-1]
    poc       = round((low + high) / 2, 2)

    # Value area: middle 70% of range
    rng = high - low
    val = round(low  + rng * 0.15, 2)   # Value Area Low
    vah = round(high - rng * 0.15, 2)   # Value Area High

    if current_price < val:
        position = "below_value_area"    # Discount — Long bias
    elif current_price > vah:
        position = "above_value_area"    # Premium — Short bias
    elif current_price < poc:
        position = "discount_in_va"      # Below POC inside VA
    else:
        position = "premium_in_va"       # Above POC inside VA

    distance_from_poc = round(current_price - poc, 2)

    return {
        "poc":                poc,
        "val":                val,
        "vah":                vah,
        "range_low":          round(low, 2),
        "range_high":         round(high, 2),
        "position":           position,
        "distance_from_poc":  distance_from_poc,
        "tp_target_high":     round(high, 2),   # HVN = ideal TP for longs
        "tp_target_low":      round(low, 2),    # HVN = ideal TP for shorts
    }


# ── Liquidity Swings parser ────────────────────────────────────────────────

def parse_liquidity(labels, current_price, top_n=6):
    """Parse Liquidity Swings [LuxAlgo].
    Label text = number of times this level was swept (strength indicator).
    """
    levels = []
    for l in labels:
        try:
            count = int(l.get("text", "0"))
            levels.append({"price": l["price"], "strength": count})
        except (ValueError, TypeError):
            pass

    # Sort by strength descending
    levels.sort(key=lambda x: x["strength"], reverse=True)

    above = [l for l in levels if l["price"] > current_price]
    below = [l for l in levels if l["price"] < current_price]

    above.sort(key=lambda x: x["price"])           # nearest first
    below.sort(key=lambda x: x["price"], reverse=True)

    return {
        "nearest_resistance": above[:3],
        "nearest_support":    below[:3],
        "top_levels":         levels[:top_n],
        "strongest_above":    max((l for l in above), key=lambda x: x["strength"]) if above else None,
        "strongest_below":    max((l for l in below), key=lambda x: x["strength"]) if below else None,
    }


# ── RSI Divergence parser ─────────────────────────────────────────────────

def parse_rsi(study_values):
    """Parse RSI Divergence Indicator from data_get_study_values output."""
    for s in study_values:
        if "RSI Divergence" in s.get("name", ""):
            vals = s.get("values", {})
            try:
                rsi = float(vals.get("RSI", "50").replace(",", ""))
            except ValueError:
                rsi = None

            zone = "oversold" if rsi and rsi < 35 else \
                   "overbought" if rsi and rsi > 65 else "neutral"

            bear_div = any(k in vals for k in ("Regular Bearish", "Hidden Bearish"))
            bull_div = any(k in vals for k in ("Regular Bullish", "Hidden Bullish"))

            return {
                "rsi":            round(rsi, 2) if rsi else None,
                "zone":           zone,
                "bull_divergence": bull_div,
                "bear_divergence": bear_div,
                "bias":           "BEARISH" if rsi and rsi < 50 else "BULLISH",
            }
    return {"rsi": None, "zone": "unknown", "bull_divergence": False,
            "bear_divergence": False, "bias": "UNKNOWN"}


# ── MACD MTF parser ────────────────────────────────────────────────────────

def parse_macd(study_values):
    """Parse CM_MacD_Ult_MTF (multi-timeframe MACD)."""
    def clean(s):
        return s.replace("−", "-").replace(",", "").strip() if s else "0"

    for s in study_values:
        if "MacD" in s.get("name", "") or "MACD" in s.get("name", ""):
            vals = s.get("values", {})
            try:
                macd   = float(clean(vals.get("MACD", "0")))
                signal = float(clean(vals.get("Signal Line", "0")))
                hist   = float(clean(vals.get("Histogram", "0")))
            except ValueError:
                continue

            direction  = "BULLISH" if hist > 0 else "BEARISH"
            recovering = hist > 0 and macd < 0        # histogram positive but MACD still neg = recovering
            crossover  = None
            if macd > signal and macd < 0:
                crossover = "BULL_CROSS_BELOW_ZERO"   # early bull signal
            elif macd > signal and macd > 0:
                crossover = "BULL_CROSS_ABOVE_ZERO"   # confirmed bull
            elif macd < signal and macd > 0:
                crossover = "BEAR_CROSS_ABOVE_ZERO"   # early bear signal

            return {
                "macd":      macd,
                "signal":    signal,
                "histogram": hist,
                "direction": direction,
                "recovering": recovering,
                "crossover":  crossover,
            }
    return {"macd": None, "signal": None, "histogram": None,
            "direction": "UNKNOWN", "recovering": False, "crossover": None}


# ── Reversal warning logic ────────────────────────────────────────────────

def check_reversal_warning(smc, rsi, macd, current_price):
    """Emit reversal warning when SMC CHoCH + RSI divergence + MACD shift align.
    Returns: {warning: bool, direction: 'LONG'|'SHORT'|None, reason: str}
    """
    reasons = []
    long_signals, short_signals = 0, 0

    # SMC CHoCH near current price (within 0.5%)
    if smc.get("reversal_at_price"):
        choch_price = smc["reversal_at_price"]
        pct_diff    = abs(choch_price - current_price) / current_price
        if pct_diff <= 0.005:
            if smc["structure"] == "bearish":
                # CHoCH bearish near price = short-term bearish, but if RSI oversold → potential bounce
                short_signals += 1
                reasons.append(f"SMC CHoCH bearish tại {choch_price:,.0f} (±{pct_diff*100:.2f}% giá hiện tại)")
            elif smc["structure"] == "bullish":
                long_signals += 1
                reasons.append(f"SMC CHoCH bullish tại {choch_price:,.0f}")

    # RSI divergence
    if rsi.get("bear_divergence"):
        short_signals += 1
        reasons.append(f"RSI {rsi.get('rsi','')} — Regular/Hidden Bearish divergence")
    if rsi.get("bull_divergence"):
        long_signals += 1
        reasons.append(f"RSI {rsi.get('rsi','')} — Regular/Hidden Bullish divergence")

    # RSI extreme zone
    if rsi.get("zone") == "oversold":
        long_signals += 1
        reasons.append(f"RSI oversold ({rsi.get('rsi','')})")
    elif rsi.get("zone") == "overbought":
        short_signals += 1
        reasons.append(f"RSI overbought ({rsi.get('rsi','')})")

    # MACD momentum shift
    if macd.get("recovering"):
        long_signals += 1
        reasons.append(f"MACD recovering: hist +{macd.get('histogram',0):.0f} (bearish→bullish)")
    if macd.get("crossover") in ("BULL_CROSS_BELOW_ZERO", "BULL_CROSS_ABOVE_ZERO"):
        long_signals += 1
        reasons.append(f"MACD crossover: {macd.get('crossover')}")
    elif macd.get("crossover") in ("BEAR_CROSS_ABOVE_ZERO",):
        short_signals += 1
        reasons.append(f"MACD crossover: {macd.get('crossover')}")

    warning   = (long_signals >= 2) or (short_signals >= 2)
    direction = "LONG" if long_signals > short_signals else \
                "SHORT" if short_signals > long_signals else None

    return {
        "warning":   warning,
        "direction": direction,
        "long_signals":  long_signals,
        "short_signals": short_signals,
        "reasons":   reasons,
    }


# ── TV Confluence bonus scorer ─────────────────────────────────────────────

def compute_tv_bonus(smc, po3, vp, rsi, macd, trade_direction=None):
    """Compute additional confluence points from TV indicators.
    Returns: {bonus: int, signals: [str], notes: [str]}
    """
    bonus   = 0
    signals = []
    notes   = []

    # RSI extreme at POI → +1 (replaces or reinforces Volume step)
    if rsi.get("zone") in ("oversold", "overbought"):
        bonus += 1
        signals.append(f"RSI_{rsi['zone'].upper()}")
        notes.append(f"RSI {rsi['rsi']} tại {rsi['zone']} — xác nhận exhaustion")

    # MACD direction matches trade direction (or recovering bullish)
    if trade_direction == "LONG" and (macd["direction"] == "BULLISH" or macd["recovering"]):
        bonus += 1
        signals.append("MACD_BULLISH_CONFIRM")
        notes.append(f"MACD {'recovering bullish' if macd['recovering'] else 'bullish'} — momentum hỗ trợ LONG")
    elif trade_direction == "SHORT" and macd["direction"] == "BEARISH" and not macd["recovering"]:
        bonus += 1
        signals.append("MACD_BEARISH_CONFIRM")
        notes.append(f"MACD bearish — momentum hỗ trợ SHORT")

    # PO3 position matches direction
    if trade_direction == "LONG" and po3["position"] == "discount":
        bonus += 1
        signals.append("PO3_DISCOUNT_LONG")
        notes.append(f"PO3 phase: {po3['phase']} ({po3['pct_from_low']:.0f}% từ đáy range)")
    elif trade_direction == "SHORT" and po3["position"] == "premium":
        bonus += 1
        signals.append("PO3_PREMIUM_SHORT")
        notes.append(f"PO3 phase: {po3['phase']} ({po3['pct_from_high']:.0f}% từ đỉnh range)")

    # SMC structure matches direction
    if trade_direction == "LONG" and smc["structure"] == "bullish":
        bonus += 1
        signals.append("SMC_STRUCTURE_BULLISH")
        notes.append("SMC structure bullish — BOS/CHoCH xác nhận hướng")
    elif trade_direction == "SHORT" and smc["structure"] == "bearish":
        bonus += 1
        signals.append("SMC_STRUCTURE_BEARISH")
        notes.append("SMC structure bearish — BOS/CHoCH xác nhận hướng")

    return {"bonus": min(bonus, 2), "signals": signals, "notes": notes}  # cap at 2 extra points


# ── Main build snapshot ────────────────────────────────────────────────────

_CURRENT_SYMBOL = "BTCUSD"  # set by caller via data["symbol"]


def build_snapshot(data):
    global _CURRENT_SYMBOL
    price         = data.get("price", 0)
    _CURRENT_SYMBOL = data.get("symbol", "BTCUSD")
    study_values  = data.get("study_values", [])
    smc_labels    = data.get("smc_labels", [])
    po3_labels    = data.get("po3_labels", [])
    vp_lines      = data.get("vp_lines", [])
    liq_labels    = data.get("liq_labels", [])
    trade_dir     = data.get("trade_direction")  # optional hint

    smc  = parse_smc(smc_labels, price)
    po3  = parse_po3(po3_labels, price)
    vp   = parse_vp(vp_lines, price)
    liq  = parse_liquidity(liq_labels, price)
    rsi  = parse_rsi(study_values)
    macd = parse_macd(study_values)
    rev  = check_reversal_warning(smc, rsi, macd, price)
    tvb  = compute_tv_bonus(smc, po3, vp, rsi, macd, trade_dir)

    # Overall TV bias
    bull_count = sum([
        1 if smc["structure"] == "bullish" else 0,
        1 if po3["position"] == "discount" else 0,
        1 if rsi["bias"] == "BULLISH" else 0,
        1 if macd["direction"] == "BULLISH" or macd["recovering"] else 0,
    ])
    bear_count = sum([
        1 if smc["structure"] == "bearish" else 0,
        1 if po3["position"] == "premium" else 0,
        1 if rsi["bias"] == "BEARISH" else 0,
        1 if macd["direction"] == "BEARISH" and not macd["recovering"] else 0,
    ])
    tv_bias = "BULLISH" if bull_count > bear_count else \
              "BEARISH" if bear_count > bull_count else "MIXED"

    now = datetime.datetime.now()
    snapshot = {
        "timestamp":    now.strftime("%Y-%m-%dT%H:%M") + " GMT+7",
        "ts_unix":      int(now.timestamp()),
        "symbol":       _CURRENT_SYMBOL,
        "price":        price,
        "smc":          smc,
        "po3":          po3,
        "vp":           vp,
        "liquidity":    liq,
        "rsi":          rsi,
        "macd":         macd,
        "reversal_warning": rev,
        "tv_bonus":     tvb,
        "tv_bias":      tv_bias,
        "bull_signals": bull_count,
        "bear_signals": bear_count,
    }
    return snapshot


def print_summary(snap):
    p   = snap["price"]
    smc = snap["smc"]
    po3 = snap["po3"]
    vp  = snap["vp"]
    rsi = snap["rsi"]
    mac = snap["macd"]
    rev = snap["reversal_warning"]
    tvb = snap["tv_bonus"]

    SEP = "─" * 54
    print(SEP)
    print(f"  TV INDICATORS  {snap['timestamp']}")
    print(SEP)
    print(f"  Price        ${p:,.2f}")
    print(f"  SMC          {smc['structure'].upper():10s}  "
          f"CHoCH@{smc['last_choch']['price'] if smc['last_choch'] else 'N/A'}")
    print(f"  PO3          {po3['phase']:20s}  ({po3['pct_from_low']:.0f}% từ đáy)")
    poc_str = f"{vp['poc']:,.2f}" if vp['poc'] else 'N/A'
    print(f"  VP POC       {poc_str}  pos={vp['position']}")
    print(f"  RSI          {rsi['rsi'] or 'N/A'}  {rsi['zone']:10s}  "
          f"BearDiv={'✅' if rsi['bear_divergence'] else '—'}  "
          f"BullDiv={'✅' if rsi['bull_divergence'] else '—'}")
    hist = mac['histogram']
    hist_str = f"+{hist:.0f}" if hist and hist > 0 else f"{hist:.0f}" if hist else "N/A"
    print(f"  MACD         {mac['direction']:8s}  Hist {hist_str}  "
          f"{'⚡Recovering' if mac['recovering'] else ''}")
    print(SEP)
    print(f"  TV Bias      {snap['tv_bias']}  ({snap['bull_signals']}🟢 / {snap['bear_signals']}🔴)")
    if tvb["bonus"] > 0:
        print(f"  TV Bonus     +{tvb['bonus']} điểm Confluence")
        for n in tvb["notes"]:
            print(f"    → {n}")
    print(SEP)
    if rev["warning"]:
        dirn_str = rev["direction"] or "MIXED (tín hiệu xung đột)"
        print(f"  ⚠️  CẢNH BÁO ĐỔI CHIỀU → {dirn_str}")
        for r in rev["reasons"]:
            print(f"     • {r}")
        print(SEP)

    # Key levels
    if smc["eqh_near"]:
        print(f"  EQH gần  : {[f'{x:,.0f}' for x in smc['eqh_near']]}")
    if smc["eql_near"]:
        print(f"  EQL gần  : {[f'{x:,.0f}' for x in smc['eql_near']]}")
    nr = liq_summary(snap["liquidity"], "resistance")
    ns = liq_summary(snap["liquidity"], "support")
    if nr: print(f"  Resistance: {nr}")
    if ns: print(f"  Support   : {ns}")
    print()


def liq_summary(liq, side):
    key = "nearest_resistance" if side == "resistance" else "nearest_support"
    items = liq.get(key, [])[:3]
    if not items: return ""
    return "  |  ".join(f"{l['price']:,.0f}×{l['strength']}" for l in items)


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    # Parse input
    data = None

    if "--demo" in sys.argv:
        # Demo mode: build test data from market_state.json if available
        if MARKET_STATE.exists():
            state = json.loads(MARKET_STATE.read_text())
            data = {
                "price": state.get("btc", {}).get("price", 80000),
                "study_values": [],
                "smc_labels": [],
                "po3_labels": [],
                "vp_lines": [],
                "liq_labels": [],
            }
            print("⚠️  Demo mode — sử dụng giá từ market_state.json, không có indicator data.")
        else:
            print("❌ Không tìm thấy market_state.json")
            sys.exit(1)

    elif "--file" in sys.argv:
        idx = sys.argv.index("--file")
        path = Path(sys.argv[idx + 1])
        data = json.loads(path.read_text())

    elif not sys.stdin.isatty():
        # Pipe mode
        raw = sys.stdin.read().strip()
        if raw:
            data = json.loads(raw)

    if data is None:
        print(__doc__)
        sys.exit(0)

    snap = build_snapshot(data)
    TV_SNAPSHOT.write_text(json.dumps(snap, indent=2, ensure_ascii=False))
    print_summary(snap)
    print(f"  → Saved: {TV_SNAPSHOT}")


if __name__ == "__main__":
    main()
