"""
This module provides analytics endpoints for retrieving and visualizing
expense data. It includes routes to generate visualizations for expenses
from a specified number of days.
"""

import base64
import io
import datetime

from bson import ObjectId
import matplotlib.pyplot as plt
import pandas as pd
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from api.utils.auth import verify_token
from config.config import MONGO_URI

# MongoDB setup
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)
db = client.mmdb
users_collection = db.users
expenses_collection = db.expenses
accounts_collection = db.accounts

router = APIRouter(prefix="/analytics", tags=["Analytics"])




# Utility function to fetch data
async def fetch_data(
    user_id: str, from_date: Optional[datetime.date], to_date: Optional[datetime.date]
):
    """Fetch data from the database based on user ID and date range."""
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail="Invalid date range: 'from_date' must be before 'to_date'",
        )

    from_dt = (
        datetime.datetime.combine(from_date, datetime.time.min) if from_date else None
    )
    to_dt = datetime.datetime.combine(to_date, datetime.time.max) if to_date else None

    query = {"user_id": user_id}
    if from_dt and to_dt:
        query["date"] = {"$gte": from_dt, "$lte": to_dt}  # type: ignore
    elif from_dt:
        query["date"] = {"$gte": from_dt}  # type: ignore
    elif to_dt:
        query["date"] = {"$lte": to_dt}  # type: ignore

    expenses = await expenses_collection.find(query).to_list(1000)
    accounts = await accounts_collection.find({"user_id": user_id}).to_list(100)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    return expenses, accounts, user


@router.get("/expense/bar", response_class=HTMLResponse)
async def expense_bar(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a bar chart of daily expenses within a date range.
    Args:
        from_date (datetime.date, optional): Start date for expense data
        to_date (datetime.date, optional): End date for expense data
        token (str): Authorization token for user verification
    Returns:
        HTMLResponse: An HTML page displaying the bar chart.
    """
    user_id = await verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    expenses, _, _ = await fetch_data(user_id, from_date, to_date)

    if not expenses:
        raise HTTPException(
            status_code=404, detail="No expenses found for the specified period"
        )

    # Convert to DataFrame and process data
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    daily_expenses = df.groupby(df["date"].dt.date)["amount"].sum()

    # Plotting the bar graph
    plt.figure(figsize=(10, 6))
    ax = daily_expenses.plot(kind="bar", color="skyblue")
    date_range = f"from {from_date} to {to_date}" if from_date and to_date else "all time"
    plt.title(f"Total Expenses per Day ({date_range})")
    plt.xlabel("Date")
    plt.ylabel("Total Expense Amount")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Adding labels on top of each bar
    for i, value in enumerate(daily_expenses):
        ax.text(
            i,
            value + 0.5,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            color="black",
        )

    # Convert the plot to a base64-encoded image
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    image_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Return the HTML response with the embedded image
    return HTMLResponse(
        content=f"""
        <html>
            <head><title>Expense Bar Chart</title></head>
            <body>
                <h1>Total Expenses per Day ({date_range})</h1>
                <img src="data:image/png;base64,{image_data}" alt="Expense Bar Chart">
            </body>
        </html>
        """
    )


@router.get("/expense/pie", response_class=HTMLResponse)
async def expense_pie(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a pie chart of expenses categorized by type within a date range.
    Args:
        from_date (datetime.date, optional): Start date for expense data
        to_date (datetime.date, optional): End date for expense data
        token (str): Authorization token for user verification
    Returns:
        HTMLResponse: An HTML page displaying the pie chart.
    """
    user_id = await verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    expenses, _, _ = await fetch_data(user_id, from_date, to_date)

    if not expenses:
        raise HTTPException(
            status_code=404, detail="No expenses found for the specified period"
        )

    # Convert to DataFrame and process data
    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])

    # Group by category and sum the amounts
    category_expenses = df.groupby("category")["amount"].sum()

    # Plotting the pie chart
    plt.figure(figsize=(8, 8))
    date_range = f"from {from_date} to {to_date}" if from_date and to_date else "all time"
    plt.title(f"Expense Distribution by Category ({date_range})")
    plt.pie(
        category_expenses,
        labels=category_expenses.index.astype(str).tolist(),
        autopct="%1.1f%%",
        startangle=140,
        colors=["#FF9999", "#FF4D4D", "#FF0000"],
    )
    plt.axis("equal")  # Equal aspect ratio ensures that pie chart is circular.

    # Convert the plot to a base64-encoded image
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    image_data = base64.b64encode(buf.getvalue()).decode("utf-8")

    # Return the HTML response with the embedded image
    return HTMLResponse(
        content=f"""
        <html>
            <head><title>Expense Pie Chart</title></head>
            <body>
                <h1>Expense Distribution by Category ({date_range})</h1>
                <img src="data:image/png;base64,{image_data}" alt="Expense Pie Chart">
            </body>
        </html>
        """
    )
