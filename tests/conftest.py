# tests/conftest.py
import pytest
import json
from fastapi.testclient import TestClient
from web3 import Web3
from app.main import app
from app import utils

@pytest.fixture(autouse=True, scope="session")
def set_testing_mode():
    """Set MODE=testing for all tests."""
    utils.set_environment_variable('MODE', 'testing')

@pytest.fixture(scope="session")
def client():
    """Provide a FastAPI test client."""
    return TestClient(app)

@pytest.fixture(scope="session")
def web3():
    """Provide a Web3 instance."""
    return Web3()

@pytest.fixture(scope="session")
def user_account(web3):
    """Provide a test user account, reusing or creating a wallet in SECRET_DATA.json."""
    secret_data = utils.get_secret_data()
    
    if 'address' in secret_data and 'private_key' in secret_data:
        account = web3.eth.account.from_key(secret_data["private_key"])
    else:
        account = web3.eth.account.create()
        secret_data.update({
            "address": account.address,
            "private_key": account.key.hex()
        })
        secret_file = utils.join_paths(utils.get_data_path(), 'SECRET_DATA.json')
        with open(secret_file, "w") as f:
            json.dump(secret_data, f, indent=2)
    
    return account

@pytest.fixture
def user_1():
    """Generate address and JWT token for user 1."""
    address = "0x1234567890abcdef1234567890abcdef12345678"
    success, token = utils.generate_jwt(address)
    assert success, f"Failed to generate token: {token}"
    return {"address": address, "token": token}

@pytest.fixture
def user_2():
    """Generate address and JWT token for user 2."""
    address = "0xabcdef1234567890abcdef1234567890abcdef12"
    success, token = utils.generate_jwt(address)
    assert success, f"Failed to generate token: {token}"
    return {"address": address, "token": token}

@pytest.fixture
def channel_name(user_1, user_2):
    """Generate channel name from user_1 and user_2 addresses."""
    return utils.generate_channel_name(user_1["address"], user_2["address"])

@pytest.fixture
def websocket_1(client, user_1):
    """Connect WebSocket client for user 1 and close after test."""
    with client.websocket_connect(f"/ws/chat?token={user_1['token']}") as ws:
        yield ws

@pytest.fixture
def websocket_2(client, user_2):
    """Connect WebSocket client for user 2 and close after test."""
    with client.websocket_connect(f"/ws/chat?token={user_2['token']}") as ws:
        yield ws

@pytest.fixture
def user_3():
    """Generate address and JWT token for user 3."""
    address = "0x9999999999999999999999999999999999999999"
    success, token = utils.generate_jwt(address)
    assert success, f"Failed to generate token: {token}"
    return {"address": address, "token": token}

@pytest.fixture
def websocket_3(client, user_3):
    """Connect WebSocket client for user 3 and close after test."""
    with client.websocket_connect(f"/ws/chat?token={user_3['token']}") as ws:
        yield ws

@pytest.fixture
def store():
    """Return the server storage instance."""
    from app.routers import websocket
    return websocket.store

@pytest.fixture
def websocket_1_2(client, user_1):
    """Fixture to create a second WebSocket connection for user_1."""
    with client.websocket_connect(f"/ws/chat?token={user_1['token']}") as ws:
        yield ws

@pytest.fixture
def websocket_2_2(client, user_2):
    """Fixture to create a second WebSocket connection for user_2."""
    with client.websocket_connect(f"/ws/chat?token={user_2['token']}") as ws:
        yield ws