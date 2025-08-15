# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import logging
from app import utils


# Configure logging
logger = utils.get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Store active WebSocket connections
connections = {}

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
                message_type = data.get("type")

                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    continue

                to_address = data.get("to")
                content = data.get("content")
                
                if not to_address or not content:
                    await websocket.send_json({"error": "Invalid message format"})
                    continue
                
                # Send message to recipient
                recipient_ws = connections.get(to_address)
                if recipient_ws:
                    await recipient_ws.send_json({
                        "from": address,
                        "content": content
                    })
                else:
                    await websocket.send_json({"error": "Recipient not connected"})
        except WebSocketDisconnect:
            # Remove connection on disconnect
            connections.pop(address, None)
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"Unexpected error in WebSocket: {str(e)}")
            connections.pop(address, None)
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed during initialization")