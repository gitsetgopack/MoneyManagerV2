# savings_tracker.py

from datetime import datetime
import helper

def run(message, bot):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Please enter the maximum expenditure limit you'd like to set:")

    # Prompt for the limit
    bot.register_next_step_handler(message, set_limit, bot)

def set_limit(message, bot):
    chat_id = message.chat.id
    try:
        limit = float(message.text)
        bot.send_message(chat_id, "Got it! Now, please enter the start date for this limit (format: DD-MM-YYYY):")
        
        # Store limit and proceed to date range selection
        bot.register_next_step_handler(message, set_start_date, bot, limit)
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid number for the expenditure limit.")
        bot.register_next_step_handler(message, set_limit, bot)
        # run(message, bot)  # Restart the flow if input is invalid

def set_start_date(message, bot, limit):
    chat_id = message.chat.id
    try:
        start_date = datetime.strptime(message.text, '%d-%m-%Y')
        bot.send_message(chat_id, "Now, please enter the end date for this limit (format: DD-MM-YYYY):")
        
        # Proceed to end date with stored limit and start date
        bot.register_next_step_handler(message, set_end_date, bot, limit, start_date)
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid date in DD-MM-YYYY format.")
        bot.register_next_step_handler(message, set_start_date, bot, limit)
        # set_limit(message, bot)  # Restart from limit input if date is invalid

def set_end_date(message, bot, limit, start_date):
    chat_id = message.chat.id
    try:
        end_date = datetime.strptime(message.text, '%d-%m-%Y')
        
        if end_date < start_date:
            bot.send_message(chat_id, "End date cannot be before the start date. Please try again.")
            bot.register_next_step_handler(message, set_start_date, bot, limit)
            # set_start_date(message, bot, limit)  # Restart from start date if end date is invalid
        else:
            # Call the helper function to set the expenditure limit
            time_frame = f"{start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}"
            helper.set_max_expenditure_limit(chat_id, limit, time_frame)
            bot.send_message(chat_id, f"Your savings goal has been set with a limit of {limit} from {time_frame}.")
    except ValueError:
        bot.send_message(chat_id, "Please enter a valid date in DD-MM-YYYY format.")
        bot.register_next_step_handler(message, set_start_date, bot, limit)
        # set_start_date(message, bot)  # Restart from start date if date is invalid
