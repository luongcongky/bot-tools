import asyncio
import sys
import os
import datetime

# Add project root to sys.path
sys.path.append(os.getcwd())

from tools.google_calendar import create_event, get_events, delete_event

async def test_calendar():
    print("="*50)
    print("🚀 TESTING GOOGLE CALENDAR REAL API")
    print("="*50)
    
    # 1. Test Get Events (Hôm nay)
    print("\n[1/2] Testing get_events (Today)...")
    try:
        events = await get_events()
        print(f"Result:\n{events}")
    except Exception as e:
        print(f"❌ get_events failed: {e}")

    # 2. Test Create Event
    print("\n[2/2] Testing create_event...")
    try:
        title = f"Test Unit Bot - {datetime.datetime.now().strftime('%H:%M')}"
        start_time = (datetime.datetime.now() + datetime.timedelta(hours=2)).isoformat()
        result = await create_event(
            title=title,
            start_time=start_time,
            description="Đây là sự kiện được tạo tự động từ Unit Test"
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ create_event failed: {e}")

    # 3. Test Delete Event
    print("\n[3/3] Testing delete_event...")
    try:
        # Xóa sự kiện vừa tạo ở bước 2
        result = await delete_event(title=title)
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ delete_event failed: {e}")

    # 4. Test get_events with specific date
    print("\n[4/4] Testing get_events with specific date (2026-03-11)...")
    try:
        # Giả sử ngày mai là 2026-03-11
        result = await get_events(start_time="2026-03-11")
        print(f"Result:\n{result}")
    except Exception as e:
        print(f"❌ get_events (specific date) failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_calendar())
