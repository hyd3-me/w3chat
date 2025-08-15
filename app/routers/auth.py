# app/routers/auth.py
from fastapi import APIRouter, HTTPException
from app import utils

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(auth: utils.AuthRequest):
    is_valid, message = utils.verify_signature(auth)
    if not is_valid:
        raise HTTPException(status_code=401, detail=message)
    
    success, result = utils.generate_jwt(auth.address)
    if not success:
        raise HTTPException(status_code=500, detail=result)
    
    return {"token": result}