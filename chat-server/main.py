from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import json
import dotenv
from RealtimeAPI import LLMConsole
from chatting_command import command

dotenv.load_dotenv()

app = FastAPI()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    llm = LLMConsole(websocket)
    await llm.load()
    try:
        while True:
            message = await websocket.receive_json()
            await command(llm, message)
    except:
        await llm.free()
        

@app.get("/chat-test")
async def root():
    with open("test.html", "r") as file:
        return HTMLResponse(file.read())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
