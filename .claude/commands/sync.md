# /sync — Force Refresh Market Checkpoint

Run: `python3 /Users/ttcenter/trade_engine.py`

This forces a full re-fetch of BTC/ETH prices, H1 klines, DXY, and session levels,
then overwrites `market_state.json` with a fresh checkpoint.

**After running, report:**
- New `ts` timestamp
- `last_structure` (bullish/bearish)
- `key_levels` list (5 nearest price levels)
- Confluence Score + verdict
- Active setup (if any)

Use `/sync` whenever `/market` shows `[DATA DELAYED]` or before making an entry
decision after a period of inactivity.
