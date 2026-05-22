#!/bin/bash
# patch_tv_cdp.sh — Áp dụng CDP patch vào TradingView Desktop
# Chạy trong Terminal (không phải Claude Code)

set -e

echo "=== TradingView CDP Patch ==="
echo ""

# Kiểm tra patched asar đã có chưa
if [ ! -f /tmp/app_patched.asar ]; then
  echo "❌ Không tìm thấy /tmp/app_patched.asar"
  echo "   Hãy báo Claude để tạo lại file này."
  exit 1
fi

# Kiểm tra kích thước file hợp lệ
SIZE=$(wc -c < /tmp/app_patched.asar)
if [ "$SIZE" -lt 50000000 ]; then
  echo "❌ File /tmp/app_patched.asar quá nhỏ ($SIZE bytes) — có vẻ bị lỗi"
  exit 1
fi
echo "✅ Patched asar: $(ls -lh /tmp/app_patched.asar | awk '{print $5}')"

# Backup gốc (vào ~/app.asar.bak đã có từ trước)
if [ ! -f ~/app.asar.bak ]; then
  echo "📦 Tạo backup..."
  cp /Applications/TradingView.app/Contents/Resources/app.asar ~/app.asar.bak
  echo "✅ Backup: ~/app.asar.bak"
else
  echo "✅ Backup đã có: ~/app.asar.bak"
fi

# Copy patched asar vào app
echo ""
echo "📋 Copy patched asar → TradingView.app..."
cp /tmp/app_patched.asar /Applications/TradingView.app/Contents/Resources/app.asar
echo "✅ Copy OK"

# Ad-hoc re-sign
echo ""
echo "🔏 Re-signing TradingView.app (ad-hoc)..."
codesign --force --deep --sign - "/Applications/TradingView.app" 2>&1
echo "✅ Re-sign OK"

# Remove quarantine
echo ""
echo "🔓 Remove quarantine..."
xattr -rd com.apple.quarantine "/Applications/TradingView.app" 2>/dev/null || true
echo "✅ Done"

echo ""
echo "=== Patch hoàn tất! ==="
echo ""
echo "Tiếp theo: Mở TradingView Desktop, đợi 10s, rồi chạy:"
echo "  curl http://localhost:9222/json/version"
echo ""
echo "Nếu thấy JSON có 'Browser' → CDP thành công ✅"
echo "Nếu thất bại → restore: cp ~/app.asar.bak /Applications/TradingView.app/Contents/Resources/app.asar"
