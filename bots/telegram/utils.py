"""Utility functions for the Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current conversation and clear user data.

    Args:
        update: Update from Telegram
        context: CallbackContext for this update

    Returns:
        ConversationHandler.END to end the conversation
    """
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END
