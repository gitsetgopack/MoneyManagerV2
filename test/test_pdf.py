import unittest
from unittest.mock import MagicMock, patch
from telebot import types
from datetime import datetime
from code import pdf  # Assuming pdf.py is the filename of the file you provided

class TestPDFGenerator(unittest.TestCase):

    @patch('pdf.helper.getIncomeOrExpense', return_value={})
    def test_run_no_options(self, mock_getIncomeOrExpense):
        bot = MagicMock()
        message = MagicMock()
        
        # Call the run function
        pdf.run(message, bot)
        
        # Check that reply_to was called with the "No options available." message
        bot.reply_to.assert_called_once_with(message, 'No options available.')

    @patch('pdf.helper.read_json')
    def test_post_type_selection_valid_type(self, mock_read_json):
        bot = MagicMock()
        message = MagicMock()
        message.text = "Income"
        message.chat.id = 12345
        
        pdf.post_type_selection(message, bot)
        
        bot.reply_to.assert_called_once_with(message, "Enter start date (YYYY-MM-DD):")
        bot.register_next_step_handler.assert_called_once()

    @patch("pdf.helper.read_json", side_effect=Exception("Test Exception"))
    def test_post_type_selection_invalid_type(self, mock_read_json):
        bot = MagicMock()
        message = MagicMock()
        message.chat.id = 12345
        message.text = "InvalidType"

        # Call the function and capture the result
        result = pdf.post_type_selection(message, bot)

        # Assert that the result contains the exception message
        self.assertIn("Test Exception", result)
        # Ensure reply_to was never called due to the exception
        bot.reply_to.assert_not_called()

    def test_get_start_date_valid_date(self):
        bot = MagicMock()
        message = MagicMock()
        message.text = "2024-10-10"
        start_date = datetime.strptime("2024-10-10", "%Y-%m-%d")
        
        pdf.get_start_date(message, bot, "Income", 12345)
        
        bot.reply_to.assert_called_once_with(message, "Enter end date (YYYY-MM-DD):")
        bot.register_next_step_handler.assert_called_once()

    def test_get_start_date_invalid_date_format(self):
        bot = MagicMock()
        message = MagicMock()
        message.text = "invalid-date"
        
        result = pdf.get_start_date(message, bot, "Income", 12345)
        
        self.assertEqual(result, "Invalid date format. Please use YYYY-MM-DD.")

    @patch('pdf.helper.getUserHistory', return_value=["2024-10-11 12:00:00,Salary,1000"])
    def test_get_end_date_valid_dates_with_records(self, mock_getUserHistory):
        bot = MagicMock()
        message = MagicMock()
        message.text = "2024-10-12"
        start_date = datetime.strptime("2024-10-10", "%Y-%m-%d")
        
        result = pdf.get_end_date(message, bot, "Income", 12345, start_date)
        
        bot.send_document.assert_called_once()
        self.assertEqual(result, "PDF generated and sent successfully!")

    def test_get_end_date_invalid_date_format(self):
        bot = MagicMock()
        message = MagicMock()
        message.text = "invalid-date"
        start_date = datetime.strptime("2024-10-10", "%Y-%m-%d")
        
        result = pdf.get_end_date(message, bot, "Income", 12345, start_date)
        
        self.assertEqual(result, "Invalid date format. Please use YYYY-MM-DD.")

    def test_generate_pdf_no_records(self):
        bot = MagicMock()
        user_history = []
        
        result = pdf.generate_pdf(user_history, "Income", 12345, bot)
        
        bot.send_document.assert_not_called()
        self.assertEqual(result, "No records to generate a PDF.")

if __name__ == "__main__":
    unittest.main()
