import asyncio
import sys
import os

sys.path.append(os.getcwd())

from tools.automated_task_manager import register_automated_task, list_automated_tasks
from app.adapters.scheduler.scheduler_adapter import check_dynamic_tasks

async def test_dynamic_automation():
    print("==================================================")
    print("🚀 TESTING DYNAMIC AUTOMATION SYSTEM")
    print("==================================================")

    # 1. Đăng ký task giả lập: Nhắc nghỉ mắt mỗi 1 phút (để test nhanh)
    print("\n[1/3] Đăng ký task nhắc nghỉ mắt (interval 1p)...")
    reg_msg = await register_automated_task(
        task_description="Nhắc nghỉ mắt mỗi phút",
        intent_key="send_notification",
        schedule_type="interval",
        schedule_expr="1",
        params={"message": "👀 Đã đến lúc nghỉ mắt rồi anh ơi!", "title": "Sức khỏe"}
    )
    print(reg_msg)

    # 2. Liệt kê danh sách
    print("\n[2/3] Liệt kê danh sách task...")
    list_msg = await list_automated_tasks()
    print(list_msg)

    # 3. Chạy scheduler loop check (giả lập 1 lần quét)
    print("\n[3/3] Chạy quét dynamic tasks...")
    await check_dynamic_tasks()
    print("✅ Đã chạy quét scheduler. Hãy kiểm tra Telegram.")

if __name__ == "__main__":
    asyncio.run(test_dynamic_automation())
