import helper
import logging
from telebot import types
import csv
import os
from datetime import datetime

def run(message, bot):
    """
    Initial function to handle the /csv command
    """
    try:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
        options = helper.getIncomeOrExpense()
        markup.row_width = 2
        for c in options.values():
            markup.add(c)
        msg = bot.reply_to(message, 'Select Income or Expense', reply_markup=markup)
        bot.register_next_step_handler(msg, post_type_selection, bot)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"Error in initial setup: {str(e)}")

def post_type_selection(message, bot):
    """
    Handles the selection of Income or Expense and generates the CSV file
    """
    try:
        helper.read_json()
        chat_id = message.chat.id
        selected_type = message.text
        user_history = helper.getUserHistory(chat_id, selected_type)
        
        if user_history is None or len(user_history) == 0:
            bot.send_message(chat_id, "No records found!")
            return
        
        # Create filename with timestamp and chat_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{chat_id}_{timestamp}.csv"
        
        # Write data to CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            # Write header
            csvwriter.writerow(['Date', 'Category', 'Amount'])
            
            # Write transactions
            for record in user_history:
                try:
                    date_time, category, amount = record.split(",")
                    date, _ = date_time.split(" ")
                    csvwriter.writerow([date, category, amount])
                except ValueError as ve:
                    logging.warning(f"Skipping malformed record: {record}. Error: {str(ve)}")
                    continue
        
        # Send file to user
        try:
            with open(filename, 'rb') as csvfile:
                bot.send_document(
                    chat_id, 
                    csvfile, 
                    caption=f"Here's your {selected_type} history as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
        except Exception as e:
            logging.exception(f"Error sending file: {str(e)}")
            bot.reply_to(message, "Error sending the file. Please try again.")
            
        # Clean up - remove the file after sending
        try:
            if os.path.exists(filename):
                os.remove(filename)
        except Exception as e:
            logging.warning(f"Could not remove temporary file {filename}: {str(e)}")
            
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"An error occurred while generating the CSV: {str(e)}")