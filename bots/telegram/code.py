import os
import sys
import logging
import requests
from rich import inspect
from motor.motor_asyncio import AsyncIOMotorClient
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from typing import Dict
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from config import config

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
 
# States for conversation
AMOUNT, DESCRIPTION, CATEGORY, DATE = range(4)
USERNAME, PASSWORD, LOGIN_PASSWORD, SIGNUP_CONFIRM = range(4, 8)  # Changed PHONE to USERNAME
user_tokens: Dict[int, str] = {}  # Store user tokens in memory

# API Base URL from config
API_BASE_URL = config.TELEGRAM_BOT_API_BASE_URL

# Add MongoDB connection after API_BASE_URL config
mongodb_client = AsyncIOMotorClient(config.MONGO_URI)
telegram_collection = mongodb_client.mmdb.telegram_bot

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Welcome to Money Manager Bot!\n\n"
        "Use /login to access your account\n"
        "Use /signup to create new account\n"
        "Use /add to add a new expense\n"
        "Use /view to view your expenses\n"
        "Use /total to see total expenses"
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Please enter your username:")
    return USERNAME

# Update handle_username to check which flow we're in
async def handle_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['username'] = update.message.text
    await update.message.reply_text("Please enter your password:")
    # Check if we're in signup flow by looking at the command that started the conversation
    if context.user_data.get('is_signup'):
        return PASSWORD
    return LOGIN_PASSWORD

async def handle_login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # Call login endpoint with token expiration
        response = requests.post(
            f"{API_BASE_URL}/users/token/?token_expires=43200",
            data={
                'username': context.user_data['username'],
                'password': update.message.text
            }
        )
        
        if response.status_code == 200:
            token = response.json()["result"]["token"]
            user_id = update.effective_user.id

            # Update or insert telegram user data
            user = await telegram_collection.find_one({"username": context.user_data['username']})
            if user:
                await telegram_collection.update_one(
                    {"telegram_id": user_id},
                    {"$set": {"token": token, "username": context.user_data['username']}}
                )
            else:
                user_data = {
                    "username": context.user_data['username'],
                    "token": token,
                    "telegram_id": user_id,
                }
                await telegram_collection.insert_one(user_data)

            # Store token in memory
            user_tokens[user_id] = token
            await update.message.reply_text("Login successful!")
        else:
            await update.message.reply_text(
                f"Login failed: {response.json()['detail']}\n /signup if you haven't, otherwise /login"
            )
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")
        return ConversationHandler.END

async def signup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # Mark that we're in signup flow
    context.user_data['is_signup'] = True
    await update.message.reply_text("Please enter your username:")
    return USERNAME

async def handle_signup_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['password'] = update.message.text
    await update.message.reply_text("Please confirm your password:")
    return SIGNUP_CONFIRM

async def handle_signup_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        if update.message.text != context.user_data['password']:
            await update.message.reply_text("Passwords don't match. Please try again.")
            return ConversationHandler.END

        # Create user
        signup_data = {
            'username': context.user_data['username'],
            'password': context.user_data['password']
        }
        response = requests.post(f"{API_BASE_URL}/users/", json=signup_data)
        
        if response.status_code == 200:
            # After successful signup, attempt to login
            login_response = requests.post(
                f"{API_BASE_URL}/users/token/?token_expires=43200",
                data={
                    'username': context.user_data['username'],
                    'password': context.user_data['password']
                }
            )
            
            if login_response.status_code == 200:
                token = login_response.json()["result"]["token"]
                user_id = update.effective_user.id
                
                # Store user data in MongoDB
                user_data = {
                    "username": context.user_data['username'],
                    "token": token,
                    "telegram_id": user_id,
                }
                await telegram_collection.insert_one(user_data)
                
                # Store token in memory
                user_tokens[user_id] = token
                await update.message.reply_text("Signup successful! You are now logged in.")
            else:
                await update.message.reply_text("Account created! Please use /login to access your account.")
        else:
            error_msg = response.json().get('detail', 'Username may already exist.')
            await update.message.reply_text(f"Signup failed: {error_msg}")
        
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        await update.message.reply_text("An error occurred during signup. Please try again.")
        return ConversationHandler.END

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
    await update.message.reply_text("Please enter the category:")
    return CATEGORY

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['category'] = update.message.text
    calendar, step = DetailedTelegramCalendar().build()
    await update.message.reply_text(f"Please select the date: {step}", reply_markup=calendar)
    return DATE

async def date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    result, key, step = DetailedTelegramCalendar().process(update.callback_query.data)
    if not result and key:
        await update.callback_query.message.edit_text(f"Please select the date: {step}", reply_markup=key)
        return DATE
    elif result:
        context.user_data['date'] = result
        token = user_tokens.get(update.effective_user.id)
        if not token:
            await update.callback_query.message.edit_text("Please login first using /login")
            return ConversationHandler.END

        # Format the amount as string and ensure it's a valid number
        amount_str = str(float(context.user_data['amount']))
        
        expense_data = {
            'amount': amount_str,
            'description': context.user_data['description'],
            'category': context.user_data['category'],
            'currency': 'USD',
            'date': result.strftime("%Y-%m-%dT%H:%M:%S.%f")  # Save date in the specified format
        }
        
        headers = {'token': token}
        response = requests.post(f"{API_BASE_URL}/expenses/", json=expense_data, headers=headers)
        
        if response.status_code == 200:
            await update.callback_query.message.edit_text("Expense added successfully!")
        else:
            error_detail = response.json().get('detail', 'Unknown error')
            await update.callback_query.message.edit_text(f"Failed to add expense: {error_detail}")
            
        context.user_data.clear()
        return ConversationHandler.END

async def view_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    token = user_tokens.get(update.effective_user.id)
    if not token:
        await update.message.reply_text("Please login first using /login")
        return

    headers = {'token': token}
    response = requests.get(f"{API_BASE_URL}/expenses/", headers=headers)
    if response.status_code == 200:
        expenses = response.json()['expenses']
        if not expenses:
            await update.message.reply_text("No expenses found.")
            return

        message = "💰 *Your Expenses:*\n\n"
        for expense in expenses:
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

        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text("Failed to fetch expenses.")

async def get_total(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        token = user_tokens.get(update.effective_user.id)
        if not token:
            await update.message.reply_text("Please login first using /login")
            return

        headers = {'token': token}  # Changed from 'Authorization': f'Bearer {token}'
        response = requests.get(f"{API_BASE_URL}/expenses/total", headers=headers)
        if response.status_code == 200:
            total = response.json()['total']
            await update.message.reply_text(f"Total expenses: {total}")
        else:
            await update.message.reply_text("Failed to fetch total expenses.")
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    # Get token directly from config
    token = config.TELEGRAM_BOT_TOKEN
    application = Application.builder().token(token).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_expense)],
        states={
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
            DATE: [CallbackQueryHandler(date)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add auth handlers
    login_handler = ConversationHandler(
        entry_points=[CommandHandler("login", login)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_login_password)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Fix the signup handler state configuration
    signup_handler = ConversationHandler(
        entry_points=[CommandHandler("signup", signup)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signup_password)],
            SIGNUP_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_signup_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(login_handler)
    application.add_handler(signup_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("view", view_expenses))
    application.add_handler(CommandHandler("total", get_total))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()