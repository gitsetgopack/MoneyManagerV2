# DollarBot Email Sender

This document outlines the functionality of the Python script used for sending budget reports via email in the DollarBot application. The script employs the Gmail SMTP server to dispatch emails with attachments of budget reports.

## Functions and Methods

### send_email(user_email, subject, message, attachments)
This function sends an email to the specified user.

- **user_email**: The recipient's email address.
- **subject**: The subject of the email.
- **message**: The main body of the email, formatted in HTML.
- **attachments**: A list of paths to files that will be attached to the email.

### generate_spending_summary(user_data)
This function generates a spending summary using the Gemini API based on the user's financial data.

- **user_data**: The financial data provided by the user, structured as a list of dictionaries.

### create_spending_charts(df)
This function creates PDF charts for monthly and categorized spending from the provided DataFrame.

- **df**: A pandas DataFrame containing the user's financial data.

### save_data_to_excel(expense_data, income_data)
This function saves the user's expenses and income into an Excel file with separate sheets for each.

- **expense_data**: A list of expense records.
- **income_data**: A list of income records.

### run(message, bot)
This function initiates the main process, prompting the user to enter their email address.

- **message**: The message object from the bot containing the user's request.
- **bot**: A reference to the Telegram bot instance.

### process_email_input(message, bot)
This function processes the user's email input and sends the budget report.

- **message**: The message object containing the user's email input.
- **bot**: A reference to the Telegram bot instance.

## Main Workflow

1. The user is prompted to enter their email address.
2. User financial data is retrieved from the database, including income and expenses.
3. A spending summary is generated using the Gemini API.
4. Monthly and categorized spending charts are created as PDF files.
5. The data is saved to an Excel file.
6. The email is prepared with the summary and attached files.
7. The email is sent to the user.

## Variables

- **smtp_port**: The standard secure SMTP port (587).
- **smtp_server**: The Google SMTP server ("smtp.gmail.com").
- **email_from**: The sender's email address (DollarBot's email).
- **pswd**: The application password used to authenticate with Gmail.
- **msg**: The MIME multipart object to define email parts.
- **attachments**: A list of paths to the files to be attached.
- **TIE_server**: The SMTP server connection used for sending the email.

## Dependencies

The script relies on several libraries:
- `smtplib`: For sending emails using SMTP.
- `email.mime`: For creating email messages with attachments.
- `pandas`: For handling data in a DataFrame format.
- `matplotlib`: For creating visualizations of financial data.
- `extract`: A module for data extraction functionalities.
- `helper`: A module for user data retrieval.
- `gemini_helper`: A module for interacting with the Gemini API to generate summaries.

## Usage

1. Run the script. The bot will prompt the user to enter their email address.
2. The script retrieves user financial data and generates the spending summary and charts.
3. The generated charts and summary are sent as attachments to the provided email address.

**Important**: Ensure that the Gmail account is properly set up and that an application-specific password is created before using this script.

## Testing

The script includes logging to monitor the status of email sending and error handling to capture issues during execution.
