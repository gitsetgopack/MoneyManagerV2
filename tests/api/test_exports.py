import datetime
import pytest
from fastapi.testclient import TestClient
from bson import ObjectId
from api.app import app
from api.routers.exports import fetch_data

client = TestClient(app)

@pytest.fixture
def mock_db(monkeypatch):
    class MockCursor:
        def __init__(self, data):
            self.data = data

        async def to_list(self, length):
            return self.data

    class MockCollection:
        def __init__(self, data):
            self.data = data

        def find(self, query):
            return MockCursor(self.data)

        async def find_one(self, query):
            return self.data[0] if self.data else None

    expenses_data = [
        {
            "_id": ObjectId(),
            "user_id": ObjectId("507f1f77bcf86cd799439011"),
            "date": datetime.datetime(2023, 1, 1),
            "amount": 100,
            "currency": "USD",
            "category": "Food",
            "description": "Groceries",
            "account_name": "Checking",
        }
    ]
    accounts_data = [
        {
            "_id": ObjectId(),
            "user_id": ObjectId("507f1f77bcf86cd799439011"),
            "name": "Checking",
            "balance": 1000,
            "currency": "USD",
        }
    ]
    users_data = [
        {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "username": "test_user",
            "categories": {
                "Food": {"monthly_budget": 500},
            },
        }
    ]

    monkeypatch.setattr(
        "api.routers.exports.expenses_collection", MockCollection(expenses_data)
    )
    monkeypatch.setattr(
        "api.routers.exports.accounts_collection", MockCollection(accounts_data)
    )
    monkeypatch.setattr(
        "api.routers.exports.users_collection", MockCollection(users_data)
    )

@pytest.mark.anyio
async def test_fetch_data(mock_db):
    user_id = "507f1f77bcf86cd799439011"
    from_date = datetime.date(2023, 1, 1)
    to_date = datetime.date(2023, 1, 31)
    expenses, accounts, user = await fetch_data(user_id, from_date, to_date)
    assert len(expenses) == 1
    assert len(accounts) == 1
    assert user is not None

@pytest.mark.anyio
async def test_data_to_xlsx(mock_db, async_client_auth):
    response = await async_client_auth.get(
        "/exports/xlsx",
        params={"from_date": "2023-01-01", "to_date": "2023-01-31"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=data.xlsx"

@pytest.mark.anyio
async def test_data_to_csv_expenses(mock_db, async_client_auth):
    response = await async_client_auth.get(
        "/exports/csv",
        params={"export_type": "expenses", "from_date": "2023-01-01", "to_date": "2023-01-31"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=expenses.csv"

@pytest.mark.anyio
async def test_data_to_csv_accounts(mock_db, async_client_auth):
    response = await async_client_auth.get(
        "/exports/csv",
        params={"export_type": "accounts", "from_date": "2023-01-01", "to_date": "2023-01-31"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=accounts.csv"

@pytest.mark.anyio
async def test_data_to_csv_categories(mock_db, async_client_auth):
    response = await async_client_auth.get(
        "/exports/csv",
        params={"export_type": "categories", "from_date": "2023-01-01", "to_date": "2023-01-31"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=categories.csv"

@pytest.mark.anyio
async def test_data_to_pdf(mock_db, async_client_auth):
    response = await async_client_auth.get(
        "/exports/pdf",
        params={"from_date": "2023-01-01", "to_date": "2023-01-31"},
    )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
