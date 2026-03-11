import os
import datetime
import logging
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.transport.requests import Request

# Đường dẫn đến các file xác thực
CREDENTIALS_PATH = "app/infrastructure/google/credentials.json"
TOKEN_PATH = "app/infrastructure/google/token.json"

logger = logging.getLogger("GoogleCalendar")

def get_calendar_service():
    """Thiết lập kết nối với Google Calendar API."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, ['https://www.googleapis.com/auth/calendar'])
    
    # Nếu token hết hạn, hãy refresh nó
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            # Lưu lại token mới vào file
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
            logger.info("🔄 Đã tự động làm mới (refresh) Google Calendar Token.")
        except Exception as e:
            logger.error(f"Lỗi khi refresh token: {e}")
            creds = None

    if not creds or not creds.valid:
        # Nếu không có creds hoặc vẫn không hợp lệ sau khi refresh
        raise Exception("Google Calendar Token không hợp lệ hoặc đã hết hạn. Vui lòng kiểm tra file token.json.")

    service = build('calendar', 'v3', credentials=creds)
    return service

async def create_event(title, start_time, end_time=None, description="", location="", **kwargs):
    """Tạo sự kiện thực tế trên Google Calendar."""
    try:
        service = get_calendar_service()
        
        # Xử lý end_time mặc định (+1h)
        if not end_time:
            dt_start = datetime.datetime.fromisoformat(start_time.replace('Z', ''))
            dt_end = dt_start + datetime.timedelta(hours=1)
            end_time = dt_end.isoformat() + ('' if 'Z' in start_time else 'Z')

        event = {
            'summary': title,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time if 'T' in start_time else f"{start_time}T09:00:00Z",
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
            'end': {
                'dateTime': end_time if 'T' in end_time else f"{end_time}T10:00:00Z",
                'timeZone': 'Asia/Ho_Chi_Minh',
            },
        }

        event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Đã tạo sự kiện: '{event.get('summary')}' thành công!\n🔗 Link: {event.get('htmlLink')}"

    except Exception as e:
        logger.error(f"Lỗi Google Calendar (Create): {e}")
        return f"❌ Không thể tạo lịch: {str(e)}"

async def get_events(time_min=None, time_max=None, start_time=None, end_time=None, **kwargs):
    """
    Lấy danh sách sự kiện từ Google Calendar.
    - Ưu tiên start_time/end_time (nếu có) hoặc time_min/time_max.
    """
    try:
        service = get_calendar_service()
        
        # 1. Xác định khoảng thời gian
        # Ưu tiên các tham số từ AI truyền vào
        t_start = start_time or time_min
        t_end = end_time or time_max
        
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        
        if t_start:
            # Làm sạch dữ liệu từ AI
            t_start = str(t_start).strip()
            # Nếu chỉ truyền ngày (YYYY-MM-DD), bot nên tự hiểu là cả ngày đó
            if len(t_start) <= 10:
                t_min = f"{t_start}T00:00:00Z"
                if not t_end:
                    t_max = f"{t_start}T23:59:59Z"
                else:
                    t_end = str(t_end).strip()
                    t_max = t_end if 'T' in t_end else f"{t_end}T23:59:59Z"
            else:
                t_min = t_start
                if t_end:
                    t_max = str(t_end).strip()
                else:
                    try:
                        base_dt = datetime.datetime.fromisoformat(t_min.replace('Z', ''))
                        t_max = (base_dt + datetime.timedelta(days=1)).isoformat()
                    except Exception:
                        t_max = (now_dt + datetime.timedelta(days=1)).isoformat()
        else:
            # Mặc định lấy từ bây giờ đến 7 ngày tới
            t_min = now_dt.isoformat()
            t_max = (now_dt + datetime.timedelta(days=7)).isoformat()

        logger.info(f"🔎 [CALENDAR] Đang lấy lịch từ {t_min} đến {t_max}")

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=format_google_iso(t_min), 
            timeMax=format_google_iso(t_max),
            maxResults=20, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])

        if not events:
            return "📅 Không tìm thấy lịch hẹn nào trong khoảng thời gian này."

        res = f"📅 Danh sách sự kiện của bạn ({len(events)}): \n"
        for event in events:
            start_raw = event['start'].get('dateTime', event['start'].get('date'))
            start_pretty = pretty_format_time(start_raw)
            res += f"- {start_pretty}: {event['summary']}\n"
        
        return res

    except Exception as e:
        logger.error(f"Lỗi Google Calendar (List): {str(e)}")
        return f"❌ Không thể lấy danh sách lịch: {str(e)}"

async def get_raw_events(time_min=None, time_max=None):
    """
    Lấy danh sách sự kiện thô (dạng dict) từ Google Calendar.
    Dành cho các tác vụ tự động (scheduler).
    """
    try:
        service = get_calendar_service()
        
        # Mặc định lấy từ bây giờ đến 1 ngày tới nếu không truyền
        if not time_min:
            time_min = datetime.datetime.now(datetime.timezone.utc).isoformat()
        if not time_max:
            time_max = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()

        events_result = service.events().list(
            calendarId='primary', 
            timeMin=format_google_iso(time_min), 
            timeMax=format_google_iso(time_max),
            maxResults=50, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])
    except Exception as e:
        logger.error(f"Lỗi get_raw_events: {str(e)}")
        return []

def format_google_iso(dt_input):
    """
    Đảm bảo định dạng ISO 8601 hợp lệ cho Google API.
    Google API không thích việc trộn lẫn Offset (+07:00) và 'Z'.
    """
    if isinstance(dt_input, str):
        # AI có thể truyền '2026-03-11 09:42:10', cần đổi sang '2026-03-11T09:42:10'
        dt_input = dt_input.replace(' ', 'T')
        # Nếu có cả +07:00 và Z, ta ưu tiên xóa Z
        if '+' in dt_input and 'Z' in dt_input:
            dt_input = dt_input.replace('Z', '')
        return dt_input
    
    # Nếu là đối tượng datetime, trả về ISO có Z (UTC)
    return dt_input.isoformat() + 'Z'

def pretty_format_time(iso_str):
    """
    Chuyển đổi ISO 8601 sang định dạng dễ đọc: YYYY-MM-DD HH:mm:ss
    """
    if not iso_str:
        return "N/A"
    try:
        # Xử lý các định dạng ISO khác nhau (có hoặc không có offset/Z)
        clean_iso = iso_str.replace('Z', '')
        if '+' in clean_iso:
            clean_iso = clean_iso.split('+')[0]
        
        dt = datetime.datetime.fromisoformat(clean_iso)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_str # Fallback nếu lỗi parse

async def delete_event(title=None, start_time=None, **kwargs):
    """Xóa sự kiện trên Google Calendar với logic tìm kiếm linh hoạt."""
    try:
        service = get_calendar_service()
        
        # 1. Xác định khoảng thời gian tìm kiếm
        now_dt = datetime.datetime.now(datetime.timezone.utc)
        
        if start_time:
            # Làm sạch dữ liệu từ AI
            start_time = str(start_time).strip()
            try:
                if len(start_time) <= 10:
                    # Nếu chỉ có ngày, tìm trong cả ngày đó (00:00 -> 23:59)
                    t_min = f"{start_time}T00:00:00+07:00"
                    t_max = f"{start_time}T23:59:59+07:00"
                else:
                    # Nếu có giờ cụ thể, duy trì cửa sổ +/- 2 tiếng
                    target_dt = datetime.datetime.fromisoformat(start_time.replace('Z', ''))
                    if not target_dt.tzinfo:
                        target_dt = target_dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=7)))
                    t_min = (target_dt - datetime.timedelta(hours=2)).isoformat()
                    t_max = (target_dt + datetime.timedelta(hours=2)).isoformat()
            except Exception:
                t_min = now_dt.isoformat()
                t_max = (now_dt + datetime.timedelta(days=2)).isoformat()
        else:
            t_min = now_dt.isoformat()
            t_max = (now_dt + datetime.timedelta(days=7)).isoformat()

        logger.info(f"🔎 [CALENDAR] Tìm kiếm để xóa: '{title}' trong khoảng {t_min} -> {t_max}")

        events_result = service.events().list(
            calendarId='primary', timeMin=format_google_iso(t_min), timeMax=format_google_iso(t_max),
            singleEvents=True, orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"❓ Không tìm thấy lịch hẹn nào trong khoảng thời gian này để hủy."

        target_event = None
        if title:
            # Ưu tiên tìm khớp chính xác hoặc chứa từ khóa
            title_clean = title.lower().strip()
            # Bước 1: Khớp chính xác hoàn toàn
            for event in events:
                if title_clean == event.get('summary', '').lower().strip():
                    target_event = event
                    break
            
            # Bước 2: Tìm theo từ khóa nếu chưa thấy
            if not target_event:
                for event in events:
                    if title_clean in event.get('summary', '').lower():
                        target_event = event
                        break
        else:
            # Nếu không có tên, lấy sự kiện sắp tới nhất
            target_event = events[0]

        if not target_event:
            if title:
                # Không khớp tên - thử lấy event gần nhất trong cùng khung thời gian
                if events:
                    # Nếu chỉ có 1 event trong khoảng thời gian, xóa luôn
                    if len(events) == 1:
                        target_event = events[0]
                        logger.info(f"⚠️ Không khớp tiêu đề nhưng chỉ có 1 sự kiện trong khung giờ, sẽ xóa: '{target_event.get('summary')}'")
                    else:
                        # Nhiều events, không xóa bừa
                        event_names = ', '.join([f"'{e.get('summary', '?')}'"
                                                  for e in events])
                        return f"❓ Không tìm thấy lịch khớp tên '{title}'. Các lịch trong khung giờ: {event_names}. Hãy chỉ định đúng tên lịch nhé."
                else:
                    return f"❓ Không tìm thấy lịch hẹn nào trong khoảng thời gian này để hủy."
            else:
                target_event = events[0] if events else None

        if not target_event:
            return f"❓ Không tìm thấy lịch hẹn nào trong khoảng thời gian này để hủy."

        # 2. Tiến hành xóa
        service.events().delete(calendarId='primary', eventId=target_event['id']).execute()
        
        summary = target_event.get('summary', 'Không tên')
        event_time_raw = target_event['start'].get('dateTime', target_event['start'].get('date'))
        event_time_pretty = pretty_format_time(event_time_raw)
        
        return f"🗑️ Đã hủy thành công: '{summary}' (Lúc: {event_time_pretty})"

    except Exception as e:
        logger.error(f"Lỗi Google Calendar (Delete): {str(e)}")
        return f"❌ Lỗi hủy lịch: {str(e)}"
