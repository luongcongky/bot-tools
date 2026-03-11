import asyncio
import sys
import os
import json

sys.path.append(os.getcwd())

from app.core.orchestration.planner import generate_plan

async def test_planner():
    user_inputs = [
        "Thực hiện đăng kí giờ làm việc ngay bây giờ giúp tôi",
        "Hãy tự động đăng kí giờ làm việc giúp tôi hằng ngày lúc 8h30 nhé"
    ]
    
    for ui in user_inputs:
        print(f"\n--- Testing User Input: {ui} ---")
        try:
            plan_data = await generate_plan(ui)
            print(f"Generated Plan: {json.dumps(plan_data, indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_planner())
