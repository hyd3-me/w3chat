# app/routers/auth.py
from fastapi import APIRouter, HTTPException
from app import utils

# Configure logging
logger = utils.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(auth: utils.AuthRequest):
    logger.debug(f"Processing login request for address: {auth.address}")
    is_valid, message = utils.verify_signature(auth)
    if not is_valid:
        logger.error(f"Signature verification failed: {message}")
        raise HTTPException(status_code=401, detail=message)
    
    success, result = utils.generate_jwt(auth.address)
    if not success:
        logger.error(f"JWT generation failed: {result}")
        raise HTTPException(status_code=500, detail=result)
    logger.info(f"JWT generated for address: {auth.address}")
    return {"token": result}