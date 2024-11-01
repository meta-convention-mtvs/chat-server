from fastapi import WebSocket
from datetime import datetime
from uuid import uuid4
import websockets
import asyncio
import json
import os
import re
from prompt import instruction
from sample import org_rockhead_martin

ERROR_REQ_PARAM = {"type": "server.error", "code": 4}
FOOTER = "만일 제가 담당자와의 연결을 원하면, 관심을 가져줌에 감사함을 전하고, 화면에 보이는 '비즈니스 미팅 신청' 버튼을 누르라고 응답해주세요."
LOG_DIR = "/conversation"
os.makedirs(LOG_DIR, exist_ok=True)

class LLMConsole:
    STATUS_WAIT = 0
    STATUS_RUN = 1
    
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.status = LLMConsole.STATUS_WAIT
        self.use_audio = False
        self.modalities = None
        self.uuid = str(uuid4())
        self.log_file = None
    
    async def load(self):
        self.log_file = open(LOG_DIR + "/" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + self.uuid + ".txt", "+w")
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.ai = await websockets.connect(url, extra_headers=headers)
        loop = asyncio.get_event_loop()
        loop.create_task(self.onmessage())
    
    async def set_org(self, org_id):
        await self.ai.send(json.dumps({
            "type": "session.update",
            "session": { 
                "instructions": instruction.CONTENT,
                "input_audio_transcription": { "model": "whisper-1" }
            }
        }))
        await self.add_text("user", await self.load_org_info(org_id), "input_text", log_label="prompt")
        await self.add_text("user", FOOTER, "input_text", log_label="prompt")
        # await self.add_text("system", SAMPLE_INFO, "input_text")
    
    async def load_org_info(self, org_id):
        return org_rockhead_martin.CONTENT
    
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
    
    async def add_text(self, role, text, type="input_text", log_label="text"):
        await self.ai.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "status": "completed",
                "role": role,
                "content": [{ "type": type, "text": text }]
            }
        }))
        if log_label == "prompt":
            self.log(f">>> ({log_label}) {text}")
        else:
            self.log(f">> ({log_label}) {text}")
    
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
        await self.ai.send(json.dumps({ "type": "response.cancel" }))
        if "text" in self.modalities:
            await self.ws.send_json({ "type": "generated.text.canceled" })
        if "audio" in self.modalities:
            await self.ws.send_json({ "type": "generated.audio.canceled" })

    async def onmessage(self):
        while True:
            raw = await self.ai.recv()
            data = json.loads(raw)
            if self.status == LLMConsole.STATUS_RUN and (data.get("type") == "response.audio_transcript.delta" or data.get("type") == "response.text.delta"):
                await self.ws.send_json({ "type": "generated.text.delta", "delta": data.get("delta") })
                print("generated.text.delta:", data.get("delta"), flush=True)
            elif self.status == LLMConsole.STATUS_RUN and (data.get("type") == "response.text.done"):
                await self.ws.send_json({ "type": "generated.text.done", "text": data.get("text") })
                print("generated.text.done:", data.get("text"), flush=True)
                self.log("<< (text) " + data.get("text"))
            elif self.status == LLMConsole.STATUS_RUN and data.get("type") == "response.audio_transcript.done":
                await self.ws.send_json({ "type": "generated.text.done", "text": data.get("transcript") })
                print("generated.text.done:", data.get("transcript"), flush=True)
                self.log("<< (audio) " + data.get("transcript"))
            elif self.status == LLMConsole.STATUS_RUN and (data.get("type") == "response.audio.delta"):
                await self.ws.send_json({ "type": "generated.audio.delta", "delta": data.get("delta") })
                print("generated.audio.delta:", str(len(data.get("delta"))), flush=True)
            elif self.status == LLMConsole.STATUS_RUN and (data.get("type") == "response.audio.done"):
                await self.ws.send_json({ "type": "generated.audio.done" })
                print("generated.audio.done:", data.get("audio done!"), flush=True)
            elif data.get("type") == "conversation.item.input_audio_transcription.completed":
                self.log(">> (audio) " + data.get("transcript", ""))
            elif data.get("type") == "response.done":
                self.status = LLMConsole.STATUS_WAIT
                print("response.done", flush=True)
            elif data.get("type") == "error":
                print("error:", data.get("error"), flush=True)
            else:
                if "delta" in data:
                    data["delta"] = str(len(data.get("delta")))
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
        self.log_file.write(str(datetime.now()) + ": " + re.sub(r"\s+", " ", s) + "\n")
        self.log_file.flush()
        
    async def free(self):
        self.log("close")
        self.log_file.close()
        await self.ws.close()
        await self.ai.close()