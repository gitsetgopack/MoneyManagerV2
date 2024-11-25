import pytest
from bots.telegram.auth import AuthHandler, UnauthorizedError

@pytest.fixture
def auth_handler():
    return AuthHandler()

@pytest.fixture
def valid_credentials():
    return {'username': 'user', 'password': 'pass'}

@pytest.fixture
def invalid_credentials():
    return {'username': 'user', 'password': 'wrong_pass'}

def test_valid_login(auth_handler, valid_credentials):
    result = auth_handler.login(**valid_credentials)
    assert result
    assert auth_handler.is_authenticated

def test_invalid_login(auth_handler, invalid_credentials):
    result = auth_handler.login(**invalid_credentials)
    assert not result
    assert not auth_handler.is_authenticated

def test_logout(auth_handler, valid_credentials):
    auth_handler.login(**valid_credentials)
    auth_handler.logout()
    assert not auth_handler.is_authenticated

def test_token_refresh(auth_handler, valid_credentials):
    auth_handler.login(**valid_credentials)
    old_token = auth_handler.token
    auth_handler.refresh_token()
    new_token = auth_handler.token
    assert old_token != new_token
    assert auth_handler.is_authenticated

def test_access_protected_resource(auth_handler, valid_credentials):
    auth_handler.login(**valid_credentials)
    response = auth_handler.access_protected_resource()
    assert response == 'Resource content'

def test_access_protected_resource_unauthenticated(auth_handler):
    with pytest.raises(UnauthorizedError):
        auth_handler.access_protected_resource()

def test_login_exceptions(auth_handler):
    with pytest.raises(ValueError):
        auth_handler.login(username='', password='')

def test_refresh_token_unauthenticated(auth_handler):
    auth_handler.refresh_token()
    assert auth_handler.token is None
    assert not auth_handler.is_authenticated

def test_logout_when_not_authenticated(auth_handler):
    auth_handler.logout()
    assert not auth_handler.is_authenticated

def test_multiple_logins(auth_handler, valid_credentials):
    auth_handler.login(**valid_credentials)
    result = auth_handler.login(**valid_credentials)
    assert result
    assert auth_handler.is_authenticated

def test_invalid_refresh_token(auth_handler, invalid_credentials):
    auth_handler.login(**invalid_credentials)
    auth_handler.refresh_token()
    assert auth_handler.token is None
    assert not auth_handler.is_authenticated

def test_logout_after_invalid_login(auth_handler, invalid_credentials):
    auth_handler.login(**invalid_credentials)
    auth_handler.logout()
    assert not auth_handler.is_authenticated

def test_access_protected_resource_after_logout(auth_handler, valid_credentials):
    auth_handler.login(**valid_credentials)
    auth_handler.logout()
    with pytest.raises(UnauthorizedError):
        auth_handler.access_protected_resource()
