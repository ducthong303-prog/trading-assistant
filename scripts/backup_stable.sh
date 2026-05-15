#!/bin/bash
# backup_stable.sh — Tạo snapshot có timestamp của toàn bộ code cốt lõi
# Usage: ./backup_stable.sh [label]
# Example: ./backup_stable.sh "before_fvg_sniper"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LABEL="${1:+_$1}"
BACKUP_DIR="/Users/ttcenter/stable_version/backup_${TIMESTAMP}${LABEL}"

mkdir -p "${BACKUP_DIR}/commands"

# ── Core files ────────────────────────────────────────────────────────────────
CORE_FILES=(
    "/Users/ttcenter/trade_engine.py"
    "/Users/ttcenter/market_monitor.py"
    "/Users/ttcenter/tv_indicator_parser.py"
    "/Users/ttcenter/btc_watch_alert.py"
    "/Users/ttcenter/dxy_monitor.py"
    "/Users/ttcenter/session_analyzer.py"
    "/Users/ttcenter/CLAUDE.md"
    "/Users/ttcenter/startup_trade.sh"
    "/Users/ttcenter/launch_tradingview.sh"
    "/Users/ttcenter/trading_mode.json"
    "/Users/ttcenter/Library/LaunchAgents/com.user.trading_startup.plist"
)

count=0
missing=()
for f in "${CORE_FILES[@]}"; do
    if [ -f "$f" ]; then
        cp "$f" "${BACKUP_DIR}/"
        ((count++))
    else
        missing+=("$(basename $f)")
    fi
done

# ── Slash commands ────────────────────────────────────────────────────────────
cmd_count=0
if [ -d "/Users/ttcenter/.claude/commands" ]; then
    for cmd in /Users/ttcenter/.claude/commands/*.md; do
        [ -f "$cmd" ] && cp "$cmd" "${BACKUP_DIR}/commands/" && ((cmd_count++))
    done
fi

total=$((count + cmd_count))

# ── Symlink "latest" → bản vừa tạo ───────────────────────────────────────────
ln -sfn "${BACKUP_DIR}" "/Users/ttcenter/stable_version/latest"

# ── Metadata ──────────────────────────────────────────────────────────────────
cat > "${BACKUP_DIR}/BACKUP_INFO.txt" << EOF
Timestamp : ${TIMESTAMP}
Label     : ${1:-}
Files     : ${count} core + ${cmd_count} commands = ${total} total
Created by: backup_stable.sh
EOF

# ── Output ────────────────────────────────────────────────────────────────────
echo ""
echo "✅ Backup hoàn tất"
echo "   Vị trí : ${BACKUP_DIR}"
echo "   Files   : ${total} (${count} core + ${cmd_count} commands)"
[ ${#missing[@]} -gt 0 ] && echo "   Thiếu  : ${missing[*]}"
echo "   Latest  : /Users/ttcenter/stable_version/latest → $(basename ${BACKUP_DIR})"
echo ""
