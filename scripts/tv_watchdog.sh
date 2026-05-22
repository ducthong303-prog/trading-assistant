#!/bin/bash
# tv_watchdog.sh — Giữ TradingView Chromium luôn chạy khi ở Auto Trading Mode
# Chạy bởi cron mỗi 5 phút (cùng với market_monitor.py)
#
# Logic:
#   - Nếu trading_mode.json = "auto" → đảm bảo CDP port 9222 luôn sẵn sàng
#   - Nếu mode = "monitor" → không làm gì (tiết kiệm tài nguyên)

TRADING_MODE_FILE="/Users/ttcenter/trading_mode.json"
LOG="/tmp/tv_watchdog.log"

# Đọc mode hiện tại
MODE=$(python3 -c "
import json, sys
try:
    d = json.load(open('$TRADING_MODE_FILE'))
    print(d.get('mode', 'monitor'))
except:
    print('monitor')
" 2>/dev/null)

if [ "$MODE" != "auto" ]; then
    exit 0
fi

# Kiểm tra CDP health
if curl -s --max-time 2 "http://localhost:9222/json/version" >/dev/null 2>&1; then
    # Kiểm tra có tab TradingView không
    TV_TABS=$(curl -s "http://localhost:9222/json" | python3 -c "
import json, sys
tabs = json.load(sys.stdin)
tv = [t for t in tabs if 'tradingview' in t.get('url','')]
print(len(tv))
" 2>/dev/null)
    if [ "${TV_TABS:-0}" -gt 0 ]; then
        exit 0  # TradingView đang chạy bình thường
    fi
fi

# CDP không sẵn sàng hoặc không có tab TV → relaunch
echo "$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG] TradingView không sẵn sàng — đang relaunch..." >> "$LOG"
bash /Users/ttcenter/launch_tradingview.sh >> "$LOG" 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') [WATCHDOG] Relaunch hoàn tất." >> "$LOG"
