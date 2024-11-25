"""Main module for the Telegram bot."""

import logging
import os
import sys

from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from bots.telegram.auth import login_handler, logout, signup_handler
from bots.telegram.expenses import (
    expenses_conv_handler,
    expenses_delete_all_conv_handler,
    expenses_delete_conv_handler,
    expenses_delete_page,
    expenses_view,
    expenses_view_page,
)
from bots.telegram.utils import unknown, get_menu_commands
from config import config
from bots.telegram.auth import get_user

# Add project root to Python path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(project_root)

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = await get_user(update=update)
    if user:
        username = user.get("username")
        await update.message.reply_text(f"Welcome back, {username}!\n\n{get_menu_commands()}")
    else:
        await update.message.reply_text("Welcome to Money Manager Telegram Bot!\nPlease /login or /signup to continue.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /menu command."""
    await update.message.reply_text(get_menu_commands())

def main() -> None:
    """Initialize and start the bot."""
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
    application.add_handler(
        CallbackQueryHandler(expenses_view_page, pattern="view_expenses#")
    )
    application.add_handler(
        CallbackQueryHandler(expenses_delete_page, pattern=r"^delete_expenses#\d+$")
    )
    application.add_handler(expenses_delete_all_conv_handler)
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("unknown", unknown))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
