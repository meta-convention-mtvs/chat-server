from fastapi import WebSocket
import websockets
import asyncio
import json
import os

ERROR_REQ_PARAM = {"type": "server.error", "code": 4}
INSTRUCTION = """
You are an AI introducing a company in an exhibition hall.
You must introduce the company and its items based on the information, and you must provide assistance using only the given company information and product information.
Since this is a place to introduce the company and its products, please only give positive answers.
Users often want a simple explanation from you. Please answer as concisely as possible, and only give detailed answers if the user wants a detailed answer.
Please answer in the same language as the user.
"""
SAMPLE_INFO = """
당신은 Apple에 대해 소개해야 합니다.
{
    "company_name": "Apple",
    "company_mission": "혁신이라는 이름으로 애플은 많은 제품을 내놓았았습니다. 아이폰, 아이패드, 맥, 애플워치 등 대부분의 사람들이 들으면 단번에 알 수 있는 제품들이며 이 제품들은 이미 사람들의 우리의 삶에 깊숙이 자리 잡았습니다. 하지만 애플은 단순히 새로운 제품을 만드는 것에 그치지 않습니다. 애플의 궁극적인 목표는 사용자에게 최고의 경험을 제공하는 것입니다. 애플은 '혁신적인 하드웨어, 소프트웨어 등 서비스들을 통해 소비자들에게 최고의 제품사용경험을 제공하겠다'는 사업 목표를 가지고 있습니다. 이는 단순히 기술적 진보에 그치는 것이 아니라, 사용자 경험을 획기적으로 개선하고 시장 기준을 새롭게 정립하는 것을 의미합니다. 애플의 제품들은 직관적이고 세련된 디자인, 강력한 성능, 그리고 끊김 없는 생태계를 바탕으로 사용자에게 최상의 경험을 선사합니다. 아이폰, 아이패드, 맥북 등 모든 기기가 긴밀하게 연결되어 일관되고 편리한 사용자 경험을 제공하는 것이 바로 애플만의 강점입니다.",
    "company_website": "https://www.apple.com/",
    "products": [
        {
            "name": "애플워치2",
            "description": "애플워치 시리즈 2 개요\n애플워치 시리즈 2는 2016년 9월에 출시된 애플의 두 번째 세대 스마트워치입니다. 초기 모델의 성공을 바탕으로 여러 가지 중요한 개선 사항을 도입하여 사용자 경험을 한층 향상시켰습니다.\n주요 특징\n1. 방수 기능\n50미터 방수 기능 탑재\n수영 등 수중 활동 시 착용 가능\n2. 내장 GPS\n독립적인 위치 추적 가능\n스마트폰 없이도 러닝 경로 기록\n3. 향상된 성능\n듀얼 코어 S2 칩 탑재로 처리 속도 향상\n더 밝아진 디스플레이 (1000 니트)\n4. watchOS 3\n더 빠르고 직관적인 사용자 인터페이스\n새로운 앱과 기능 추가\n5. 건강 및 피트니스 기능 강화\n수영 운동 추적 기능\n심박수 모니터링 개선\n디자인 및 모델\n알루미늄, 스테인리스 스틸, 세라믹 등 다양한 소재\n38mm와 42mm 두 가지 크기 옵션\nNike+, Hermès 등 특별 에디션 모델 출시\n배터리 수명\n일반 사용 시 약 18시간\nGPS 사용 시 약 5시간",
            "resources": [
                {
                    "type": "3d", 
                    "description": "애플워치2의 3d 오브젝트 모델"
                }
            ]
        }
    ]
}
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
    
    async def load(self, org_id):
        url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "OpenAI-Beta": "realtime=v1",
        }
        self.ai = await websockets.connect(url, extra_headers=headers)
        loop = asyncio.get_event_loop()
        loop.create_task(self.onmessage())
        await self.ai.send(json.dumps({ "type": "session.update", "session": { "instructions": INSTRUCTION }}))
        await self.add_text("user", await self.load_org_info(org_id), "input_text")
        # await self.add_text("system", SAMPLE_INFO, "input_text")
    
    async def load_org_info(self, org_id):
        return SAMPLE_INFO
    
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