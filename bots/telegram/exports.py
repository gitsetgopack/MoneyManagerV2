
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes, CommandHandler
import requests
from io import BytesIO

from config.config import TELEGRAM_BOT_API_BASE_URL
from bots.telegram.auth import authenticate


TIMEOUT = 10

@authenticate
async def exports(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Export command with format options."""
    keyboard = [
        [InlineKeyboardButton("PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("Excel", callback_data="export_xlsx")],
        [InlineKeyboardButton("CSV", callback_data="export_csv")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📊 *Export Data*\n\nChoose a format:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

@authenticate
async def export_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Handle export format selection."""
    query = update.callback_query
    await query.answer()
    
    data_parts = query.data.split('_')
    format_type = data_parts[1]
    
    if format_type == 'csv' and len(data_parts) == 2:
        keyboard = [
            [InlineKeyboardButton("Expenses", callback_data="export_csv_expenses")],
            [InlineKeyboardButton("Accounts", callback_data="export_csv_accounts")],
            [InlineKeyboardButton("Categories", callback_data="export_csv_categories")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.message.edit_text(
            "Select data to export:",
            reply_markup=reply_markup
        )
        return

    try:
        headers = {"token": token}
        
        if format_type == 'csv':
            export_type = data_parts[2]
            endpoint = f"exports/csv?export_type={export_type}"
            filename = f"{export_type}.csv"
        else:
            endpoint = f"exports/{format_type}"
            filename = "Ultimate Analytics.pdf" if format_type == 'pdf' else "All Data.xlsx"

        response = requests.get(
            f"{TELEGRAM_BOT_API_BASE_URL}/{endpoint}",
            headers=headers,
            timeout=TIMEOUT
        )

        if response.status_code == 200:
            file = BytesIO(response.content)
            file.name = filename
            await query.message.reply_document(document=file)
        else:
            await query.message.reply_text(f"Failed to generate export")
    except Exception as e:
        await query.message.reply_text(f"Error: {str(e)}")

exports_handlers = [
    CommandHandler('exports', exports),
    CallbackQueryHandler(export_callback, pattern=r'^export_')
]