# tests/test_auth.py
from eth_account.messages import encode_defunct

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