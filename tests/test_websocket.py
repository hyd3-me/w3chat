# tests/test_websocket.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from jose import jwt
from datetime import datetime, timedelta

import config

# Secret key must match the one in auth.py
SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_websocket_connect(client):
    # Generate a valid JWT token
    payload = {
        "sub": "0x1234567890abcdef1234567890abcdef12345678",
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    # Connect to WebSocket with token
    with client.websocket_connect(f"/ws/chat?token={token}") as websocket:
        # Send a test JSON message and expect a response
        websocket.send_json({"type": "ping"})
        response = websocket.receive_json()
        assert response == {"type": "pong"}
        # Explicitly close the connection
        websocket.close()

@pytest.mark.asyncio
async def test_websocket_message(client):
    # Generate JWT tokens for two users
    user1_address = "0x1234567890abcdef1234567890abcdef12345678"
    user2_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    payload1 = {
        "sub": user1_address,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    payload2 = {
        "sub": user2_address,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    token1 = jwt.encode(payload1, SECRET_KEY, algorithm=ALGORITHM)
    token2 = jwt.encode(payload2, SECRET_KEY, algorithm=ALGORITHM)
    
    # Connect two users
    with client.websocket_connect(f"/ws/chat?token={token1}") as ws1:
        with client.websocket_connect(f"/ws/chat?token={token2}") as ws2:
            # Send message from user1 to user2
            message = {
                "to": user2_address,
                "content": "Hello from user1!"
            }
            ws1.send_json(message)
            
            # Receive message on user2
            received = ws2.receive_json()
            assert received["from"] == user1_address
            assert received["content"] == message["content"]
                        
            # Explicitly close connections
            ws1.close()
            ws2.close()