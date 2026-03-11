import logging
from app.infrastructure.repositories.chat_history import get_chat_history, save_chat
from app.core.orchestration.planner import generate_plan
from app.core.orchestration.executor import execute_plan

logger = logging.getLogger("Orchestrator")

async def process_request(user_input, chat_id="default"):
    """
    Main Orchestration Logic
    """
    # 1. Save user input
    save_chat(chat_id, "user", user_input)
    
    # 2. Generate Plan (Planner)
    plan_data = await generate_plan(user_input)
    plan = plan_data.get("plan", [])
    
    if plan:
        # 4. Show plan summary in console
        logger.info(f"📋 Bắt đầu thực thi kế hoạch: {[task.get('intent') for task in plan]}")
        
        # 5. Execute Plan (Executor)
        final_answer = await execute_plan(plan, user_input, chat_id=chat_id)
    else:
        # 5. Handle conversation
        final_answer = plan_data.get("message", "Em chưa hiểu ý anh. Hãy hỏi em theo 1 cách khác chi tiết hơn nhé.")

    # 6. Save response
    save_chat(chat_id, "assistant", final_answer)
    return final_answer
