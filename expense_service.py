
from api_utils import make_authenticated_request

def add_expense(expense_data):
    """Add a new expense with proper authentication."""
    url = 'your_api_endpoint/expenses'
    response = make_authenticated_request(url, method='POST', data=expense_data)
    return response.json()