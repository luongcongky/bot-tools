import logging
import json
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from telegram.request import HTTPXRequest
from app.core.orchestration.orchestrator import process_request
from app.adapters.scheduler.scheduler_adapter import start_scheduler, stop_scheduler

logger = logging.getLogger("TelegramAdapter")

# --- CẤU HÌNH ---
# Trong thực tế, nên dùng environment variable
TELEGRAM_TOKEN = "8631041747:AAFWilc9E3TKYgLaIs4y_VprblEkj5A-mFM"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_text = update.message.text
    chat_id = update.message.chat_id

    logger.info("="*30)
    logger.info(f"📩 Nhận tin nhắn từ {chat_id}: {user_text}")
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response_text = await process_request(user_text, chat_id=chat_id)
        
        if not isinstance(response_text, str):
            try:
                response_text = json.dumps(response_text, indent=2, ensure_ascii=False)
            except:
                response_text = str(response_text)
        
        await update.message.reply_text(response_text)
        logger.info(f"✅ Đã phản hồi cho {chat_id} : {response_text}")
        
    except Exception as e:
        logger.error(f"❌ Lỗi xử lý tại Telegram Adapter: {e}")
        await update.message.reply_text(f"Có lỗi xảy ra: {str(e)}")

    logger.info("="*30 + "\n")

def run_bot():
    t_request = HTTPXRequest(
        connect_timeout=30.0, 
        read_timeout=90.0,
        write_timeout=30.0
    )

    async def post_init(application):
        # Khởi động scheduler ngay khi bot chuẩn bị chạy
        start_scheduler()
        # logger.info("📅 [BOT] Scheduler đã được kích hoạt trong post_init.")

    async def post_stop(application):
        # Dừng scheduler khi bot dừng
        await stop_scheduler()
        # logger.info("🛑 [BOT] Scheduler đã dừng.")

    application = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .request(t_request)
        .get_updates_request(t_request)
        .post_init(post_init)
        .post_stop(post_stop)
        .build()
    )
    
    text_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(text_handler)
    
    print("\n" + "="*50)
    print("🚀 TELEGRAM BOT & SCHEDULER ĐANG CHẠY")
    print("="*50 + "\n")
    
    application.run_polling()
