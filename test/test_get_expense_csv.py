import os
import json
from telebot import types
from unittest.mock import patch, mock_open, ANY
import pytest
from datetime import datetime

# Import the module containing get_csv functionality
from code import get_csv

def create_message(text, chat_id=11):
    """Helper function to create a message object"""
    params = {'messagebody': text}
    chat = types.User(chat_id, False, 'test')
    return types.Message(1, None, None, chat, 'text', params, "")

@patch('telebot.telebot')
def test_run_initial_setup(mock_telebot, mocker):
    """Test the initial setup of CSV generation"""
    mc = mock_telebot.return_value
    mc.reply_to.return_value = True
    
    # Mock helper function
    mocker.patch.object(get_csv, 'helper')
    get_csv.helper.getIncomeOrExpense.return_value = {'1': 'Income', '2': 'Expense'}
    
    message = create_message("hello")
    get_csv.run(message, mc)
    
    # Verify bot interactions
    mc.reply_to.assert_called_with(message, 'Select Income or Expense', reply_markup=ANY)
    assert mc.register_next_step_handler.called

@patch('telebot.telebot')
def test_post_type_selection_with_expenses(mock_telebot, mocker):
    """Test CSV generation with existing expense records"""
    mc = mock_telebot.return_value
    test_chat_id = 894127939
    
    # Mock helper functions
    mocker.patch.object(get_csv, 'helper')
    get_csv.helper.read_json.return_value = True
    
    # Sample expense data
    test_expenses = [
        "19-Oct-2023 15:27,Food,2.3",
        "19-Oct-2023 15:28,Groceries,20.0",
        "19-Oct-2023 15:28,Utilities,10.0"
    ]
    get_csv.helper.getUserHistory.return_value = test_expenses
    
    # Create test message
    message = create_message("Expense", test_chat_id)
    
    # Mock file operations
    mock_csv = mock_open()
    with patch('builtins.open', mock_csv):
        get_csv.post_type_selection(message, mc)
    
    # Verify file operations and bot interactions
    assert mock_csv.call_count >= 2  # One for writing CSV, one for reading to send
    mc.send_document.assert_called_once()
    
    # Verify cleanup
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('os.remove') as mock_remove:
            get_csv.post_type_selection(message, mc)
            assert mock_remove.called

@patch('telebot.telebot')
def test_post_type_selection_no_expenses(mock_telebot, mocker):
    """Test CSV generation with no expense records"""
    mc = mock_telebot.return_value
    test_chat_id = 1574038305
    
    # Mock helper functions
    mocker.patch.object(get_csv, 'helper')
    get_csv.helper.read_json.return_value = True
    get_csv.helper.getUserHistory.return_value = []
    
    # Create test message
    message = create_message("Expense", test_chat_id)
    
    get_csv.post_type_selection(message, mc)
    
    # Verify bot sends "No records found" message
    mc.send_message.assert_called_with(test_chat_id, "No records found!")
    
    # Verify no file operations occurred
    mc.send_document.assert_not_called()

@patch('telebot.telebot')
def test_post_type_selection_malformed_record(mock_telebot, mocker):
    """Test CSV generation with malformed expense records"""
    mc = mock_telebot.return_value
    test_chat_id = 8941298739
    
    # Mock helper functions
    mocker.patch.object(get_csv, 'helper')
    get_csv.helper.read_json.return_value = True
    
    # Include a malformed record
    test_expenses = [
        "19-Oct-2023 15:27,Food,2.3",
        "malformed_record",  # This should be skipped
        "19-Oct-2023 15:28,Utilities,10.0"
    ]
    get_csv.helper.getUserHistory.return_value = test_expenses
    
    # Create test message
    message = create_message("Expense", test_chat_id)
    
    # Mock file operations
    mock_csv = mock_open()
    with patch('builtins.open', mock_csv):
        with patch('logging.warning') as mock_logging:
            get_csv.post_type_selection(message, mc)
            # Verify logging of malformed record
            assert mock_logging.called
    
    # Verify file was still created and sent
    mc.send_document.assert_called_once()

@patch('telebot.telebot')
def test_post_type_selection_file_error(mock_telebot, mocker):
    """Test CSV generation with file operation errors"""
    mc = mock_telebot.return_value
    test_chat_id = 894127939
    
    # Mock helper functions
    mocker.patch.object(get_csv, 'helper')
    get_csv.helper.read_json.return_value = True
    get_csv.helper.getUserHistory.return_value = ["19-Oct-2023 15:27,Food,2.3"]
    
    # Create test message
    message = create_message("Expense", test_chat_id)
    
    # Simulate file operation error
    with patch('builtins.open', side_effect=Exception("File error")):
        get_csv.post_type_selection(message, mc)
    
    # Verify error handling
    mc.reply_to.assert_called_with(message, ANY)