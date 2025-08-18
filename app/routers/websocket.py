# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app import utils


# Configure logging
logger = utils.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
connections = {}

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
    
    # Check if recipient is connected
    recipient_ws = connections.get(to_address)
    if not recipient_ws:
        await websocket.send_json({"type": "error", "message": f"Recipient not connected: {to_address}"})
        logger.warning(f"Recipient {to_address} not connected")
        return
    
    # Send acknowledgment to sender
    await websocket.send_json({"type": "ack"})
    logger.debug(f"Sent ack to {sender_address}")
    
    # Forward message to recipient
    await recipient_ws.send_json({
        "type": "message",
        "from": sender_address,
        "data": data_content
    })
    logger.info(f"Message sent from {sender_address} to {to_address}")

process_map = {
    "ping": process_ping,
    "message": process_message,
}

async def process_type(websocket: WebSocket, data: dict, sender_address: str):
    """Process incoming WebSocket message based on its type."""
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
        
        # Store connection
        connections[address] = websocket
        logger.info("New WebSocket connection established")
        
        try:
            while True:
                # Receive JSON message
                data = await websocket.receive_json()
                await process_type(websocket, data, address)
        except WebSocketDisconnect:
            # Remove connection on disconnect
            connections.pop(address, None)
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket: {str(e)}")
            connections.pop(address, None)
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed during initialization")