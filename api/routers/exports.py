import csv
from enum import Enum
from io import BytesIO, StringIO
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Header, HTTPException, Query, Response
from motor.motor_asyncio import AsyncIOMotorClient
from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet
from reportlab.lib import colors  # type: ignore
from reportlab.lib.pagesizes import letter  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.platypus import (  # type: ignore
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tables import CellStyle  # type: ignore

from api.utils.auth import verify_token
from config import MONGO_URI

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
async def data_to_xlsx(token: str = Header(None)) -> Response:
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
    expenses_sheet: Optional[Worksheet] = workbook.active
    if expenses_sheet is not None:
        expenses_sheet.title = "Expenses"
        expenses_sheet.append(
            [
                "date",
                "amount",
                "currency",
                "category",
                "description",
                "account_name",
                "_id",
            ]
        )
        for expense in expenses:
            expenses_sheet.append(
                [
                    expense["date"].isoformat() if expense.get("date") else "",
                    expense["amount"],
                    expense["currency"],
                    expense["category"],
                    expense.get("description", ""),
                    expense["account_name"],
                    str(expense["_id"]),
                ]
            )

    # Write accounts
    accounts_sheet: Optional[Worksheet] = workbook.create_sheet(title="Accounts")
    if accounts_sheet is not None:
        accounts_sheet.append(["name", "balance", "currency", "_id"])
        for account in accounts:
            accounts_sheet.append(
                [
                    account["name"],
                    account["balance"],
                    account["currency"],
                    str(account["_id"]),
                ]
            )

    # Write categories
    categories_sheet: Optional[Worksheet] = workbook.create_sheet(title="Categories")
    if categories_sheet is not None:
        categories_sheet.append(["name", "monthly_budget"])
        if user and "categories" in user:
            for category_name, category_data in user["categories"].items():
                categories_sheet.append(
                    [category_name, category_data["monthly_budget"]]
                )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    response = Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.headers["Content-Disposition"] = "attachment; filename=data.xlsx"
    return response


@router.get("/csv")
async def data_to_csv(
    token: str = Header(None), export_type: ExportType = Query(...)
) -> Response:
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
        writer.writerow(
            [
                "date",
                "amount",
                "currency",
                "category",
                "description",
                "account_name",
                "_id",
            ]
        )
        for expense in expenses:
            writer.writerow(
                [
                    expense["date"].isoformat() if expense.get("date") else "",
                    expense["amount"],
                    expense["currency"],
                    expense["category"],
                    expense.get("description", ""),
                    expense["account_name"],
                    str(expense["_id"]),
                ]
            )
    elif export_type == ExportType.accounts:
        accounts = await accounts_collection.find({"user_id": user_id}).to_list(100)
        if not accounts:
            raise HTTPException(status_code=404, detail="No accounts found")
        writer.writerow(["name", "balance", "currency", "_id"])
        for account in accounts:
            writer.writerow(
                [
                    account["name"],
                    account["balance"],
                    account["currency"],
                    str(account["_id"]),
                ]
            )
    elif export_type == ExportType.categories:
        user = await users_collection.find_one({"_id": ObjectId(user_id)})
        if not user or "categories" not in user:
            raise HTTPException(status_code=404, detail="No categories found")
        writer.writerow(["name", "monthly_budget"])
        for category_name, category_data in user["categories"].items():
            writer.writerow([category_name, category_data["monthly_budget"]])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers[
        "Content-Disposition"
    ] = f"attachment; filename={export_type.value}.csv"
    return response


@router.get("/pdf")
async def data_to_pdf(token: str = Header(None)) -> Response:
    """
    Export all expenses, accounts, and categories for a user to a PDF file.

    Args:
        token (str): Authentication token.

    Returns:
        Response: PDF file containing expenses, accounts, and categories data.
    """
    user_id = await verify_token(token)
    expenses = await expenses_collection.find({"user_id": user_id}).to_list(1000)
    accounts = await accounts_collection.find({"user_id": user_id}).to_list(100)
    user = await users_collection.find_one({"_id": ObjectId(user_id)})

    if not expenses and not accounts and not user:
        raise HTTPException(status_code=404, detail="No data found")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Table of Contents
    elements.append(Paragraph("Table of Contents", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph("1. Expenses", styles["Normal"]))
    elements.append(Paragraph("2. Accounts", styles["Normal"]))
    elements.append(Paragraph("3. Categories", styles["Normal"]))
    elements.append(PageBreak())

    # Helper function to wrap text in table cells
    def wrap_text(data):
        wrapped_data = []
        for row in data:
            wrapped_row = []
            for cell in row:
                wrapped_row.append(Paragraph(str(cell), styles["Normal"]))
            wrapped_data.append(wrapped_row)
        return wrapped_data

    # Expenses
    elements.append(Paragraph("Expenses", styles["Title"]))
    elements.append(Spacer(1, 12))
    expenses_data = [
        ["Date", "Amount", "Currency", "Category", "Description", "Account Name", "ID"]
    ]
    for expense in expenses:
        expenses_data.append(
            [
                expense["date"].isoformat() if expense.get("date") else "",
                expense["amount"],
                expense["currency"],
                expense["category"],
                expense.get("description", ""),
                expense["account_name"],
                str(expense["_id"]),
            ]
        )
    expenses_table = Table(
        wrap_text(expenses_data), colWidths=[60, 60, 60, 60, 120, 80, 80]
    )
    expenses_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(expenses_table)
    elements.append(PageBreak())

    # Accounts
    elements.append(Paragraph("Accounts", styles["Title"]))
    elements.append(Spacer(1, 12))
    accounts_data = [["Name", "Balance", "Currency", "ID"]]
    for account in accounts:
        accounts_data.append(
            [
                account["name"],
                account["balance"],
                account["currency"],
                str(account["_id"]),
            ]
        )
    accounts_table = Table(wrap_text(accounts_data), colWidths=[100, 100, 100, 100])
    accounts_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(accounts_table)
    elements.append(PageBreak())

    # Categories
    elements.append(Paragraph("Categories", styles["Title"]))
    elements.append(Spacer(1, 12))
    categories_data = [["Name", "Monthly Budget"]]
    if user and "categories" in user:
        for category_name, category_data in user["categories"].items():
            categories_data.append([category_name, category_data["monthly_budget"]])
    categories_table = Table(wrap_text(categories_data), colWidths=[200, 200])
    categories_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(categories_table)

    doc.build(elements)
    buffer.seek(0)

    response = Response(content=buffer.getvalue(), media_type="application/pdf")
    response.headers["Content-Disposition"] = "attachment; filename=data.pdf"
    return response
