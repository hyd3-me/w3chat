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
        # Check if connection is accepted
        assert websocket.accepted
        # Send a test message and expect a response
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"