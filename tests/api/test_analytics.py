from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient

from api.app import app


@pytest.mark.anyio
class TestNoExpenses:
    async def test_expense_bar_no_expenses(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/expense/bar",
            params={
                "from_date": datetime.now().date().isoformat(),
                "to_date": (datetime.now() + timedelta(days=7)).date().isoformat()
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No expenses found"

    async def test_category_pie_no_expenses(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/category/pie",
            params={
                "from_date": datetime.now().date().isoformat(),
                "to_date": (datetime.now() + timedelta(days=7)).date().isoformat()
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No expenses found for the specified period"


@pytest.mark.anyio
class TestAddExpensesForAnalytics:
    async def test_add_expenses(self, async_client_auth: AsyncClient):
        test_date = datetime.now()
        expenses = [
            {
                "amount": 100.0,
                "currency": "USD",
                "category": "Food",
                "description": "Groceries",
                "account_name": "Checking",
                "date": test_date.date().isoformat(),
                "type": "expense"
            },
            {
                "amount": 50.0,
                "currency": "USD",
                "category": "Transport",
                "description": "Bus fare",
                "account_name": "Checking",
                "date": (test_date - timedelta(days=1)).date().isoformat(),
                "type": "expense"
            },
            {
                "amount": 200.0,
                "currency": "USD",
                "category": "Utilities",
                "description": "Concert ticket",
                "account_name": "Checking",
                "date": (test_date - timedelta(days=2)).date().isoformat(),
                "type": "expense"
            },
        ]
        for expense in expenses:
            response = await async_client_auth.post("/expenses/", json=expense)
            assert response.status_code == 200
            assert response.json()["message"] == "Expense added successfully"


@pytest.mark.anyio
class TestAnalyticsCharts:
    async def test_expense_bar_success(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/expense/bar",
            params={
                "from_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
                "to_date": datetime.now().date().isoformat()
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_category_pie_success(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/category/pie",
            params={
                "from_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
                "to_date": datetime.now().date().isoformat()
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_monthly_line_success(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/expense/line-monthly",
            params={
                "from_date": (datetime.now() - timedelta(days=30)).date().isoformat(),
                "to_date": datetime.now().date().isoformat()
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_category_bar_success(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/category/bar",
            params={
                "from_date": (datetime.now() - timedelta(days=7)).date().isoformat(),
                "to_date": datetime.now().date().isoformat()
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_budget_vs_actual_success(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/budget/actual-vs-budget",
            params={
                "from_date": (datetime.now() - timedelta(days=30)).date().isoformat(),
                "to_date": datetime.now().date().isoformat()
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"


@pytest.mark.anyio
class TestAnalyticsEdgeCases:
    async def test_invalid_date_format(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/expense/bar",
            params={
                "from_date": "invalid-date",
                "to_date": "invalid-date"
            },
        )
        assert response.status_code == 422  # Validation error

    async def test_missing_dates(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get("/analytics/expense/bar")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_reversed_dates(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/expense/bar",
            params={
                "from_date": datetime.now().date().isoformat(),
                "to_date": (datetime.now() - timedelta(days=7)).date().isoformat()
            },
        )
        assert response.status_code == 422  # Date validation error
        assert "Invalid date range" in response.json()["detail"]

    async def test_future_date_range(self, async_client_auth: AsyncClient):
        response = await async_client_auth.get(
            "/analytics/category/pie",
            params={
                "from_date": (datetime.now() + timedelta(days=1)).date().isoformat(),
                "to_date": (datetime.now() + timedelta(days=7)).date().isoformat()
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No expenses found for the specified period"
