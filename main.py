"""Table for Three AI - Multi-model conversation platform"""
import json
import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TableForThree")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Table for Three AI API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "1.0.0"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "response", "content": f"Echo: {data}"})
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
