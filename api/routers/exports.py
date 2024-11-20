import csv
from io import BytesIO, StringIO
from fastapi import APIRouter, Header, HTTPException, Response, Query
from enum import Enum
from bson import ObjectId
from api.utils.auth import verify_token
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI
from openpyxl import Workbook

router = APIRouter(prefix="/exports", tags=["Export"])

# MongoDB setup
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)
db = client.mmdb
expenses_collection = db.expenses
accounts_collection = db.accounts
users_collection = db.users

class ExportType(str, Enum):
    expenses = "expenses"
    accounts = "accounts"
    categories = "categories"

@router.get("/xlsx")
async def data_to_xlsx(token: str = Header(None)):
    """
    Export all expenses, accounts, and categories for a user to an XLSX file.

    Args:
        token (str): Authentication token.

    Returns:
        Response: XLSX file containing expenses, accounts, and categories data.
    """
    user_id = await verify_token(token)
    expenses = await expenses_collection.find({"user_id": user_id}).to_list(1000)
    accounts = await accounts_collection.find({"user_id": user_id}).to_list(100)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not expenses and not accounts and not user:
        raise HTTPException(status_code=404, detail="No data found")

    workbook = Workbook()
    
    # Write expenses
    expenses_sheet = workbook.active
    expenses_sheet.title = "Expenses"
    expenses_sheet.append(["date", "amount", "currency", "category", "description", "account_name", "_id"])
    for expense in expenses:
        expenses_sheet.append([
            expense["date"].isoformat() if expense.get("date") else "",
            expense["amount"],
            expense["currency"],
            expense["category"],
            expense.get("description", ""),
            expense["account_name"],
            str(expense["_id"])
        ])

    # Write accounts
    accounts_sheet = workbook.create_sheet(title="Accounts")
    accounts_sheet.append(["name", "balance", "currency", "_id"])
    for account in accounts:
        accounts_sheet.append([
            account["name"],
            account["balance"],
            account["currency"],
            str(account["_id"])
        ])

    # Write categories
    categories_sheet = workbook.create_sheet(title="Categories")
    categories_sheet.append(["name", "monthly_budget"])
    if user and "categories" in user:
        for category_name, category_data in user["categories"].items():
            categories_sheet.append([
                category_name,
                category_data["monthly_budget"]
            ])

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response.headers["Content-Disposition"] = "attachment; filename=data.xlsx"
    return response

@router.get("/csv")
async def data_to_csv(token: str = Header(None), export_type: ExportType = Query(...)):
    """
    Export expenses, accounts, or categories for a user to a CSV file.

    Args:
        token (str): Authentication token.
        export_type (ExportType): Type of data to export (expenses, accounts, categories).

    Returns:
        Response: CSV file containing the selected data.
    """
    user_id = await verify_token(token)
    output = StringIO()
    writer = csv.writer(output)

    if export_type == ExportType.expenses:
        expenses = await expenses_collection.find({"user_id": user_id}).to_list(1000)
        if not expenses:
            raise HTTPException(status_code=404, detail="No expenses found")
        writer.writerow(["date", "amount", "currency", "category", "description", "account_name", "_id"])
        for expense in expenses:
            writer.writerow([
                expense["date"].isoformat() if expense.get("date") else "",
                expense["amount"],
                expense["currency"],
                expense["category"],
                expense.get("description", ""),
                expense["account_name"],
                str(expense["_id"])
            ])
    elif export_type == ExportType.accounts:
        accounts = await accounts_collection.find({"user_id": user_id}).to_list(100)
        if not accounts:
            raise HTTPException(status_code=404, detail="No accounts found")
        writer.writerow(["name", "balance", "currency", "_id"])
        for account in accounts:
            writer.writerow([
                account["name"],
                account["balance"],
                account["currency"],
                str(account["_id"])
            ])
    elif export_type == ExportType.categories:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user or "categories" not in user:
            raise HTTPException(status_code=404, detail="No categories found")
        writer.writerow(["name", "monthly_budget"])
        for category_name, category_data in user["categories"].items():
            writer.writerow([
                category_name,
                category_data["monthly_budget"]
            ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename={export_type.value}.csv"
    return response
