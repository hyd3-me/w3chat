# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
import json
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config

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
            raise WebSocketDisconnect(code=1008, reason="Invalid token")
        return address
    except JWTError:
        raise WebSocketDisconnect(code=1008, reason="Invalid token")

@router.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, token: str):
    # Verify token
    address = await get_current_user(token)
    await websocket.accept()
    
    # Store connection
    connections[address] = websocket
    
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