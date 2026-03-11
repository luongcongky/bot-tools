import json
import logging
import re
from app.core.ai.llm_client import get_llm_response
from app.core.ai.prompt_templates import get_planner_prompt
from app.infrastructure.database.session import get_db_connection
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("Planner")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_relevant_tools(user_query, limit=10):
    try:
        query_vector = embed_model.encode(user_query).tolist()
        conn = get_db_connection()
        cur = conn.cursor()
        search_query = """
            SELECT intent_key, description 
            FROM ai_intents 
            WHERE is_action = True 
            ORDER BY description_vector <=> %s::vector 
            LIMIT %s
        """
        cur.execute(search_query, (query_vector, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"key": r[0], "desc": r[1]} for r in rows]
    except Exception as e:
        logger.error(f"Lỗi Vector Search: {e}")
        return []

def clean_json_response(raw_response):
    match = re.search(r'\[.*\]|\{.*\}', raw_response, re.DOTALL)
    return match.group(0) if match else raw_response

async def generate_plan(user_input):
    relevant_tools = get_relevant_tools(user_input)
    tools_str = "\n".join([f"- {t['key']}: {t['desc']}" for t in relevant_tools])
    
    # Lấy thời gian thực tế theo múi giờ Việt Nam (UTC+7) để AI tính toán chính xác
    import datetime
    # Giả định server chạy UTC, ta cộng thêm 7 tiếng
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_vnt = now_utc + datetime.timedelta(hours=7)
    current_time_str = now_vnt.strftime("%Y-%m-%d %H:%M:%S (%A) [Múi giờ: GMT+7]")
    
    planner_prompt = get_planner_prompt(tools_str, current_time_str)
    messages = [{"role": "system", "content": planner_prompt}, {"role": "user", "content": user_input}]
    
    try:
        response_content = await get_llm_response(model='gemma2:2b', messages=messages, format='json')
        plan_data = json.loads(clean_json_response(response_content))
        
        # Log the plan clearly
        plan = plan_data.get("plan", [])
        if plan:
            logger.info(f"📋 KẾ HOẠCH ĐÃ LẬP: {len(plan)} bước.")
        else:
            logger.info("ℹ️ Không có kế hoạch công việc, chỉ là hội thoại thông thường.")
            
        return plan_data
    except Exception as e:
        logger.error(f"Lỗi generate_plan: {e}")
        return {"plan": [], "message": "Xin lỗi anh, em gặp trục trặc khi lập kế hoạch."}
