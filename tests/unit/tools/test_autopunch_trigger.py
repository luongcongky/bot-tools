import asyncio
import datetime
import sys
import os

sys.path.append(os.getcwd())

from app.adapters.scheduler.scheduler_adapter import run_auto_punch

async def test_manual_trigger():
    print("==================================================")
    print("🚀 TESTING AUTO-PUNCH MANUAL TRIGGER")
    print("==================================================")
    
    # Giả lập việc chạy auto_punch ngay lập tức
    print("\n[1/1] Kích hoạt run_auto_punch()...")
    await run_auto_punch()
    print("\n✅ Test hoàn tất. Hãy kiểm tra logs và Telegram.")

if __name__ == "__main__":
    asyncio.run(test_manual_trigger())
