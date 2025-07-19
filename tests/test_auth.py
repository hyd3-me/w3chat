# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from web3 import Web3
from eth_account.messages import encode_defunct

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def web3():
    return Web3()

@pytest.fixture
def user_account(web3):
    # Create a test account for signing
    return web3.eth.account.create()

def test_web3_auth(client, web3, user_account):
    # Prepare test data
    message = "Login to Web3 Chat"
    message_hash = encode_defunct(text=message)
    signature = user_account.sign_message(message_hash).signature.hex()
    payload = {
        "address": user_account.address,
        "message": message,
        "signature": signature
    }

    # Send POST request to /auth/login
    response = client.post("/auth/login", json=payload)
    
    # Assert response
    assert response.status_code == 200
    assert "token" in response.json()
    assert isinstance(response.json()["token"], str)