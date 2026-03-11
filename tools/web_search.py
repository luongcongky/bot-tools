import logging
from telegram import Update, constants
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
# Import bộ não từ file orchestration.py
from orchestration import AIOrchestrator

TOKEN = "8631041747:AAFWilc9E3TKYgLaIs4y_VprblEkj5A-mFM"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text: return

    # Hiệu ứng đang gõ
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=constants.ChatAction.TYPING)
    
    # Gửi qua Orchestration xử lý
    response = await AIOrchestrator.get_response(user_text)
    
    await update.message.reply_text(response)

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot Bridge đang chạy...")
    application.run_polling()

if __name__ == '__main__':
    main()
