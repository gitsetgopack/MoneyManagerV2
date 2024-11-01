# DollarBot PDF Exporter

This document describes the functionality of the Python script used for exporting user financial data to a PDF file in the DollarBot application. The script allows users to select either income or expense records and specify a date range to filter the results before generating and sending the report.

## Functions and Methods

### run(message, bot)
This function initiates the process when the `/pdf` command is issued by the user.

- **message**: The message object received from the user.
- **bot**: A reference to the Telegram bot instance.

### post_type_selection(message, bot)
Handles the user's selection of either "Income" or "Expense" and prompts them for a start date.

- **message**: The message object containing the user's selection.
- **bot**: A reference to the Telegram bot instance.

### get_start_date(message, bot, selected_type)
Prompts the user to enter the start date of the date range and validates the input format.

- **message**: The message object from the user.
- **bot**: A reference to the Telegram bot instance.
- **selected_type**: The type of data the user selected (income or expense).

### get_end_date(message, bot, selected_type, start_date_obj)
Prompts the user to enter the end date and validates it against the start date.

- **message**: The message object from the user.
- **bot**: A reference to the Telegram bot instance.
- **selected_type**: The type of data the user selected (income or expense).
- **start_date_obj**: The validated start date as a datetime object.

### generate_pdf(chat_id, bot, selected_type, user_history, start_date_obj, end_date_obj)
Generates a PDF file containing filtered user financial records within the specified date range and sends it to the user.

- **chat_id**: The ID of the chat with the user.
- **bot**: A reference to the Telegram bot instance.
- **selected_type**: The type of data to be exported (income or expense).
- **user_history**: The complete financial history of the user.
- **start_date_obj**: The validated start date as a datetime object.
- **end_date_obj**: The validated end date as a datetime object.

## Main Workflow

1. The user invokes the `/pdf` command, prompting them to select either "Income" or "Expense."
2. The user is asked to enter a start date, which is validated for correct formatting.
3. The user is prompted for an end date, which is also validated against the start date.
4. The user's financial history is retrieved and filtered based on the specified date range.
5. A PDF file is generated containing the filtered data, displaying each record in a readable format.
6. The generated PDF is sent to the user via Telegram.

## Variables

- **markup**: A keyboard markup object used for creating reply buttons.
- **chat_id**: The ID of the chat with the user.
- **selected_type**: The type of financial data selected by the user (Income or Expense).
- **start_date_obj**: The start date entered by the user, validated as a datetime object.
- **end_date_obj**: The end date entered by the user, validated as a datetime object.
- **pdf_filename**: The name of the generated PDF file, including the user's chat ID.

## Dependencies

The script relies on several libraries:
- `helper`: A module that provides utility functions, including retrieving user history.
- `logging`: For logging error messages and debugging information.
- `telebot`: For interacting with the Telegram Bot API.
- `datetime`: For date handling and validation.
- `matplotlib`: For creating visual representations of data and generating PDF documents.

## Usage

1. Users can issue the `/pdf` command to start the export process.
2. They will select either income or expense records and enter the desired date range.
3. The bot will generate and send the filtered financial records in a PDF format.

**Note**: Ensure the bot has the necessary permissions to send messages and documents to users.

## Testing

The script includes logging to monitor actions taken during the export process and captures exceptions for troubleshooting.
