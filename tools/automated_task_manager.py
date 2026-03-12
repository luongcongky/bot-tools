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

async def list_automated_tasks(chat_id="default", include_inactive=False, **kwargs):
    """
    Liệt kê các tác vụ tự động của người dùng.
    - Mặc định: chỉ liệt kê các tác vụ đang hoạt động (is_active=True).
    - include_inactive=True: liệt kê cả các tác vụ đang bị tạm dừng.
    """
    chat_id = str(chat_id)
    # Hỗ trợ AI truyền chuỗi "true"/"false" thay vì boolean
    if isinstance(include_inactive, str):
        include_inactive = include_inactive.lower() in ("true", "1", "yes")
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if include_inactive:
            # Lấy tất cả, bao gồm cả tạm dừng
            cur.execute("""
                SELECT id, task_description, schedule_expr, schedule_type, is_active 
                FROM automated_tasks 
                WHERE chat_id = %s::text
                ORDER BY is_active DESC, created_at DESC
            """, (chat_id,))
        else:
            # Chỉ lấy đang active
            cur.execute("""
                SELECT id, task_description, schedule_expr, schedule_type, is_active 
                FROM automated_tasks 
                WHERE chat_id = %s::text AND is_active = TRUE
                ORDER BY created_at DESC
            """, (chat_id,))
        
        rows = cur.fetchall()
        
        if not rows:
            if include_inactive:
                return "📋 Bạn hiện không có tác vụ tự động nào (kể cả đang tạm dừng)."
            return "📋 Bạn hiện không có tác vụ tự động nào đang hoạt động."
        
        status_label = "(bao gồm tạm dừng)" if include_inactive else "(đang hoạt động)"
        res = f"📋 **Danh sách tác vụ tự động của bạn** {status_label}:\n"
        for row in rows:
            task_id, desc, expr, s_type, is_active = row
            status_icon = "▶️" if is_active else "⏸️"
            res += f"- {status_icon} [ID: {task_id}] {desc} (Lịch: {expr})\n"
        
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
    Xóa vĩnh viễn một tác vụ tự động.
    """
    chat_id = str(chat_id)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM automated_tasks 
            WHERE id = %s AND chat_id = %s::text
            RETURNING task_description
        """, (task_id, chat_id))
        
        row = cur.fetchone()
        if not row:
            return f"❌ Không tìm thấy tác vụ với ID {task_id} để xóa."
            
        conn.commit()
        return f"🗑️ Đã xóa tác vụ: {row[0]}"

    except Exception as e:
        logger.error(f"Lỗi xóa tác vụ tự động: {e}")
        return f"❌ Lỗi khi xóa tác vụ: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()

async def disable_automated_task(task_description=None, task_id=None, chat_id="default", **kwargs):
    """
    Tạm dừng (deactivate) một tác vụ tự động theo tên hoặc ID mà không xóa.
    """
    chat_id = str(chat_id)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if task_id:
            # Vô hiệu hóa theo ID
            cur.execute("""
                UPDATE automated_tasks 
                SET is_active = FALSE 
                WHERE id = %s AND chat_id = %s::text
                RETURNING task_description
            """, (task_id, chat_id))
        elif task_description:
            # Tìm và vô hiệu hóa theo tên (fuzzy match)
            cur.execute("""
                UPDATE automated_tasks 
                SET is_active = FALSE 
                WHERE chat_id = %s::text 
                  AND is_active = TRUE
                  AND task_description ILIKE %s
                RETURNING id, task_description
            """, (chat_id, f"%{task_description}%"))
        else:
            return "❌ Vui lòng cung cấp ID hoặc tên tác vụ cần tạm dừng."
        
        rows = cur.fetchall()
        if not rows:
            return f"❌ Không tìm thấy tác vụ đang hoạt động phù hợp để tạm dừng."
            
        conn.commit()
        names = ", ".join(r[1] if len(r) == 2 else r[0] for r in rows)
        return f"⏸️ Đã tạm dừng thành công tác vụ: {names}"

    except Exception as e:
        logger.error(f"Lỗi tạm dừng tác vụ tự động: {e}")
        return f"❌ Lỗi khi tạm dừng tác vụ: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()

async def enable_automated_task(task_description=None, task_id=None, chat_id="default", **kwargs):
    """
    Kích hoạt lại một tác vụ tự động đã tạm dừng.
    """
    chat_id = str(chat_id)
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        if task_id:
            cur.execute("""
                UPDATE automated_tasks 
                SET is_active = TRUE 
                WHERE id = %s AND chat_id = %s::text
                RETURNING task_description
            """, (task_id, chat_id))
        elif task_description:
            cur.execute("""
                UPDATE automated_tasks 
                SET is_active = TRUE 
                WHERE chat_id = %s::text 
                  AND is_active = FALSE
                  AND task_description ILIKE %s
                RETURNING id, task_description
            """, (chat_id, f"%{task_description}%"))
        else:
            return "❌ Vui lòng cung cấp ID hoặc tên tác vụ cần kích hoạt lại."
        
        rows = cur.fetchall()
        if not rows:
            return f"❌ Không tìm thấy tác vụ đã tạm dừng phù hợp để kích hoạt lại."
            
        conn.commit()
        names = ", ".join(r[1] if len(r) == 2 else r[0] for r in rows)
        return f"▶️ Đã kích hoạt lại thành công tác vụ: {names}"

    except Exception as e:
        logger.error(f"Lỗi kích hoạt lại tác vụ: {e}")
        return f"❌ Lỗi khi kích hoạt lại tác vụ: {str(e)}"
    finally:
        if conn:
            cur.close()
            conn.close()
