# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app import utils


# Configure logging
logger = utils.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
connections = {}
# Store channel subscriptions as a dictionary of lists
channels = {}
# Store channel requests as a dictionary
channel_requests = {}

async def add_connection(address: str, websocket: WebSocket):
    """Add a WebSocket connection for the given address."""
    if address not in connections:
        connections[address] = []
    connections[address].append(websocket)
    logger.info("New WebSocket connection established")

async def remove_connection(address: str, websocket: WebSocket):
    """Remove a WebSocket connection for the given address."""
    if address in connections:
        connections[address].remove(websocket)
        if not connections[address]:
            del connections[address]
    logger.info("WebSocket connection closed")

async def add_channel(channel_name: str):
    """Add a new channel if it doesn't exist."""
    if channel_name not in channels:
        channels[channel_name] = []
    logger.debug("Channel added")

async def send_to_subscribers(recipient_connections: list[WebSocket], message: dict):
    """Send a message to all recipient WebSocket connections."""
    for recipient_ws in recipient_connections:
        await recipient_ws.send_json(message)
    logger.info("Message sent successfully")

async def send_ack(websocket: WebSocket):
    """Send acknowledgment to the websocket."""
    await websocket.send_json({"type": "ack"})
    logger.debug("Sent acknowledgment")

async def add_channel_request(channel_name: str, sender_address: str):
    """Store a channel request."""
    channel_requests[channel_name] = {"from": sender_address}
    logger.debug("Channel request created")

async def process_ping(websocket: WebSocket, data: dict, sender_address: str):
    """Process ping message and send pong response."""
    await websocket.send_json({"type": "pong"})
    logger.debug("Processed ping message")

async def process_message(websocket: WebSocket, data: dict, sender_address: str):
    """Process message type and forward to recipient."""
    to_address = data.get("to")
    data_content = data.get("data")
    if not to_address or not data_content:
        await websocket.send_json({"error": "Invalid message format"})
        logger.warning(f"Invalid message format: {data}")
        return
    
    # Check if recipient has any connections
    recipient_connections = connections.get(to_address, [])
    if not recipient_connections:
        await websocket.send_json({"type": "error", "message": f"Recipient not connected: {to_address}"})
        logger.warning("Recipient not connected")
        return
    
    await send_ack(websocket)
    
    # Forward message to all recipient connections
    await send_to_subscribers(recipient_connections, {
        "type": "message",
        "from": sender_address,
        "data": data_content,
    })

async def process_subscribe(websocket: WebSocket, data: dict, sender_address: str):
    """Process subscribe message and add websocket to channel."""
    channel_name = data.get("channel")
    if not channel_name:
        await websocket.send_json({"type": "error", "message": "Invalid channel name"})
        logger.warning("Invalid channel name")
        return
    
    # Add channel and subscribe websocket
    await add_channel(channel_name)
    if websocket not in channels[channel_name]:
        channels[channel_name].append(websocket)
    
    await send_ack(websocket)

async def process_channel(websocket: WebSocket, data: dict, sender_address: str):
    """Process channel message type and forward to all channel subscribers."""
    channel_name = data.get("channel")
    data_content = data.get("data")
    
    if not channel_name or not data_content:
        await websocket.send_json({"type": "error", "message": "Invalid channel message format"})
        logger.warning("Invalid channel message format")
        return
    
    # Channel-based message handling
    recipient_connections = channels.get(channel_name, [])
    if not recipient_connections:
        await websocket.send_json({"type": "error", "message": f"No subscribers in channel: {channel_name}"})
        logger.warning("No subscribers in channel")
        return
    
    await send_ack(websocket)
    await send_to_subscribers(recipient_connections, {
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
    
    # Generate channel name
    channel_name = utils.generate_channel_name(sender_address, to_address)
    
    # Check if channel or request already exists
    if channel_name in channels:
        await websocket.send_json({"type": "error", "message": "Channel already exists"})
        logger.warning("Channel already exists")
        return
    if channel_name in channel_requests:
        await websocket.send_json({"type": "error", "message": "Channel request already exists"})
        logger.warning("Channel request already exists")
        return
    
    # Store channel request
    await add_channel_request(channel_name, sender_address)
    
    # Send acknowledgment to sender
    await send_ack(websocket)
    
    # Notify recipient if online
    recipient_connections = connections.get(to_address, [])
    if recipient_connections:
        await send_to_subscribers(recipient_connections, {
            "type": "channel_request",
            "from": sender_address,
            "channel": channel_name
        })

process_map = {
    "ping": process_ping,
    "message": process_message,
    "subscribe": process_subscribe,
    "channel": process_channel,
    "channel_request": process_channel_request,
}

async def process_type(websocket: WebSocket, sender_address: str):
    """Process incoming WebSocket message based on its type."""
    data = await websocket.receive_json()
    message_type = data.get("type")
    if not message_type or message_type not in process_map:
        await websocket.send_json({"error": f"Invalid message type: {message_type}"})
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
        await add_connection(address, websocket)
        
        try:
            while True:
                # Receive JSON message
                await process_type(websocket, address)
        except WebSocketDisconnect:
            await remove_connection(address, websocket)
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket: {str(e)}")
            await remove_connection(address, websocket)
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed during initialization")