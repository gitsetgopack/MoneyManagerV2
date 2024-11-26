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
from api.utils.plots import (
    create_expense_bar, create_category_pie, create_monthly_line,
    create_category_bar, create_budget_vs_actual
)

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
    """Generate bar chart of daily expenses."""
    user_id = await verify_token(token)
    expenses, _, _ = await fetch_data(user_id, from_date, to_date)
    
    if not expenses:
        raise HTTPException(status_code=404, detail="No expenses found")
    
    buf = create_expense_bar(expenses, from_date, to_date)
    return Response(content=buf.getvalue(), media_type="image/png")

@router.get("/category/pie")
async def category_pie(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a pie chart of categories categorized by type.
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

    buf = create_category_pie(expenses, from_date, to_date)
    return Response(content=buf.getvalue(), media_type="image/png")

@router.get("/expense/line-monthly", response_class=Response)
async def expense_line_monthly(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a line chart of monthly expenses within a date range.
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

    buf = create_monthly_line(expenses, from_date, to_date)
    return Response(content=buf.getvalue(), media_type="image/png")

@router.get("/category/bar", response_class=Response)
async def category_bar(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a bar chart of expenses categorized by type within a date range.
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

    buf = create_category_bar(expenses, from_date, to_date)
    return Response(content=buf.getvalue(), media_type="image/png")

def prorate_budget(budget: float, from_date: Optional[datetime.date], to_date: Optional[datetime.date], first_expense_date: Optional[datetime.date], last_expense_date: Optional[datetime.date]) -> float:
    """Prorate the budget based on the date range."""
    if from_date and to_date:
        days_in_range = (to_date - from_date).days + 1
    elif from_date:
        days_in_range = (last_expense_date - from_date).days + 1 if last_expense_date else (datetime.date.today() - from_date).days + 1
    elif to_date:
        days_in_range = (to_date - first_expense_date).days + 1 if first_expense_date else (to_date - datetime.date(1970, 1, 1)).days + 1
    else:
        days_in_range = 30  # Default to 30 days if no date range is provided

    print(f"Prorating budget: {budget}, Days in range: {days_in_range}")
    return (budget / 30) * days_in_range

@router.get("/budget/actual-vs-budget", response_class=Response)
async def budget_vs_actual(
    from_date: Optional[datetime.date] = None,
    to_date: Optional[datetime.date] = None,
    token: str = Header(None)
):
    """
    Endpoint to generate a bar chart comparing budgeted vs actual expenses within a date range.
    Returns a PNG image file directly.
    """
    user_id = await verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    expenses, accounts, user = await fetch_data(user_id, from_date, to_date)

    if not expenses:
        raise HTTPException(
            status_code=404, detail="No expenses found for the specified period"
        )

    buf = create_budget_vs_actual(expenses, user["categories"], from_date, to_date)
    
    return Response(content=buf.getvalue(), media_type="image/png")
