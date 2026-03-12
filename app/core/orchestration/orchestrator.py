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
    
    # 2. Lấy lịch sử hội thoại gần đây (5 câu gần nhất)
    chat_history = get_chat_history(chat_id, limit=5)
    
    # 3. Generate Plan (Planner) kèm theo ngữ cảnh
    plan_data = await generate_plan(user_input, chat_history=chat_history)
    plan = plan_data.get("plan", [])
    
    if plan:
        # 4. Show plan summary in console
        # Đảm bảo mỗi task là một dict trước khi gọi .get
        intents = []
        for task in plan:
            if isinstance(task, dict):
                intents.append(task.get('intent'))
            else:
                intents.append(str(task))
        logger.info(f"📋 Bắt đầu thực thi kế hoạch: {intents}")
        
        # 5. Execute Plan (Executor)
        final_answer = await execute_plan(plan, user_input, chat_id=chat_id)
    else:
        # 5. Handle conversation
        final_answer = plan_data.get("message", "Em chưa hiểu ý anh. Hãy hỏi em theo 1 cách khác chi tiết hơn nhé.")

    # 6. Save response
    save_chat(chat_id, "assistant", final_answer)
    return final_answer
