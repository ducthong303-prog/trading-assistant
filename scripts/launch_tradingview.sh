#!/bin/bash
# launch_tradingview.sh — Mở TradingView trong Chromium với CDP enabled
# Dùng cho Auto Trading Mode (Claude MCP)

CHROMIUM="/Applications/Chromium.app/Contents/MacOS/Chromium"
CDP_PORT=9222
TV_URL="https://www.tradingview.com/chart/"
USER_DATA="$HOME/.tradingview_chromium_profile"

# Kill existing Chromium CDP session (nếu có)
pkill -f "Chromium.*remote-debugging-port" 2>/dev/null
sleep 1

# Launch Chromium với CDP + isolated profile (không ảnh hưởng browser khác)
"$CHROMIUM" \
  --remote-debugging-port=$CDP_PORT \
  --user-data-dir="$USER_DATA" \
  --no-first-run \
  --no-default-browser-check \
  --disable-background-networking \
  --disable-background-timer-throttling \
  "$TV_URL" \
  > /tmp/tv_chromium.log 2>&1 &

echo "🚀 Chromium đang khởi động... (PID: $!)"
echo "📊 URL: $TV_URL"
echo "🔌 CDP port: $CDP_PORT"
echo ""

# Đợi CDP sẵn sàng (tối đa 20s)
for i in $(seq 1 20); do
  sleep 1
  if curl -s "http://localhost:$CDP_PORT/json/version" >/dev/null 2>&1; then
    echo "✅ CDP sẵn sàng! Claude có thể kết nối TradingView ngay."
    exit 0
  fi
  echo -n "."
done

echo ""
echo "⚠️ CDP chưa phản hồi sau 20s."
echo "   Kiểm tra: curl http://localhost:$CDP_PORT/json/version"
echo "   Log: cat /tmp/tv_chromium.log"
exit 1
