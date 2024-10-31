import helper
import logging
from telebot import types
from matplotlib import pyplot as plt
from datetime import datetime


def run(message, bot):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    options = helper.getIncomeOrExpense()
    markup.row_width = 2
    for c in options.values():
        markup.add(c)
    msg = bot.reply_to(message, 'Select Income or Expense', reply_markup=markup)
    bot.register_next_step_handler(msg, post_type_selection, bot)


def post_type_selection(message, bot):
    try:
        chat_id = message.chat.id
        selectedType = message.text
        helper.read_json()
        
        msg = bot.reply_to(
            message, "Enter start date (YYYY-MM-DD):"
        )
        bot.register_next_step_handler(msg, get_start_date, bot, selectedType, chat_id)
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, "Oops! " + str(e))


def get_start_date(message, bot, selectedType, chat_id):
    try:
        start_date = datetime.strptime(message.text, "%Y-%m-%d")
        msg = bot.reply_to(
            message, "Enter end date (YYYY-MM-DD):"
        )
        bot.register_next_step_handler(
            msg, get_end_date, bot, selectedType, chat_id, start_date
        )
    except ValueError:
        bot.reply_to(message, "Invalid date format. Please use YYYY-MM-DD.")
        return


def get_end_date(message, bot, selectedType, chat_id, start_date):
    try:
        end_date = datetime.strptime(message.text, "%Y-%m-%d")
        start_date = start_date  # ensure start_date remains a datetime object
        
        if end_date < start_date:
            bot.reply_to(
                message, "End date cannot be before start date. Please try again."
            )
            return

        user_history = helper.getUserHistory(chat_id, selectedType) or []  # fallback to empty list
        filtered_history = [
            rec for rec in user_history if start_date <= datetime.strptime(rec.split(",")[0], "%Y-%m-%d %H:%M:%S") <= end_date
        ]

        if not filtered_history:
            bot.send_message(chat_id, f"No {selectedType} records found between {start_date.date()} and {end_date.date()}.")
            return

        bot.send_message(chat_id, f"Created a PDF of your {selectedType} history from {start_date.date()} to {end_date.date()}!")
        generate_pdf(filtered_history, selectedType, chat_id, bot)

    except ValueError:
        bot.reply_to(message, "Invalid date format. Please use YYYY-MM-DD.")
    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, "Oops! " + str(e))


def generate_pdf(user_history, selectedType, chat_id, bot):
    if not user_history:  # Handle empty user history gracefully
        bot.send_message(chat_id, "No records to generate a PDF.")
        return
    
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    top = 0.8

    for rec in user_history:
        date, category, amount = rec.split(",")
        date, time = date.split(" ")
        if selectedType == "Income":
            rec_str = f"{amount}$ {category} income on {date} at {time}"
        else:
            rec_str = f"{amount}$ {category} expense on {date} at {time}"
        plt.text(
            0,
            top,
            rec_str,
            horizontalalignment="left",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=14,
            bbox=dict(facecolor="red", alpha=0.3),
        )
        top -= 0.15

    plt.axis("off")
    plt.savefig("history.pdf")
    plt.close()
    bot.send_document(chat_id, open("history.pdf", "rb"))

