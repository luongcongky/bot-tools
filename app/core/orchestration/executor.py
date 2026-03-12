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
        if isinstance(task, dict):
            logger.info(f"   {i+1}. {task.get('intent')} - {task.get('params')}")
        else:
            logger.info(f"   {i+1}. Invalid task format: {task}")
    
    for i, task in enumerate(plan):
        if not isinstance(task, dict):
            execution_results.append({"step": i + 1, "error": "Invalid task format"})
            continue
            
        intent = task.get("intent")
        params = task.get("params", {})
        
        logger.info(f"🚀 [BƯỚC {i+1}] Thực thi: {intent}...")
        result = await execute_tool(intent, params, user_input=user_input, chat_id=chat_id)
        display_result = str(result)
        if len(display_result) > 500:
            display_result = display_result[:500] + "..."
        logger.info(f"✅ [RAW OUTPUT]: {display_result}")
        
        # Trích xuất message/result an toàn
        output_text = "Xong"
        if isinstance(result, dict):
            output_text = result.get("result", result.get("message", str(result)))
        else:
            output_text = str(result)

        # Nếu output quá dài và có phần LINK ĐIỀU HƯỚNG, hãy ưu tiên phần đó cho Summarizer
        summarizer_output = output_text
        if len(summarizer_output) > 2000:
            nav_marker = "### 🔗 LINK ĐIỀU HƯỚNG"
            if nav_marker in summarizer_output:
                nav_part = summarizer_output[summarizer_output.find(nav_marker):]
                summarizer_output = summarizer_output[:1000] + "\n... (nội dung dài đã cắt) ...\n" + nav_part
            else:
                summarizer_output = summarizer_output[:2000] + "\n... (nội dung dài đã cắt) ..."

        execution_results.append({
            "step": i + 1,
            "intent": intent,
            "output": summarizer_output
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
