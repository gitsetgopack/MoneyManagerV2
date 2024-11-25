import requests


def get_auth_headers():
    """Get authentication headers with token."""
    token = localStorage.getItem("token")  # Adjust based on where you store the token
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def make_authenticated_request(url, method="GET", data=None):
    """Make an authenticated API request."""
    headers = get_auth_headers()
    response = None

    if method == "GET":
        response = requests.get(url, headers=headers)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=data)
    elif method == "PUT":
        response = requests.put(url, headers=headers, json=data)
    elif method == "DELETE":
        response = requests.delete(url, headers=headers)

    return response
