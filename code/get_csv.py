import helper
import logging
from telebot import types
import pandas as pd
import xlsxwriter
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

        # Convert user history to DataFrame
        data = []
        for record in user_history:
            try:
                date_time, category, amount = record.split(",")
                date, _ = date_time.split(" ")
                data.append([date, category, float(amount)])
            except ValueError:
                logging.warning(f"Skipping malformed record: {record}")
                continue
        
        df = pd.DataFrame(data, columns=['Date', 'Category', 'Amount'])
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%b-%Y')
        df['Month'] = df['Date'].dt.to_period('M')

        # Create filename with timestamp and chat_id
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"history_{chat_id}_{timestamp}.xlsx"

        # Create a pivot table for monthly spending and category spending
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            # Write main data
            df.to_excel(writer, sheet_name='Transactions', index=False)

            # Monthly spending pivot
            monthly_pivot = df.pivot_table(values='Amount', index='Month', aggfunc='sum')
            monthly_pivot.to_excel(writer, sheet_name='Monthly_Spending')

            # Category spending pivot
            category_pivot = df.pivot_table(values='Amount', index='Category', aggfunc='sum')
            category_pivot.to_excel(writer, sheet_name='Category_Spending')

            workbook = writer.book

            # Add monthly spending chart
            chart1 = workbook.add_chart({'type': 'line'})
            chart1.add_series({
                'name': 'Monthly Spending',
                'categories': ['Monthly_Spending', 1, 0, len(monthly_pivot), 0],
                'values': ['Monthly_Spending', 1, 1, len(monthly_pivot), 1],
                'line': {'color': 'blue'},
            })
            chart1.set_title({'name': 'Spending per Month'})
            chart1.set_x_axis({'name': 'Month'})
            chart1.set_y_axis({'name': 'Amount'})
            writer.sheets['Monthly_Spending'].insert_chart('D2', chart1)

            # Add category spending chart
            chart2 = workbook.add_chart({'type': 'pie'})
            chart2.add_series({
                'name': 'Category Spending',
                'categories': ['Category_Spending', 1, 0, len(category_pivot), 0],
                'values': ['Category_Spending', 1, 1, len(category_pivot), 1],
            })
            chart2.set_title({'name': 'Spending by Category'})
            writer.sheets['Category_Spending'].insert_chart('D2', chart2)

        # Send file to user
        with open(filename, 'rb') as file:
            bot.send_document(
                chat_id, 
                file, 
                caption=f"Here's your {selected_type} history with charts as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

        # Clean up temporary file
        os.remove(filename)

    except Exception as e:
        logging.exception(str(e))
        bot.reply_to(message, f"An error occurred while generating the CSV: {str(e)}")
