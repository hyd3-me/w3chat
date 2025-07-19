# tests/test_auth.py
import pytest
import json
import os
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
    # Path to store wallet data
    wallet_file = "../test_wallet.json"
    
    # Check if wallet already exists
    if os.path.exists(wallet_file):
        with open(wallet_file, "r") as f:
            wallet_data = json.load(f)
        account = web3.eth.account.from_key(wallet_data["private_key"])
    else:
        # Create a new test account
        account = web3.eth.account.create()
        # Save address and private key to file
        wallet_data = {
            "address": account.address,
            "private_key": account.key.hex()
        }
        with open(wallet_file, "w") as f:
            json.dump(wallet_data, f, indent=2)
    
    return account

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