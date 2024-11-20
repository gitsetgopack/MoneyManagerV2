import csv
from io import StringIO
from fastapi import APIRouter, Header, HTTPException, Response
from bson import ObjectId
from api.utils.auth import verify_token
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI

router = APIRouter(prefix="/export", tags=["Export"])

# MongoDB setup
client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_URI)
db = client.mmdb
expenses_collection = db.expenses

@router.get("/expenses/csv")
async def export_expenses_to_csv(token: str = Header(None)):
    """
    Export all expenses for a user to a CSV file.

    Args:
        token (str): Authentication token.

    Returns:
        Response: CSV file containing expenses data.
    """
    user_id = await verify_token(token)
    expenses = await expenses_collection.find({"user_id": user_id}).to_list(1000)

    if not expenses:
        raise HTTPException(status_code=404, detail="No expenses found")

    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "amount", "currency", "category", "description", "account_name", "_id"])

    for expense in expenses:
        writer.writerow([
            str(expense["_id"]),
            expense["amount"],
            expense["currency"],
            expense["category"],
            expense.get("description", ""),
            expense["account_name"],
            expense["date"].isoformat() if expense.get("date") else ""
        ])

    response = Response(content=output.getvalue(), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"
    return response
