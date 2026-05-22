#!/usr/bin/env python3
"""
Wyckoff Spring Detector — Phase C→D Pattern Recognition
========================================================
Phát hiện và chấm điểm pattern Wyckoff Spring từ dữ liệu OHLCV.
So sánh với dữ liệu lịch sử để đánh giá chất lượng pattern.

Usage:
  # Từ JSON OHLCV (pipe từ Claude MCP)
  echo '{"pair":"XAUUSD","bars":[...]}' | python3 wyckoff_spring_detector.py

  # Từ file
  python3 wyckoff_spring_detector.py --file ohlcv.json

  # Với giá hiện tại và SL/TP suggestion
  python3 wyckoff_spring_detector.py --file ohlcv.json --price 4685 --suggest-entry

Output: JSON phase analysis + comparison + recommendations
"""

import json
import sys
import os
import argparse
from statistics import mean, stdev
from typing import Optional

REFERENCE_FILE = os.path.join(os.path.dirname(__file__), "wyckoff_spring_reference.json")

# ── Scoring thresholds ──────────────────────────────────────────────
SC_VOL_MULTIPLIER = 2.0       # SC vol phải > avg × 2.0
NO_SUPPLY_MAX_RATIO = 0.80    # ST vol / SC vol < 80% = No Supply
ST_MIN_DISTANCE = 1.0         # ST low phải cách SC ít nhất 1 pt
BOS_FAKE_VOL_RATIO = 1.2      # BOS vol < base_avg_vol × 1.2 = fake
ABSORPTION_MAX_RANGE_PCT = 0.3 # Range / avg_range < 30% = absorption
LPS_MIN_HIGHER_LOWS = 2       # Cần ít nhất 2 higher low để xác nhận LPS

def load_reference():
    """Load historical Wyckoff Spring reference data."""
    try:
        with open(REFERENCE_FILE) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"patterns": [], "detection_params": {}}

def calc_sma(values, period):
    """Simple Moving Average."""
    if len(values) < period:
        return sum(values) / len(values) if values else 0
    return sum(values[-period:]) / period

def detect_sc(bars, avg_vol):
    """
    Detect Selling Climax.
    Returns: (index, score, details) or (None, 0, {})

    SC là nến có:
    - Volume cao nhất trong lookback (≥ avg × multiplier)
    - Spread rộng (bearish)
    - Có lower wick (close > low → SM hấp thụ)
    """
    best_score = 0
    best_idx = None
    best_details = {}

    for i, bar in enumerate(bars):
        vol = bar.get("volume", 0)
        if vol < avg_vol * SC_VOL_MULTIPLIER:
            continue

        o, h, l, c = bar["open"], bar["high"], bar["low"], bar["close"]
        spread = h - l
        body = abs(c - o)
        lower_wick = min(o, c) - l
        avg_spread = calc_sma([abs(b["high"] - b["low"]) for b in bars[:i] + bars[i+1:]], 20) or spread

        score = 0
        # Volume significance (0-3)
        vol_ratio = vol / avg_vol if avg_vol > 0 else 0
        if vol_ratio >= 4:      score += 3
        elif vol_ratio >= 3:    score += 2
        elif vol_ratio >= 2:    score += 1

        # Spread (0-2)
        spread_ratio = spread / avg_spread if avg_spread > 0 else 1
        if spread_ratio >= 2:   score += 2
        elif spread_ratio >= 1.5: score += 1

        # Wick quality (0-2) — lower wick shows absorption
        if spread > 0:
            wick_pct = lower_wick / spread
            if wick_pct >= 0.4:     score += 2
            elif wick_pct >= 0.2:   score += 1

        # Bearish bias (close < open for SC)
        if c < o:
            score += 1

        if score > best_score:
            best_score = score
            best_idx = i
            best_details = {
                "bar_index": i,
                "price": l,
                "close": c,
                "volume": vol,
                "vol_ratio": round(vol_ratio, 1),
                "spread_ratio": round(spread_ratio, 1),
                "wick_pct": round(lower_wick / spread * 100, 1) if spread > 0 else 0,
                "score": score,
                "max_score": 8
            }

    # Also consider: lowest low in window
    if best_idx is not None:
        # Check if it's near the lowest low
        sc_low = bars[best_idx]["low"]
        all_lows = [b["low"] for b in bars]
        if sc_low > min(all_lows):
            best_details["note"] = "Không phải đáy thấp nhất — có thể không phải SC thật"

    return best_idx, best_score, best_details

def detect_ar(bars, sc_idx, sc_low):
    """
    Detect Automatic Rally after SC.
    AR = FIRST significant rally after SC — not necessarily the highest high.
    Strategy: find the first bar with significant bullish range (>10 pts above SC low),
    then use the high of that initial rally cluster (next 3 bars after first signal).
    Returns: (ar_high_idx, ar_high, details)
    """
    if sc_idx is None or sc_idx >= len(bars) - 1:
        return None, 0, {}

    remaining = bars[sc_idx + 1:]
    if not remaining:
        return None, 0, {}

    # Step 1: Find the FIRST bar that shows significant rally (>10 pts above SC low)
    first_rally_idx = None
    for i, bar in enumerate(remaining):
        if bar["high"] - sc_low > 10:
            first_rally_idx = i
            break

    if first_rally_idx is None:
        # No significant rally found — use max of first 5 bars as fallback
        lookahead = min(5, len(remaining))
        first_rally_idx = max(range(lookahead), key=lambda i: remaining[i]["high"])

    # Step 2: AR high = highest point within 4 bars of the first rally
    cluster_start = first_rally_idx
    cluster_end = min(first_rally_idx + 5, len(remaining))
    cluster = remaining[cluster_start:cluster_end]

    ar_high = max(b["high"] for b in cluster)
    # Find index of AR high within the full bars list
    for j, b in enumerate(cluster):
        if b["high"] == ar_high:
            ar_idx = sc_idx + 1 + cluster_start + j
            break
    else:
        ar_idx = sc_idx + 1 + cluster_start

    ar_range = ar_high - sc_low
    ar_vol = bars[ar_idx]["volume"]

    note = "AR range " + ("tốt" if ar_range > 15 else "yếu — cần theo dõi")
    note += f" | first rally tại bar +{first_rally_idx + 1}"

    return ar_idx, ar_high, {
        "bar_index": ar_idx,
        "high": ar_high,
        "range_pts": round(ar_range, 2),
        "volume": ar_vol,
        "first_rally_offset": first_rally_idx + 1,
        "note": note
    }

def detect_st(bars, sc_idx, sc_low, sc_vol, ar_idx, ar_high):
    """
    Detect Secondary Tests (ST1, ST2).
    Returns: list of ST events with No Supply scoring.
    """
    if ar_idx is None:
        return []

    st_events = []
    # Scan between AR and current for ST lows
    start = ar_idx + 1
    remaining = bars[start:]

    if len(remaining) < 3:
        return []

    # Find significant lows (pullbacks toward SC)
    for i, bar in enumerate(remaining):
        idx = start + i
        low = bar["low"]
        vol = bar["volume"]

        # ST must be in the lower half of SC→AR range
        ar_range = ar_high - sc_low
        midpoint = sc_low + ar_range * 0.5
        if low > midpoint:
            continue

        # Must be above SC
        if low <= sc_low:
            continue

        # No Supply check
        no_supply_ratio = vol / sc_vol if sc_vol > 0 else 1
        no_supply = no_supply_ratio < NO_SUPPLY_MAX_RATIO

        distance_from_sc = low - sc_low

        st_events.append({
            "bar_index": idx,
            "low": low,
            "volume": vol,
            "distance_from_sc": round(distance_from_sc, 2),
            "no_supply_ratio": round(no_supply_ratio, 2),
            "no_supply": no_supply,
            "quality": "GOOD" if no_supply and distance_from_sc > ST_MIN_DISTANCE else "WEAK"
        })

    # Classify: deepest test = ST2 (Spring)
    if len(st_events) >= 2:
        # ST1 = first test, ST2 = deepest test (or last test near SC)
        st_events.sort(key=lambda x: x["low"])
        st_events[0]["type"] = "ST2 (Spring — deepest)"
        if len(st_events) > 1:
            st_events[1]["type"] = "ST1 (initial test)"
    elif len(st_events) == 1:
        st_events[0]["type"] = "ST (only one test detected)"

    return st_events

def detect_lps(bars, st2_low, sc_low):
    """
    Detect Last Point of Support sequence after ST2.
    Returns: LPS analysis with higher low sequence.
    """
    if st2_low is None:
        return {"detected": False, "sequence": [], "quality": "NONE"}

    # Find bars after ST2
    st2_bars = [i for i, b in enumerate(bars) if b["low"] == st2_low]
    if not st2_bars:
        return {"detected": False, "sequence": [], "quality": "NONE"}

    st2_idx = st2_bars[-1]
    after_st2 = bars[st2_idx + 1:]

    if len(after_st2) < 2:
        return {"detected": False, "sequence": [], "quality": "NONE"}

    # Track higher lows
    higher_lows = []
    last_low = st2_low
    vols = []

    for bar in after_st2:
        low = bar["low"]
        if low > last_low:
            higher_lows.append({
                "price": low,
                "volume": bar["volume"],
                "time": bar.get("time", "?")
            })
            vols.append(bar["volume"])
            last_low = low

    # Also track the min volume for No Supply identification
    min_vol = min(vols) if vols else 0

    quality = "NONE"
    if len(higher_lows) >= 3:
        # Check volume pattern: decreasing on dips, increasing on rises = healthy
        vol_increasing = vols[-1] > vols[0] if len(vols) >= 2 else False
        if vol_increasing:
            quality = "STRONG"
        else:
            quality = "FORMING"
    elif len(higher_lows) >= LPS_MIN_HIGHER_LOWS:
        quality = "FORMING"

    return {
        "detected": len(higher_lows) >= LPS_MIN_HIGHER_LOWS,
        "sequence": higher_lows,
        "count": len(higher_lows),
        "min_volume": min_vol,
        "min_volume_note": "No Supply" if min_vol < 1500 else "Volume bình thường",
        "quality": quality
    }

def detect_absorption(bars, recent_idx, avg_vol):
    """
    Detect absorption base near current price.
    Returns absorption analysis.
    """
    # Look at last 5 bars for absorption pattern
    start = max(0, recent_idx - 5)
    recent = bars[start:recent_idx + 1]

    if len(recent) < 3:
        return {"detected": False}

    # Absorption = high vol + narrow range
    high_vol_narrow = []
    for bar in recent:
        vol = bar["volume"]
        spread = bar["high"] - bar["low"]
        avg_spread = calc_sma([abs(b["high"] - b["low"]) for b in bars], 20)

        if vol > avg_vol * 1.2 and spread < avg_spread * ABSORPTION_MAX_RANGE_PCT:
            high_vol_narrow.append({
                "bar_time": bar.get("time", "?"),
                "volume": vol,
                "spread": round(spread, 2),
                "open": bar["open"],
                "close": bar["close"]
            })

    return {
        "detected": len(high_vol_narrow) >= 2,
        "bars": high_vol_narrow,
        "count": len(high_vol_narrow),
        "note": "Absorption base — SM đang hấp thụ" if len(high_vol_narrow) >= 2 else "Chưa đủ absorption"
    }

def predict_bos(bars, ar_high, lps_data, absorption):
    """
    Predict BOS quality based on current conditions.
    """
    if ar_high is None:
        return {"status": "UNKNOWN", "advice": "Chưa xác định được AR high"}

    current_price = bars[-1]["close"]
    distance_to_ar = ar_high - current_price

    # Check if we have the ingredients for real BOS
    has_lps = lps_data.get("detected", False)
    has_absorption = absorption.get("detected", False)

    if has_lps and has_absorption:
        bos_quality = "HIGH — LPS + Absorption = BOS thật tiềm năng"
        advice = "Nếu phá AR high với vol > avg × 1.2 → BOS THẬT. Dời SL về BE."
    elif has_lps:
        bos_quality = "MEDIUM — có LPS nhưng thiếu absorption"
        advice = "Đợi absorption base trước BOS. BOS đầu có thể là FAKE."
    else:
        bos_quality = "LOW — thiếu cả LPS và absorption"
        advice = "BOS sắp tới có thể là FAKE. Giữ SL, không vội."

    return {
        "ar_high": ar_high,
        "current_price": current_price,
        "distance_to_ar": round(distance_to_ar, 2),
        "has_lps": has_lps,
        "has_absorption": has_absorption,
        "quality": bos_quality,
        "advice": advice
    }

def compare_historical(current_phases, reference):
    """Compare current pattern with historical references."""
    comparisons = []

    for hist in reference.get("patterns", []):
        hp = hist["phases"]
        match_score = 0
        details = []

        # Compare No Supply ratio
        if "st2" in current_phases and "st2" in hp:
            current_ns = current_phases["st2"].get("no_supply_ratio", 1)
            hist_ns = hp["st2"].get("no_supply_ratio", 1)

            if current_ns < hist_ns:
                match_score += 2
                details.append(f"No Supply tốt HƠN historical ({current_ns:.0%} vs {hist_ns:.0%})")
            elif current_ns < 0.8:
                match_score += 1
                details.append(f"No Supply tương đương ({current_ns:.0%} vs {hist_ns:.0%})")
            else:
                details.append(f"No Supply YẾU hơn ({current_ns:.0%} vs {hist_ns:.0%})")

        # Compare SC volume significance
        if "sc" in current_phases and "sc" in hp:
            cur_vol = current_phases["sc"].get("volume", 0)
            hist_vol = hp["sc"].get("volume", 0)
            if cur_vol >= hist_vol * 1.5:
                match_score += 1
                details.append(f"SC vol mạnh hơn ({cur_vol} vs {hist_vol})")

        # Compare ST distance from SC
        if "st2" in current_phases and "st2" in hp:
            cur_dist = current_phases["st2"].get("distance_from_sc", 0)
            hist_dist = hp["st2"].get("distance_from_sc", 0)
            if cur_dist > hist_dist:
                match_score += 1
                details.append(f"ST2 an toàn hơn ({cur_dist:.1f} vs {hist_dist:.1f} pts)")

        verdict = "STRONGER" if match_score >= 3 else "SIMILAR" if match_score >= 1 else "WEAKER"

        comparisons.append({
            "reference_id": hist["id"],
            "reference_date": hist["date"],
            "reference_outcome": hist["outcome"],
            "match_score": match_score,
            "verdict": verdict,
            "details": details
        })

    return comparisons

def suggest_entry(current_phases, bars, current_price=None):
    """
    Suggest entry/SL/TP based on detected phases.
    """
    if current_price is None:
        current_price = bars[-1]["close"]

    sc = current_phases.get("sc", {})
    st2 = current_phases.get("st2", {})
    ar = current_phases.get("ar", {})

    sc_low = sc.get("price", 0)
    st2_low = st2.get("low", 0)
    ar_high = ar.get("high", 0)

    if not sc_low or not ar_high:
        return {"ready": False, "reason": "Chưa đủ phase SC + AR"}

    # Entry zones based on Fibonacci of SC→AR range
    fib_range = ar_high - sc_low
    fib_50 = sc_low + fib_range * 0.5
    fib_62 = sc_low + fib_range * 0.618
    fib_79 = sc_low + fib_range * 0.79

    # Entry: 50% Fib (optimal) or current if already there
    entry_zone_low = round(fib_62, 2)
    entry_zone_high = round(fib_50, 2)

    # SL: Below ST2 low or below 79% Fib
    sl_candidate = min(st2_low - 2, fib_79 - 1) if st2_low else fib_79 - 1
    sl = round(sl_candidate, 2)

    # TP: AR high first, then measured move
    tp1 = ar_high
    tp2 = round(ar_high + fib_range * 0.618, 2)  # Extension

    # RR
    risk = abs(current_price - sl) if current_price > sl else 5
    reward_tp1 = abs(tp1 - current_price)
    rr = round(reward_tp1 / risk, 1) if risk > 0 else 0

    # Determine if current price is in entry zone
    # entry zone = fib 50% to fib 62% (reversed for Fib: 50% is higher price)
    zone_bottom = round(min(fib_50, fib_62), 2)
    zone_top = round(max(fib_50, fib_62) + 2, 2)
    in_zone = zone_bottom <= current_price <= zone_top

    return {
        "ready": True,
        "current_price": current_price,
        "fib_range": round(fib_range, 2),
        "entry_zone": f"{zone_bottom} – {zone_top}",
        "fib_50": fib_50,
        "fib_62": fib_62,
        "fib_79": fib_79,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "risk_pts": round(risk, 2),
        "reward_tp1_pts": round(reward_tp1, 2),
        "rr": rr,
        "in_entry_zone": in_zone,
        "status": "IN ZONE" if in_zone else "ABOVE" if current_price > zone_top else "BELOW"
    }

def run_detector(bars, pair="XAUUSD", current_price=None, suggest=False):
    """
    Main detector pipeline.
    """
    if current_price is None:
        current_price = bars[-1]["close"]

    # Phase storage
    phases = {}
    warnings = []
    signals = []

    # Calculate baseline
    volumes = [b["volume"] for b in bars]
    avg_vol = sum(volumes) / len(volumes) if volumes else 0
    spreads = [abs(b["high"] - b["low"]) for b in bars]
    avg_spread = sum(spreads) / len(spreads) if spreads else 0

    # ── Step 1: Detect SC ──
    sc_idx, sc_score, sc_details = detect_sc(bars, avg_vol)
    if sc_idx is not None:
        phases["sc"] = sc_details
        if sc_score >= 5:
            signals.append(f"✅ SC detected at {sc_details['price']} (score {sc_score}/{sc_details['max_score']})")
        else:
            warnings.append(f"⚠️ SC yếu (score {sc_score}/{sc_details['max_score']})")
    else:
        warnings.append("❌ Không phát hiện SC rõ ràng — có thể không phải Spring")
        phases["sc"] = {"detected": False}

    # ── Step 2: Detect AR ──
    if sc_idx is not None:
        sc_low = bars[sc_idx]["low"]
        ar_idx, ar_high, ar_details = detect_ar(bars, sc_idx, sc_low)
        if ar_idx is not None:
            phases["ar"] = ar_details
            signals.append(f"✅ AR detected at {ar_high} (+{ar_details['range_pts']} pts)")
        else:
            warnings.append("⚠️ Chưa thấy AR rõ — đang trong quá trình?")
            phases["ar"] = {"detected": False}
    else:
        phases["ar"] = {"detected": False}

    # ── Step 3: Detect ST (Secondary Tests) ──
    if sc_idx is not None and phases["ar"].get("detected", True):
        sc_low = bars[sc_idx]["low"]
        sc_vol = bars[sc_idx]["volume"]
        ar_high_val = phases["ar"].get("high", 0)
        ar_idx_val = phases["ar"].get("bar_index", sc_idx + 1)

        st_events = detect_st(bars, sc_idx, sc_low, sc_vol, ar_idx_val, ar_high_val)

        if st_events:
            phases["st_events"] = st_events
            # Find ST2 (deepest)
            st2_candidates = [s for s in st_events if "ST2" in s.get("type", "")]
            if st2_candidates:
                phases["st2"] = st2_candidates[0]
                ns = st2_candidates[0]["no_supply_ratio"]
                if st2_candidates[0]["no_supply"]:
                    signals.append(f"✅ ST2 No Supply confirmed (ratio {ns:.0%} < {NO_SUPPLY_MAX_RATIO:.0%})")
                else:
                    warnings.append(f"⚠️ ST2 vol cao ({ns:.0%}) — không phải No Supply rõ")

            st1_candidates = [s for s in st_events if "ST1" in s.get("type", "")]
            if st1_candidates:
                phases["st1"] = st1_candidates[0]
        else:
            phases["st_events"] = []
            phases["st2"] = {"detected": False}

    # ── Step 4: Detect LPS ──
    st2_low = phases.get("st2", {}).get("low")
    sc_low_val = phases.get("sc", {}).get("price", 0)
    lps_data = detect_lps(bars, st2_low, sc_low_val)
    phases["lps"] = lps_data

    if lps_data["quality"] == "STRONG":
        signals.append(f"✅ LPS STRONG — {lps_data['count']} higher lows, vol tăng dần")
    elif lps_data["quality"] == "FORMING":
        signals.append(f"🔄 LPS đang hình thành — {lps_data['count']} higher lows")
    elif lps_data["detected"]:
        signals.append(f"⚠️ LPS yếu — cần theo dõi thêm")

    # ── Step 5: Detect Absorption ──
    absorption = detect_absorption(bars, len(bars) - 1, avg_vol)
    phases["absorption"] = absorption
    if absorption["detected"]:
        signals.append(f"✅ Absorption base {absorption['count']} bar — SM đang hấp thụ")

    # ── Step 6: Predict BOS ──
    ar_high_val = phases.get("ar", {}).get("high", 0)
    bos_prediction = predict_bos(bars, ar_high_val, lps_data, absorption)
    phases["bos_prediction"] = bos_prediction

    # ── Step 7: Historical comparison ──
    reference = load_reference()
    comparisons = compare_historical(phases, reference)

    # ── Step 8: Entry suggestion ──
    entry_suggestion = None
    if suggest:
        entry_suggestion = suggest_entry(phases, bars, current_price)

    # ── Determine overall confidence ──
    confidence = 0
    max_confidence = 7

    if phases.get("sc", {}).get("score", 0) >= 5:
        confidence += 1
    if phases.get("ar", {}).get("range_pts", 0) > 15:
        confidence += 1
    if phases.get("st2", {}).get("no_supply", False):
        confidence += 1
    if phases.get("st2", {}).get("no_supply_ratio", 1) < 0.6:
        confidence += 1  # Extra point for very strong No Supply
    if lps_data["quality"] in ("STRONG", "FORMING"):
        confidence += 1
    if absorption["detected"]:
        confidence += 1
    if comparisons and comparisons[0]["verdict"] == "STRONGER":
        confidence += 1

    verdict = "STAND ASIDE"
    if confidence >= 5:
        verdict = "HIGH CONVICTION — Entry được"
    elif confidence >= 3:
        verdict = "ACTIONABLE — Cần xác nhận thêm"
    elif confidence >= 2:
        verdict = "WEAK — Đợi thêm tín hiệu"

    # ── Build output ──
    result = {
        "pair": pair,
        "current_price": current_price,
        "timestamp_bars": len(bars),
        "confidence": confidence,
        "max_confidence": max_confidence,
        "verdict": verdict,
        "phases": phases,
        "signals": signals,
        "warnings": warnings,
        "avg_volume": round(avg_vol, 1),
        "avg_spread": round(avg_spread, 2),
        "historical_comparison": comparisons,
        "entry_suggestion": entry_suggestion
    }

    return result

def format_output(result):
    """Format results as readable text (falls back to JSON for programmatic use)."""
    print("=" * 60)
    print(f"  WYCKOFF SPRING DETECTOR — {result['pair']} @ {result['current_price']}")
    print("=" * 60)
    print(f"  Verdict: {result['verdict']}")
    print(f"  Confidence: {result['confidence']}/{result['max_confidence']}")
    print()

    for s in result.get("signals", []):
        print(f"  {s}")
    for w in result.get("warnings", []):
        print(f"  {w}")

    if result.get("entry_suggestion"):
        es = result["entry_suggestion"]
        print()
        print(f"  ── ENTRY PLAN ──")
        print(f"  Entry Zone: {es.get('entry_zone', 'N/A')}")
        print(f"  SL:         {es.get('sl', 'N/A')}")
        print(f"  TP1:        {es.get('tp1', 'N/A')}")
        print(f"  TP2:        {es.get('tp2', 'N/A')}")
        print(f"  RR:         {es.get('rr', 'N/A')}:1")
        print(f"  Status:     {es.get('status', 'N/A')}")

    if result.get("historical_comparison"):
        print()
        print(f"  ── SO SÁNH LỊCH SỬ ──")
        for hc in result["historical_comparison"]:
            print(f"  {hc['reference_id']} ({hc['reference_date']}): {hc['verdict']}")
            for d in hc.get("details", []):
                print(f"    • {d}")

    print()
    print(f"  ── RAW JSON ──")
    print(json.dumps(result, indent=2, default=str))

def main():
    parser = argparse.ArgumentParser(description="Wyckoff Spring Detector")
    parser.add_argument("--file", help="JSON file with OHLCV bars")
    parser.add_argument("--price", type=float, help="Current price override")
    parser.add_argument("--suggest-entry", action="store_true", help="Generate entry/SL/TP suggestion")
    parser.add_argument("--json-only", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    # Read input
    if args.file:
        with open(args.file) as f:
            data = json.load(f)
        pair = data.get("pair", "XAUUSD")
        bars = data.get("bars", data.get("data", []))
    elif not sys.stdin.isatty():
        data = json.load(sys.stdin)
        pair = data.get("pair", "XAUUSD")
        bars = data.get("bars", data.get("data", []))
    else:
        print("Usage: echo '{\"bars\":[...]}' | python3 wyckoff_spring_detector.py", file=sys.stderr)
        print("   or: python3 wyckoff_spring_detector.py --file ohlcv.json", file=sys.stderr)
        sys.exit(1)

    if not bars:
        print("❌ No OHLCV bars provided", file=sys.stderr)
        sys.exit(1)

    # Run detector
    result = run_detector(
        bars=bars,
        pair=pair,
        current_price=args.price,
        suggest=args.suggest_entry
    )

    if args.json_only:
        print(json.dumps(result, indent=2, default=str))
    else:
        format_output(result)

if __name__ == "__main__":
    main()
