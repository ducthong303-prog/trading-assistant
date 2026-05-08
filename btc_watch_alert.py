#!/usr/bin/env python3
"""
btc_watch_alert.py — London Watch Alert (14:00–15:00 VN)
Phát hiện BTC sweep Asia Low / PDL + Engulfing / Wick Rejection
→ Báo cáo §7 SIGNAL OUTPUT FORMAT, phân loại A1 Judas Swing
"""
import urllib.request, json, datetime, time

TOKEN   = "8613005077:AAGLTh9Zp8hv4yTIr6TXNYr7jBZvgAXz2dg"
CHAT_ID = "7850734762"
TG_URL  = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# ── Levels từ session_analyzer lúc 12:27 VN ────────────────────────────────────
ASIA_LOW  = 79_181.48
ASIA_HIGH = 80_142.84
PDL       = 79_500.00
PDH       = 81_709.32

WATCH_START_H = 14
WATCH_END_H   = 15

# ── API ─────────────────────────────────────────────────────────────────────────

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())

def klines_m5(limit=10):
    data = fetch(f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit={limit}")
    return [{"o": float(k[1]), "h": float(k[2]), "l": float(k[3]),
             "c": float(k[4]), "v": float(k[5])} for k in data]

def spot():
    return float(fetch("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")["price"])

def send_tg(text):
    data = json.dumps({"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).encode()
    req  = urllib.request.Request(TG_URL, data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)

# ── Pattern detection ────────────────────────────────────────────────────────────

def engulfing_bullish(bars):
    """bars[-2]=last closed, bars[-3]=prev. Body >= 50% candle (§3A filter)."""
    if len(bars) < 3:
        return False
    p, c = bars[-3], bars[-2]
    total = c["h"] - c["l"]
    if total == 0:
        return False
    body  = c["c"] - c["o"]
    return (p["c"] < p["o"]        # prev bearish
            and c["c"] > p["o"]    # close above prev open
            and c["o"] < p["c"]    # open below prev close
            and c["c"] > c["o"]    # current bullish
            and body / total >= 0.5)

def wick_rejection_bullish(bars):
    """§3B: lower wick ≥ 50% total candle + close in top 30%."""
    if len(bars) < 2:
        return False
    c = bars[-2]
    total = c["h"] - c["l"]
    if total == 0:
        return False
    lower_wick = min(c["o"], c["c"]) - c["l"]
    close_pct  = (c["c"] - c["l"]) / total
    return lower_wick / total >= 0.5 and close_pct >= 0.70

def swept_and_closed_above(bars, level):
    """Last closed bar dipped below level but closed back above."""
    if len(bars) < 2:
        return False
    c = bars[-2]
    return c["l"] < level and c["c"] > level

# ── DXY quick check ─────────────────────────────────────────────────────────────

def dxy_check():
    try:
        url  = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d"
        meta = fetch(url)["chart"]["result"][0]["meta"]
        p    = meta["regularMarketPrice"]
        prev = meta["chartPreviousClose"]
        w52h = meta.get("fiftyTwoWeekHigh", 0)
        bearish    = p < prev
        at_supply  = bool(w52h and p >= w52h * 0.99)
        score = 1 if (bearish and at_supply) else 0
        label = f"DXY {p:.3f} {'BEARISH' if bearish else 'BULLISH'}"
        if score:
            label += " tại Supply → +1 Long XAU/BTC"
        return score, label
    except Exception as e:
        return 0, f"DXY N/A ({e})"

# ── §7 Signal Output Format ──────────────────────────────────────────────────────

def build_signal(price, trigger, swept_lvl, dxy_score, dxy_label, now_vn):
    in_kz = 14 <= now_vn.hour < 17

    # Confluence scoring
    htf_score  = 1   # D1 test PDL → bearish context, sweep = reversal signal
    kz_score   = 1 if in_kz else 0
    vol_score  = 1   # sweep bar inherently high volume
    sweep_score = 1
    total = htf_score + kz_score + vol_score + sweep_score + dxy_score

    entry = price
    sl    = swept_lvl - 55       # dưới điểm sweep + 55$ buffer
    tp1   = ASIA_HIGH            # TP1 = Asia High (đỉnh đối diện A1 Judas)
    rr    = round((tp1 - entry) / (entry - sl), 1) if entry > sl else 0

    if total >= 4:
        action = "⚡ Vào lệnh ngay"
    elif total == 3:
        action = "👀 Đặt Limit / Đợi xác nhận"
    else:
        action = "🚫 Đứng ngoài (score thấp)"

    msg = [
        "🚨 <b>WATCH ALERT — LONDON SWEEP DETECTED</b>",
        "",
        f"<b>Phân loại :</b>  A1 — Judas Swing",
        f"<b>Trạng thái:</b>  Reversal → LONG",
        "",
        f"<b>Confluence Score: {total}/5</b>",
        f"  (+{htf_score}) HTF Bias        ✅ D1 test vùng PDL/Asia Low",
        f"  (+{kz_score}) Killzone        {'✅ London 14–17h active' if in_kz else '❌ Ngoài KZ'}",
        f"  (+{vol_score}) Volume          ✅ Sweep bar (vol cao ngầm định)",
        f"  (+{sweep_score}) Liquidity Sweep ✅ Quét {'PDL' if swept_lvl >= PDL else 'Asia Low'}"
        f" {swept_lvl:,.0f} → closed back",
        f"  (+{dxy_score}) DXY Correlation {'✅' if dxy_score else '❌'} {dxy_label}",
        "",
        f"<b>Trigger:</b> {trigger}",
        f"<b>Hành động:</b> {action}",
        "",
        "<b>Chi tiết entry:</b>",
        f"  Entry : ${entry:,.1f}",
        f"  SL    : ${sl:,.1f}  (dưới sweep {swept_lvl:,.0f})",
        f"  TP    : ${tp1:,.1f}  (Asia High — đỉnh đối diện Judas Swing)",
        f"  RR    : {rr}:1",
        f"  Size  : 1% tài khoản (A1 standard)",
    ]

    if total <= 2:
        msg += ["", "⚠️ <b>Thị trường chưa sẵn sàng.</b> Score ≤ 2 — không vào lệnh."]

    return "\n".join(msg)

# ── Main loop ────────────────────────────────────────────────────────────────────

def main():
    now_vn = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    print(f"🔍 Watch Alert BTC A1 — khởi động {now_vn.strftime('%H:%M')} GMT+7")
    print(f"   Mức theo dõi : Asia Low {ASIA_LOW:,.0f}  |  PDL {PDL:,.0f}")
    print(f"   Cửa sổ      : {WATCH_START_H:02d}:00–{WATCH_END_H:02d}:00 VN (London)\n")

    # Chờ đến giờ mở cửa sổ
    if now_vn.hour < WATCH_START_H:
        wait_s = (WATCH_START_H - now_vn.hour) * 3600 - now_vn.minute * 60 - now_vn.second
        print(f"⏳ Còn {wait_s // 60} phút đến {WATCH_START_H:02d}:00 VN — đang chờ...\n")
        time.sleep(max(0, wait_s))

    alerted = False
    poll_no = 0

    while True:
        now_vn = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

        if now_vn.hour >= WATCH_END_H:
            print(f"\n⏹  {WATCH_END_H:02d}:00 VN — Đóng cửa sổ. "
                  f"{'Alert đã gửi.' if alerted else 'Không có tín hiệu trong khung giờ này.'}")
            break

        if alerted:
            print("✅ Alert đã gửi thành công. Kết thúc.")
            break

        poll_no += 1
        try:
            bars  = klines_m5(limit=12)
            price = spot()
            tag   = now_vn.strftime("%H:%M")

            sw_pdl  = swept_and_closed_above(bars, PDL)
            sw_alow = swept_and_closed_above(bars, ASIA_LOW)

            status = []
            if sw_pdl:  status.append("PDL SWEPT")
            if sw_alow: status.append("ASIA_LOW SWEPT")
            status_str = " | ".join(status) if status else "no sweep yet"
            print(f"[{tag}] #{poll_no:02d}  BTC ${price:,.1f}  {status_str}")

            swept_lvl = None
            if sw_alow:
                swept_lvl = ASIA_LOW
            elif sw_pdl:
                swept_lvl = PDL

            if swept_lvl:
                eng  = engulfing_bullish(bars)
                wick = wick_rejection_bullish(bars)
                trigger = None
                if eng:
                    trigger = "🕯 Bullish Engulfing M5 (body ≥ 50%)"
                elif wick:
                    trigger = "📌 Wick Rejection §3B (lower wick ≥ 50%, close top 30%)"

                if trigger:
                    dxy_score, dxy_label = dxy_check()
                    msg = build_signal(price, trigger, swept_lvl, dxy_score, dxy_label, now_vn)
                    send_tg(msg)
                    print(f"\n{'='*60}")
                    print(msg)
                    print(f"{'='*60}\n")
                    alerted = True
                else:
                    print(f"   ⚠️  Swept {swept_lvl:,.0f} — chờ Engulfing / Wick Rejection")

        except Exception as e:
            print(f"   [ERR] {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
