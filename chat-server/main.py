from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import dotenv
from Consultant import LLMConsole
from chatting_command import command
from MeetingRoom import Manager as MeetingRoomManager
from config import log

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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
