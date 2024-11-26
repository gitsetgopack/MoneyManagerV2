from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes
import requests
from io import BytesIO

from config.config import TELEGRAM_BOT_API_BASE_URL

from config.config import MONGO_URI, TIME_ZONE
from bots.telegram.auth import authenticate
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
TIMEOUT = 10

@authenticate
async def analytics(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Main analytics command with plot options."""
    keyboard = [
        [InlineKeyboardButton("Expense Bar Chart", callback_data="plot_expense_bar")],
        [InlineKeyboardButton("Category Pie Chart", callback_data="plot_category_pie")],
        [InlineKeyboardButton("Monthly Expense Line Chart", callback_data="plot_expense_line_monthly")],
        [InlineKeyboardButton("Category Bar Chart", callback_data="plot_category_bar")],
        [InlineKeyboardButton("Budget vs Actual", callback_data="plot_budget_vs_actual")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📊 *Lets Analyse*\n\nChoose a plot type:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@authenticate
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Handle button clicks for different plots."""
    query = update.callback_query
    await query.answer()
    
    plot_endpoints = {
        "plot_expense_bar": "analytics/expense/bar",
        "plot_category_pie": "analytics/category/pie",
        "plot_expense_line_monthly": "analytics/expense/line-monthly",
        "plot_category_bar": "analytics/category/bar",
        "plot_budget_vs_actual": "analytics/budget/actual-vs-budget"
    }
    
    if query.data in plot_endpoints:
        try:
            headers = {"token": token}
            response = requests.get(
                f"{TELEGRAM_BOT_API_BASE_URL}/{plot_endpoints[query.data]}",
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                image_bytes = BytesIO(response.content)
                await query.message.reply_photo(photo=image_bytes)
            else:
                await query.message.reply_text(f"Failed to generate {query.data.replace('_', ' ')}")
        except Exception as e:
            await query.message.reply_text(f"Error: {str(e)}")

# Remove or comment out the old expense_bar function since it's now handled by the callback

analytics_handlers = [
    CommandHandler('analytics', analytics),
    CallbackQueryHandler(button_callback, pattern=r'^plot_'),
]
