import asyncio
import datetime
import logging
import json
import os
from app.services.tool_manager import execute_tool
from tools.notification import send_notification
from tools.google_calendar import get_raw_events
from app.infrastructure.database.session import get_db_connection

logger = logging.getLogger("SchedulerAdapter")

# Mặc định gửi thông báo đến chat_id này (chat_id của người dùng)
ADMIN_CHAT_ID = "8590020658"
NOTIFIED_ALERTS_FILE = "data/notified_alerts.json"

# Biến toàn cục để theo dõi task chạy ngầm
_SCHEDULER_TASK = None

def load_notified_alerts():
    """Tải danh sách các event_id đã được thông báo từ file."""
    if os.path.exists(NOTIFIED_ALERTS_FILE):
        try:
            with open(NOTIFIED_ALERTS_FILE, 'r') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_notified_alerts(notified_set):
    """Lưu danh sách event_id đã được thông báo xuống file."""
    os.makedirs("data", exist_ok=True)
    try:
        with open(NOTIFIED_ALERTS_FILE, 'w') as f:
            json.dump(list(notified_set), f)
    except Exception as e:
        logger.error(f"Lỗi lưu notified_alerts: {e}")

# Cache trong bộ nhớ
NOTIFIED_EVENTS = load_notified_alerts()

async def run_auto_punch():
    """Thực hiện tự động punch_task và báo cáo."""
    logger.info("⏰ [SCHEDULER] Bắt đầu tự động Punch-In...")
    
    try:
        # 1. Thực thi punch_task
        # Chúng ta giả định user/pass mặc định trong tool hoặc cấu hình môi trường
        result_punch = await execute_tool("punch_task", {}, chat_id=ADMIN_CHAT_ID)
        
        status = result_punch.get("status")
        msg = result_punch.get("result", result_punch.get("message", "Không có phản hồi"))
        
        # 2. Gửi thông báo kết quả
        if status == "success":
            icon = "✅"
            title = "Tự động Check-in Thành công"
        else:
            icon = "❌"
            title = "Tự động Check-in Thất bại"
            
        await send_notification(
            message=f"{icon} Hệ thống đã thực hiện check-in tự động.\nChi tiết: {msg}",
            channel="telegram",
            chat_id=ADMIN_CHAT_ID,
            title=title
        )
        logger.info(f"✅ [SCHEDULER] Đã hoàn thành và báo cáo: {title}")
        
    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Lỗi thực thi auto-punch: {e}")
        await send_notification(
            message=f"❌ Lỗi hệ thống khi tự động check-in: {str(e)}",
            channel="telegram",
            chat_id=ADMIN_CHAT_ID,
            title="Lỗi Scheduler"
        )

async def check_upcoming_meetings():
    """Quét Google Calendar và gửi cảnh báo trước 30 phút."""
    global NOTIFIED_EVENTS
    # logger.info("🔍 [SCHEDULER] Đang quét lịch hẹn sắp tới...")
    
    try:
        # 1. Quét lịch trong cửa sổ 40 phút tới
        now = datetime.datetime.now(datetime.timezone.utc)
        time_min = now.isoformat()
        time_max = (now + datetime.timedelta(minutes=40)).isoformat()
        
        events = await get_raw_events(time_min=time_min, time_max=time_max)
        
        for event in events:
            event_id = event.get('id')
            if event_id in NOTIFIED_EVENTS:
                continue
                
            summary = event.get('summary', 'Cuộc họp không tên')
            start_raw = event['start'].get('dateTime', event['start'].get('date'))
            
            # Parse thời gian bắt đầu
            # Google trả về: '2026-03-11T10:00:00+07:00'
            try:
                # Thay thế Z hoặc + Offset để parse đồng nhất nếu cần, 
                # nhưng fromisoformat xử lý tốt đa số trường hợp
                start_dt = datetime.datetime.fromisoformat(start_raw.replace('Z', '+00:00'))
            except Exception:
                continue
            
            # Tính khoảng thời gian còn lại (phút)
            diff = (start_dt - now).total_seconds() / 60
            
            # Nếu còn 25-35 phút (Target 30p)
            if 25 <= diff <= 35:
                # 2. Gửi thông báo
                logger.info(f"🔔 [SCHEDULER] Cảnh báo cuộc họp: {summary} (bắt đầu sau {int(diff)} phút)")
                
                msg = (
                    f"📅 **Nhắc nhở cuộc họp sắp tới**\n"
                    f"━━━━━━━━━━━━━━━━\n"
                    f"📌 **Sự kiện:** {summary}\n"
                    f"⏰ **Bắt đầu lúc:** {start_dt.astimezone(datetime.timezone(datetime.timedelta(hours=7))).strftime('%H:%M:%S')}\n"
                    f"⏳ **Còn lại:** {int(diff)} phút nữa.\n"
                    f"━━━━━━━━━━━━━━━━"
                )
                
                await send_notification(
                    message=msg,
                    channel="telegram",
                    chat_id=ADMIN_CHAT_ID,
                    title="Cảnh báo họp"
                )
                
                # 3. Đánh dấu đã notify
                NOTIFIED_EVENTS.add(event_id)
                save_notified_alerts(NOTIFIED_EVENTS)

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Lỗi check_upcoming_meetings: {e}")

async def check_dynamic_tasks():
    """Tải và kiểm tra các tác vụ tự động do người dùng đăng ký."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Lấy các task đang active
        cur.execute("""
            SELECT id, chat_id, task_description, intent_key, params, schedule_type, schedule_expr, last_run_at 
            FROM automated_tasks 
            WHERE is_active = TRUE
        """)
        tasks = cur.fetchall()
        
        now = datetime.datetime.now()
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        
        for task in tasks:
            task_id, chat_id, desc, intent, params_json, s_type, s_expr, last_run = task
            params = json.loads(params_json) if isinstance(params_json, str) else params_json
            
            should_run = False
            
            # --- LOGIC KIỂM TRA LỊCH TRÌNH ---
            if s_type == "cron":
                # Hỗ trợ đơn giản: HH:MM (chạy hàng ngày)
                if ":" in s_expr:
                    try:
                        target_h, target_m = map(int, s_expr.split(":"))
                        if now.hour == target_h and now.minute == target_m:
                            # Tránh chạy lại trong cùng 1 phút
                            if not last_run or (now_utc - last_run).total_seconds() > 120:
                                should_run = True
                    except ValueError:
                        pass
            
            elif s_type == "interval":
                # Hỗ trợ interval theo phút
                try:
                    interval_min = int(s_expr)
                    if not last_run or (now_utc - last_run).total_seconds() >= interval_min * 60:
                        should_run = True
                except ValueError:
                    pass
            
            # --- THỰC THI NẾU KHỚP ---
            if should_run:
                logger.info(f"⚡ [SCHEDULER] Thực thi động task {task_id}: {desc}")
                
                # 1. Chạy tool
                result = await execute_tool(intent, params, chat_id=chat_id)
                
                # 2. Update trạng thái lần chạy cuối
                cur.execute("UPDATE automated_tasks SET last_run_at = %s WHERE id = %s", (now_utc, task_id))
                conn.commit()
                
                # 3. Thông báo cho người dùng (tùy chọn theo task)
                # Đa số auto-task sẽ tự gửi notification bên trong tool (như punch_task)
                # Nếu không, ta có thể gửi bổ sung ở đây nếu cần.

    except Exception as e:
        logger.error(f"❌ [SCHEDULER] Lỗi check_dynamic_tasks: {e}")
    finally:
        if conn:
            cur.close()
            conn.close()

async def scheduler_loop():
    """Vòng lặp kiểm tra thời gian để thực hiện task."""
    logger.info("🚀 Scheduler Adapter started.")
    
    while True:
        now = datetime.datetime.now()
        
        # Task 1: Check Meetings (Mỗi 5 phút)
        if now.minute % 5 == 0:
            await check_upcoming_meetings()
            # Đợi 1s để tránh lặp trong cùng 1 phút (scheduler_loop tốn thời gian chạy)
            await asyncio.sleep(1) 
        
        # Task 2: Check Dynamic Tasks (Mỗi phút)
        # Các task tự động (bao gồm Punch-in) sẽ được nạp từ DB ở đây
        await check_dynamic_tasks()
        
        # Kiểm tra mỗi 60 giây (để đồng nhất với phút)
        await asyncio.sleep(60)

def start_scheduler():
    """Entry point để chạy scheduler trong event loop hiện tại."""
    global _SCHEDULER_TASK
    if _SCHEDULER_TASK is None or _SCHEDULER_TASK.done():
        _SCHEDULER_TASK = asyncio.create_task(scheduler_loop())
        logger.info("📅 [SCHEDULER] Task đã được khởi tạo.")

async def stop_scheduler():
    """Dừng scheduler một cách êm ái."""
    global _SCHEDULER_TASK
    if _SCHEDULER_TASK:
        # logger.info("🛑 Đang dừng Scheduler...")
        _SCHEDULER_TASK.cancel()
        try:
            await _SCHEDULER_TASK
        except asyncio.CancelledError:
            logger.info("🛑 Scheduler đã dừng thành công.")
        _SCHEDULER_TASK = None
