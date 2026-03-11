import sys
import os
import asyncio
sys.path.append(os.getcwd())

from tools.notification import send_notification

# ⚠️ Thay YOUR_CHAT_ID bằng chat_id thực của bạn (số ID Telegram của bạn)
MY_CHAT_ID = "8590020658"  # Từ logs, đây là chat_id của người dùng

async def test_notification():
    print("==================================================")
    print("🚀 TESTING NOTIFICATION TOOL")
    print("==================================================")

    # Test 1: Thông báo cơ bản
    print("\n[1/3] Gửi thông báo cơ bản...")
    result = await send_notification(
        message="Đây là thông báo kiểm tra từ bot.",
        channel="telegram",
        chat_id=MY_CHAT_ID
    )
    print(f"Result: {result}")

    # Test 2: Thông báo có tiêu đề
    print("\n[2/3] Gửi thông báo có tiêu đề...")
    result = await send_notification(
        message="Cuộc họp định kỳ sẽ bắt đầu sau 15 phút. Hãy chuẩn bị!",
        channel="telegram",
        chat_id=MY_CHAT_ID,
        title="Nhắc nhở họp"
    )
    print(f"Result: {result}")

    # Test 3: Kênh không hợp lệ
    print("\n[3/3] Kiểm tra kênh không hợp lệ...")
    result = await send_notification(
        message="Test",
        channel="slack",  # chưa hỗ trợ
        chat_id=MY_CHAT_ID
    )
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_notification())
