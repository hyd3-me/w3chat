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
async def test_websocket_channel_messaging(websocket_1, websocket_2, user_1, user_2, channel_name, store):
    """Test sending and receiving messages in a channel after creation."""
    # Clean up channel and channel request state before test
    success, msg = await store.delete_channel(channel_name)
    assert success, f"Failed to clean up channel: {msg}"
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"

    # Send channel request
    websocket_1.send_json({"type": "channel_request", "to": user_2["address"]})
    ws1_ack = websocket_1.receive_json()  # Ack
    assert ws1_ack == {"type": "ack"}
    ws2_notification = websocket_2.receive_json()  # Notification
    assert ws2_notification == {
        "type": "channel_request",
        "from": user_1["address"],
        "channel": channel_name
    }

    # Approve channel
    websocket_2.send_json({"type": "channel_approve", "channel": channel_name})
    ws2_ack = websocket_2.receive_json()  # Ack
    assert ws2_ack == {"type": "ack"}
    ws1_info = websocket_1.receive_json()  # Channel creation notification
    assert ws1_info == {"type": "info", "message": "Channel created", "channel": channel_name}
    ws2_info = websocket_2.receive_json()  # Channel creation notification
    assert ws2_info == {"type": "info", "message": "Channel created", "channel": channel_name}

    # Send message to channel
    message = {
        "type": "channel",
        "channel": channel_name,
        "data": "Hello in channel!"
    }
    websocket_1.send_json(message)

    # Check sender receives acknowledgment
    ws1_message_ack = websocket_1.receive_json()
    assert ws1_message_ack == {"type": "ack"}

    # Check both users receive the message
    ws1_received = websocket_1.receive_json()
    assert ws1_received == {
        "type": "message",
        "from": user_1["address"],
        "channel": channel_name,
        "data": message["data"]
    }
    ws2_received = websocket_2.receive_json()
    assert ws2_received == {
        "type": "message",
        "from": user_1["address"],
        "channel": channel_name,
        "data": message["data"]
    }

@pytest.mark.asyncio
async def test_websocket_channel_request(websocket_1, websocket_2, user_1, user_2, channel_name, store):
    """Test sending a channel request and notifying recipient."""
    success, msg = await store.delete_channel(channel_name)
    assert success, f"Failed to clean up channel: {msg}"
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"
    websocket_1.send_json({"type": "channel_request", "to": user_2["address"]})
    ws1_ack = websocket_1.receive_json()
    assert ws1_ack == {"type": "ack"}
    ws2_notification = websocket_2.receive_json()
    assert ws2_notification == {
        "type": "channel_request",
        "from": user_1["address"],
        "channel": channel_name
    }

@pytest.mark.asyncio
async def test_websocket_channel_approve(websocket_1, websocket_2, user_1, user_2, channel_name, store):
    """Test approving a channel request and creating the channel."""
    # Clean up channel request state before test
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"

    websocket_1.send_json({"type": "channel_request", "to": user_2["address"]})
    websocket_1.receive_json()  # Ack
    websocket_2.receive_json()  # Notification
    websocket_2.send_json({"type": "channel_approve", "channel": channel_name})
    ws2_ack = websocket_2.receive_json()
    assert ws2_ack == {"type": "ack"}

@pytest.mark.asyncio
async def test_websocket_channel_auto_subscribe(websocket_1, websocket_2, user_1, user_2, channel_name, store):
    """Test automatic subscription of both participants after channel approval."""
    # Clean up channel request state before test
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"
    success, msg = await store.delete_channel(channel_name)
    assert success, f"Failed to clean up channel: {msg}"

    # Send channel request
    websocket_1.send_json({"type": "channel_request", "to": user_2["address"]})
    ws1_ack = websocket_1.receive_json()  # Ack
    assert ws1_ack == {"type": "ack"}
    ws2_notification = websocket_2.receive_json()  # Notification
    assert ws2_notification == {
        "type": "channel_request",
        "from": user_1["address"],
        "channel": channel_name
    }

    # Approve channel
    websocket_2.send_json({"type": "channel_approve", "channel": channel_name})
    ws2_ack = websocket_2.receive_json()  # Ack
    assert ws2_ack == {"type": "ack"}

    # Check that both participants receive channel creation notification
    ws1_info = websocket_1.receive_json()
    assert ws1_info == {"type": "info", "message": "Channel created", "channel": channel_name}
    ws2_info = websocket_2.receive_json()
    assert ws2_info == {"type": "info", "message": "Channel created", "channel": channel_name}

@pytest.mark.asyncio
async def test_websocket_channel_reject(websocket_1, websocket_2, user_1, user_2, channel_name, store):
    """Test rejecting a channel request and notifying the requester."""
    # Clean up channel and channel request state before test
    success, msg = await store.delete_channel(channel_name)
    assert success, f"Failed to clean up channel: {msg}"
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"

    # Send channel request
    websocket_1.send_json({"type": "channel_request", "to": user_2["address"]})
    ws1_ack = websocket_1.receive_json()  # Ack
    assert ws1_ack == {"type": "ack"}
    ws2_notification = websocket_2.receive_json()  # Notification
    assert ws2_notification == {
        "type": "channel_request",
        "from": user_1["address"],
        "channel": channel_name
    }

    # Reject channel request
    websocket_2.send_json({"type": "channel_reject", "channel": channel_name})
    ws2_ack = websocket_2.receive_json()  # Ack
    assert ws2_ack == {"type": "ack"}

    # Check that requester receives rejection notification
    ws1_info = websocket_1.receive_json()
    assert ws1_info == {"type": "info", "message": f"Channel request rejected by {user_2['address']}"}

@pytest.mark.asyncio
async def test_websocket_channel_access_validation(websocket_1, websocket_2, websocket_3, user_1, user_2, channel_name, store):
    """Test that only channel participants can send messages to the channel."""

    # Ensure channel exists and subscribe participants
    status = await store.channel_exists(channel_name)
    if not status:
        success, msg = await store.ensure_channel(channel_name, [user_1["address"], user_2["address"]])
        assert success, f"Failed to ensure channel: {msg}"
    
    # Third user tries to send a message to the channel
    message = {
        "type": "channel",
        "channel": channel_name,
        "data": "Unauthorized message!"
    }
    websocket_3.send_json(message)
    ws3_response = websocket_3.receive_json()
    assert ws3_response == {"type": "error", "message": "Unauthorized access to channel"}

@pytest.mark.asyncio
async def test_websocket_channel_approve_validation(websocket_1, websocket_2, websocket_3, user_1, user_2, user_3, channel_name, store):
    """Test that only non-requester participants can approve channel creation."""

    # Clean up channel and channel request state
    success, msg = await store.delete_channel(channel_name)
    assert success, f"Failed to clean up channel: {msg}"
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"

    # Check that channel does not exist
    assert not await store.channel_exists(channel_name), f"Channel {channel_name} should not exist"

    # User1 sends channel request to User2
    websocket_1.send_json({"type": "channel_request", "to": user_2["address"]})
    ws1_ack = websocket_1.receive_json()  # Ack
    assert ws1_ack == {"type": "ack"}
    ws2_notification = websocket_2.receive_json()  # Notification
    assert ws2_notification == {
        "type": "channel_request",
        "from": user_1["address"],
        "channel": channel_name
    }

    # Test case 1: User1 (requester) tries to approve own request
    websocket_1.send_json({"type": "channel_approve", "channel": channel_name})
    ws1_response = websocket_1.receive_json()
    assert ws1_response == {"type": "error", "message": "Requester cannot approve own channel request"}

    # Test case 2: User3 (non-participant) tries to approve
    websocket_3.send_json({"type": "channel_approve", "channel": channel_name})
    ws3_response = websocket_3.receive_json()
    assert ws3_response == {"type": "error", "message": "Unauthorized channel approval"}

@pytest.mark.asyncio
async def test_websocket_channel_request_self_channel(websocket_1, websocket_2, user_1, user_2, channel_name, store):
    """Test that a user cannot create a channel with themselves."""

    # Test case 1: User1 tries to create channel with self
    websocket_1.send_json({"type": "channel_request", "to": user_1["address"]})
    ws1_response = websocket_1.receive_json()
    assert ws1_response == {"type": "error", "message": "Cannot create channel with self"}

@pytest.mark.asyncio
async def test_websocket_channel_name_validation(websocket_1, user_1, user_2, channel_name, store, client):
    """Test validation of channel name format in channel creation, subscription, and messaging."""
    # Clean up channel and channel request state
    success, msg = await store.delete_channel(channel_name)
    assert success, f"Failed to clean up channel: {msg}"
    success, msg = await store.delete_channel_request(channel_name)
    assert success, f"Failed to clean up channel request: {msg}"

    # Test case 1: Try to create channel with invalid to_address
    invalid_address = "0xInvalidAddress"
    websocket_1.send_json({"type": "channel_request", "to": invalid_address})
    ws1_response = websocket_1.receive_json()
    assert ws1_response == {"type": "error", "message": "Invalid Ethereum address"}

@pytest.mark.asyncio
async def test_websocket_multiple_websockets_channel_messaging(websocket_1, websocket_1_2, websocket_2, websocket_2_2, user_1, user_2, channel_name, store):
    """Test that a channel message is received by all WebSocket connections of subscribed addresses."""
    # Create channel and subscribe both addresses
    success, msg = await store.ensure_channel(channel_name, [user_1["address"], user_2["address"]])

    # Send message from websocket_1
    message = {
        "type": "channel",
        "channel": channel_name,
        "data": "Test message from user_1"
    }
    websocket_1.send_json(message)

    # Check acknowledgment on websocket_1
    ws1_1_ack = websocket_1.receive_json()
    assert ws1_1_ack == {"type": "ack"}

    # Define expected messages
    expected_message = {
        "type": "message",
        "from": user_1["address"],
        "channel": channel_name,
        "data": message["data"]
    }

    # Check message received on ws1_1 (user_1's first WebSocket)
    ws1_1_received = websocket_1.receive_json()
    assert ws1_1_received == expected_message

    # Check message received on websocket_1_2 (user_1's second WebSocket)
    ws1_2_received = websocket_1_2.receive_json()
    assert ws1_2_received == expected_message

    # Check message received on websocket_2 (user_2's first WebSocket)
    ws2_received = websocket_2.receive_json()
    assert ws2_received == expected_message

    # Check message received on websocket_2_2 (user_2's second WebSocket)
    ws2_2_received = websocket_2_2.receive_json()
    assert ws2_2_received == expected_message