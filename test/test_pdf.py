import os
import json
from unittest.mock import patch, MagicMock, ANY
from datetime import datetime
from telebot import types
from code import pdf

date_format = "%Y-%m-%d"


@patch("telebot.telebot")
def test_run_working(mock_telebot, mocker):
    mc = mock_telebot.return_value
    mc.reply_to.return_value = True
    mocker.patch.object(pdf.helper, "getIncomeOrExpense", return_value={"1": "Income", "2": "Expense"})
    message = create_message("Start PDF generation test")
    
    pdf.run(message, mc)
    
    assert mc.reply_to.called
    mc.reply_to.assert_called_with(message, "Select Income or Expense", reply_markup=ANY)


@patch("telebot.telebot")
def test_post_type_selection_income_history(mock_telebot, mocker):
    mc = mock_telebot.return_value
    mc.reply_to.return_value = True
    mocker.patch.object(pdf.helper, "read_json", return_value={})
    
    message = create_message("Income")
    pdf.post_type_selection(message, mc)
    
    assert mc.reply_to.called
    mc.reply_to.assert_called_with(message, "Enter start date (YYYY-MM-DD):")


@patch("telebot.telebot")
def test_get_start_date_working(mock_telebot, mocker):
    mc = mock_telebot.return_value
    message = create_message("2024-01-01")
    
    pdf.get_start_date(message, mc, "Income", 12345)
    
    assert mc.reply_to.called
    mc.reply_to.assert_called_with(message, "Enter end date (YYYY-MM-DD):")


@patch("telebot.telebot")
def test_get_end_date_with_data(mock_telebot, mocker):
    mc = mock_telebot.return_value
    message = create_message("2024-01-15")
    start_date = datetime.strptime("2024-01-01", date_format)
    
    mocker.patch.object(pdf.helper, "getUserHistory", return_value=[
        "2024-01-01 10:00:00,Salary,5000",
        "2024-01-05 12:00:00,Freelance,1200"
    ])
    
    pdf.get_end_date(message, mc, "Income", 12345, start_date)
    
    assert mc.send_message.called
    mc.send_message.assert_called_with(12345, "Created a PDF of your Income history from 2024-01-01 to 2024-01-15!")


@patch("telebot.telebot")
def test_generate_pdf_with_content(mock_telebot, mocker):
    mc = mock_telebot.return_value
    chat_id = 12345
    user_history = [
        "2024-01-01 10:00:00,Salary,5000",
        "2024-01-05 12:00:00,Freelance,1200"
    ]
    
    mocker.patch("pdf.plt.savefig")  
    pdf.generate_pdf(user_history, "Income", chat_id, mc)
    
    assert mc.send_document.called
    args, kwargs = mc.send_document.call_args
    assert args[0] == chat_id
    assert args[1].name.endswith("history.pdf")


def create_message(text):
    """Helper function to create a mock message."""
    params = {"messagebody": text}
    chat = types.User(11, False, "test")
    return types.Message(1, None, None, chat, "text", params, "")
