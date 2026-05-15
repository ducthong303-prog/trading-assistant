#!/bin/bash
# restore_stable.sh — Khôi phục từ một stable backup
# Usage: ./restore_stable.sh              → dùng "latest"
#        ./restore_stable.sh backup_20260509_054016
#        ./restore_stable.sh list         → liệt kê tất cả backup

STABLE_DIR="/Users/ttcenter/stable_version"

# ── List mode ─────────────────────────────────────────────────────────────────
if [ "$1" = "list" ]; then
    echo "📁 Các bản backup hiện có:"
    for d in "${STABLE_DIR}"/backup_*; do
        [ -d "$d" ] || continue
        name=$(basename "$d")
        info=""
        [ -f "$d/BACKUP_INFO.txt" ] && info=$(grep "^Files" "$d/BACKUP_INFO.txt" | sed 's/Files.*: //')
        is_latest=""
        [ "$(readlink ${STABLE_DIR}/latest 2>/dev/null)" = "$d" ] && is_latest=" ← latest"
        echo "  ${name}  [${info}]${is_latest}"
    done
    exit 0
fi

# ── Resolve backup path ───────────────────────────────────────────────────────
if [ -z "$1" ]; then
    BACKUP="${STABLE_DIR}/latest"
elif [ -d "${STABLE_DIR}/$1" ]; then
    BACKUP="${STABLE_DIR}/$1"
elif [ -d "$1" ]; then
    BACKUP="$1"
else
    echo "❌ Không tìm thấy backup: $1"
    echo "   Dùng './restore_stable.sh list' để xem danh sách."
    exit 1
fi

# Resolve symlink
REAL_BACKUP=$(readlink -f "$BACKUP" 2>/dev/null || python3 -c "import os; print(os.path.realpath('$BACKUP'))")

if [ ! -d "$REAL_BACKUP" ]; then
    echo "❌ Backup path không hợp lệ: ${REAL_BACKUP}"
    exit 1
fi

# ── Xác nhận ──────────────────────────────────────────────────────────────────
echo ""
echo "🔄 Sắp khôi phục từ: $(basename ${REAL_BACKUP})"
[ -f "${REAL_BACKUP}/BACKUP_INFO.txt" ] && cat "${REAL_BACKUP}/BACKUP_INFO.txt" | grep -E "^(Timestamp|Files)"
echo ""
echo "⚠️  Hành động này sẽ GHI ĐÈ các file hiện tại. Tiếp tục? (y/N): "
read -r confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Hủy — không có gì thay đổi."
    exit 0
fi

echo ""
restored=0

# ── Restore .py, .md, .sh ─────────────────────────────────────────────────────
for f in "${REAL_BACKUP}"/*.py "${REAL_BACKUP}"/CLAUDE.md "${REAL_BACKUP}"/startup_trade.sh; do
    [ -f "$f" ] || continue
    dest="/Users/ttcenter/$(basename $f)"
    cp "$f" "$dest" && echo "  ✅ $(basename $f)" && ((restored++))
done

# ── Restore plist ─────────────────────────────────────────────────────────────
plist="${REAL_BACKUP}/com.user.trading_startup.plist"
if [ -f "$plist" ]; then
    cp "$plist" "/Users/ttcenter/Library/LaunchAgents/"
    echo "  ✅ com.user.trading_startup.plist"
    ((restored++))
fi

# ── Restore slash commands ────────────────────────────────────────────────────
if [ -d "${REAL_BACKUP}/commands" ]; then
    for cmd in "${REAL_BACKUP}/commands/"*.md; do
        [ -f "$cmd" ] || continue
        cp "$cmd" "/Users/ttcenter/.claude/commands/"
        echo "  ✅ commands/$(basename $cmd)"
        ((restored++))
    done
fi

echo ""
echo "✅ Khôi phục hoàn tất — ${restored} file từ $(basename ${REAL_BACKUP})"
echo ""
