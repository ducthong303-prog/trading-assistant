import urllib.request, json

def get_dxy_status():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            meta       = data["chart"]["result"][0]["meta"]
            price      = meta["regularMarketPrice"]
            prev_close = meta["chartPreviousClose"]
            change_pct = (price - prev_close) / prev_close * 100
            trend      = "BULLISH" if price > prev_close else "BEARISH"

            # Supply/Demand zone hint (simple: near 52w high/low)
            week52_high = meta.get("fiftyTwoWeekHigh", 0)
            week52_low  = meta.get("fiftyTwoWeekLow", 0)
            zone = ""
            if week52_high and price >= week52_high * 0.99:
                zone = " ⚠️ GẦN VÙNG SUPPLY (52w High)"
            elif week52_low and price <= week52_low * 1.01:
                zone = " ⚠️ GẦN VÙNG DEMAND (52w Low)"

            confluence = ""
            if trend == "BEARISH" and zone and "SUPPLY" in zone:
                confluence = " → +1 Confluence cho Long XAU/BTC"
            elif trend == "BULLISH" and zone and "DEMAND" in zone:
                confluence = " → +1 Confluence cho Short XAU/BTC"

            return f"DXY: {price:.3f} ({trend} {change_pct:+.2f}%){zone}{confluence}"
    except Exception as e:
        return f"DXY: Data Unavailable ({e})"

if __name__ == "__main__":
    print(get_dxy_status())
