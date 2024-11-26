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
from fastapi import APIRouter, Header, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse
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


@router.get("/expense/bar")
async def expense_bar(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a bar chart of daily expenses within a date range.
    Returns a PNG image file directly.
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

    # Send image directly from memory
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    
    return Response(content=buf.getvalue(), media_type="image/png")

@router.get("/expense/pie")
async def expense_pie(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a pie chart of expenses categorized by type.
    Returns a PNG image file directly.
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
    plt.title(f"Expense Distribution by Category ({date_range})", pad=20)  # Add padding below title

    # Define a visually appealing color palette
    colors = [
        '#2ecc71',  # emerald green
        '#3498db',  # bright blue
        '#9b59b6',  # amethyst purple
        '#e74c3c',  # alizarin red
        '#f1c40f',  # sunflower yellow
        '#1abc9c',  # turquoise
        '#e67e22',  # carrot orange
        '#34495e',  # wet asphalt
        '#7f8c8d',  # concrete gray
        '#16a085',  # green sea
    ]

    # Create custom labels with amounts
    labels = [
        f'{cat}\n(${amount:,.2f})'
        for cat, amount in category_expenses.items()
    ]

    plt.pie(
        category_expenses,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors,
    )
    plt.axis("equal")  # Equal aspect ratio ensures that pie chart is circular.

    # Send image directly from memory
    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    plt.close()
    buf.seek(0)
    
    return Response(content=buf.getvalue(), media_type="image/png")
