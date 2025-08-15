# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
import json
import os, sys
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])

# Secret key must match the one in auth.py
SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"

# Store active WebSocket connections
connections = {}

async def get_current_user(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        address: str = payload.get("sub")
        if address is None:
            logger.error("Invalid token: missing 'sub' field")
            raise WebSocketDisconnect(code=1008, reason="Invalid token")
        return address
    except JWTError:
        logger.error(f"JWT verification failed: {str(e)}")
        raise WebSocketDisconnect(code=1008, reason="Invalid token")

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