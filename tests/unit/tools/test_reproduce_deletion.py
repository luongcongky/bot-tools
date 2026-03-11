import sys
import os
import asyncio
import datetime

# Add root directory to sys.path
sys.path.append(os.getcwd())

from tools.google_calendar import delete_event, get_events, create_event

async def test_reproduce_deletion_issue():
    print("==================================================")
    print("🚀 REPRODUCING DELETION ISSUE (English vs Vietnamese)")
    print("==================================================")

    # 1. Create a Vietnamese event for tomorrow
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    title = "Đi bộ sáng mai"
    print(f"\n[1/3] Creating event: '{title}' on {tomorrow}...")
    create_res = await create_event(title=title, start_time=f"{tomorrow}T10:00:00")
    print(create_res)

    # 2. Try to delete with an English title (matching LLM hallucination)
    wrong_title = "Walk tomorrow morning"
    print(f"\n[2/3] Trying to delete using WRONG title: '{wrong_title}'...")
    delete_res = await delete_event(title=wrong_title, start_time=f"{tomorrow}T10:00:00")
    print(f"Result (Expected failure or logic check): {delete_res}")

    # 3. Try to delete with correct title (Verify connectivity)
    print(f"\n[3/3] Trying to delete using CORRECT title: '{title}'...")
    delete_res_correct = await delete_event(title=title, start_time=f"{tomorrow}T10:00:00")
    print(f"Result: {delete_res_correct}")

if __name__ == "__main__":
    asyncio.run(test_reproduce_deletion_issue())
