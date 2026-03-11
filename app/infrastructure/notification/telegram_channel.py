import logging
from telegram import Bot
from telegram.request import HTTPXRequest
from app.infrastructure.notification.base_channel import BaseNotificationChannel

logger = logging.getLogger("TelegramChannel")

# Dùng lại token đã cấu hình trong adapter
TELEGRAM_TOKEN = "8631041747:AAFWilc9E3TKYgLaIs4y_VprblEkj5A-mFM"
DEFAULT_CHAT_ID = None  # Sẽ được cung cấp lúc gọi hàm


class TelegramChannel(BaseNotificationChannel):
    """Gửi thông báo qua Telegram Bot."""

    def __init__(self):
        t_request = HTTPXRequest(connect_timeout=15.0, read_timeout=30.0)
        self.bot = Bot(token=TELEGRAM_TOKEN, request=t_request)

    async def send(self, message: str, chat_id: str = None, **kwargs) -> str:
        if not chat_id:
            return "❌ Không thể gửi thông báo: thiếu chat_id (ID người nhận)."
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message
            )
            logger.info(f"📤 Đã gửi thông báo Telegram đến {chat_id}")
            return f"✅ Đã gửi thông báo thành công đến Telegram ({chat_id})."
        except Exception as e:
            logger.error(f"Lỗi gửi Telegram: {e}")
            return f"❌ Lỗi gửi Telegram: {str(e)}"
