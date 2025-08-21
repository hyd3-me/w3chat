# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app import utils, storage

# Configure logging
logger = utils.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Initialize storage
store = storage.Storage()

async def send_to_subscribers(recipient_addresses: list[str], message: dict):
    """Send a message to all WebSocket connections of recipient addresses."""
    for address in recipient_addresses:
        recipient_connections = store.connections.get(address, [])
        for ws in recipient_connections:
            try:
                await ws.send_json(message)
            except (WebSocketDisconnect, RuntimeError) as e:
                logger.debug(f"Failed to send message to WebSocket for address {address}: {str(e)}")
                continue
    logger.info("Message sent successfully")

async def send_ack(websocket: WebSocket):
    """Send acknowledgment to the websocket."""
    await websocket.send_json({"type": "ack"})
    logger.debug("Sent acknowledgment")

async def process_ping(websocket: WebSocket, data: dict, sender_address: str):
    """Process ping message and send pong response."""
    await websocket.send_json({"type": "pong"})
    logger.debug("Processed ping message")

async def process_channel(websocket: WebSocket, data: dict, sender_address: str):
    """Process channel message type and forward to all channel subscribers."""
    channel_name = data.get("channel")
    data_content = data.get("data")
    
    if not channel_name or not data_content:
        await websocket.send_json({"type": "error", "message": "Invalid channel message format"})
        logger.warning("Invalid channel message format")
        return
    
    # Check if sender is a participant in the channel
    if not utils.is_channel_participant(channel_name, sender_address):
        await websocket.send_json({"type": "error", "message": "Unauthorized access to channel"})
        logger.warning(f"Unauthorized access to channel {channel_name} by {sender_address}")
        return
    
    # Channel-based message handling
    recipient_addresses = store.channels.get(channel_name, [])
    if not recipient_addresses:
        await websocket.send_json({"type": "error", "message": f"No subscribers in channel: {channel_name}"})
        logger.warning("No subscribers in channel")
        return
    
    await send_ack(websocket)
    await send_to_subscribers(recipient_addresses, {
        "type": "message",
        "from": sender_address,
        "channel": channel_name,
        "data": data_content
    })

async def process_channel_request(websocket: WebSocket, data: dict, sender_address: str):
    """Process channel request and notify recipient."""
    to_address = data.get("to")
    if not to_address:
        await websocket.send_json({"type": "error", "message": "Invalid recipient address"})
        logger.warning("Invalid recipient address")
        return
    
    if not (utils.is_valid_address(sender_address) and utils.is_valid_address(to_address)):
        await websocket.send_json({"type": "error", "message": "Invalid Ethereum address"})
        logger.warning(f"Invalid Ethereum address: sender={sender_address}, to={to_address}")
        return
    
    # Check if trying to create channel with self
    if sender_address == to_address:
        await websocket.send_json({"type": "error", "message": "Cannot create channel with self"})
        logger.warning(f"Attempted to create channel with self by {sender_address}")
        return
    
    # Generate channel name
    channel_name = utils.generate_channel_name(sender_address, to_address)
    
    if not utils.is_channel_participant(channel_name, sender_address):
        await websocket.send_json({"type": "error", "message": "Unauthorized channel approval"})
        logger.warning(f"Unauthorized channel approval for {channel_name} by {sender_address}")
        return
    
    # Check if channel or request already exists
    if channel_name in store.channels:
        # Subscribe if channel already exists
        success, msg = await store.subscribe_to_channel(channel_name, [sender_address])
        if not success:
            await websocket.send_json({"type": "error", "message": msg})
            logger.warning(msg)
            return
    if channel_name in store.channel_requests:
        await websocket.send_json({"type": "error", "message": "Channel request already exists"})
        logger.warning("Channel request already exists")
        return
    
    # Notify recipient if online
    recipient_connections = store.connections.get(to_address, [])
    if recipient_connections:
        # Store channel request
        await store.add_channel_request(channel_name, sender_address)
        
        # Send acknowledgment to sender
        await send_ack(websocket)
        await send_to_subscribers([to_address], {
            "type": "channel_request",
            "from": sender_address,
            "channel": channel_name
        })
    else:
        await websocket.send_json({"type": "error", "message": "user is unavailable"})
        logger.warning("attempt to request channel with unavailable user")


async def process_channel_approve(websocket: WebSocket, data: dict, sender_address: str):
    """Process channel approval and create the channel."""
    channel_name = data.get("channel")
    if not channel_name:
        await websocket.send_json({"type": "error", "message": "Invalid channel name"})
        logger.warning("Invalid channel name")
        return
    if channel_name not in store.channel_requests:
        await websocket.send_json({"type": "error", "message": "No such channel request"})
        logger.warning("No such channel request")
        return
    
    # Check if sender is a participant in the channel and not the requester
    requester_address = store.channel_requests[channel_name]["from"]
    if sender_address == requester_address:
        await websocket.send_json({"type": "error", "message": "Requester cannot approve own channel request"})
        logger.warning(f"Requester {sender_address} attempted to approve own channel request for {channel_name}")
        return
    if not utils.is_channel_participant(channel_name, sender_address):
        await websocket.send_json({"type": "error", "message": "Unauthorized channel approval"})
        logger.warning(f"Unauthorized channel approval for {channel_name} by {sender_address}")
        return
    
    await store.add_channel(channel_name)
    
    # Delete channel request
    success, msg = await store.delete_channel_request(channel_name)
    if not success:
        await websocket.send_json({"type": "error", "message": msg})
        logger.warning(msg)
        return
    await send_ack(websocket)

    # Subscribe both participants
    success, msg = await store.subscribe_to_channel(channel_name, [sender_address, requester_address])
    if not success:
        await websocket.send_json({"type": "error", "message": msg})
        logger.warning(msg)
        return
    
    # Notify subscribers
    await store.notify_channel_creation(channel_name)

async def process_channel_reject(websocket: WebSocket, data: dict, sender_address: str):
    """Process channel request rejection and notify the requester."""
    channel_name = data.get("channel")
    if not channel_name:
        await websocket.send_json({"type": "error", "message": "Invalid channel name"})
        logger.warning("Invalid channel name")
        return
    if channel_name not in store.channel_requests:
        await websocket.send_json({"type": "error", "message": "No such channel request"})
        logger.warning("No such channel request")
        return
    
    # Get requester address
    requester_address = store.channel_requests[channel_name]["from"]
    
    # Delete channel request
    success, msg = await store.delete_channel_request(channel_name)
    
    # Send acknowledgment to rejector
    await send_ack(websocket)
    
    # Notify requester if online
    requester_connections = store.connections.get(requester_address, [])
    if requester_connections:
        await send_to_subscribers([requester_address], {
            "type": "info",
            "message": f"Channel request rejected by {sender_address}",
        })

process_map = {
    "ping": process_ping,
    "channel": process_channel,
    "channel_request": process_channel_request,
    "channel_approve": process_channel_approve,
    "channel_reject": process_channel_reject,
}

async def process_type(websocket: WebSocket, sender_address: str):
    """Process incoming WebSocket message based on its type."""
    data = await websocket.receive_json()
    message_type = data.get("type")
    if not message_type or message_type not in process_map:
        await websocket.send_json({"type": "error", "message": f"Invalid message type: {message_type}"})
        logger.warning(f"Invalid message type received: {message_type}")
        return
    await process_map[message_type](websocket, data, sender_address)

async def get_current_user(token: str):
    success, result = utils.decode_jwt(token)
    if not success:
        logger.error(result)
        raise WebSocketDisconnect(code=1008, reason=result)
    return result

@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, token: str):
    try:
        # Verify token
        address = await get_current_user(token)
        await websocket.accept()
        
        # Add connection
        await store.add_connection(address, websocket)
        
        try:
            while True:
                # Receive JSON message
                await process_type(websocket, address)
        except WebSocketDisconnect:
            await store.remove_connection(address, websocket)
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket: {str(e)}")
            await store.remove_connection(address, websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed during initialization")