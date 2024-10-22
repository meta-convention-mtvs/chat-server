from fastapi import WebSocket
import websockets
import asyncio
import json
import os

ERROR_REQ_PARAM = {"type": "server.error", "code": 4}
INSTRUCTION = "당신은 전시장의 한 기업을 소개하는 AI입니다. 정보를 바탕으로 기업과 기업의 아이템을 소개해야하며 주어진 정보를 바탕으로 도움을 주어야 합니다. 회사와 상품을 소개하는 자리이므로 긍정적인 답변만 해주세요."
SAMPLE_INFO = """
회사 이름: 메타버스아카데미
회사 소개: 메타버스아카데미는 융합적 사고, 인문학적 사고, 협업능력, 창의적 사고, 도전정신의 인재상을 기르는 메타버스 교육기관입니다.
아이템: AI, XR, TA, 기획, 백엔드 기술을 가르치고 미래 인재상에 걸맞는 인재를 양성하는 프로젝트를 가지고 있습니다.
"""

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
        await self.ai.send(json.dumps({ "type": "session.update", "session": { "instructions": INSTRUCTION }}))
        await self.add_text("user", SAMPLE_INFO, "input_text")
        # await self.add_text("system", SAMPLE_INFO, "input_text")
    
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
    
    async def add_text(self, role, text, type="input_text"):
        await self.ai.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "status": "completed",
                "role": role,
                "content": [{ "type": type, "text": text }]
            }
        }))
    
    def is_gen_ready(self):
        return self.status == LLMConsole.STATUS_WAIT

    async def response_error(self, code):
        await self.ws.send_json({"type": "server.error", "code": code}) # dup
        
    
    async def generate(self, modalities=["text", "audio"]):
        if not self.is_gen_ready():
            return
        self.modalities = modalities
        self.status = LLMConsole.STATUS_RUN
        if self.use_audio:
            self.use_audio = False
            await self.ai.send(json.dumps({ "type": "input_audio_buffer.commit" }))
        await self.ai.send(json.dumps({ "type": "response.create", "response": {"modalities": self.modalities} }))

    async def cancel(self):
        if self.is_gen_ready():
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

    def log(self, s):
        with open("srcs/conn.log", "+a") as file:
            file.write(s + "\n")