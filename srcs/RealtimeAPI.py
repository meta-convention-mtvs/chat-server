from fastapi import WebSocket
import websockets
import asyncio
import json
import os

ERROR_REQ_PARAM = {"type": "server.error", "code": 4}

class LLMConsole:
    STATUS_WAIT = 0
    STATUS_RUN = 1
    
    def __init__(self, ws: WebSocket, org):
        self.ws = ws
        self.org = org
        self.status = LLMConsole.STATUS_WAIT
        self.use_audio = False
        self.modalities = None
    
    async def load(self):
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.ai = await websockets.connect(url, extra_headers=headers)
        loop = asyncio.get_event_loop()
        loop.create_task(self.onmessage())
    
    async def add_audio(self, buffer):
        if not buffer:
            return
        self.use_audio = True
        await self.ai.send(json.dumps({
            "type": "input_audio_buffer.append",
            "audio": buffer
        }))
    
    async def clear_audio(self):
        self.use_audio = False
        await self.ai.send(json.dumps({ "type": "input_audio_buffer.clear" }))
    
    async def add_text(self, text):
        await self.ai.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{ "type": "input_text", "text": text }]
            }
        }))
    
    async def generate(self, modalities=["text", "audio"]):
        if self.status != LLMConsole.STATUS_WAIT:
            await self.ws.send_json({"type": "server.error", "code": 3}) # dup
            return
        self.modalities = modalities
        self.status = LLMConsole.STATUS_RUN
        if self.use_audio:
            self.use_audio = False
            await self.ai.send(json.dumps({ "type": "input_audio_buffer.commit" }))
        await self.ai.send(json.dumps({ "type": "response.create", "response": {"modalities": modalities} }))

    async def cancel(self):
        if self.status == LLMConsole.STATUS_WAIT:
            return
        self.status = LLMConsole.STATUS_WAIT
        if "text" in self.modalities:
            self.ws.send_json({ "type": "generated.text.canceled" })
        if "audio" in self.modalities:
            self.ws.send_json({ "type": "generated.audio.canceled" })

    async def onmessage(self):
        while True:
            raw = await self.ai.recv()
            data = json.loads(raw)
            if data.get("type") == "response.audio_transcript.delta" or data.get("type") == "response.text.delta":
                await self.ws.send_json({ "type": "generated.text.delta", "delta": data.get("delta") })
                print("generated.text.delta:", data.get("delta"), flush=True)
            elif data.get("type") == "response.audio_transcript.done" or data.get("type") == "response.text.done":
                await self.ws.send_json({ "type": "generated.text.done", "text": data.get("transcript", data.get("text")) })
                print("generated.text.done:", data.get("transcript", data.get("text")), flush=True)
            elif data.get("type") == "response.audio.delta":
                await self.ws.send_json({ "type": "generated.audio.delta", "delta": data.get("delta") })
                print("generated.audio.delta:", str(len(data.get("delta"))), flush=True)
            elif data.get("type") == "response.audio.done":
                await self.ws.send_json({ "type": "generated.audio.done" })
                print("generated.audio.done:", data.get("audio done!"), flush=True)
            elif data.get("type") == "response.done":
                self.status = LLMConsole.STATUS_WAIT
                print("response.done", flush=True)
            elif data.get("type") == "error":
                print("error:", data.get("error"), flush=True)
            else:
                print("ect:", data, flush=True)

    async def send_text(self, text, time=0.016):
        if self.status != LLMConsole.STATUS_RUN or "text" not in self.generate_type:
            return
        await self.ws.send_json({ "type": "generated.text.delta", "delta": text })
        await asyncio.sleep(time)
    async def send_audio(self, file_name, time=0.016):
        if self.status != LLMConsole.STATUS_RUN or "audio" not in self.generate_type:
            return
        with open(file_name) as file:
            content = file.read()
        await self.ws.send_json({ "type": "generated.audio.delta", "delta": content })
        await asyncio.sleep(time)
    # await asyncio.sleep(0.016)
    # await send_text("메타")
    # await send_text(" 컨벤션")
    # await send_audio("srcs/sample/pcm_file_0.txt")
    # await send_audio("srcs/sample/pcm_file_1.txt")
    # await send_audio("srcs/sample/pcm_file_2.txt")
    # await send_text("에")
    # await send_text(" 오신")
    # await send_text(" 것")
    # await send_audio("srcs/sample/pcm_file_3.txt")
    # await send_audio("srcs/sample/pcm_file_4.txt")
    # await send_audio("srcs/sample/pcm_file_5.txt")
    # await send_text("을", time=0.5)
    # await send_text(" 환영")
    # await send_text("합니다")
    # await send_text(".")
    # if self.status == LLMConsole.STATUS_RUN and "text" in self.modalities:
    #     await self.ws.send_json({ "type": "generated.text.done" })
    #     await asyncio.sleep(0.016)
    # await send_audio("srcs/sample/pcm_file_6.txt")
    # await send_audio("srcs/sample/pcm_file_7.txt")
    # await send_audio("srcs/sample/pcm_file_8.txt", time=1)
    # await send_audio("srcs/sample/pcm_file_9.txt")
    # if self.status == LLMConsole.STATUS_RUN and "audio" in self.modalities:
    #     await self.ws.send_json({ "type": "generated.audio.done" })
    #     await asyncio.sleep(0.016)
    # self.status = LLMConsole.STATUS_WAIT

    def log(self, s):
        with open("srcs/conn.log", "+a") as file:
            file.write(s + "\n")