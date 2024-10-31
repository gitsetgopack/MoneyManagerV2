from unittest.mock import Mock, patch, ANY
from telebot import types
from code import pdf
from datetime import datetime

@patch('telebot.TeleBot')
def test_run_income_selection(mock_telebot, mocker):
    mc = mock_telebot.return_value
    mocker.patch.object(pdf.helper, 'getIncomeOrExpense', return_value={'1': 'Income', '2': 'Expense'})
    message = create_message("Choose Income or Expense")
    pdf.run(message, mc)
    assert mc.reply_to.called
    mc.reply_to.assert_called_with(message, 'Select Income or Expense', reply_markup=ANY)


@patch('telebot.TeleBot')
def test_post_type_selection_income_history(mock_telebot, mocker):
    mc = mock_telebot.return_value
    message = create_message("Income")
    mocker.patch.object(pdf.helper, 'read_json')
    mocker.patch.object(pdf.helper, 'getUserHistory', return_value=["2024-01-01 10:00:00,Salary,5000"])
    pdf.post_type_selection(message, mc)
    assert mc.send_message.called
    mc.send_message.assert_called_with(message.chat.id, "Enter start date (YYYY-MM-DD):")


@patch('telebot.TeleBot')
def test_get_end_date_with_data(mock_telebot, mocker):
    mc = mock_telebot.return_value
    message = create_message("2024-01-02")  
    selected_type = "Income"
    start_date = datetime.strptime("2024-01-01", "%Y-%m-%d")  
    mocker.patch.object(pdf.helper, 'getUserHistory', return_value=[
        "2024-01-01 10:00:00,Salary,5000",
        "2024-01-02 12:00:00,Freelance,1200"
    ])
    pdf.get_end_date(message, mc, selected_type, message.chat.id, start_date)
    assert mc.send_document.called

@patch('telebot.TeleBot')
def test_get_end_date_no_data(mock_telebot, mocker):
    mc = mock_telebot.return_value
    message = create_message("2024-01-02")  
    selected_type = "Income"
    start_date = datetime.strptime("2024-01-01", "%Y-%m-%d")  
    mocker.patch.object(pdf.helper, 'getUserHistory', return_value=[])
    pdf.get_end_date(message, mc, selected_type, message.chat.id, start_date)
    assert mc.send_message.called
    mc.send_message.assert_called_with(message.chat.id, "No Income records found between 2024-01-01 and 2024-01-02.")



@patch('telebot.TeleBot')
def test_generate_pdf_with_content(mock_telebot, mocker):
    mc = mock_telebot.return_value
    chat_id = 12345
    selected_type = "Income"
    user_history = [
        "2024-01-01 10:00:00,Salary,5000",
        "2024-01-02 12:00:00,Freelance,1200"
    ]
    pdf.generate_pdf(user_history, selected_type, chat_id, mc)
    assert mc.send_document.called
    args, kwargs = mc.send_document.call_args
    assert args[0] == chat_id
    assert args[1].name.endswith("history.pdf")


def create_message(text):
    params = {'messagebody': text}
    chat = types.User(11, False, 'test')
    message = types.Message(1, None, None, chat, 'text', params, "")
    message.text = text
    return message
