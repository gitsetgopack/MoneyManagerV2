import datetime

import pytest
from bson import ObjectId
from fastapi import HTTPException
from fastapi.testclient import TestClient

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


@pytest.fixture
def mock_db_no_data(monkeypatch):
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
            return None

    monkeypatch.setattr("api.routers.exports.expenses_collection", MockCollection([]))
    monkeypatch.setattr("api.routers.exports.accounts_collection", MockCollection([]))
    monkeypatch.setattr("api.routers.exports.users_collection", MockCollection([]))


@pytest.fixture
def mock_db_no_accounts(monkeypatch):
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
    monkeypatch.setattr("api.routers.exports.accounts_collection", MockCollection([]))
    monkeypatch.setattr(
        "api.routers.exports.users_collection", MockCollection(users_data)
    )


@pytest.fixture
def mock_db_no_categories(monkeypatch):
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
class TestFetchData:
    async def test_fetch_data(self, mock_db):
        user_id = "507f1f77bcf86cd799439011"
        from_date = datetime.date(2023, 1, 1)
        to_date = datetime.date(2023, 1, 31)
        expenses, accounts, user = await fetch_data(user_id, from_date, to_date)
        assert len(expenses) == 1
        assert len(accounts) == 1
        assert user is not None

    async def test_fetch_data_no_date_range(self, mock_db):
        user_id = "507f1f77bcf86cd799439011"
        expenses, accounts, user = await fetch_data(user_id, None, None)
        assert len(expenses) == 1
        assert len(accounts) == 1
        assert user is not None

    async def test_fetch_data_only_from_date(self, mock_db):
        user_id = "507f1f77bcf86cd799439011"
        from_date = datetime.date(2023, 1, 1)
        expenses, accounts, user = await fetch_data(user_id, from_date, None)
        assert len(expenses) == 1
        assert len(accounts) == 1
        assert user is not None

    async def test_fetch_data_only_to_date(self, mock_db):
        user_id = "507f1f77bcf86cd799439011"
        to_date = datetime.date(2023, 1, 31)
        expenses, accounts, user = await fetch_data(user_id, None, to_date)
        assert len(expenses) == 1
        assert len(accounts) == 1
        assert user is not None

    async def test_fetch_data_invalid_date_range(self, mock_db):
        user_id = "507f1f77bcf86cd799439011"
        from_date = datetime.date(2023, 1, 31)
        to_date = datetime.date(2023, 1, 1)
        with pytest.raises(HTTPException) as exc_info:
            await fetch_data(user_id, from_date, to_date)
        assert exc_info.value.status_code == 422
        assert (
            exc_info.value.detail
            == "Invalid date range: 'from_date' must be before 'to_date'"
        )

    async def test_fetch_data_same_from_to_date(self, mock_db):
        user_id = "507f1f77bcf86cd799439011"
        from_date = datetime.date(2023, 1, 1)
        to_date = datetime.date(2023, 1, 1)
        expenses, accounts, user = await fetch_data(user_id, from_date, to_date)
        assert len(expenses) == 1
        assert len(accounts) == 1
        assert user is not None


@pytest.mark.anyio
class TestXLSXExport:
    async def test_data_to_xlsx(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/xlsx",
            params={"from_date": "2023-01-01", "to_date": "2023-01-31"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.xlsx"
        )

    async def test_data_to_xlsx_no_data(self, mock_db_no_data, async_client_auth):
        response = await async_client_auth.get(
            "/exports/xlsx",
            params={"from_date": "2024-01-01", "to_date": "2024-01-31"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No data found"

    async def test_data_to_xlsx_no_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get("/exports/xlsx")
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.xlsx"
        )

    async def test_data_to_xlsx_only_from_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/xlsx",
            params={"from_date": "2023-01-01"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.xlsx"
        )

    async def test_data_to_xlsx_only_to_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/xlsx",
            params={"to_date": "2023-01-31"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.xlsx"
        )

    async def test_data_to_xlsx_same_from_to_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/xlsx",
            params={"from_date": "2023-01-01", "to_date": "2023-01-01"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.xlsx"
        )

    async def test_data_to_xlsx_invalid_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/xlsx",
            params={"from_date": "2023-01-31", "to_date": "2023-01-01"},
        )
        assert response.status_code == 422


@pytest.mark.anyio
class TestCSVExport:
    async def test_data_to_csv_expenses(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "expenses",
                "from_date": "2023-01-01",
                "to_date": "2023-01-31",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=expenses.csv"
        )

    async def test_data_to_csv_accounts(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "accounts",
                "from_date": "2023-01-01",
                "to_date": "2023-01-31",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=accounts.csv"
        )

    async def test_data_to_csv_categories(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "categories",
                "from_date": "2023-01-01",
                "to_date": "2023-01-31",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=categories.csv"
        )

    async def test_data_to_csv_no_data(self, mock_db_no_data, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "expenses",
                "from_date": "2024-01-01",
                "to_date": "2024-01-31",
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No expenses found"

    async def test_data_to_csv_no_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={"export_type": "expenses"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=expenses.csv"
        )

    async def test_data_to_csv_only_from_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={"export_type": "expenses", "from_date": "2023-01-01"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=expenses.csv"
        )

    async def test_data_to_csv_only_to_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={"export_type": "expenses", "to_date": "2023-01-31"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=expenses.csv"
        )

    async def test_data_to_csv_same_from_to_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "expenses",
                "from_date": "2023-01-01",
                "to_date": "2023-01-01",
            },
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == "attachment; filename=expenses.csv"
        )

    async def test_data_to_csv_no_accounts(
        self, mock_db_no_accounts, async_client_auth
    ):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "accounts",
                "from_date": "2023-01-01",
                "to_date": "2023-01-31",
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No accounts found"

    async def test_data_to_csv_no_categories(
        self, mock_db_no_categories, async_client_auth
    ):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "categories",
                "from_date": "2023-01-01",
                "to_date": "2023-01-31",
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No categories found"

    async def test_data_to_csv_invalid_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/csv",
            params={
                "export_type": "expenses",
                "from_date": "2023-01-31",
                "to_date": "2023-01-01",
            },
        )
        assert response.status_code == 422


@pytest.mark.anyio
class TestPDFExport:
    async def test_data_to_pdf(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"from_date": "2023-01-01", "to_date": "2023-01-31"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
        )

    async def test_data_to_pdf_no_data(self, mock_db_no_data, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"from_date": "2024-01-01", "to_date": "2024-01-31"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No data found"

    async def test_data_to_pdf_no_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get("/exports/pdf")
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
        )

    async def test_data_to_pdf_only_from_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"from_date": "2023-01-01"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
        )

    async def test_data_to_pdf_only_to_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"to_date": "2023-01-31"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
        )

    async def test_data_to_pdf_large_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"from_date": "2020-01-01", "to_date": "2023-12-31"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
        )

    async def test_data_to_pdf_invalid_date_range(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"from_date": "2023-01-31", "to_date": "2023-01-01"},
        )
        assert response.status_code == 422

    async def test_data_to_pdf_same_from_to_date(self, mock_db, async_client_auth):
        response = await async_client_auth.get(
            "/exports/pdf",
            params={"from_date": "2023-01-01", "to_date": "2023-01-01"},
        )
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=data.pdf"
        )
