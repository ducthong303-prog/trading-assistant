#!/usr/bin/env python3
"""
trade_engine.py  —  Trading Intelligence Engine
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Encapsulates CLAUDE.md §2 (Confluence) + §4 (Setups) + §7 (Signal Output).
Python handles ALL computation → compact JSON checkpoint → Claude handles judgment.

Modes:
  python3 trade_engine.py            # compact summary + write checkpoint
  python3 trade_engine.py --json     # full JSON to stdout
  python3 trade_engine.py --silent   # write checkpoint only, no stdout
"""
import urllib.request, json, datetime, sys
from pathlib import Path

STATE_FILE = Path(__file__).parent / "market_state.json"

# ── Zone definitions ──────────────────────────────────────────────────────────

BTC_ZONES = [
    ("DƯỚI_SL",  0,        79_500),
    ("ZONE_B",   79_500,   80_044),
    ("ZONE_A",   80_044,   80_900),
    ("SILENT",   80_900,   81_397),
    ("BREAKOUT", 81_397,   float("inf")),
]
ETH_ZONES = [
    ("DƯỚI_SL",  0,        2_278),
    ("ENTRY",    2_278,    2_308),
    ("SILENT",   2_308,    2_346),
    ("BREAKOUT", 2_346,    float("inf")),
]

# ── HTTP / API helpers ────────────────────────────────────────────────────────

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def spot(symbol):
    return float(fetch(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")["price"])

def klines(symbol, interval, limit=30):
    data = fetch(
        f"https://api.binance.com/api/v3/klines"
        f"?symbol={symbol}&interval={interval}&limit={limit}"
    )
    return [{"o": float(k[1]), "h": float(k[2]), "l": float(k[3]),
             "c": float(k[4]), "v": float(k[5])} for k in data]

def get_dxy():
    try:
        meta = fetch(
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            "DX-Y.NYB?interval=1d&range=5d"
        )["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev  = meta["chartPreviousClose"]
        w52h  = meta.get("fiftyTwoWeekHigh", 0)
        w52l  = meta.get("fiftyTwoWeekLow", 0)
        trend = "BEARISH" if price < prev else "BULLISH"
        at_supply = bool(w52h and price >= w52h * 0.99)
        at_demand = bool(w52l and price <= w52l * 1.01)
        bonus = 1 if (trend == "BEARISH" and at_supply) or (trend == "BULLISH" and at_demand) else 0
        return {"price": round(price, 3), "trend": trend,
                "at_supply": at_supply, "at_demand": at_demand, "bonus": bonus}
    except Exception as e:
        return {"price": None, "trend": "N/A", "at_supply": False,
                "at_demand": False, "bonus": 0, "err": str(e)}

WATCHLIST = {
    "EURUSD":  "EURUSD=X",
    "GBPUSD":  "GBPUSD=X",
    "USDJPY":  "JPY=X",
    "AUDUSD":  "AUDUSD=X",
    "GBPNZD":  "GBPNZD=X",
    "EURTRY":  "EURTRY=X",
    "XAUUSD":  "GC=F",
    "XAGUSD":  "SI=F",
    "USOIL":   "CL=F",
    "USTEC":   "NQ=F",
}

def get_watchlist_prices():
    """Fetch last price + % change for each watchlist pair from Yahoo Finance."""
    results = {}
    for label, yf_sym in WATCHLIST.items():
        try:
            url  = (f"https://query1.finance.yahoo.com/v8/finance/chart/"
                    f"{yf_sym}?interval=1d&range=1d")
            meta = fetch(url)["chart"]["result"][0]["meta"]
            p    = meta["regularMarketPrice"]
            # % change — prefer direct field, fallback tính từ chartPreviousClose
            chg  = meta.get("regularMarketChangePercent")
            if chg is None:
                prev = meta.get("chartPreviousClose")
                chg  = round((p - prev) / prev * 100, 2) if prev else None
            else:
                chg  = round(chg, 2)
            price_fmt      = round(p, 4) if p < 10 else round(p, 2)
            results[label] = {"price": price_fmt, "change": chg}
        except Exception:
            results[label] = {"price": None, "change": None}
    return results

def session_levels(symbol):
    """Return Asia H/L + PDH/PDL for a Binance symbol."""
    now_utc = datetime.datetime.utcnow()
    now_vn  = now_utc + datetime.timedelta(hours=7)
    tvn     = now_vn.date()

    def vn2utc(d, h):
        return datetime.datetime(d.year, d.month, d.day, h) - datetime.timedelta(hours=7)

    def ms(dt):
        return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)

    def hl(rows):
        if not rows: return None, None
        return max(r["h"] for r in rows), min(r["l"] for r in rows)

    asia_s = vn2utc(tvn, 6)
    asia_e = vn2utc(tvn, 12) if now_vn.hour >= 12 else now_utc
    if now_vn.hour < 6:
        yd = tvn - datetime.timedelta(days=1)
        asia_s, asia_e = vn2utc(yd, 6), vn2utc(yd, 12)

    yd   = tvn - datetime.timedelta(days=1)
    pd_s = vn2utc(yd, 0)
    pd_e = vn2utc(tvn, 0)

    def fetch_hl(s, e):
        url = (f"https://api.binance.com/api/v3/klines?symbol={symbol}"
               f"&interval=1h&startTime={ms(s)}&endTime={ms(e)}&limit=30")
        return [{"h": float(k[2]), "l": float(k[3])} for k in fetch(url)]

    ah, al   = hl(fetch_hl(asia_s, asia_e))
    pdh, pdl = hl(fetch_hl(pd_s, pd_e))
    return {"asia_high": ah, "asia_low": al, "pdh": pdh, "pdl": pdl}

# ── Classify ──────────────────────────────────────────────────────────────────

def zone_of(price, zones):
    for name, lo, hi in zones:
        if lo <= price < hi:
            return name
    return "UNKNOWN"

def vol_ratio(bars, n=20):
    vols = [b["v"] for b in bars]
    sma  = sum(vols[-n:]) / min(n, len(vols)) if vols else 1
    return round(vols[-2] / sma, 2) if len(vols) >= 2 else 0.0

# ── Pattern detection ─────────────────────────────────────────────────────────

def eng_bull(bars):
    if len(bars) < 3: return False
    p, c  = bars[-3], bars[-2]
    total = c["h"] - c["l"]
    return bool(total
                and p["c"] < p["o"]
                and c["c"] > p["o"] and c["o"] < p["c"]
                and c["c"] > c["o"]
                and (c["c"] - c["o"]) / total >= 0.5)

def eng_bear(bars):
    if len(bars) < 3: return False
    p, c  = bars[-3], bars[-2]
    total = c["h"] - c["l"]
    return bool(total
                and p["c"] > p["o"]
                and c["c"] < p["o"] and c["o"] > p["c"]
                and c["c"] < c["o"]
                and (c["o"] - c["c"]) / total >= 0.5)

def wick_bull(bars):
    if len(bars) < 2: return False
    c = bars[-2]; total = c["h"] - c["l"]
    if not total: return False
    return ((min(c["o"], c["c"]) - c["l"]) / total >= 0.5
            and (c["c"] - c["l"]) / total >= 0.7)

def wick_bear(bars):
    if len(bars) < 2: return False
    c = bars[-2]; total = c["h"] - c["l"]
    if not total: return False
    return ((c["h"] - max(c["o"], c["c"])) / total >= 0.5
            and (c["h"] - c["c"]) / total >= 0.7)

# ── Advanced pattern detection ───────────────────────────────────────────────

def is_silver_bullet_hour():
    """Returns (active, label) for ICT Silver Bullet windows.
    London Open SB: 14–15h VN (7–8h UTC).
    NY AM SB:       21–22h VN (14–15h UTC).
    """
    h = (datetime.datetime.utcnow().hour + 7) % 24
    if 14 <= h < 15: return True, "London Open SB (14–15h VN)"
    if 21 <= h < 22: return True, "NY AM SB (21–22h VN)"
    return False, ""


def check_smt_divergence(bars_a, bars_b, n=5):
    """Detect SMT divergence between two correlated assets.
    Compares last n bars vs prior n bars for each asset.
    Returns dict: {type, direction, magnitude, note}
    - BULLISH_SMT: A makes LL but B holds HL → expect Long
    - BEARISH_SMT: A makes HH but B makes LH → expect Short
    """
    if len(bars_a) < n * 2 or len(bars_b) < n * 2:
        return {"type": None, "direction": None, "magnitude": 0.0, "note": "Không đủ dữ liệu"}

    a_now   = bars_a[-n:];    a_prev  = bars_a[-n*2:-n]
    b_now   = bars_b[-n:];    b_prev  = bars_b[-n*2:-n]

    a_hh = max(b["h"] for b in a_now) > max(b["h"] for b in a_prev)
    b_hh = max(b["h"] for b in b_now) > max(b["h"] for b in b_prev)
    a_ll = min(b["l"] for b in a_now) < min(b["l"] for b in a_prev)
    b_ll = min(b["l"] for b in b_now) < min(b["l"] for b in b_prev)

    a_hi_now = max(b["h"] for b in a_now)
    b_hi_now = max(b["h"] for b in b_now)
    a_hi_prev = max(b["h"] for b in a_prev)
    a_lo_now = min(b["l"] for b in a_now)
    b_lo_now = min(b["l"] for b in b_now)
    a_lo_prev = min(b["l"] for b in a_prev)

    # Bearish SMT: one makes HH while the other doesn't
    if a_hh and not b_hh:
        mag = round((a_hi_now - a_hi_prev) / a_hi_prev * 100, 3) if a_hi_prev else 0.0
        return {"type": "BEARISH_SMT", "direction": "SHORT", "magnitude": mag,
                "note": f"A HH({a_hi_now:,.0f}) | B LH({b_hi_now:,.0f}) — phân kỳ {mag:.3f}%"}
    if b_hh and not a_hh:
        b_hi_prev = max(b["h"] for b in b_prev)
        mag = round((b_hi_now - b_hi_prev) / b_hi_prev * 100, 3) if b_hi_prev else 0.0
        return {"type": "BEARISH_SMT", "direction": "SHORT", "magnitude": mag,
                "note": f"B HH({b_hi_now:,.0f}) | A LH({a_hi_now:,.0f}) — phân kỳ {mag:.3f}%"}
    # Bullish SMT: one makes LL while the other holds
    if a_ll and not b_ll:
        mag = round((a_lo_prev - a_lo_now) / a_lo_prev * 100, 3) if a_lo_prev else 0.0
        return {"type": "BULLISH_SMT", "direction": "LONG", "magnitude": mag,
                "note": f"A LL({a_lo_now:,.0f}) | B HL({b_lo_now:,.0f}) — phân kỳ {mag:.3f}%"}
    if b_ll and not a_ll:
        b_lo_prev = min(b["l"] for b in b_prev)
        mag = round((b_lo_prev - b_lo_now) / b_lo_prev * 100, 3) if b_lo_prev else 0.0
        return {"type": "BULLISH_SMT", "direction": "LONG", "magnitude": mag,
                "note": f"B LL({b_lo_now:,.0f}) | A HL({a_lo_now:,.0f}) — phân kỳ {mag:.3f}%"}

    return {"type": None, "direction": None, "magnitude": 0.0, "note": "Không có phân kỳ"}


def detect_msb(bars, n=10):
    """Detect Market Structure Break (MSB) — micro-level BOS confirmation.
    Looks at last-2 closed bar vs swing H/L of prior n bars.
    Returns dict: {direction, level, confirmed, displacement_pct}
    """
    if len(bars) < n + 3:
        return {"direction": None, "level": None, "confirmed": False, "displacement_pct": 0.0}

    window     = bars[-(n+2):-2]      # prior n bars (exclude last 2)
    swing_high = max(b["h"] for b in window)
    swing_low  = min(b["l"] for b in window)
    last       = bars[-2]             # most recently closed bar

    if last["c"] > swing_high and last["c"] > last["o"]:
        disp = round((last["c"] - swing_high) / swing_high * 100, 3)
        return {"direction": "BULLISH", "level": round(swing_high, 2),
                "confirmed": True, "displacement_pct": disp}

    if last["c"] < swing_low and last["c"] < last["o"]:
        disp = round((swing_low - last["c"]) / swing_low * 100, 3)
        return {"direction": "BEARISH", "level": round(swing_low, 2),
                "confirmed": True, "displacement_pct": disp}

    return {"direction": None, "level": None, "confirmed": False, "displacement_pct": 0.0}


def detect_breaker_block(bars, n=20):
    """Detect C1 Breaker Block setup: high-volume OB broken → price retests from opposite side.
    - Bearish Breaker: bullish OB broken downward → retest OB from below → Short
    - Bullish Breaker: bearish OB broken upward  → retest OB from above → Long
    Returns dict: {type, zone_top, zone_bottom, direction, retest_active}
    """
    if len(bars) < n:
        return {"type": None}

    window  = bars[-n:]
    vols    = [b["v"] for b in window]
    sma_vol = sum(vols) / len(vols) if vols else 1

    # Scan high-volume OB candidates (exclude last 3 bars — too recent)
    candidates = [(i, b) for i, b in enumerate(window[:-3]) if b["v"] > sma_vol * 1.5]
    if not candidates:
        return {"type": None}

    last = window[-2]   # most recently closed bar

    for i, ob_bar in reversed(candidates):
        ob_top    = ob_bar["h"]
        ob_bot    = ob_bar["l"]
        ob_is_bull = ob_bar["c"] > ob_bar["o"]
        later     = window[i+1:-1]  # bars after OB, excluding current
        if len(later) < 2:
            continue

        if ob_is_bull:
            # Bullish OB broken below → becomes Bearish Breaker
            broke_below = any(b["c"] < ob_bot for b in later[:-1])
            if broke_below and ob_bot <= last["c"] <= ob_top and last["v"] < sma_vol:
                return {"type": "BEARISH_BREAKER", "zone_top": round(ob_top, 2),
                        "zone_bottom": round(ob_bot, 2), "direction": "SHORT",
                        "retest_active": True}
        else:
            # Bearish OB broken above → becomes Bullish Breaker
            broke_above = any(b["c"] > ob_top for b in later[:-1])
            if broke_above and ob_bot <= last["c"] <= ob_top and last["v"] < sma_vol:
                return {"type": "BULLISH_BREAKER", "zone_top": round(ob_top, 2),
                        "zone_bottom": round(ob_bot, 2), "direction": "LONG",
                        "retest_active": True}

    return {"type": None}


# ── Structure & key levels ────────────────────────────────────────────────────

def detect_structure(bars):
    """Detect most recent BOS direction from H1 klines.
    Returns 'bullish', 'bearish', or 'unknown'."""
    if len(bars) < 6:
        return "unknown"
    window  = bars[-20:]
    mid     = len(window) // 2
    highs   = [b["h"] for b in window]
    lows    = [b["l"] for b in window]
    made_hh = max(highs[mid:]) > max(highs[:mid])
    made_ll = min(lows[mid:])  < min(lows[:mid])
    if made_hh and not made_ll:
        return "bullish"
    if made_ll and not made_hh:
        return "bearish"
    # tiebreaker: last closed candle direction
    return "bullish" if window[-2]["c"] > window[-2]["o"] else "bearish"

def build_key_levels(price, lvl, zones):
    """Collect up to 5 nearest price levels (Asia H/L, PDH/PDL, zone boundaries)."""
    candidates = []
    for k, label in [("asia_high", "Asia High"), ("asia_low", "Asia Low"),
                     ("pdh", "PDH"), ("pdl", "PDL")]:
        v = lvl.get(k)
        if v:
            candidates.append({"label": label, "price": round(v, 2)})
    # Add current zone boundaries
    for name, lo, hi in zones:
        if lo <= price < hi:
            if lo > 0:
                candidates.append({"label": f"{name}_lo", "price": round(lo, 2)})
            if hi != float("inf"):
                candidates.append({"label": f"{name}_hi", "price": round(hi, 2)})
            break
    # Deduplicate, sort by proximity to current price, return 5 closest
    seen, unique = set(), []
    for c in candidates:
        if c["price"] not in seen:
            seen.add(c["price"])
            unique.append(c)
    unique.sort(key=lambda x: abs(x["price"] - price))
    return unique[:5]

# ── Killzone ──────────────────────────────────────────────────────────────────

def kz():
    h = (datetime.datetime.utcnow().hour + 7) % 24
    if 14 <= h < 17: return True, "London (14–17h VN)"
    if 19 <= h < 22: return True, "NY (19–22h VN)"
    return False, "Ngoài KZ"

# ── §2  Confluence engine ─────────────────────────────────────────────────────

def confluence(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, dxy):
    in_kz, kz_label = kz()
    vr      = vol_ratio(btc_h1)
    vol_ok  = vr >= 1.5

    # Sweep detection
    swept = False; swept_note = "Chưa sweep"
    for lbl, price, lvl, bars in [
        ("BTC", btc_p, btc_lvl, btc_h1),
        ("ETH", eth_p, eth_lvl, eth_h1),
    ]:
        if len(bars) < 2: continue
        last = bars[-2]
        if lvl["asia_low"] and last["l"] < lvl["asia_low"] and price > lvl["asia_low"]:
            swept = True; swept_note = f"{lbl} swept Asia Low {lvl['asia_low']:,.0f}"
        elif lvl["pdl"] and last["l"] < lvl["pdl"] and price > lvl["pdl"]:
            swept = True; swept_note = f"{lbl} swept PDL {lvl['pdl']:,.0f}"
        elif lvl["asia_high"] and last["h"] > lvl["asia_high"] and price < lvl["asia_high"]:
            swept = True; swept_note = f"{lbl} swept Asia High {lvl['asia_high']:,.0f}"

    # DXY / SMT — use quantified check_smt_divergence for accuracy
    smt_data   = check_smt_divergence(btc_h1, eth_h1)
    smt        = smt_data["type"] is not None
    dxy_note   = f"DXY {dxy['price']} {dxy['trend']}"
    if dxy["at_supply"]: dxy_note += " — Supply (+1 Long XAU/BTC)"
    if dxy["at_demand"]: dxy_note += " — Demand (+1 Short XAU/BTC)"
    if smt:
        dxy_note += f" | SMT {smt_data['type']} ({smt_data['magnitude']:.3f}%)"
    corr_score = max(dxy["bonus"], 1 if smt else 0)

    bd = {
        "htf":    {"s": 0, "note": "MANUAL — kiểm tra D1/H4 trên chart"},
        "kz":     {"s": 1 if in_kz else 0, "note": kz_label},
        "volume": {"s": 1 if vol_ok else 0, "note": f"BTC H1 vol {vr}× SMA20"},
        "sweep":  {"s": 1 if swept else 0,  "note": swept_note},
        "corr":   {"s": corr_score,          "note": dxy_note},
    }
    score   = sum(v["s"] for v in bd.values())
    verdict = ("STAND_ASIDE"  if score <= 2 else
               "WAIT_CONFIRM" if score == 3 else
               "ACTIONABLE")
    return score, bd, verdict

# ── FVG detection ────────────────────────────────────────────────────────────

def find_micro_fvg(bars):
    """Find unfilled FVGs. Returns up to 8 most recent."""
    fvgs = []
    for i in range(2, len(bars)):
        if bars[i-2]["h"] < bars[i]["l"]:           # Bullish gap
            fvgs.append({"type": "BULLISH",
                         "top":      bars[i]["l"],
                         "bottom":   bars[i-2]["h"],
                         "midpoint": (bars[i]["l"] + bars[i-2]["h"]) / 2,
                         "bar_idx":  i})
        elif bars[i-2]["l"] > bars[i]["h"]:          # Bearish gap
            fvgs.append({"type": "BEARISH",
                         "top":      bars[i-2]["l"],
                         "bottom":   bars[i]["h"],
                         "midpoint": (bars[i-2]["l"] + bars[i]["h"]) / 2,
                         "bar_idx":  i})

    # Keep only unfilled: drop if subsequent bars traded through entire range
    unfilled = []
    for fvg in fvgs:
        filled = False
        for b in bars[fvg["bar_idx"] + 1:]:
            if b["l"] <= fvg["bottom"] and b["h"] >= fvg["top"]:
                filled = True
                break
        if not filled:
            unfilled.append({k: v for k, v in fvg.items() if k != "bar_idx"})
    return unfilled[-8:]


def nearest_fvg(fvgs, price, direction):
    """Find closest unfilled FVG to current price in the given direction.
    direction='BULLISH' → FVG below price (Long entry zone).
    direction='BEARISH' → FVG above price (Short entry zone).
    """
    candidates = [f for f in fvgs if f["type"] == direction]
    if direction == "BULLISH":
        below = [f for f in candidates if f["top"] < price]
        return min(below, key=lambda f: price - f["midpoint"]) if below else None
    else:
        above = [f for f in candidates if f["bottom"] > price]
        return min(above, key=lambda f: f["midpoint"] - price) if above else None


# ── §4  Setup classifier ──────────────────────────────────────────────────────

def detect_setup(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, score,
                 btc_fvg_h1=None, btc_fvg_m5=None):
    h             = (datetime.datetime.utcnow().hour + 7) % 24
    in_london     = 14 <= h < 17
    in_kz_now, _ = kz()
    sb_active, sb_label = is_silver_bullet_hour()
    btc_fvg_h1    = btc_fvg_h1 or []
    btc_fvg_m5    = btc_fvg_m5 or []

    def sw_lo(bars, lvl): return (len(bars) >= 2 and lvl
                                  and bars[-2]["l"] < lvl and bars[-1]["c"] > lvl)
    def sw_hi(bars, lvl): return (len(bars) >= 2 and lvl
                                  and bars[-2]["h"] > lvl and bars[-1]["c"] < lvl)

    btc_sl = sw_lo(btc_h1, btc_lvl["asia_low"]) or sw_lo(btc_h1, btc_lvl["pdl"])
    btc_sh = sw_hi(btc_h1, btc_lvl["asia_high"])
    eth_sl = sw_lo(eth_h1, eth_lvl["asia_low"])

    trig_bull = eng_bull(btc_h1) or wick_bull(btc_h1)
    trig_bear = eng_bear(btc_h1) or wick_bear(btc_h1)

    # A+3 — SMT Reversal: highest conviction, check before Judas/PO3
    smt_data = check_smt_divergence(btc_h1, eth_h1)
    msb      = detect_msb(btc_h1)
    if in_kz_now and smt_data["type"] and msb["confirmed"] and score >= 3:
        dirn = smt_data["direction"]
        return ("A+3",
                f"SMT Reversal {dirn} — {smt_data['note']} | MSB {msb['direction']} "
                f"at {msb['level']:,.0f} (Δ{msb['displacement_pct']:.3f}%)")

    # A1 — Judas Swing: sweep + trigger confirmed, add FVG note if available
    if in_london and (btc_sl or btc_sh) and (trig_bull or trig_bear):
        dirn     = "LONG" if btc_sl else "SHORT"
        fvg_type = "BULLISH" if btc_sl else "BEARISH"
        fvg      = nearest_fvg(btc_fvg_h1, btc_p, fvg_type)
        note     = f"Judas Swing — {dirn}"
        if fvg:
            note += f" | FVG {fvg['bottom']:,.0f}–{fvg['top']:,.0f}"
        return "A1", note

    # A+2 — Power of 3: sweep detected, awaiting FVG retest
    if in_london and (btc_sl or btc_sh):
        dirn     = "LONG" if btc_sl else "SHORT"
        fvg_type = "BULLISH" if btc_sl else "BEARISH"
        fvg      = nearest_fvg(btc_fvg_h1, btc_p, fvg_type)
        if fvg:
            return "A+2", f"Power of 3 — pha Manipulation | FVG retest {fvg['bottom']:,.0f}–{fvg['top']:,.0f}"
        return "A+2", "Power of 3 — pha Manipulation, chờ FVG retest"

    # A2 — Symmetry SMT (simpler zone-level check, lower conviction than A+3)
    if in_kz_now and ((btc_sl and not eth_sl) or (eth_sl and not btc_sl)):
        return "A2", "Symmetry SMT BTC/ETH divergence tại POI"

    # C1 — Breaker Block: broken OB retest (check before B setups)
    bb = detect_breaker_block(btc_h1)
    if bb["type"] and in_kz_now:
        dirn = bb["direction"]
        return ("C1",
                f"Breaker Block {bb['type']} {dirn} — retest "
                f"{bb['zone_bottom']:,.0f}–{bb['zone_top']:,.0f}")

    # B1 — Silver Bullet: both London Open (14–15h) and NY AM (21–22h) windows
    if sb_active and score >= 2:
        fvg_m5 = (nearest_fvg(btc_fvg_m5, btc_p, "BULLISH") or
                  nearest_fvg(btc_fvg_m5, btc_p, "BEARISH"))
        if fvg_m5:
            return ("B1",
                    f"Silver Bullet [{sb_label}] — FVG M5 "
                    f"{fvg_m5['bottom']:,.0f}–{fvg_m5['top']:,.0f}")
        return None, f"B1 [{sb_label}]: chưa có FVG M5 trong cửa sổ này"

    # B2 — FTR
    if score >= 2 and (trig_bull or trig_bear):
        return "B2", "FTR — continuation retest Base"

    return None, "Không có setup"

# ── §7  Signal format ─────────────────────────────────────────────────────────

def signal_text(setup, note, score, bd, btc_p, btc_lvl,
                btc_fvg=None, direction=None):
    if score <= 2:
        return "Thị trường chưa sẵn sàng."

    # Detect direction from note if not provided
    if direction is None:
        direction = "LONG" if any(k in note for k in ("LONG", "Bull", "sweep Low")) else "SHORT"

    btc_fvg = btc_fvg or []
    fvg_type = "BULLISH" if direction == "LONG" else "BEARISH"
    fvg = nearest_fvg(btc_fvg, btc_p, fvg_type)

    # Entry + SL from FVG when available
    if fvg:
        entry = round(fvg["midpoint"], 1)
        sl    = (round(fvg["bottom"] - 55, 1) if direction == "LONG"
                 else round(fvg["top"] + 55, 1))
        entry_note = f"${entry:,.1f}  (FVG {fvg['bottom']:,.0f}–{fvg['top']:,.0f} midpoint)"
    else:
        entry = btc_p
        sl    = round((btc_lvl.get("pdl") or btc_p * 0.993) - 55, 1)
        entry_note = f"${entry:,.1f}  (market — FVG chưa xác định)"

    # TP: asia_high for LONG, asia_low for SHORT
    tp_ref = (btc_lvl.get("asia_high") if direction == "LONG"
              else btc_lvl.get("asia_low")) or btc_p
    tp = round(tp_ref, 1)

    risk   = abs(entry - sl)
    reward = abs(tp - entry)
    rr     = round(reward / risk, 1) if risk else 0

    action = {5: "⚡ Vào lệnh ngay", 4: "⚡ Vào lệnh ngay",
              3: "👀 Đặt Limit / Đợi xác nhận"}.get(score, "🚫 Đứng ngoài")
    size   = {"A+1":"2%","A+3":"1.5%","A+2":"1%","A1":"1%","A2":"0.5–1%",
              "B1":"0.5–1%","B2":"0.5%","C1":"0.5%"}.get(setup, "0.5%")
    state  = "Reversal" if any(k in note for k in ("Judas", "LONG", "SHORT")) else "Continuation"

    return "\n".join([
        f"Phân loại:  {setup} — {note}",
        f"Trạng thái: {state}",
        "",
        f"Confluence Score: {score}/5",
        f"  (+{bd['htf']['s']}) HTF Bias       — {bd['htf']['note']}",
        f"  (+{bd['kz']['s']}) Killzone        — {bd['kz']['note']}",
        f"  (+{bd['volume']['s']}) Volume          — {bd['volume']['note']}",
        f"  (+{bd['sweep']['s']}) Liquidity Sweep — {bd['sweep']['note']}",
        f"  (+{bd['corr']['s']}) DXY/SMT         — {bd['corr']['note']}",
        "",
        f"Hành động: {action}",
        "Chi tiết:",
        f"  Entry: {entry_note}",
        f"  SL:    ${sl:,.1f}",
        f"  TP:    ${tp:,.1f}  (RR: {rr}:1)",
        f"  Size:  {size} tài khoản",
    ])

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    mode   = sys.argv[1] if len(sys.argv) > 1 else ""
    now_vn = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    in_kz_now, kz_label = kz()

    # Fetch all data
    btc_p  = spot("BTCUSDT");   eth_p  = spot("ETHUSDT")
    # Validate — tránh giá rác (0, cực lớn) kích hoạt hard alert sai
    if not (1_000 < btc_p < 200_000):
        print(f"ERROR: BTC giá không hợp lệ ({btc_p}) — dừng chu kỳ"); sys.exit(1)
    if not (100 < eth_p < 20_000):
        print(f"ERROR: ETH giá không hợp lệ ({eth_p}) — dừng chu kỳ"); sys.exit(1)
    btc_h1  = klines("BTCUSDT", "1h", 30)
    eth_h1  = klines("ETHUSDT", "1h", 30)
    btc_m5  = klines("BTCUSDT", "5m", 50)
    eth_m5  = klines("ETHUSDT", "5m", 50)
    dxy     = get_dxy()
    btc_lvl = session_levels("BTCUSDT")
    eth_lvl = session_levels("ETHUSDT")

    # FVG detection
    btc_fvg_h1 = find_micro_fvg(btc_h1)
    btc_fvg_m5 = find_micro_fvg(btc_m5)
    eth_fvg_h1 = find_micro_fvg(eth_h1)
    eth_fvg_m5 = find_micro_fvg(eth_m5)

    # Compute
    score, bd, verdict = confluence(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, dxy)
    setup, s_note      = detect_setup(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, score,
                                      btc_fvg_h1=btc_fvg_h1, btc_fvg_m5=btc_fvg_m5)
    # Pass combined FVG list (H1 + M5) to signal, prefer H1 for entry precision
    sig = signal_text(setup, s_note, score, bd, btc_p, btc_lvl,
                      btc_fvg=btc_fvg_h1 + btc_fvg_m5) if setup else None
    btc_z         = zone_of(btc_p, BTC_ZONES)
    eth_z         = zone_of(eth_p, ETH_ZONES)
    vr            = vol_ratio(btc_h1)
    btc_structure  = detect_structure(btc_h1)
    btc_key_levels = build_key_levels(btc_p, btc_lvl, BTC_ZONES)
    watchlist      = get_watchlist_prices()
    smt_data       = check_smt_divergence(btc_h1, eth_h1)
    msb_data       = detect_msb(btc_h1)
    sb_active, sb_label = is_silver_bullet_hour()

    # Checkpoint
    state = {
        "ts":             now_vn.strftime("%Y-%m-%dT%H:%M") + " GMT+7",
        "last_structure": btc_structure,
        "key_levels":     btc_key_levels,
        "kz":  {"active": in_kz_now, "label": kz_label},
        "btc": {"price": round(btc_p, 2), "zone": btc_z, "vol_ratio": vr,
                "engulfing": eng_bull(btc_h1) or eng_bear(btc_h1),
                "wick":      wick_bull(btc_h1) or wick_bear(btc_h1),
                "fvg_h1": [{"type": f["type"], "top": round(f["top"], 2),
                             "bottom": round(f["bottom"], 2)} for f in btc_fvg_h1],
                "fvg_m5": [{"type": f["type"], "top": round(f["top"], 2),
                             "bottom": round(f["bottom"], 2)} for f in btc_fvg_m5],
                **{k: (round(v, 2) if v else None) for k, v in btc_lvl.items()}},
        "eth": {"price": round(eth_p, 2), "zone": eth_z,
                "fvg_h1": [{"type": f["type"], "top": round(f["top"], 2),
                             "bottom": round(f["bottom"], 2)} for f in eth_fvg_h1],
                "fvg_m5": [{"type": f["type"], "top": round(f["top"], 2),
                             "bottom": round(f["bottom"], 2)} for f in eth_fvg_m5],
                **{k: (round(v, 2) if v else None) for k, v in eth_lvl.items()}},
        "dxy": dxy,
        "confluence": {
            "score":     score,
            "verdict":   verdict,
            "breakdown": {k: {"score": v["s"], "note": v["note"]} for k, v in bd.items()},
        },
        "setup":     {"code": setup, "note": s_note, "signal": sig},
        "smt":       {"type": smt_data["type"], "direction": smt_data["direction"],
                      "magnitude": smt_data["magnitude"], "note": smt_data["note"]},
        "msb":       {"direction": msb_data["direction"], "level": msb_data["level"],
                      "confirmed": msb_data["confirmed"],
                      "displacement_pct": msb_data["displacement_pct"]},
        "silver_bullet": {"active": sb_active, "label": sb_label},
        "watchlist": watchlist,
    }
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

    if mode == "--silent": return
    if mode == "--json":
        print(json.dumps(state, indent=2, ensure_ascii=False))
        return

    # Compact human-readable output (replaces reading CLAUDE.md on every call)
    V   = {"STAND_ASIDE": "⏸", "WAIT_CONFIRM": "👀", "ACTIONABLE": "⚡"}
    SEP = "─" * 54
    print(SEP)
    print(f"  TRADE ENGINE  {state['ts']}")
    print(SEP)
    print(f"  BTC  ${btc_p:>10,.2f}  [{btc_z}]  vol {vr}×")
    print(f"  ETH  ${eth_p:>10,.2f}  [{eth_z}]")
    dxy_str = str(dxy["price"] or "N/A")
    print(f"  DXY  {dxy_str:>10}   {dxy['trend']}"
          + ("  ⚠️ Supply" if dxy["at_supply"] else ""))
    print(SEP)
    print(f"  KZ     : {kz_label}")
    print(f"  Sweep  : {bd['sweep']['note']}")
    print(f"  Vol    : {bd['volume']['note']}")
    print(SEP)
    print(f"  Score  : {score}/5  {V[verdict]}  {verdict}")
    print(f"  Setup  : {setup or '—'}  {s_note}")
    print(SEP)
    if sig and score >= 3:
        print()
        print(sig)
    else:
        print(f"  → {'Thị trường chưa sẵn sàng.' if score <= 2 else s_note}")
    print()


# ── Trade logger ──────────────────────────────────────────────────────────────

LOG_FILE = Path(__file__).parent / "trade_log.json"

def log_trade(data_str):
    """Append a trade record (JSON string) into trade_log.json → trades array.
    Keeps the existing account / weekly_summary structure intact.
    Retains the 50 most recent trades."""
    try:
        new_trade = json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON không hợp lệ: {e}")
        return

    # Load existing file or create skeleton
    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            log = json.load(f)
    else:
        log = {"account": {}, "trades": [], "weekly_summary": []}

    # Ensure structure is a dict with a trades list (guard against flat-list files)
    if isinstance(log, list):
        log = {"account": {}, "trades": log, "weekly_summary": []}

    new_trade["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log["trades"].append(new_trade)
    log["trades"] = log["trades"][-50:]  # keep latest 50

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(f"✅ Đã ghi nhật ký lệnh {new_trade.get('pair', new_trade.get('trade_id', 'Unknown'))}")


def analyze_open_trade(trade):
    """Evaluate a trade against CLAUDE.md rules (§5 RR/KZ/Score, §4 Setup, §6 Zone).
    Returns dict: {verdict, issues, confirmations, advice, rr}."""
    entry  = float(trade.get("entry", 0))
    sl     = float(trade.get("sl", 0))
    tp1    = trade.get("tp1")
    score  = trade.get("entry_score")
    in_kz  = trade.get("entry_in_kz")
    zone   = (trade.get("entry_zone") or "").upper()
    setup  = trade.get("entry_setup") or ""

    risk   = abs(entry - sl) or 1
    reward = abs(float(tp1) - entry) if tp1 else None
    rr     = round(reward / risk, 1) if reward else None

    issues, confirmations, advice = [], [], []

    # §5 RR filter
    if rr is None:
        issues.append("Không có TP1 — không tính được RR")
    elif rr < 1.5:
        issues.append(f"RR {rr}:1 dưới ngưỡng tối thiểu 1.5 — §5 từ chối")
    elif rr < 2.0:
        advice.append(f"RR {rr}:1 — scalp only, size tối đa 0.5%")
    elif rr >= 3.0:
        confirmations.append(f"RR {rr}:1 — đủ điều kiện A+1 Unicorn")
    else:
        confirmations.append(f"RR {rr}:1 — acceptable")

    # §5 Killzone HARD rule
    if in_kz is False:
        issues.append("Vào ngoài Killzone — vi phạm §5 HARD rule (trừ B2 FTR)")
    elif in_kz is True:
        confirmations.append("Trong Killzone")

    # §7 Confluence score threshold
    if score is not None:
        if score <= 2:
            issues.append(f"Score {score}/5 — §7: Stand Aside, cần ≥ 3 để vào lệnh")
        elif score == 3:
            advice.append(f"Score {score}/5 — xác nhận bắt buộc, size tối thiểu")
        elif score >= 4:
            confirmations.append(f"Score {score}/5")

    # §6 Zone check
    if "SILENT" in zone:
        issues.append("Entry vùng SILENT — vùng trung gian, không có edge rõ ràng")
    elif zone in ("ZONE_B", "ZONE_A", "ENTRY"):
        confirmations.append(f"Vùng {zone}")

    # §4 Setup
    if not setup:
        advice.append("Không detect được setup — ghi thủ công để cải thiện tracking")

    # Verdict
    has_critical = any(True for i in issues if "RR" in i or "Killzone" in i or "Score" in i)
    verdict = ("✅ Hợp lệ theo quy tắc" if not issues else
               "❌ Vi phạm quy tắc cứng — cân nhắc lại" if has_critical else
               "⚠️ Có điểm cần lưu ý")
    return {"verdict": verdict, "issues": issues,
            "confirmations": confirmations, "advice": advice, "rr": rr}


def open_trade(data_str):
    """Log a new OPEN trade, snapshotting market context from market_state.json."""
    try:
        new_trade = json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"❌ JSON không hợp lệ: {e}")
        return

    # Snapshot context at entry time
    try:
        snap = json.loads(STATE_FILE.read_text())
        pair = new_trade.get("pair", "").upper()
        if "ETH" in pair:
            new_trade.setdefault("entry_zone", snap["eth"]["zone"])
        else:
            new_trade.setdefault("entry_zone", snap["btc"]["zone"])
        new_trade.setdefault("entry_score",  snap["confluence"]["score"])
        new_trade.setdefault("entry_setup",  snap["setup"]["code"])
        new_trade.setdefault("entry_in_kz",  snap["kz"]["active"])
    except Exception:
        pass

    now = datetime.datetime.now()
    # Generate trade_id if not provided
    if "trade_id" not in new_trade:
        log = {}
        if LOG_FILE.exists():
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        today = now.strftime("%Y%m%d")
        existing = [t for t in log.get("trades", []) if t.get("trade_id", "").startswith(f"TS_{today}")]
        new_trade["trade_id"] = f"TS_{today}_{len(existing)+1:02d}"

    new_trade.update({
        "status":     "OPEN",
        "result":     None,
        "exit":       None,
        "pnl_pts":    None,
        "date_open":  now.strftime("%Y-%m-%d"),
        "date_close": None,
        "timestamp":  now.strftime("%Y-%m-%d %H:%M:%S"),
    })

    log_trade(json.dumps(new_trade))
    print(f"📋 Trade ID: {new_trade['trade_id']}  |  Status: OPEN")
    print(f"   {new_trade.get('pair','')} {new_trade.get('direction','')}  "
          f"Entry:{new_trade.get('entry','')}  SL:{new_trade.get('sl','')}  "
          f"TP1:{new_trade.get('tp1','')}")

    # ── Rule scan §2/§4/§5/§6 ────────────────────────────────────────────────
    a = analyze_open_trade(new_trade)
    SEP = "─" * 44
    print(f"\n{SEP}")
    print(f"  Kiểm tra quy tắc  {a['verdict']}")
    print(SEP)
    for c in a["confirmations"]:
        print(f"  ✅ {c}")
    for w in a["advice"]:
        print(f"  ⚠️  {w}")
    for e in a["issues"]:
        print(f"  ❌ {e}")
    if a["issues"]:
        print(f"\n  → Có {len(a['issues'])} vi phạm — xem lại trước khi thực hiện.")
    print(SEP)


def close_trade(pair, exit_price_str):
    """Find the most recent OPEN trade for pair, close it with exit_price.
    Prints the closed trade as JSON to stdout for slash command consumption."""
    try:
        exit_price = float(exit_price_str)
    except ValueError:
        print(f"❌ Exit price không hợp lệ: {exit_price_str}")
        sys.exit(1)

    if not LOG_FILE.exists():
        print("❌ Không tìm thấy trade_log.json")
        sys.exit(1)

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log = json.load(f)

    # Find most recent OPEN trade matching pair (normalize: remove /, uppercase)
    def norm(s): return s.upper().replace("/", "")
    pair_n = norm(pair)
    open_trades = [
        (i, t) for i, t in enumerate(log.get("trades", []))
        if t.get("status") == "OPEN" and pair_n in norm(t.get("pair", ""))
    ]

    if not open_trades:
        print(f"❌ Không tìm thấy lệnh OPEN cho {pair}")
        sys.exit(1)

    idx, trade = open_trades[-1]

    entry = float(trade["entry"])
    sl    = float(trade["sl"])
    tp1   = trade.get("tp1")
    dirn  = trade.get("direction", "LONG").upper()
    risk  = abs(entry - sl) or 1
    pnl   = (exit_price - entry) if dirn == "LONG" else (entry - exit_price)
    rr    = round(pnl / risk, 2)

    if pnl > 0:
        result = "WIN"
    elif pnl < 0:
        result = "LOSS"
    else:
        result = "BE"

    trade.update({
        "status":       "CLOSED",
        "exit":         round(exit_price, 2),
        "pnl_pts":      round(pnl, 2),
        "rr_achieved":  rr,
        "result":       result,
        "date_close":   datetime.datetime.now().strftime("%Y-%m-%d"),
    })
    log["trades"][idx] = trade

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(json.dumps(trade, ensure_ascii=False))


def update_weekly_summary():
    """Recalculate weekly_summary for current ISO week from closed trades.
    Upserts the record and prints the summary JSON to stdout."""
    if not LOG_FILE.exists():
        print("❌ Không tìm thấy trade_log.json")
        sys.exit(1)

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        log = json.load(f)

    today   = datetime.date.today()
    # ISO week string, e.g. "2026-W19"
    week_str = today.strftime("%G-W%V")
    monday  = today - datetime.timedelta(days=today.weekday())
    sunday  = monday + datetime.timedelta(days=6)

    week_trades = []
    for t in log.get("trades", []):
        if t.get("status") != "CLOSED":
            continue
        d_str = t.get("date_close") or t.get("date_open") or ""
        try:
            d = datetime.date.fromisoformat(d_str)
            if monday <= d <= sunday:
                week_trades.append(t)
        except ValueError:
            pass

    wins   = [t for t in week_trades if t.get("result") == "WIN"]
    losses = [t for t in week_trades if t.get("result") == "LOSS"]
    bes    = [t for t in week_trades if t.get("result") == "BE"]
    total  = len(week_trades)

    summary = {
        "week":           week_str,
        "trades_closed":  total,
        "trades_open":    sum(1 for t in log.get("trades", []) if t.get("status") == "OPEN"),
        "trades_win":     len(wins),
        "trades_loss":    len(losses),
        "trades_be":      len(bes),
        "win_rate_pct":   round(len(wins) / total * 100) if total else 0,
        "pnl_pts_closed": round(sum(t.get("pnl_pts", 0) or 0 for t in week_trades), 2),
    }

    summaries = log.get("weekly_summary", [])
    existing  = next((i for i, s in enumerate(summaries) if s.get("week") == week_str), None)
    if existing is not None:
        summaries[existing].update(summary)
    else:
        summaries.append(summary)
    log["weekly_summary"] = summaries

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    # Handle sub-commands before delegating to main()
    if len(sys.argv) >= 3 and sys.argv[1] == "--log-trade":
        log_trade(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "--open-trade":
        open_trade(sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "--close-trade":
        close_trade(sys.argv[2], sys.argv[3])
    elif sys.argv[1:2] == ["--update-weekly"]:
        update_weekly_summary()
    else:
        main()
