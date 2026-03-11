import logging
import json
from app.services.tool_manager import execute_tool
from app.core.ai.llm_client import get_llm_response
from app.core.ai.prompt_templates import SUMMARIZER_SYSTEM_PROMPT, get_summary_prompt

logger = logging.getLogger("Executor")

async def execute_plan(plan, user_input, chat_id="default"):
    execution_results = []
    logger.info(f"📋 BẮT ĐẦU KẾ HOẠCH ({len(plan)} bước):")
    for i, task in enumerate(plan):
        logger.info(f"   {i+1}. {task.get('intent')} - {task.get('params')}")
    
    for i, task in enumerate(plan):
        intent = task.get("intent")
        params = task.get("params", {})
        
        logger.info(f"🚀 [BƯỚC {i+1}] Thực thi: {intent}...")
        result = await execute_tool(intent, params, user_input=user_input, chat_id=chat_id)
        logger.info(f"✅ [RAW OUTPUT]: {result}")
        
        execution_results.append({
            "step": i + 1,
            "intent": intent,
            "output": result.get("result", result.get("message", "Xong"))
        })

    summary_prompt = [
        {"role": "system", "content": SUMMARIZER_SYSTEM_PROMPT},
        {"role": "user", "content": get_summary_prompt(user_input, execution_results)}
    ]
    
    try:
        final_answer = await get_llm_response(model='gemma2:2b', messages=summary_prompt)
        return final_answer
    except Exception as e:
        logger.error(f"Lỗi execute_plan summary: {e}")
        return "Xin lỗi anh, em gặp trục trặc khi tổng hợp kết quả."
