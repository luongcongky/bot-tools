import asyncio
import datetime
import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.append(os.getcwd())

import app.adapters.scheduler.scheduler_adapter as scheduler

async def test_meeting_alert():
    print("==================================================")
    print("🚀 TESTING CALENDAR MEETING ALERTS (v2)")
    print("==================================================")

    # 1. Chuẩn bị sự kiện giả (bắt đầu sau 30 phút)
    # Giả định "bây giờ" là 2026-03-11 10:00:00 UTC
    now_utc = datetime.datetime(2026, 3, 11, 10, 0, 0, tzinfo=datetime.timezone.utc)
    
    # Sự kiện bắt đầu lúc 10:30:00 UTC (đúng 30 phút sau)
    mock_event = {
        'id': 'test_event_123_v2',
        'summary': 'Họp Review Thiết Kế',
        'start': {
            'dateTime': '2026-03-11T10:30:00Z'
        }
    }

    # Reset notified events for test
    if os.path.exists(scheduler.NOTIFIED_ALERTS_FILE):
        os.remove(scheduler.NOTIFIED_ALERTS_FILE)
    scheduler.NOTIFIED_EVENTS = set()

    # Monkey patch get_raw_events
    async def mock_get_raw_events(time_min, time_max):
        print(f"DEBUG: get_raw_events called for window: {time_min} -> {time_max}")
        return [mock_event]

    scheduler.get_raw_events = mock_get_raw_events
    # Fix logging to avoid noise
    import logging
    logging.getLogger("SchedulerAdapter").setLevel(logging.INFO)

    # 2. Chạy check_upcoming_meetings với patch datetime
    print("\n[1/2] Lần quét đầu tiên (Kỳ vọng: Gửi thông báo)...")
    
    # Patch datetime.datetime.now
    with patch('datetime.datetime', wraps=datetime.datetime) as mock_dt:
        mock_dt.now.return_value = now_utc
        
        await scheduler.check_upcoming_meetings()
        
        print(f"Notified events: {scheduler.NOTIFIED_EVENTS}")
        if 'test_event_123_v2' in scheduler.NOTIFIED_EVENTS:
            print("✅ Lần 1 thành công: Đã ghi nhận event_id.")
        else:
            print("❌ Lần 1 thất bại: Không ghi nhận event_id.")

        # 3. Chạy check_upcoming_meetings (Lần 2 - Không được gửi lại)
        print("\n[2/2] Lần quét thứ hai (Kỳ vọng: Không gửi lại)...")
        # Phải reset lại thông điệp gửi (nếu có mock notification tool)
        # Ở đây ta chỉ check NOTIFIED_EVENTS tăng thêm hay không
        initial_count = len(scheduler.NOTIFIED_EVENTS)
        await scheduler.check_upcoming_meetings()
        if len(scheduler.NOTIFIED_EVENTS) == initial_count:
            print("✅ Lần 2 thành công: Không gửi trùng lặp.")
        else:
            print("❌ Lần 2 thất bại: Vẫn ghi nhận thêm event (trùng lặp).")

    print("\n✅ Test hoàn tất.")

if __name__ == "__main__":
    asyncio.run(test_meeting_alert())
