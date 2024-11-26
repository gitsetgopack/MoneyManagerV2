"""Category management handlers for the Telegram bot."""

import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram_bot_pagination import InlineKeyboardPaginator

from bots.telegram.auth import authenticate
from config.config import TELEGRAM_BOT_API_BASE_URL
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from bots.telegram.utils import cancel

# Constants
TIMEOUT = 10  # seconds

# States for category conversation
(
    CATEGORY_NAME,
    CONFIRM_DELETE,
    SELECT_CATEGORY,
    NEW_CATEGORY_NAME,
) = range(4)

@authenticate
async def categories_view(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """View the list of categories with pagination."""
    headers = {"token": token}
    response = requests.get(
        f"{TELEGRAM_BOT_API_BASE_URL}/categories/",
        headers=headers,
        timeout=TIMEOUT
    )

    if response.status_code == 200:
        categories_dict = response.json().get("categories", {})
        if not categories_dict:
            await update.message.reply_text("No categories found.")
            return

        # Sort categories by name
        sorted_categories = dict(sorted(categories_dict.items()))

        # Pagination setup
        page = int(context.args[0]) if context.args else 1
        items_per_page = 5
        total_pages = len(sorted_categories) // items_per_page + (1 if len(sorted_categories) % items_per_page else 0)
        paginator = InlineKeyboardPaginator(
            total_pages,
            current_page=page,
            data_pattern="view_categories#{page}"
        )

        # Get categories for current page
        categories_items = list(sorted_categories.items())
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = categories_items[start_idx:end_idx]

        # Format message
        message = "📁 *Your Categories:*\n\n"
        for category, details in page_items:
            message += (
                f"📌 *Category:* {category}\n"
                f"💰 *Monthly Budget:* {details['monthly_budget']}\n"
                "-------------------\n"
            )

        # Send or edit message with pagination
        if update.message:
            await update.message.reply_text(
                message,
                parse_mode="Markdown",
                reply_markup=paginator.markup
            )
        elif update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                parse_mode="Markdown",
                reply_markup=paginator.markup
            )
    else:
        error_message = "Failed to fetch categories."
        if update.message:
            await update.message.reply_text(error_message)
        elif update.callback_query:
            await update.callback_query.message.edit_text(error_message)

@authenticate
async def categories_view_page(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Handle pagination for viewing categories."""
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("#")[1])
    context.args = [page]
    await categories_view(update, context)

# Handlers for categories
categories_handlers = [
    CommandHandler("categories_view", categories_view),
    CallbackQueryHandler(categories_view_page, pattern="^view_categories#"),
]
