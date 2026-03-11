import logging
from app.infrastructure.database.session import get_db_connection

logger = logging.getLogger("ChatHistoryRepository")

def get_chat_history(chat_id, limit=6):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content FROM chat_history 
            WHERE chat_id = %s 
            ORDER BY created_at DESC LIMIT %s
        """, (str(chat_id), limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    except Exception as e:
        logger.error(f"Lỗi lấy lịch sử: {e}")
        return []

def save_chat(chat_id, role, content):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO chat_history (chat_id, role, content) VALUES (%s, %s, %s)", 
                    (str(chat_id), role, content))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Lỗi lưu chat: {e}")
