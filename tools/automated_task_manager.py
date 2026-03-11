import logging
import json
from app.infrastructure.database.session import get_db_connection

logger = logging.getLogger("AutomatedTaskManager")

async def register_automated_task(task_description, intent_key, schedule_type, schedule_expr, params=None, chat_id="default", **kwargs):
    """
    Đăng ký một tác vụ tự động mới vào cơ sở dữ liệu.
    """
    if not params:
        params = {}
    
    chat_id = str(chat_id)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO automated_tasks (chat_id, task_description, intent_key, params, schedule_type, schedule_expr)
            VALUES (%s::text, %s, %s, %s, %s, %s)
            RETURNING id
        """, (chat_id, task_description, intent_key, json.dumps(params), schedule_type, schedule_expr))
        
        task_id = cur.fetchone()[0]
        conn.commit()
        
        logger.info(f"✅ Đã đăng ký tác vụ tự động mới: ID={task_id}, Intent={intent_key}")
        return f"✅ Đã đăng ký tác vụ tự động thành công!\n- ID: {task_id}\n- Tác vụ: {task_description}\n- Lịch trình: {schedule_expr} ({schedule_type})"

    except Exception as e:
        logger.error(f"Lỗi đăng ký tác vụ tự động: {e}")
        return f"❌ Lỗi khi đăng ký tác vụ: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()

async def list_automated_tasks(chat_id="default", **kwargs):
    """
    Liệt kê các tác vụ tự động đang hoạt động của người dùng.
    """
    chat_id = str(chat_id)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, task_description, schedule_expr, schedule_type, is_active 
            FROM automated_tasks 
            WHERE chat_id = %s::text AND is_active = TRUE
            ORDER BY created_at DESC
        """, (chat_id,))
        
        rows = cur.fetchall()
        if not rows:
            return "📋 Bạn hiện không có tác vụ tự động nào đang hoạt động."
            
        res = "📋 **Danh sách tác vụ tự động của bạn:**\n"
        for row in rows:
            res += f"- [ID: {row[0]}] {row[1]} (Lịch: {row[2]})\n"
        
        return res

    except Exception as e:
        logger.error(f"Lỗi liệt kê tác vụ tự động: {e}")
        return f"❌ Lỗi khi lấy danh sách tác vụ: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()

async def remove_automated_task(task_id, chat_id="default", **kwargs):
    """
    Hủy đăng ký một tác vụ tự động.
    """
    chat_id = str(chat_id)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE automated_tasks 
            SET is_active = FALSE 
            WHERE id = %s AND chat_id = %s::text
            RETURNING task_description
        """, (task_id, chat_id))
        
        row = cur.fetchone()
        if not row:
            return f"❌ Không tìm thấy tác vụ với ID {task_id} để xóa."
            
        conn.commit()
        return f"🗑️ Đã hủy đăng ký tác vụ: {row[0]}"

    except Exception as e:
        logger.error(f"Lỗi xóa tác vụ tự động: {e}")
        return f"❌ Lỗi khi xóa tác vụ: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()
