import aiohttp
from config import config

class APIHelper:
    BASE_URL = config.TELEGRAM_BOT_API_BASE_URL  # Update to use correct base URL

    @staticmethod
    async def save_expense(user_id: int, expense_data: dict) -> dict:
        """Save expense via API following the existing pattern"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Content-Type": "application/json",
                "x-user-id": str(user_id)  # Updated to use correct header
            }
            
            # Format payload according to API expectations
            payload = {
                "amount": float(expense_data.get('total', 0)),
                "category_id": expense_data.get('category_id', 1),  # Default category ID
                "account_id": expense_data.get('account_id', 1),   # Default account ID
                "title": f"Receipt from {expense_data.get('store', 'Unknown Store')}",
                "description": f"Receipt purchase at {expense_data.get('store', 'Unknown Store')}",
                "date": expense_data.get('date'),
                "tags": ["receipt"]
            }

            try:
                async with session.post(
                    f"{APIHelper.BASE_URL}/expenses",  # Updated endpoint
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:  # Check for correct status code
                        return {"success": True, "data": await response.json()}
                    else:
                        error_data = await response.json()
                        return {"success": False, "message": error_data.get("message", "Failed to save expense")}
            except Exception as e:
                return {"success": False, "message": str(e)}