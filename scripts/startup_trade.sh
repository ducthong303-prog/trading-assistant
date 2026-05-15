#!/bin/bash
# Chờ 15 giây để đảm bảo Wifi đã kết nối
sleep 15

# Xóa lockfile cũ (phòng trường hợp tắt máy đột ngột khi process đang chạy)
rm -f /Users/ttcenter/market_monitor.lock

# Chạy cập nhật dữ liệu ngay lập tức
/usr/bin/python3 /Users/ttcenter/trade_engine.py --silent
/usr/bin/python3 /Users/ttcenter/market_monitor.py
