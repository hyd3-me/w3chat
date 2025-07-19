from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Web3 Chat API"}