#!/usr/bin/env python3
"""
session_analyzer.py
Lấy Asia Session H/L (06–12h VN) + PDH/PDL + London sweep detection
Hỗ trợ Confluence Score cho Setup A1 (Judas Swing) và A+2 (Power of 3)
"""
import urllib.request, json, datetime

# ── API helpers ─────────────────────────────────────────────────────────────────

def fetch(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def klines(symbol, interval, start_ms, end_ms):
    url = (f"https://api.binance.com/api/v3/klines"
           f"?symbol={symbol}&interval={interval}"
           f"&startTime={start_ms}&endTime={end_ms}&limit=200")
    rows = fetch(url)
    return [{"t": k[0], "h": float(k[2]), "l": float(k[3]), "c": float(k[4])} for k in rows]

def spot_price(symbol):
    return float(fetch(f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}")["price"])

def to_ms(dt):
    """datetime (UTC naive) → Unix ms"""
    return int(dt.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)

def hl(bars):
    if not bars:
        return None, None
    return max(b["h"] for b in bars), min(b["l"] for b in bars)

# ── Session windows (UTC) ───────────────────────────────────────────────────────

def session_windows():
    now_utc  = datetime.datetime.utcnow().replace(second=0, microsecond=0)
    now_vn   = now_utc + datetime.timedelta(hours=7)
    today_vn = now_vn.date()

    def vn_to_utc(d, h):
        return datetime.datetime(d.year, d.month, d.day, h, 0) - datetime.timedelta(hours=7)

    # ── Asia session: 06:00–12:00 VN ──
    asia_s = vn_to_utc(today_vn, 6)
    asia_e = vn_to_utc(today_vn, 12)

    if now_vn.hour < 6:
        # Trước Asia — dùng phiên Á hôm qua
        yday = today_vn - datetime.timedelta(days=1)
        asia_s = vn_to_utc(yday, 6)
        asia_e = vn_to_utc(yday, 12)
    elif now_vn.hour < 12:
        # Asia đang mở — cap tại now
        asia_e = now_utc

    # ── London session: 14:00–17:00 VN ──
    london_active = now_vn.hour >= 14
    london_s = vn_to_utc(today_vn, 14)
    london_e = min(vn_to_utc(today_vn, 17), now_utc) if london_active else None

    # ── Previous Day: 00:00–24:00 VN hôm qua ──
    yday     = today_vn - datetime.timedelta(days=1)
    pd_s     = vn_to_utc(yday, 0)
    pd_e     = vn_to_utc(today_vn, 0)

    return {
        "now_utc": now_utc, "now_vn": now_vn,
        "asia":     (asia_s, asia_e),
        "london":   (london_s, london_e) if london_active else None,
        "prev_day": (pd_s, pd_e),
    }

# ── Symbol analysis ─────────────────────────────────────────────────────────────

def analyze(symbol, label, price, wins):
    a_s, a_e = wins["asia"]
    p_s, p_e = wins["prev_day"]

    asia_bars = klines(symbol, "1h", to_ms(a_s), to_ms(a_e))
    pd_bars   = klines(symbol, "1h", to_ms(p_s), to_ms(p_e))
    asia_h, asia_l = hl(asia_bars)
    pdh, pdl        = hl(pd_bars)

    lon_h = lon_l = None
    if wins["london"]:
        l_s, l_e = wins["london"]
        lon_bars = klines(symbol, "1h", to_ms(l_s), to_ms(l_e))
        lon_h, lon_l = hl(lon_bars)

    # Sweep: London phá vỡ Asia range rồi price quay trở vào trong
    swept_hi = bool(lon_h and asia_h and lon_h > asia_h and price < asia_h)
    swept_lo = bool(lon_l and asia_l and lon_l < asia_l and price > asia_l)

    def pct(level):
        return (price / level - 1) * 100 if level else None

    return {
        "label": label, "price": price,
        "asia_h": asia_h, "asia_l": asia_l, "asia_bars": len(asia_bars),
        "pdh": pdh, "pdl": pdl,
        "lon_h": lon_h, "lon_l": lon_l,
        "swept_hi": swept_hi, "swept_lo": swept_lo,
        "pct_pdh": pct(pdh), "pct_pdl": pct(pdl),
    }

# ── Confluence hints ────────────────────────────────────────────────────────────

def hints(r, wins):
    now_vn = wins["now_vn"]
    lines  = []

    # Killzone
    in_kz = (14 <= now_vn.hour < 17) or (19 <= now_vn.hour < 22)
    lines.append("✅ KILLZONE active" if in_kz else "⏸ Ngoài Killzone")

    # Sweep tín hiệu
    if r["swept_hi"]:
        lines.append(f"🔴 London quét Asia High ({r['asia_h']:,.2f}) → pha Manipulation SHORT")
        lines.append(f"   → A1 Judas Swing / A+2 PO3: Chờ FVG retest + Engulfing để entry Short")
    if r["swept_lo"]:
        lines.append(f"🟢 London quét Asia Low ({r['asia_l']:,.2f}) → pha Manipulation LONG")
        lines.append(f"   → A1 Judas Swing / A+2 PO3: Chờ FVG retest + Engulfing để entry Long")
    if not r["swept_hi"] and not r["swept_lo"]:
        if wins["london"]:
            lines.append("ℹ️ London chưa quét Asia range — theo dõi tiếp")
        else:
            lines.append("ℹ️ London chưa mở (14h VN) — chuẩn bị theo dõi sweep đầu phiên")

    # PDH/PDL
    if r["pct_pdh"] is not None:
        if abs(r["pct_pdh"]) < 0.3:
            lines.append(f"⚠️ Giá sát PDH {r['pdh']:,.2f} ({r['pct_pdh']:+.2f}%) — kháng cự, chú ý Rejection")
        elif r["pct_pdh"] > 0.3:
            lines.append(f"🚀 Giá vượt PDH {r['pdh']:,.2f} ({r['pct_pdh']:+.2f}%) — Breakout → xét B2 FTR retest")
    if r["pct_pdl"] is not None:
        if abs(r["pct_pdl"]) < 0.3:
            lines.append(f"⚠️ Giá sát PDL {r['pdl']:,.2f} ({r['pct_pdl']:+.2f}%) — hỗ trợ, chú ý Bounce")
        elif r["pct_pdl"] < -0.3:
            lines.append(f"📉 Giá phá PDL {r['pdl']:,.2f} ({r['pct_pdl']:+.2f}%) — Breakdown → xét B2 FTR retest")

    return lines

# ── Print ───────────────────────────────────────────────────────────────────────

SEP = "─" * 56

def fmt(v, fmt_str=","):
    return f"{v:{fmt_str}.2f}" if v is not None else "N/A"

def print_block(r, wins):
    print(f"┌─ {r['label']}  ${r['price']:,.2f} {SEP[len(r['label'])+16:]}")
    print(f"│  Asia (06–12h VN)  [{r['asia_bars']} bars]")
    print(f"│    High : {fmt(r['asia_h']):>14}")
    print(f"│    Low  : {fmt(r['asia_l']):>14}")
    if r["asia_h"] and r["asia_l"]:
        print(f"│    Range: {fmt(r['asia_h'] - r['asia_l']):>14}")
    print(f"│  Previous Day")
    print(f"│    PDH  : {fmt(r['pdh']):>14}")
    print(f"│    PDL  : {fmt(r['pdl']):>14}")
    if r["lon_h"] is not None:
        swept_h = "  ◀ SWEPT ASIA HIGH" if r["swept_hi"] else ""
        swept_l = "  ◀ SWEPT ASIA LOW"  if r["swept_lo"] else ""
        print(f"│  London (14–17h VN)")
        print(f"│    High : {fmt(r['lon_h']):>14}{swept_h}")
        print(f"│    Low  : {fmt(r['lon_l']):>14}{swept_l}")
    print("│")
    for h in hints(r, wins):
        print(f"│  {h}")
    print(f"└{SEP}")

# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    wins   = session_windows()
    now_vn = wins["now_vn"]
    print(f"\n📊 SESSION ANALYZER  {now_vn.strftime('%d/%m/%Y %H:%M')} GMT+7\n")

    btc_p = spot_price("BTCUSDT")
    eth_p = spot_price("ETHUSDT")

    btc = analyze("BTCUSDT", "BTC/USDT", btc_p, wins)
    eth = analyze("ETHUSDT", "ETH/USDT", eth_p, wins)

    print_block(btc, wins)
    print()
    print_block(eth, wins)
    print()

    # Cross-asset SMT
    print(f"┌─ A2 SYMMETRY SMT CHECK {SEP[24:]}")
    bh, bl = btc["swept_hi"], btc["swept_lo"]
    eh, el = eth["swept_hi"], eth["swept_lo"]

    if bh and not eh:
        print("│  ⚡ BTC quét Asia High — ETH KHÔNG quét → Divergence BEARISH")
        print("│     → A2 SMT: ưu tiên Short BTC tại POI H1")
    elif eh and not bh:
        print("│  ⚡ ETH quét Asia High — BTC KHÔNG quét → Divergence BEARISH")
        print("│     → A2 SMT: ưu tiên Short ETH tại POI H1")
    elif bl and not el:
        print("│  ⚡ BTC quét Asia Low — ETH KHÔNG quét → Divergence BULLISH")
        print("│     → A2 SMT: ưu tiên Long BTC tại POI H1")
    elif el and not bl:
        print("│  ⚡ ETH quét Asia Low — BTC KHÔNG quét → Divergence BULLISH")
        print("│     → A2 SMT: ưu tiên Long ETH tại POI H1")
    elif bh and eh:
        print("│  🔴 Cả BTC + ETH quét Asia High → Xác nhận bearish (A1 / A+2)")
    elif bl and el:
        print("│  🟢 Cả BTC + ETH quét Asia Low → Xác nhận bullish (A1 / A+2)")
    else:
        print("│  ⏸ Chưa có sweep — SMT chưa áp dụng được")
    print(f"└{SEP}\n")

if __name__ == "__main__":
    main()
