import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from code import pdf  # Assuming pdf.py is the filename of the file you provided

class TestPDFGenerator(unittest.TestCase):

    @patch('pdf.helper.getIncomeOrExpense', return_value={'income': 'Income', 'expense': 'Expense'})
    def test_run_creates_markup_and_replies(self, mock_getIncomeOrExpense):
        bot = MagicMock()
        message = MagicMock()
        
        pdf.run(message, bot)
        
        bot.reply_to.assert_called_once_with(message, 'Select Income or Expense', reply_markup=MagicMock())
        bot.register_next_step_handler.assert_called_once()

    @patch('pdf.helper.getIncomeOrExpense', return_value={})
    def test_run_no_options(self, mock_getIncomeOrExpense):
        bot = MagicMock()
        message = MagicMock()
        
        pdf.run(message, bot)
        
        bot.reply_to.assert_called_once_with(message, 'Select Income or Expense', reply_markup=MagicMock())
        markup = bot.reply_to.call_args[1]['reply_markup']
        self.assertEqual(len(markup.keyboard), 0)

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

    @patch("pdf.plt.savefig")
    @patch("pdf.helper.getUserIncomeHistory", return_value=["2024-10-11 12:00:00,Salary,1000"])
    @patch("os.path.exists", return_value=True)
    @patch("builtins.open", new_callable=MagicMock)
    def test_generate_pdf_with_records(self, mock_open, mock_exists, mock_getUserIncomeHistory, mock_savefig):
        bot = MagicMock()
        user_history = ["2024-10-11 12:00:00,Salary,1000"]

        # Mock the file handle to be returned when open is called
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file

        result = pdf.generate_pdf(user_history, "Income", 12345, bot)

        # Assert that bot.send_document was called, which indicates file was "sent" successfully.
        bot.send_document.assert_called_once_with(12345, mock_file)
        self.assertEqual(result, "PDF generated and sent successfully!")

        # Check if plt.savefig was called with the correct path
        mock_savefig.assert_called_once_with("history_12345.pdf")
        
        # Ensure the mock file was opened in read-binary mode
        mock_open.assert_called_once_with("history_12345.pdf", "rb")


    def test_generate_pdf_no_records(self):
        bot = MagicMock()
        user_history = []
        
        result = pdf.generate_pdf(user_history, "Income", 12345, bot)
        
        bot.send_document.assert_not_called()
        self.assertEqual(result, "No records to generate a PDF.")

if __name__ == "__main__":
    unittest.main()
