
# About MyDollarBot's /scanreceipt Feature
This feature enables the user to scan a receipt and automatically add an expense entry to their expense tracker. It integrates with an OCR service (Gemini API) to extract key details—like date, amount, and category—from the receipt image.

After the details are extracted, the user can review and confirm or edit the entry. If confirmed, the bot stores the expense entry in the tracker, making it easy to log expenses with minimal manual input.

# Location of Code for this Feature
The code that implements this feature can be found [here](https://github.com/CSC510SEFALL2024/MyDollarBot-BOTGo/blob/main/code/scan_receipt.py).

# Code Description
## Functions

1. **run(message, bot)**:
   - Initiates the receipt scanning process by prompting the user to send a receipt photo. 
   - Takes **message** (the user's message) and **bot** (the Telegram bot instance) as arguments.

2. **handle_receipt_image(message, bot)**:
   - Manages the uploaded receipt image.
   - Validates the image file, retrieves it from Telegram’s servers, and sends it to the Gemini API for data extraction.
   - If the receipt data (date, amount, category) is valid, stores this data temporarily in `receipt_data` and saves it permanently using `add_user_record`.
   - Ends the process if the uploaded image is invalid.
   - Takes **message** and **bot** as arguments.

3. **show_receipt_details(message, bot)**:
   - Displays extracted receipt details (date, amount, and category) to the user with options to edit, add, or cancel.
   - Constructs an inline keyboard with buttons for each option.
   - Takes **message** and **bot** as arguments.

4. **add_user_record(chat_id, record_to_be_added)**:
   - Saves the receipt information in a structured format to a JSON file for persistent storage.
   - Takes **chat_id** (user’s chat ID) and **record_to_be_added** (the expense record) as arguments.
   - Ensures a new user record is created if the user does not already exist, formats the data, and appends it to the JSON file.
   - Confirms successful addition with a message that includes receipt details.

# How to Run This Feature
Once the project is running (see README.md for setup instructions), type `/scanreceipt` into the Telegram bot.

Below is an example in text format:

**User**:
`/scanreceipt`

**Bot**:
"Please send me a photo of your receipt."

**User**: *(Uploads a receipt image)*

**Bot**:
"Receipt Details:
Date: 15-Mar-2023
Amount: $45.67
Category: Groceries"

- **Edit** | **Add Transaction** | **Cancel**
