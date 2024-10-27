import helper
import gemini_helper
import logging
from telebot import types, telebot
from datetime import datetime
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
import os
from jproperties import Properties

configs = Properties()

with open('user.properties', 'rb') as read_prop:
    configs.load(read_prop)

# Temporary storage for receipt data
receipt_data = {}

api_token = str(configs.get('api_token').data)
bot = telebot.TeleBot(api_token)

def run(message, bot):
    """Start receipt scanning process"""
    chat_id = message.chat.id
    bot.send_message(chat_id, 'Please send me a photo of your receipt.')
    bot.register_next_step_handler(message, handle_receipt_image, bot)

def handle_receipt_image(message, bot):
    """Handle the receipt image upload"""
    try:
        chat_id = message.chat.id

        # Validate image
        if not hasattr(message, 'photo') or not message.photo:
            bot.send_message(chat_id, 'Please send a valid receipt photo.')
            bot.register_next_step_handler(message, handle_receipt_image, bot)
            return

        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f'https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}'

        # Process receipt with Gemini
        result, error = gemini_helper.process_receipt_image(file_url)
        if error or not result:
            bot.send_message(chat_id, error or "Image is not a receipt.")
            return  # End flow if not a valid receipt

        print("Extracted data: ", result)
        # Save receipt data temporarily
        receipt_data[chat_id] = {
            'date': result['date'],
            'amount': result['amount'],
            'category': result['category'],
        }
        
        add_user_record(chat_id, {
            'date': result['date'],
            'amount': result['amount'],
            'category': result['category'],
        })

        # Display receipt details and options
        # show_receipt_details(message, bot)

    except Exception as e:
        logging.exception("Error in handle_receipt_image")
        bot.send_message(chat_id, f'Error processing receipt: {str(e)}')

def show_receipt_details(message, bot):
    """Show receipt details with edit options"""
    try:
        chat_id = message.chat.id
        data = receipt_data[chat_id]

        # Display receipt details
        msg_text = (
            "Receipt Details:\n"
            f"Date: {data['date']}\n"
            f"Amount: {data['amount']:.2f}\n"
            f"Category: {data['category']}"
        )
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("✏️ Edit", callback_data="edit_receipt"),
            types.InlineKeyboardButton("➕ Add Transaction", callback_data="add_receipt_transaction"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_receipt")
        )
        msg = bot.send_message(chat_id, msg_text, reply_markup=markup)
        print(msg.text)

    except Exception as e:
        logging.exception("Error in show_receipt_details")
        bot.send_message(chat_id, f'Error showing receipt details: {str(e)}')

# @bot.callback_query_handler(func=lambda call: call.data == "edit_receipt")
# def handle_edit_receipt(call):
#     """Display edit options for receipt"""
#     chat_id = call.message.chat.id
#     markup = types.InlineKeyboardMarkup()
#     markup.row(
#         types.InlineKeyboardButton("Edit Date", callback_data="edit_receipt_date"),
#         types.InlineKeyboardButton("Edit Amount", callback_data="edit_receipt_amount"),
#         types.InlineKeyboardButton("Edit Category", callback_data="edit_receipt_category")
#     )
#     bot.edit_message_reply_markup(
#         chat_id=chat_id,
#         message_id=call.message.message_id,
#         reply_markup=markup
#     )

# @bot.callback_query_handler(func=lambda call: call.data == "add_receipt_transaction")
# def add_transaction(call):
#     print(data)
#     """Finalize and add transaction to the JSON"""
#     try:
#         chat_id = call.message.chat.id
#         data = receipt_data[chat_id]

#         print(data)
        
#         # Format date
#         date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
#         formatted_date = date_obj.strftime(helper.getDateFormat() + ' ' + helper.getTimeFormat())
        
#         record = f"{formatted_date},{data['category']},{data['amount']}"
#         helper.write_json(add_user_record(chat_id, record))

#         # Clean up and confirm addition
#         del receipt_data[chat_id]
#         bot.edit_message_text(
#             'Transaction added successfully!',
#             chat_id=chat_id,
#             message_id=call.message.message_id
#         )

#     except Exception as e:
#         logging.exception("Error in add_transaction")
#         bot.edit_message_text(
#             f'Error adding transaction: {str(e)}',
#             chat_id=chat_id,
#             message_id=call.message.message_id
#         )

# @bot.callback_query_handler(func=lambda call: call.data == "cancel_receipt")
# def handle_cancel_receipt(call):
#     """Cancel receipt processing"""
#     chat_id = call.message.chat.id
#     if chat_id in receipt_data:
#         del receipt_data[chat_id]
    
#     bot.edit_message_text(
#         "Receipt processing cancelled.",
#         chat_id=chat_id,
#         message_id=call.message.message_id
#     )

# # Functions to edit individual fields

# @bot.callback_query_handler(func=lambda call: call.data == "edit_receipt_date")
# def edit_receipt_date(call):
#     """Start date editing process"""
#     chat_id = call.message.chat.id
#     calendar, step = DetailedTelegramCalendar().build()
#     bot.send_message(chat_id, f"Select {LSTEP[step]}", reply_markup=calendar)

# @bot.callback_query_handler(func=lambda call: call.data == "edit_receipt_amount")
# def edit_receipt_amount(call):
#     """Start amount editing process"""
#     chat_id = call.message.chat.id
#     msg = bot.send_message(chat_id, 'Please enter the new amount:')
#     bot.register_next_step_handler(msg, process_edited_amount, bot)

# @bot.callback_query_handler(func=lambda call: call.data == "edit_receipt_category")
# def edit_receipt_category(call):
#     """Start category editing process"""
#     chat_id = call.message.chat.id
#     markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
#     categories = helper.getSpendCategories()
#     for i in range(0, len(categories), 2):
#         markup.row(categories[i], categories[i + 1] if i + 1 < len(categories) else "")
#     msg = bot.send_message(chat_id, 'Select Category:', reply_markup=markup)
#     bot.register_next_step_handler(msg, process_edited_category, bot)

# def process_edited_amount(message, bot):
#     """Process edited amount and update receipt"""
#     chat_id = message.chat.id
#     try:
#         amount_value = helper.validate_entered_amount(message.text)
#         receipt_data[chat_id]['amount'] = amount_value
#         show_receipt_details(message, bot)
#     except ValueError:
#         bot.send_message(chat_id, "Invalid amount. Please enter a valid number.")
#         bot.register_next_step_handler(message, process_edited_amount, bot)

# def process_edited_category(message, bot):
#     """Process edited category and update receipt"""
#     chat_id = message.chat.id
#     category = message.text
#     if category in helper.getSpendCategories():
#         receipt_data[chat_id]['category'] = category
#         show_receipt_details(message, bot)
#     else:
#         bot.send_message(chat_id, "Invalid category. Please select a valid category.")
#         edit_receipt_category(types.CallbackQuery(data="edit_receipt_category"), bot)

def add_user_record(chat_id, record_to_be_added):
    user_list = helper.read_json()
    
    # If user is not in the list, create a new record
    if str(chat_id) not in user_list:
        user_list[str(chat_id)] = helper.createNewUserRecord()
    
    

    original_date = datetime.strptime(record_to_be_added['date'], "%Y-%m-%d")
    formatted_date = original_date.strftime("%d-%b-%Y 00:00")
    upload_string = f'{formatted_date},{record_to_be_added["category"]},{record_to_be_added["amount"]}' 

    
    # Append the new record to the user's data
    user_list[str(chat_id)]['data'].append(upload_string)
    
    # Write the updated data back to JSON
    helper.write_json(user_list)
    
    msg_text = (
            "Added successfully! to the database.\n"
            "Receipt Details:\n"
            f"Date: {record_to_be_added['date']}\n"
            f"Amount: {record_to_be_added['amount']:.2f}\n"
            f"Category: {record_to_be_added['category']}"
        )
    bot.send_message(chat_id, msg_text)

    return user_list