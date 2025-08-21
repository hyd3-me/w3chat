# app/main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routers.auth import router as auth_router
from app.routers.websocket import router as websocket_router
from app import utils

# Setup logging
utils.setup_logging()

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend"), name="static")
app.include_router(auth_router)
app.include_router(websocket_router)

@app.get("/")
async def home():
    return FileResponse("frontend/index.html")