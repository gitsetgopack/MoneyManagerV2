import os
import sys
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler
from config import config
from utils import cancel

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# Import handlers from auth.py and expenses.py
from auth import login_handler, signup_handler, logout, authenticate
from expenses import (
    expenses_conv_handler, expenses_view, expenses_view_page,
    expenses_delete_conv_handler, expenses_delete_page,
    expenses_delete_all_conv_handler
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Money Manager Telergram Bot!\n\n"
    )

def main() -> None:
    # Get token directly from config
    token = config.TELEGRAM_BOT_TOKEN
    application = Application.builder().token(token).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(login_handler)
    application.add_handler(signup_handler)
    application.add_handler(expenses_conv_handler)
    application.add_handler(expenses_delete_conv_handler)
    application.add_handler(CommandHandler("expenses_view", expenses_view))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CallbackQueryHandler(expenses_view_page, pattern='view_expenses#'))
    application.add_handler(CallbackQueryHandler(expenses_delete_page, pattern=r'^delete_expenses#\d+$'))
    application.add_handler(expenses_delete_all_conv_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()