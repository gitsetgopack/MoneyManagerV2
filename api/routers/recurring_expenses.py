import datetime
from typing import Optional

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED  # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

from api.utils.auth import verify_token
from config import MONGO_URI

# MongoDB setup
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)
db = client.mmdb
users_collection = db.users
expenses_collection = db.expenses
accounts_collection = db.accounts
recurring_expenses_collection = db.recurring_expenses

# APScheduler setup
scheduler = BackgroundScheduler()

router = APIRouter(prefix="/recurring-expenses", tags=["Recurring Expenses"])


# Recurring Expense model for adding new recurring expenses
class RecurringExpenseCreate(BaseModel):
    amount: float
    currency: str
    category: str
    start_date: datetime.datetime
    frequency_days: int  # Number of days between each recurring expense
    account_name: str = "Checking"


# Helper function to add recurring expense
async def add_recurring_expense_to_db(user_id, expense_data):
    # Insert the recurring expense into the database
    result = await recurring_expenses_collection.insert_one(expense_data)
    return result.inserted_id


# Function to create a recurring expense (will be called by APScheduler)
async def create_recurring_expense(user_id, expense_data, account_name):
    # Fetch user and account data
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    account = await accounts_collection.find_one(
        {"user_id": user_id, "name": account_name}
    )
    if not account:
        raise HTTPException(status_code=400, detail="Invalid account")

    # Ensure the user has the currency in their account
    if expense_data.currency.upper() not in user["currencies"]:
        raise HTTPException(
            status_code=400,
            detail=f"Currency type not added to user account. Available currencies: {user['currencies']}",
        )

    # Check if the account has enough balance for the recurring expense
    converted_amount = convert_currency(
        expense_data.amount, expense_data.currency, account["currency"]
    )
    if account["balance"] < converted_amount:
        raise HTTPException(
            status_code=400, detail="Insufficient balance in the account"
        )

    # Deduct the amount from the account
    new_balance = account["balance"] - converted_amount
    await accounts_collection.update_one(
        {"_id": account["_id"]}, {"$set": {"balance": new_balance}}
    )

    # Prepare the expense data
    expense_data["user_id"] = user_id
    expense_data["date"] = datetime.datetime.now(datetime.timezone.utc)
    expense_data["account_name"] = account_name

    # Record the expense in the expenses collection
    await expenses_collection.insert_one(expense_data)

    return new_balance


# Add a recurring expense
@router.post("/")
async def add_recurring_expense(
    expense: RecurringExpenseCreate,
    token: str = Header(None),
    background_tasks: Optional[BackgroundTasks] = None,
):
    """
    Add a recurring expense that will be triggered periodically based on the start date and frequency.
    """
    user_id = await verify_token(token)

    # Fetch account info
    account = await accounts_collection.find_one(
        {"user_id": user_id, "name": expense.account_name}
    )
    if not account:
        raise HTTPException(status_code=400, detail="Invalid account name")

    # Validate that the currency is in the user's currencies
    if expense.currency.upper() not in account.get("currencies", []):
        raise HTTPException(status_code=400, detail="Invalid currency")

    # Prepare expense data
    expense_data = expense.dict()
    expense_data["currency"] = expense.currency.upper()

    # Insert the recurring expense into the database
    recurring_expense_id = await add_recurring_expense_to_db(user_id, expense_data)

    # Schedule the recurring expense
    start_date = expense.start_date
    frequency_days = expense.frequency_days
    job_id = f"recurring-expense-{recurring_expense_id}"

    # Add the job to the scheduler
    scheduler.add_job(
        create_recurring_expense,
        IntervalTrigger(days=frequency_days, start_date=start_date),
        args=[user_id, expense_data, expense.account_name],
        id=job_id,
        name="Recurring expense job",
    )

    scheduler.start()

    return {
        "message": "Recurring expense added successfully",
        "recurring_expense_id": str(recurring_expense_id),
        "next_trigger": start_date + datetime.timedelta(days=frequency_days),
    }


# Delete a recurring expense
@router.delete("/{recurring_expense_id}")
async def delete_recurring_expense(
    recurring_expense_id: str, token: str = Header(None)
):
    """
    Delete a recurring expense and cancel the scheduled task.
    """
    user_id = await verify_token(token)

    # Fetch the recurring expense
    recurring_expense = await recurring_expenses_collection.find_one(
        {"_id": ObjectId(recurring_expense_id)}
    )
    if not recurring_expense or recurring_expense["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    # Remove the recurring expense from the database
    await recurring_expenses_collection.delete_one(
        {"_id": ObjectId(recurring_expense_id)}
    )

    # Remove the scheduled job
    job_id = f"recurring-expense-{recurring_expense_id}"
    scheduler.remove_job(job_id)

    return {"message": "Recurring expense deleted successfully"}


# Update a recurring expense
@router.put("/{recurring_expense_id}")
async def update_recurring_expense(
    recurring_expense_id: str,
    expense_update: RecurringExpenseCreate,
    token: str = Header(None),
):
    """
    Update the details of a recurring expense.
    """
    user_id = await verify_token(token)

    # Fetch the recurring expense
    recurring_expense = await recurring_expenses_collection.find_one(
        {"_id": ObjectId(recurring_expense_id)}
    )
    if not recurring_expense or recurring_expense["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Recurring expense not found")

    # Cancel the old job
    job_id = f"recurring-expense-{recurring_expense_id}"
    scheduler.remove_job(job_id)

    # Update the recurring expense in the database
    expense_data = expense_update.dict()
    expense_data["currency"] = expense_update.currency.upper()
    await recurring_expenses_collection.update_one(
        {"_id": ObjectId(recurring_expense_id)}, {"$set": expense_data}
    )

    # Reschedule the updated recurring expense
    start_date = expense_update.start_date
    frequency_days = expense_update.frequency_days
    scheduler.add_job(
        create_recurring_expense,
        IntervalTrigger(days=frequency_days, start_date=start_date),
        args=[user_id, expense_data, expense_update.account_name],
        id=job_id,
        name="Recurring expense job",
    )

    return {"message": "Recurring expense updated successfully"}
