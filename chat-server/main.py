import uuid
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import dotenv
from Consultant import LLMConsole
from chatting_command import command
from MeetingRoom import Manager as MeetingRoomManager
from config import log
from firestore import load_firestore

dotenv.load_dotenv()

app = FastAPI(lifespan=load_firestore)
app.mount("/chat/static", StaticFiles(directory="static"), name="static")

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    llm = LLMConsole(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            await command(llm, message)
    except:
        await llm.free()
        

@app.get("/chat/test")
async def root():
    with open("test_chat.html", "r") as file:
        return HTMLResponse(file.read())

meeting_manager = MeetingRoomManager()
@app.websocket("/translation")
async def translation_endpoint(websocket: WebSocket):
    user = await meeting_manager.accept(websocket)
    await user.conn.loop_until_close()

@app.get("/translation/test")
async def translation_test():
    with open("test_translation.html", "r") as file:
        return HTMLResponse(file.read())

@app.get("/translation/uuid")
async def create_uuid():
    return HTMLResponse(str(uuid.uuid4()))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
