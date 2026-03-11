import datetime
import logging
from app.infrastructure.notification.telegram_channel import TelegramChannel

logger = logging.getLogger("NotificationTool")

# Registry of available channels — add more here to extend
CHANNEL_REGISTRY = {
    "telegram": TelegramChannel,
}

def _format_message(message: str, title: str = None) -> str:
    """Format thông báo theo chuẩn hiển thị."""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    divider = "━━━━━━━━━━━━━━━━"

    lines = []
    if title:
        lines.append(f"⚠️ *{title}*")
        lines.append(divider)
    lines.append(message)
    lines.append(divider)
    lines.append(f"🕐 {now}")

    return "\n".join(lines)


async def send_notification(message: str, channel: str = "telegram", chat_id: str = None, title: str = None, **kwargs) -> str:
    """
    Gửi thông báo/cảnh báo đến kênh chỉ định.
    
    Params:
        message (str): Nội dung thông báo.
        channel (str): Kênh output ('telegram', 'slack', 'email'...). Mặc định: 'telegram'.
        chat_id (str): ID người/nhóm nhận. Nếu không có, lấy giá trị mặc định.
        title (str): Tiêu đề cảnh báo (tùy chọn).
    """
    if not message:
        return "❌ Nội dung thông báo không được để trống."

    channel_key = str(channel).lower().strip()
    if channel_key not in CHANNEL_REGISTRY:
        available = ", ".join(CHANNEL_REGISTRY.keys())
        return f"❌ Kênh '{channel}' không được hỗ trợ. Các kênh khả dụng: {available}"

    formatted_msg = _format_message(message, title=title)

    logger.info(f"📤 Gửi thông báo qua kênh [{channel_key}] tới [{chat_id}]")

    channel_cls = CHANNEL_REGISTRY[channel_key]
    channel_instance = channel_cls()
    result = await channel_instance.send(formatted_msg, chat_id=chat_id)
    return result
