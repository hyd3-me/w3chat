# tests/test_websocket.py
import pytest
from app import utils

@pytest.mark.asyncio
async def test_websocket_connect(client):
    # Generate a valid JWT token
    success, token = utils.generate_jwt("0x1234567890abcdef1234567890abcdef12345678")
    assert success, f"Failed to generate token: {token}"
    
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
    success1, token1 = utils.generate_jwt(user1_address)
    assert success1, f"Failed to generate token1: {token1}"
    success2, token2 = utils.generate_jwt(user2_address)
    assert success2, f"Failed to generate token2: {token2}"
    
@pytest.mark.asyncio
async def test_websocket_message(client):
    """Test sending a message between two WebSocket clients."""
    # Generate JWT tokens for two users
    user1_address = "0x1234567890abcdef1234567890abcdef12345678"
    user2_address = "0xabcdef1234567890abcdef1234567890abcdef12"
    success1, token1 = utils.generate_jwt(user1_address)
    assert success1, f"Failed to generate token1: {token1}"
    success2, token2 = utils.generate_jwt(user2_address)
    assert success2, f"Failed to generate token2: {token2}"
    
    # Connect two users
    with client.websocket_connect(f"/ws/chat?token={token1}") as ws1:
        with client.websocket_connect(f"/ws/chat?token={token2}") as ws2:
            # Send message from user1 to user2
            message = {
                "type": "message",
                "to": user2_address,
                "data": "Hello from user1!"
            }
            ws1.send_json(message)
            
            # Check sender receives acknowledgment
            ack = ws1.receive_json()
            assert ack == {"type": "ack"}
            
            # Check recipient receives the message
            received = ws2.receive_json()
            assert received["type"] == "message"
            assert received["from"] == user1_address
            assert received["data"] == message["data"]
            
            # Explicitly close connections
            ws1.close()
            ws2.close()

@pytest.mark.asyncio
async def test_websocket_message_recipient_not_connected(client):
    """Test sending a message to a non-connected recipient."""
    # Generate JWT token for sender
    user1_address = "0x1234567890abcdef1234567890abcdef12345678"
    non_existent_address = "0x9999999999999999999999999999999999999999"
    success, token = utils.generate_jwt(user1_address)
    assert success, f"Failed to generate token: {token}"
    
    # Connect sender only
    with client.websocket_connect(f"/ws/chat?token={token}") as ws1:
        # Send message to non-existent recipient
        message = {
            "type": "message",
            "to": non_existent_address,
            "data": "Hello to nobody!"
        }
        ws1.send_json(message)
        
        # Check sender receives error
        response = ws1.receive_json()
        assert response == {"type": "error", "message": f"Recipient not connected: {non_existent_address}"}
        
        # Explicitly close connection
        ws1.close()