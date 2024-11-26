from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes, CommandHandler
import requests
from io import BytesIO
import smtplib
from email.message import EmailMessage

from config.config import TELEGRAM_BOT_API_BASE_URL
from bots.telegram.auth import authenticate
from config.config import GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT, GMAIL_SMTP_USERNAME, GMAIL_SMTP_PASSWORD


TIMEOUT = 10

@authenticate
async def exports(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Export command with format options."""
    keyboard = [
        [InlineKeyboardButton("PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("Excel", callback_data="export_xlsx")],
        [InlineKeyboardButton("CSV", callback_data="export_csv")],
        [InlineKeyboardButton("Email All", callback_data="export_email_all")],
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
    elif format_type == 'email_all':
        # Handle emailing all documents
        try:
            headers = {"token": token}
            exports = {}
            export_types = ['pdf', 'xlsx', 'csv_expenses', 'csv_accounts', 'csv_categories']
            for export_type in export_types:
                if export_type.startswith('csv'):
                    _, subtype = export_type.split('_')
                    endpoint = f"exports/csv?export_type={subtype}"
                    filename = f"{subtype}.csv"
                else:
                    endpoint = f"exports/{export_type}"
                    filename = "Ultimate Analytics.pdf" if export_type == 'pdf' else "All Data.xlsx"

            # ...existing code...

            response = requests.get(
                f"{TELEGRAM_BOT_API_BASE_URL}/{endpoint}",
                headers=headers,
                timeout=TIMEOUT
            )

            if response.status_code == 200:
                exports[filename] = BytesIO(response.content)
                exports[filename].name = filename
            else:
                await query.message.reply_text(f"Failed to generate {filename}")
                return

            # Prepare email
            msg = EmailMessage()
            msg['Subject'] = 'Your Exported Documents'
            msg['From'] = GMAIL_SMTP_USERNAME
            msg['To'] = 'user@example.com'  # Replace with recipient's email
            msg.set_content('Please find attached your exported documents.')

            for filename, file in exports.items():
                msg.add_attachment(file.getvalue(), maintype='application', subtype='octet-stream', filename=filename)

            # Send email
            with smtplib.SMTP(GMAIL_SMTP_SERVER, GMAIL_SMTP_PORT) as server:
                server.starttls()
                server.login(GMAIL_SMTP_USERNAME, GMAIL_SMTP_PASSWORD)
                server.send_message(msg)

            await query.message.reply_text("All documents have been emailed to you.")
        except Exception as e:
            await query.message.reply_text(f"Error emailing documents: {str(e)}")

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
]