from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler
import requests
from io import BytesIO
import calendar
from datetime import datetime

from config.config import TELEGRAM_BOT_API_BASE_URL
from bots.telegram.utils import cancel

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
SELECTING_FROM_DATE, SELECTING_TO_DATE, SELECTING_FORMAT, SELECTING_DATE_OPTION = range(4)

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
async def show_date_options(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Show options to select dates or skip."""
    query = update.callback_query
    if query:
        await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("Set From Date", callback_data="set_from_date")],
        [InlineKeyboardButton("Set To Date", callback_data="set_to_date")],
        [InlineKeyboardButton("Clear Dates", callback_data="clear_dates")],  # Added Clear Dates
        [InlineKeyboardButton("Next", callback_data="next")]  # Added Next button
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.message.edit_text(
            "Would you like to select dates for export?",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "📤 *Export Data*\n\nWould you like to select a date range?",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    return SELECTING_DATE_OPTION

@authenticate
async def exports(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Handle the /exports command - show date selection options"""
    return await show_date_options(update, context)

@authenticate
async def handle_date_option(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Handle user's choice on date selection"""
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "set_from_date":
        return await select_from_date(update, context)
    elif choice == "set_to_date":
        return await select_to_date(update, context)
    elif choice == "clear_dates":
        context.user_data.pop('from_date', None)
        context.user_data.pop('to_date', None)
        await query.message.reply_text("✅ Dates have been cleared.")
        return SELECTING_DATE_OPTION
    elif choice == "next":
        return await show_export_formats(update, context)
    return ConversationHandler.END

@authenticate
async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Handle date selection from calendar"""
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('date_'):
        _, year, month, day = query.data.split('_')
        selected_date = datetime(int(year), int(month), int(day)).strftime('%Y-%m-%d')
        
        if 'set_both' in context.user_data and context.user_data['set_both']:
            if 'from_date' not in context.user_data:
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
                return await show_export_formats(update, context)
        else:
            if 'from_date' in context.user_data:
                context.user_data['to_date'] = selected_date
                return await show_export_formats(update, context)
            else:
                context.user_data['from_date'] = selected_date
                return await show_export_formats(update, context)
    return SELECTING_FORMAT

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

async def show_export_formats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show export format options"""
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton("PDF", callback_data="export_pdf")],
        [InlineKeyboardButton("Excel", callback_data="export_excel")],
        [InlineKeyboardButton("CSV", callback_data="export_csv")],
        [InlineKeyboardButton("Email All", callback_data="export_email")],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_dates")]  # Added Back button
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        await query.message.edit_text(
            "Choose export format:",
            reply_markup=reply_markup
        )
    return SELECTING_FORMAT

@authenticate
async def handle_back_to_dates(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    """Handle the back button to return to date selection"""
    query = update.callback_query
    await query.answer()
    
    return await show_date_options(update, context)

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

async def select_from_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the calendar for selecting the start date."""
    calendar_markup = await create_calendar_markup(datetime.now().year, datetime.now().month)
    await update.callback_query.message.edit_text(
        "Select the start date:",
        reply_markup=calendar_markup
    )
    return SELECTING_FROM_DATE

async def select_to_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the calendar for selecting the end date."""
    calendar_markup = await create_calendar_markup(datetime.now().year, datetime.now().month)
    await update.callback_query.message.edit_text(
        "Select the end date:",
        reply_markup=calendar_markup
    )
    return SELECTING_TO_DATE

analytics_handlers = [
    CommandHandler('analytics', analytics),
    CallbackQueryHandler(button_callback, pattern=r'^plot_'),
]

# Add to existing handlers list
analytics_handlers.extend([
    ConversationHandler(
        entry_points=[CommandHandler('exports', exports)],
        states={
            SELECTING_DATE_OPTION: [
                CallbackQueryHandler(handle_date_option, pattern='^(set_from_date|set_to_date|clear_dates|next)$')  # Updated pattern
            ],
            SELECTING_FROM_DATE: [
                CallbackQueryHandler(select_from_date, pattern='^select_from_date$'),
                CallbackQueryHandler(handle_date_selection, pattern='^date_\d{4}_\d{1,2}_\d{1,2}$')
            ],
            SELECTING_TO_DATE: [
                CallbackQueryHandler(select_to_date, pattern='^select_to_date$'),
                CallbackQueryHandler(handle_date_selection, pattern='^date_\d{4}_\d{1,2}_\d{1,2}$')
            ],
            SELECTING_FORMAT: [
                CallbackQueryHandler(handle_csv_options, pattern='^export_csv$'),
                CallbackQueryHandler(handle_export, pattern='^(export_pdf|export_excel|export_email|csv_\w+)$'),
                CallbackQueryHandler(show_export_formats, pattern='^back_to_formats$'),
                CallbackQueryHandler(handle_back_to_dates, pattern='^back_to_dates$')  # Added handler for Back button
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
])
