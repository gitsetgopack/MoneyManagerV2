from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler
import requests
from io import BytesIO
import calendar
from datetime import datetime

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

# States for the conversation
SELECTING_FROM_DATE, SELECTING_TO_DATE, SELECTING_FORMAT = range(3)

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

@authenticate
async def exports(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Handle the /exports command - show date selection options"""
    keyboard = [
        [InlineKeyboardButton("Select From Date", callback_data="select_from_date"),
         InlineKeyboardButton("Skip Dates", callback_data="skip_dates")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📤 *Export Data*\n\nWould you like to select a date range?",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return SELECTING_FROM_DATE

async def create_calendar_markup(year: int, month: int) -> InlineKeyboardMarkup:
    """Create an inline keyboard with a calendar"""
    keyboard = []
    # Add year and month selection row
    keyboard.append([
        InlineKeyboardButton(f"{calendar.month_name[month]} {year}",
                            callback_data="ignore")
    ])
    # Add days header
    keyboard.append([InlineKeyboardButton(day, callback_data="ignore")
                    for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]])
    # Add calendar days
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day in week:
            if day == 0:
                row.append(InlineKeyboardButton(" ", callback_data="ignore"))
            else:
                row.append(InlineKeyboardButton(str(day),
                          callback_data=f"date_{year}_{month}_{day}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

@authenticate
async def show_export_formats(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Show export format options"""
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("Excel", callback_data="export_excel")],
        [InlineKeyboardButton("CSV", callback_data="export_csv")],
        [InlineKeyboardButton("Email All", callback_data="export_email")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.message.edit_text(
            "Choose export format:",
            reply_markup=reply_markup
        )
    return SELECTING_FORMAT

@authenticate
async def handle_csv_options(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Handle CSV export options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Expenses", callback_data="csv_expenses")],
        [InlineKeyboardButton("Accounts", callback_data="csv_accounts")],
        [InlineKeyboardButton("Categories", callback_data="csv_categories")],
        [InlineKeyboardButton("⬅️", callback_data="back_to_formats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.edit_text(
        "Select CSV export type:",
        reply_markup=reply_markup
    )

@authenticate
async def handle_export(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    """Handle the actual export process"""
    query = update.callback_query
    await query.answer()
    
    export_type = query.data
    params = {}
    from_date = context.user_data.get('from_date')
    to_date = context.user_data.get('to_date')
    if from_date:
        params['from_date'] = from_date
    if to_date:
        params['to_date'] = to_date
    
    try:
        headers = {
            "token": token,
            "Accept": "application/octet-stream"
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if export_type.startswith('csv_'):
            export_subtype = export_type[4:]  # get expenses, accounts, etc
            endpoint = f"exports/csv?export_type={export_subtype}"
            mime_type = "text/csv"
            filename = f"{export_subtype}_{timestamp}.csv"
        elif export_type == 'export_pdf':
            endpoint = "exports/pdf"
            mime_type = "application/pdf"
            filename = f"ultimate_analytics_{timestamp}.pdf"
        elif export_type == 'export_excel':
            endpoint = "exports/xlsx"
            mime_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            filename = f"all_data_{timestamp}.xlsx"
        elif export_type == 'export_email':
            endpoint = "exports/email"
            
        response = requests.get(
            f"{TELEGRAM_BOT_API_BASE_URL}/{endpoint}",
            headers=headers,
            params=params,  # Now only includes dates if they were selected
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            if export_type == 'export_email':
                await query.message.reply_text("✅ Exports have been sent to your email!")
            else:
                await query.message.reply_document(
                    document=BytesIO(response.content),
                    filename=filename,
                    caption="Here's your exported file 📎",
                    read_timeout=30,
                    write_timeout=30,
                    connect_timeout=30
                )
        else:
            await query.message.reply_text(f"❌ Export failed: {response.text}")
            
    except Exception as e:
        await query.message.reply_text(f"❌ Error during export: {str(e)}")
        return ConversationHandler.END

@authenticate
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Handle date selection from calendar"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('date_'):
        _, year, month, day = query.data.split('_')
        selected_date = datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
        
        if context.user_data.get('from_date') is None:
            context.user_data['from_date'] = selected_date
            keyboard = [[InlineKeyboardButton("Select To Date", callback_data="select_to_date")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.message.edit_text(
                f"From date selected: {selected_date}\nNow select the end date:",
                reply_markup=reply_markup
            )
            return SELECTING_TO_DATE
        else:
            context.user_data['to_date'] = selected_date
            return await show_export_formats(update, context, token)
    return SELECTING_TO_DATE

# Remove or comment out the old expense_bar function since it's now handled by the callback

analytics_handlers = [
    CommandHandler('analytics', analytics),
    CallbackQueryHandler(button_callback, pattern=r'^plot_'),
]

# Add to existing handlers list
analytics_handlers.extend([
    ConversationHandler(
        entry_points=[CommandHandler('exports', exports)],
        states={
            SELECTING_FROM_DATE: [
                CallbackQueryHandler(show_export_formats, pattern='^skip_dates$'),
                CallbackQueryHandler(lambda u, c: create_calendar_markup(datetime.now().year, datetime.now().month), 
                                   pattern='^select_from_date$'),
                CallbackQueryHandler(handle_date_selection, pattern='^date_\d{4}_\d{1,2}_\d{1,2}$')
            ],
            SELECTING_TO_DATE: [
                CallbackQueryHandler(lambda u, c: create_calendar_markup(datetime.now().year, datetime.now().month), 
                                   pattern='^select_to_date$'),
                CallbackQueryHandler(handle_date_selection, pattern='^date_\d{4}_\d{1,2}_\d{1,2}$')
            ],
            SELECTING_FORMAT: [
                CallbackQueryHandler(handle_csv_options, pattern='^export_csv$'),
                CallbackQueryHandler(handle_export, pattern='^(export_pdf|export_excel|export_email|csv_\w+)$'),
                CallbackQueryHandler(show_export_formats, pattern='^back_to_formats$')
            ]
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
])
