import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar
from telegram_bot_pagination import InlineKeyboardPaginator
from utils import cancel

from bots.telegram.auth import authenticate
from config.config import TELEGRAM_BOT_API_BASE_URL

# States for conversation
AMOUNT, DESCRIPTION, CATEGORY, DATE, CURRENCY, ACCOUNT, CONFIRM_DELETE, DELETE_ALL_CONFIRM = range(8)

@authenticate
async def expenses_add(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    await update.message.reply_text("Please enter the amount:")
    return AMOUNT

async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text)
        context.user_data['amount'] = amount
        await update.message.reply_text("Please enter a description:")
        return DESCRIPTION
    except ValueError:
        await update.message.reply_text("Please enter a valid number.")
        return AMOUNT

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['description'] = update.message.text
    await fetch_and_show_categories(update, context)
    return CATEGORY

@authenticate
async def fetch_and_show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    headers = {'token': token}
    response = requests.get(f"{TELEGRAM_BOT_API_BASE_URL}/categories/", headers=headers)
    if response.status_code == 200:
        categories = response.json().get('categories', [])
        if not categories:
            await update.message.reply_text("No categories found.")
            return

        keyboard = [
            [InlineKeyboardButton(category, callback_data=category)]
            for category in categories
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Please select a category:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Failed to fetch categories.")

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['category'] = query.data
    await fetch_and_show_currencies(update, context)
    return CURRENCY

@authenticate
async def fetch_and_show_currencies(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    headers = {'token': token}
    response = requests.get(f"{TELEGRAM_BOT_API_BASE_URL}/users/", headers=headers)
    if response.status_code == 200:
        currencies = response.json().get('currencies', [])
        if not currencies:
            await update.callback_query.message.edit_text("No currencies found.")
            return

        keyboard = [
            [InlineKeyboardButton(currency, callback_data=currency)]
            for currency in currencies
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text("Please select a currency:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("Failed to fetch currencies.")

async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['currency'] = query.data
    await fetch_and_show_accounts(update, context)
    return ACCOUNT

@authenticate
async def fetch_and_show_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    headers = {'token': token}
    response = requests.get(f"{TELEGRAM_BOT_API_BASE_URL}/accounts/", headers=headers)
    if response.status_code == 200:
        accounts = response.json().get('accounts', [])
        if not accounts:
            await update.callback_query.message.edit_text("No accounts found.")
            return

        keyboard = [
            [InlineKeyboardButton(account['name'], callback_data=account['name'])]
            for account in accounts
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.edit_text("Please select an account:", reply_markup=reply_markup)
    else:
        await update.callback_query.message.edit_text("Failed to fetch accounts.")

@authenticate
async def account(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data['account'] = query.data
    calendar, step = DetailedTelegramCalendar().build()
    await query.edit_message_text(f"Please select the date: {step}", reply_markup=calendar)
    return DATE

@authenticate
async def date(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    result, key, step = DetailedTelegramCalendar().process(update.callback_query.data)
    if not result and key:
        await update.callback_query.message.edit_text(f"Please select the date: {step}", reply_markup=key)
        return DATE
    elif result:
        # Format the amount as string and ensure it's a valid number
        amount_str = str(float(context.user_data['amount']))
        
        expense_data = {
            'amount': amount_str,
            'description': context.user_data['description'],
            'category': context.user_data['category'],
            'currency': context.user_data['currency'],
            'account': context.user_data['account'],
            'date': result.strftime("%Y-%m-%dT%H:%M:%S.%f")  # Save date in the specified format
        }
        
        headers = {'token': token}
        response = requests.post(f"{TELEGRAM_BOT_API_BASE_URL}/expenses/", json=expense_data, headers=headers)
        
        if response.status_code == 200:
            await update.callback_query.message.edit_text("Expense added successfully!")
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            await update.callback_query.message.edit_text(f"Failed to add expense: {error_detail}")
            
        context.user_data.clear()
        return ConversationHandler.END

@authenticate
async def expenses_view(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    headers = {'token': token}
    response = requests.get(f"{TELEGRAM_BOT_API_BASE_URL}/expenses/", headers=headers)
    if response.status_code == 200:
        expenses = response.json()['expenses']
        if not expenses:
            await update.message.reply_text("No expenses found.")
            return

        # Pagination setup
        page = int(context.args[0]) if context.args else 1
        items_per_page = 5
        paginator = InlineKeyboardPaginator(
            len(expenses) // items_per_page + (1 if len(expenses) % items_per_page else 0),
            current_page=page,
            data_pattern='view_expenses#{page}'
        )

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        expenses_page = expenses[start_idx:end_idx]

        message = "💰 *Your Expenses:*\n\n"
        for expense in expenses_page:
            # Convert date to human-readable format, handling datetime strings with time components
            try:
                date = datetime.strptime(expense['date'], "%Y-%m-%dT%H:%M:%S.%f").strftime("%B %d, %Y")
            except ValueError:
                date = datetime.strptime(expense['date'], "%Y-%m-%dT%H:%M:%S").strftime("%B %d, %Y")
            message += (
                f"💵 *Amount:* {expense['amount']} {expense['currency']}\n"
                f"📝 *Description:* {expense['description']}\n"
                f"📂 *Category:* {expense['category']}\n"
                f"📅 *Date:* {date}\n"
                "-------------------\n"
            )

        if update.message:
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=paginator.markup)
        elif update.callback_query:
            await update.callback_query.message.edit_text(message, parse_mode="Markdown", reply_markup=paginator.markup)
    else:
        if update.message:
            await update.message.reply_text("Failed to fetch expenses.")
        elif update.callback_query:
            await update.callback_query.message.edit_text("Failed to fetch expenses.")

@authenticate
async def expenses_view_page(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> None:
    query = update.callback_query
    page = int(query.data.split('#')[1])
    context.args = [page]
    await expenses_view(update, context)

@authenticate
async def expenses_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    headers = {'token': token}
    response = requests.get(f"{TELEGRAM_BOT_API_BASE_URL}/expenses/", headers=headers)
    if response.status_code == 200:
        expenses = response.json()['expenses']
        if not expenses:
            message = "No expenses found to delete."
            if update.message:
                await update.message.reply_text(message)
            elif update.callback_query:
                await update.callback_query.message.edit_text(message)
            return ConversationHandler.END

        # Pagination setup
        page = int(context.args[0]) if context.args else 1
        items_per_page = 2
        total_pages = len(expenses) // items_per_page + (1 if len(expenses) % items_per_page else 0)
        
        # Create pagination buttons manually
        pagination_buttons = []
        if total_pages > 1:
            if page > 1:
                pagination_buttons.append(
                    InlineKeyboardButton("⬅️", callback_data=f"delete_expenses#{page-1}")
                )
            if page < total_pages:
                pagination_buttons.append(
                    InlineKeyboardButton("➡️", callback_data=f"delete_expenses#{page+1}")
                )
        
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        expenses_page = expenses[start_idx:end_idx]

        keyboard = []
        for expense in expenses_page:
            button_text = f"{expense['description']} - {expense['amount']} {expense['currency']}"
            callback_data = f"delete_{expense['_id']}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

        # Add pagination row to keyboard if there are pagination buttons
        if pagination_buttons:
            keyboard.append(pagination_buttons)
            
        reply_markup = InlineKeyboardMarkup(keyboard)
        message = "Select an expense to delete:"
        
        if update.message:
            await update.message.reply_text(message, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        return CONFIRM_DELETE
    else:
        message = "Failed to fetch expenses."
        if update.message:
            await update.message.reply_text(message)
        elif update.callback_query:
            await update.callback_query.message.edit_text(message)
        return ConversationHandler.END

@authenticate
async def expenses_delete_page(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    query = update.callback_query
    await query.answer()
    page = int(query.data.split('#')[1])
    context.args = [page]
    return await expenses_delete(update, context)

@authenticate
async def confirm_delete(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    query = update.callback_query
    await query.answer()
    
    # If it's a pagination callback, let it pass through
    if query.data.startswith("delete_expenses#"):
        return CONFIRM_DELETE
        
    if query.data.startswith("delete_"):
        context.user_data['expense_id'] = query.data.split('_')[1]
        await query.message.edit_text(
            "Are you sure you want to delete this expense?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Yes", callback_data="confirm_delete"),
                 InlineKeyboardButton("No", callback_data="cancel_delete")]
            ])
        )
        return CONFIRM_DELETE
    elif query.data == "confirm_delete":
        expense_id = context.user_data.get('expense_id')
        headers = {'token': token}
        response = requests.delete(f"{TELEGRAM_BOT_API_BASE_URL}/expenses/{expense_id}", headers=headers)
        if response.status_code == 200:
            await query.message.edit_text("Expense deleted successfully!")
        else:
            await query.message.edit_text("Failed to delete expense.")
        context.user_data.clear()
        return ConversationHandler.END
    elif query.data == "cancel_delete":
        await query.message.edit_text("Deletion cancelled.")
        context.user_data.clear()
        return ConversationHandler.END

@authenticate
async def expenses_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    headers = {'token': token}
    response = requests.get(f"{TELEGRAM_BOT_API_BASE_URL}/expenses/", headers=headers)
    if response.status_code == 200:
        expenses = response.json()['expenses']
        if not expenses:
            await update.message.reply_text("No expenses found to delete.")
            return ConversationHandler.END
        
        total_expenses = len(expenses)
        keyboard = [[
            InlineKeyboardButton("Yes", callback_data="confirm_delete_all"),
            InlineKeyboardButton("No", callback_data="cancel_delete_all")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ Are you sure you want to delete all {total_expenses} expenses? This action cannot be undone!",
            reply_markup=reply_markup
        )
        return DELETE_ALL_CONFIRM
    else:
        await update.message.reply_text("Failed to fetch expenses.")
        return ConversationHandler.END

@authenticate
async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE, token: str) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "confirm_delete_all":
        headers = {'token': token}
        response = requests.delete(f"{TELEGRAM_BOT_API_BASE_URL}/expenses/all", headers=headers)
        if response.status_code == 200:
            await query.message.edit_text("✅ All expenses deleted successfully!")
        else:
            await query.message.edit_text("❌ Failed to delete expenses.")
        return ConversationHandler.END
    elif query.data == "cancel_delete_all":
        await query.message.edit_text("Deletion cancelled.")
        return ConversationHandler.END

# Handlers for expenses
expenses_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("expenses_add", expenses_add)],
    states={
        AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [CallbackQueryHandler(category)],
        CURRENCY: [CallbackQueryHandler(currency)],
        ACCOUNT: [CallbackQueryHandler(account)],
        DATE: [CallbackQueryHandler(date)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Add the new handlers
expenses_delete_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("expenses_delete", expenses_delete)],
    states={
        CONFIRM_DELETE: [
            CallbackQueryHandler(expenses_delete_page, pattern=r'^delete_expenses#\d+$'),
            CallbackQueryHandler(confirm_delete)
        ],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# Add the delete all conversation handler
expenses_delete_all_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("expenses_delete_all", expenses_delete_all)],
    states={
        DELETE_ALL_CONFIRM: [CallbackQueryHandler(confirm_delete_all)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)