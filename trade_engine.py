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

    # DXY / SMT
    btc_z = zone_of(btc_p, BTC_ZONES)
    eth_z = zone_of(eth_p, ETH_ZONES)
    smt   = (btc_z == "DƯỚI_SL") != (eth_z == "DƯỚI_SL")  # divergence at SL zone
    dxy_note = f"DXY {dxy['price']} {dxy['trend']}"
    if dxy["at_supply"]: dxy_note += " — Supply (+1 Long XAU/BTC)"
    if dxy["at_demand"]: dxy_note += " — Demand (+1 Short XAU/BTC)"
    if smt: dxy_note += " | SMT BTC/ETH divergence"
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

# ── §4  Setup classifier ──────────────────────────────────────────────────────

def detect_setup(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, score):
    h         = (datetime.datetime.utcnow().hour + 7) % 24
    in_london = 14 <= h < 17
    in_ny     = 19 <= h < 22
    in_kz_now, _ = kz()

    def sw_lo(bars, lvl): return (len(bars) >= 2 and lvl
                                  and bars[-2]["l"] < lvl and bars[-1]["c"] > lvl)
    def sw_hi(bars, lvl): return (len(bars) >= 2 and lvl
                                  and bars[-2]["h"] > lvl and bars[-1]["c"] < lvl)

    btc_sl = sw_lo(btc_h1, btc_lvl["asia_low"]) or sw_lo(btc_h1, btc_lvl["pdl"])
    btc_sh = sw_hi(btc_h1, btc_lvl["asia_high"])
    eth_sl = sw_lo(eth_h1, eth_lvl["asia_low"])
    eth_sh = sw_hi(eth_h1, eth_lvl["asia_high"])

    trig_bull = eng_bull(btc_h1) or wick_bull(btc_h1)
    trig_bear = eng_bear(btc_h1) or wick_bear(btc_h1)

    if in_london and (btc_sl or btc_sh) and (trig_bull or trig_bear):
        return "A1", "Judas Swing — " + ("LONG" if btc_sl else "SHORT")
    if in_london and (btc_sl or btc_sh):
        return "A+2", "Power of 3 — pha Manipulation, chờ FVG retest"
    if in_kz_now and ((btc_sl and not eth_sl) or (eth_sl and not btc_sl)):
        return "A2", "Symmetry SMT BTC/ETH divergence tại POI"
    if 21 <= h < 22 and score >= 2:
        return "B1", "Silver Bullet — theo dõi FVG M5 hình thành"
    if score >= 2 and (trig_bull or trig_bear):
        return "B2", "FTR — continuation retest Base"
    return None, "Không có setup"

# ── §7  Signal format ─────────────────────────────────────────────────────────

def signal_text(setup, note, score, bd, btc_p, btc_lvl):
    if score <= 2:
        return "Thị trường chưa sẵn sàng."

    sl_ref = btc_lvl.get("pdl") or btc_lvl.get("asia_low") or (btc_p * 0.993)
    tp_ref = btc_lvl.get("asia_high") or (btc_p * 1.012)
    entry  = btc_p
    sl     = sl_ref - 55
    tp     = tp_ref
    rr     = round((tp - entry) / (entry - sl), 1) if entry > sl else 0
    action = {5: "⚡ Vào lệnh ngay", 4: "⚡ Vào lệnh ngay",
              3: "👀 Đặt Limit / Đợi xác nhận"}.get(score, "🚫 Đứng ngoài")
    size   = {"A+1":"2%","A+2":"1%","A1":"1%","A2":"0.5–1%",
              "B1":"0.5–1%","B2":"0.5%"}.get(setup, "0.5%")

    return "\n".join([
        f"Phân loại:  {setup} — {note}",
        f"Trạng thái: {'Reversal' if ('LONG' in note or 'Judas' in note) else 'Continuation'}",
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
        f"  Entry: ${entry:,.1f}",
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
    btc_h1 = klines("BTCUSDT", "1h", 30)
    eth_h1 = klines("ETHUSDT", "1h", 30)
    dxy    = get_dxy()
    btc_lvl = session_levels("BTCUSDT")
    eth_lvl = session_levels("ETHUSDT")

    # Compute
    score, bd, verdict = confluence(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, dxy)
    setup, s_note      = detect_setup(btc_p, eth_p, btc_h1, eth_h1, btc_lvl, eth_lvl, score)
    sig                = signal_text(setup, s_note, score, bd, btc_p, btc_lvl) if setup else None
    btc_z = zone_of(btc_p, BTC_ZONES)
    eth_z = zone_of(eth_p, ETH_ZONES)
    vr    = vol_ratio(btc_h1)

    # Checkpoint
    state = {
        "ts":  now_vn.strftime("%Y-%m-%dT%H:%M") + " GMT+7",
        "kz":  {"active": in_kz_now, "label": kz_label},
        "btc": {"price": round(btc_p, 2), "zone": btc_z, "vol_ratio": vr,
                "engulfing": eng_bull(btc_h1) or eng_bear(btc_h1),
                "wick":      wick_bull(btc_h1) or wick_bear(btc_h1),
                **{k: (round(v, 2) if v else None) for k, v in btc_lvl.items()}},
        "eth": {"price": round(eth_p, 2), "zone": eth_z,
                **{k: (round(v, 2) if v else None) for k, v in eth_lvl.items()}},
        "dxy": dxy,
        "confluence": {
            "score":     score,
            "verdict":   verdict,
            "breakdown": {k: {"score": v["s"], "note": v["note"]} for k, v in bd.items()},
        },
        "setup": {"code": setup, "note": s_note, "signal": sig},
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


if __name__ == "__main__":
    main()
