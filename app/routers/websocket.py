# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app import utils


# Configure logging
logger = utils.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
connections = {}

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

async def send_to_subscribers(recipient_connections: list[WebSocket], message: dict):
    """Send a message to all recipient WebSocket connections."""
    for recipient_ws in recipient_connections:
        await recipient_ws.send_json(message)
    logger.info("Message sent successfully")

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
    
    # Send acknowledgment to sender
    await websocket.send_json({"type": "ack"})
    logger.debug(f"Sent ack to {sender_address}")
    
    # Forward message to all recipient connections
    await send_to_subscribers(recipient_connections, {
        "type": "message",
        "from": sender_address,
        "data": data_content
    })

process_map = {
    "ping": process_ping,
    "message": process_message,
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