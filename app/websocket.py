# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config

router = APIRouter(prefix="/ws", tags=["websocket"])

# Secret key must match the one in auth.py
SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"

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
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass