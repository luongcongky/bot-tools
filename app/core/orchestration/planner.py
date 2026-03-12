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

async def generate_plan(user_input, chat_history=None):
    relevant_tools = get_relevant_tools(user_input, limit=8)
    
    TASK_KEYWORDS = ["tự động", "lịch trình", "nhắc", "tắt", "bật", "tạm dừng",
                     "khởi động", "dừng", "kích hoạt", "chương trình", "danh sách", "restart"]
    WEB_KEYWORDS = ["đọc", "link", "url", "trang web", "phân tích", "tóm tắt", "chương", "tiếp theo", "sau đây"]
    FILE_KEYWORDS = ["file", "tệp", "thư mục", "folder", "tìm", "mở", "liệt kê", "danh sách", "xem có", "máy tính", "ổ đĩa", "truy cập máy"]
    
    user_lower = user_input.lower()
    is_task_related = any(kw in user_lower for kw in TASK_KEYWORDS)
    is_web_related = any(kw in user_lower for kw in WEB_KEYWORDS) or "http" in user_lower
    is_file_related = any(kw in user_lower for kw in FILE_KEYWORDS)
    
    if is_task_related or is_web_related or is_file_related:
        FORCED_TOOLS = []
        if is_task_related:
            FORCED_TOOLS.extend(["list_automated_tasks", "register_automated_task",
                                 "disable_automated_task", "enable_automated_task", "remove_automated_task"])
        if is_web_related:
            FORCED_TOOLS.append("browse_website")
        if is_file_related:
            FORCED_TOOLS.extend(["search_files", "list_directory", "open_path", "create_directory", "write_file", "delete_file", "delete_directory"])
            
        existing_keys = {t["key"] for t in relevant_tools}
        conn = get_db_connection()
        cur = conn.cursor()
        for key in FORCED_TOOLS:
            if key not in existing_keys:
                cur.execute("SELECT intent_key, description FROM ai_intents WHERE intent_key = %s", (key,))
                row = cur.fetchone()
                if row:
                    relevant_tools.append({"key": row[0], "desc": row[1]})
        cur.close()
        conn.close()
    
    tools_str = "\n".join([f"- {t['key']}: {t['desc']}" for t in relevant_tools])
    
    import datetime
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_vnt = now_utc + datetime.timedelta(hours=7)
    current_time_str = now_vnt.strftime("%Y-%m-%d %H:%M:%S (%A) [Múi giờ: GMT+7]")
    
    # Xây dựng prompt Planner (System Instructions)
    planner_prompt = get_planner_prompt(tools_str, current_time_str)
    
    # Chỉ dẫn đặc biệt cho điều hướng web
    NAV_KEYWORDS = ["chương tiếp", "link tiếp", "trang sau", "next", "sau đây", "tiếp theo", "chương sau"]
    if any(kw in user_lower for kw in NAV_KEYWORDS):
        planner_prompt += "\n\nLƯU Ý: Người dùng đang yêu cầu điều hướng web. Bạn PHẢI tìm URL từ các link điều hướng trong tin nhắn của ASSISTANT ở lịch sử và thiết lập 'extract_links': True."

    # Chỉ dẫn đặc biệt cho File Management
    COMPUTER_KEYWORDS = ["máy tính", "ổ đĩa", "thư mục", "folder", "tìm file", "xóa file", "xóa folder", "xóa thư mục"]
    if any(kw in user_lower for kw in COMPUTER_KEYWORDS):
        planner_prompt += "\n\nLƯU Ý QUAN TRỌNG: Người dùng đang yêu cầu truy cập MÁY TÍNH CÁ NHÂN. Bạn PHẢI dùng các tool quản lý file chuyên biệt (`search_files`, `create_directory`, `write_file`, v.v.). TUYỆT ĐỐI KHÔNG dùng `browse_website` để tìm kiếm trên mạng trừ khi người dùng cung cấp link URL cụ thể."

    # KHỞI TẠO DANH SÁCH TIN NHẮN
    messages = [{"role": "system", "content": planner_prompt}]
    
    # 1. Thêm Lịch sử hội thoại (nếu có)
    if chat_history:
        for msg in chat_history[-5:]: # Chỉ lấy 5 tin nhắn gần nhất để tránh quá tải cho model nhỏ
            messages.append({"role": msg['role'], "content": msg['content']})

    # 2. Thêm Few-Shot Examples (luôn ở sau history để định hướng kết quả cuối cùng)
    messages.extend([
        {"role": "user", "content": "Tìm folder Bot_Data, nếu chưa có thì tạo mới"},
        {"role": "assistant", "content": json.dumps({"plan": [
            {"intent": "search_files", "params": {"query": "Bot_Data", "root_path": "."}},
            {"intent": "create_directory", "params": {"path": "Bot_Data"}}
        ]})},
        {"role": "user", "content": "Vào thư mục Bot_Data, tạo file test.txt nội dung 'abc' rồi mở nó lên"},
        {"role": "assistant", "content": json.dumps({"plan": [
            {"intent": "create_directory", "params": {"path": "Bot_Data"}},
            {"intent": "write_file", "params": {"path": "Bot_Data/test.txt", "content": "abc"}},
            {"intent": "open_path", "params": {"path": "Bot_Data/test.txt"}}
        ]})},
        {"role": "user", "content": "Xóa file note.txt và folder Temp"},
        {"role": "assistant", "content": json.dumps({"plan": [
            {"intent": "delete_file", "params": {"path": "note.txt"}},
            {"intent": "delete_directory", "params": {"path": "Temp"}}
        ]})}
    ])

    # 3. Tin nhắn thực tế của người dùng
    messages.append({"role": "user", "content": user_input})
    
    try:
        response_content = await get_llm_response(
            model='gemma2:2b', 
            messages=messages, 
            format='json',
            options={'temperature': 0}
        )
        plan_data = json.loads(clean_json_response(response_content))
        
        return plan_data
    except Exception as e:
        logger.error(f"Lỗi generate_plan: {e}")
        return {"plan": [], "message": "Xin lỗi anh, em gặp trục trặc khi lập kế hoạch."}
