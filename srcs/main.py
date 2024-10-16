from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
import uvicorn
import json

ERROR_FATAL = {"type": "server.error", "code": 1}
ERROR_NO_ORG = {"type": "server.error", "code": 2}
ERROR_DUP_REQ = {"type": "server.error", "code": 3}
ERROR_REQ_PARAM = {"type": "server.error", "code": 4}

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    org_id = None
    llm_model = "realtime"
    while True:
        message = await websocket.receive_json()
        if message["type"] == "config.update":
            org_id = message.get("org")
            if not org_id:
                await websocket.send_json({
                    "type": "server.error",
                    "code": ERROR_REQ_PARAM
                })
            llm_model = message.get("llm", "realtime")

        elif message["type"] == "buffer.add_audio":
            audio_data = message.get("audio")

        elif message["type"] == "buffer.clear_audio":
            pass

        elif message["type"] == "generate.text_audio":
            text = message.get("text", "")

        elif message["type"] == "generate.only_text":
            text = message.get("text", "")

        elif message["type"] == "generate.cancel":
            pass

@app.get("/")
async def root():
    with open("srcs/test.html", "r") as file:
        return HTMLResponse(file.read())

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)