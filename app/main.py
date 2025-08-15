# app/main.py
from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.routers.websocket import router as websocket_router

app = FastAPI()

app.include_router(auth_router)
app.include_router(websocket_router)

@app.get("/")
async def home():
    return {"message": "Web3 Chat API"}