# app/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web3 import Web3
from eth_account.messages import encode_defunct
from jose import jwt
from datetime import datetime, timedelta
import os, sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import config

router = APIRouter(prefix="/auth", tags=["auth"])

# Secret key for JWT (in production, store in environment variables)
SECRET_KEY = config.SECRET_KEY
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

class AuthRequest(BaseModel):
    address: str
    message: str
    signature: str

@router.post("/login")
async def login(auth: AuthRequest):
    # Verify signature
    w3 = Web3()
    message_hash = encode_defunct(text=auth.message)
    recovered_address = w3.eth.account.recover_message(
        message_hash, signature=auth.signature
    )
    
    if recovered_address.lower() != auth.address.lower():
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Generate JWT
    payload = {
        "sub": auth.address,
        "exp": datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    
    return {"token": token}