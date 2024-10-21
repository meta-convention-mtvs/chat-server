from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import json
import dotenv
from .RealtimeAPI import LLMConsole

dotenv.load_dotenv()

ERROR_FATAL = {"type": "server.error", "code": 1}
ERROR_NO_ORG = {"type": "server.error", "code": 2}
ERROR_DUP_REQ = {"type": "server.error", "code": 3}
ERROR_REQ_PARAM = {"type": "server.error", "code": 4}

app = FastAPI()

@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    llm = None
    while True:
        message = await websocket.receive_json()
        if message["type"] == "config.update":
            org_id = message.get("org")
            if not org_id:
                await websocket.send_json(ERROR_REQ_PARAM)
            else:
                llm = LLMConsole(websocket, org_id)
                await llm.load()

        elif message["type"] == "buffer.add_audio":
            audio_data = message.get("audio")
            if not llm:
                await websocket.send_json(ERROR_NO_ORG)
            else:
                await llm.add_audio(audio_data)

        elif message["type"] == "buffer.clear_audio":
            if not llm:
                await websocket.send_json(ERROR_NO_ORG)
            else:
                await llm.clear_audio()

        elif message["type"] == "generate.text_audio":
            if not llm.is_gen_ready():
                await llm.response_error(ERROR_DUP_REQ)
                return
            text = message.get("text", None)
            if text:
                await llm.add_text("user", text)
            await llm.generate(["text", "audio"])

        elif message["type"] == "generate.only_text":
            if not llm.is_gen_ready():
                await llm.response_error(ERROR_DUP_REQ)
                return
            text = message.get("text", None)
            if text:
                await llm.add_text("user", text)
            await llm.generate(["text"])

        elif message["type"] == "generate.cancel":
            await llm.cancel()

@app.get("/")
async def root():
    with open("srcs/test.html", "r") as file:
        return HTMLResponse(file.read())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
