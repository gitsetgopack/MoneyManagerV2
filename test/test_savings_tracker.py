from code import savings_tracker
from code.helper import *
from unittest.mock import Mock, patch
from datetime import datetime
from telebot import types

MOCK_CHAT_ID = 101

def create_message(text):
    params = {'messagebody': text}
    chat = types.User(MOCK_CHAT_ID, False, 'test_user')
    # Create the message and set the text attribute directly
    message = types.Message(1, None, None, chat, 'text', params, "")
    message.text = text  # Set the text content for the message
    return message



@patch('code.savings_tracker.helper.set_max_expenditure_limit')
def test_set_limit_valid_amount(mock_set_limit):
    message = create_message("500")
    bot = Mock()
    
    savings_tracker.set_limit(message, bot)
    
    bot.send_message.assert_called_with(MOCK_CHAT_ID, "Got it! Now, please enter the start date for this limit (format: DD-MM-YYYY):")
    assert mock_set_limit.called == False  # Should not call `set_max_expenditure_limit` yet


def test_set_limit_invalid_amount():
    message = create_message("invalid_amount")
    bot = Mock()
    
    savings_tracker.set_limit(message, bot)
    
    bot.send_message.assert_called_with(MOCK_CHAT_ID, "Please enter a valid number for the expenditure limit.")


@patch('code.savings_tracker.datetime')
def test_set_start_date_valid(mock_datetime):
    mock_datetime.strptime.return_value = datetime(2024, 10, 1)
    message = create_message("01-10-2024")
    bot = Mock()
    limit = 500
    
    savings_tracker.set_start_date(message, bot, limit)
    
    bot.send_message.assert_called_with(MOCK_CHAT_ID, "Now, please enter the end date for this limit (format: DD-MM-YYYY):")


def test_set_start_date_invalid_format():
    message = create_message("invalid_date")
    bot = Mock()
    limit = 500
    
    savings_tracker.set_start_date(message, bot, limit)
    
    bot.send_message.assert_called_with(MOCK_CHAT_ID, "Please enter a valid date in DD-MM-YYYY format.")


@patch('code.savings_tracker.datetime')
def test_set_end_date_valid(mock_datetime):
    mock_datetime.strptime.return_value = datetime(2024, 11, 1)
    message = create_message("01-11-2024")
    bot = Mock()
    limit = 500
    start_date = datetime(2024, 10, 1)
    
    with patch('code.savings_tracker.helper.set_max_expenditure_limit') as mock_set_limit:
        savings_tracker.set_end_date(message, bot, limit, start_date)
        
        time_frame = "01-Oct-2024 to 01-Nov-2024"
        mock_set_limit.assert_called_once_with(MOCK_CHAT_ID, limit, time_frame)
        bot.send_message.assert_called_with(MOCK_CHAT_ID, f"Your savings goal has been set with a limit of {limit} from {time_frame}.")


def test_set_end_date_invalid_format():
    message = create_message("invalid_date")
    bot = Mock()
    limit = 500
    start_date = datetime(2024, 10, 1)
    
    savings_tracker.set_end_date(message, bot, limit, start_date)
    
    bot.send_message.assert_called_with(MOCK_CHAT_ID, "Please enter a valid date in DD-MM-YYYY format.")


def test_set_end_date_before_start_date():
    message = create_message("30-09-2024")
    bot = Mock()
    limit = 500
    start_date = datetime(2024, 10, 1)
    
    savings_tracker.set_end_date(message, bot, limit, start_date)
    
    bot.send_message.assert_called_with(MOCK_CHAT_ID, "End date cannot be before the start date. Please try again.")


@patch('code.savings_tracker.helper.set_max_expenditure_limit')
def test_end_to_end_savings_tracker(mock_set_limit):
    bot = Mock()
    
    # Mock initial user prompt with limit input
    limit_message = create_message("500")
    savings_tracker.set_limit(limit_message, bot)
    bot.send_message.assert_any_call(MOCK_CHAT_ID, "Got it! Now, please enter the start date for this limit (format: DD-MM-YYYY):")
    
    # Mock start date input
    start_date_message = create_message("01-10-2024")
    savings_tracker.set_start_date(start_date_message, bot, 500)
    bot.send_message.assert_any_call(MOCK_CHAT_ID, "Now, please enter the end date for this limit (format: DD-MM-YYYY):")
    
    # Mock end date input
    end_date_message = create_message("01-11-2024")
    savings_tracker.set_end_date(end_date_message, bot, 500, datetime(2024, 10, 1))
    
    # Verify set_max_expenditure_limit call
    mock_set_limit.assert_called_once_with(MOCK_CHAT_ID, 500, "01-Oct-2024 to 01-Nov-2024")


@patch('code.savings_tracker.helper.set_max_expenditure_limit')
def test_savings_tracker_limit_already_set(mock_set_limit):
    bot = Mock()
    
    message = create_message("500")
    savings_tracker.set_limit(message, bot)
    bot.send_message.assert_any_call(MOCK_CHAT_ID, "Got it! Now, please enter the start date for this limit (format: DD-MM-YYYY):")
    
    # Mock start date input
    start_date_message = create_message("01-10-2024")
    savings_tracker.set_start_date(start_date_message, bot, 500)
    
    # Mock end date input that matches start
    end_date_message = create_message("01-11-2024")
    savings_tracker.set_end_date(end_date_message, bot, 500, datetime(2024, 10, 1))
    
    # Ensure the helper is only called once
    mock_set_limit.assert_called_once_with(MOCK_CHAT_ID, 500, "01-Oct-2024 to 01-Nov-2024")

