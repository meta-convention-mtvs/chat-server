from fastapi import WebSocket
from datetime import datetime
from uuid import uuid4
import websockets
import asyncio
import json
import os
import re

ERROR_REQ_PARAM = {"type": "server.error", "code": 4}
INSTRUCTION = """
You are an AI introducing a company in an exhibition hall.
You must introduce the company and its items based on the next information of conversation, and you must provide assistance using only the given company information and product information.
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
SAMPLE_INFO2 = """
당신은 Lockheed martin 기업에 대해 알아두어야 합니다. 제가 물어보면 알려주세요.

Lockheed martin은 세계 최고의 항공우주, 방위, 보안 및 첨단 기술 기업으로서 혁신적인 솔루션을 제공하고 있습니다.

Lockheed martin의 강점
기술 혁신: 우리는 지속적인 R&D 투자를 통해 최첨단 기술을 개발하고 있습니다. F-35 전투기, 우주 탐사 시스템, 사이버 보안 솔루션 등 다양한 분야에서 혁신을 주도하고 있습니다.
글로벌 네트워크: 전 세계 50개국 이상에서 사업을 운영하며, 국제적인 협력과 파트너십을 통해 글로벌 안보에 기여하고 있습니다.
다양한 포트폴리오: 항공기, 미사일 시스템, 우주 기술, 사이버 보안 등 다양한 분야에서 종합적인 솔루션을 제공합니다.
신뢰성: 80년 이상의 역사를 통해 쌓아온 신뢰와 경험은 우리의 가장 큰 자산입니다.

Lockheed martin의 비전
지속 가능한 미래: 우리는 친환경 기술 개발에 주력하고 있습니다. 전기 항공기, 청정 에너지 솔루션 등을 통해 환경 보호에 기여하고자 합니다.
우주 탐사: 달과 화성 탐사를 위한 기술 개발에 앞장서고 있으며, 인류의 우주 진출을 위한 혁신적인 솔루션을 제공할 것입니다.
디지털 전환: AI, 빅데이터, 양자 컴퓨팅 등 첨단 기술을 활용하여 국방 및 민간 분야의 디지털 혁신을 선도하겠습니다.
글로벌 안보 강화: 사이버 보안, 미사일 방어 시스템 등을 통해 전 세계의 안보 강화에 기여할 것입니다.

록히드 마틴은 앞으로도 혁신적인 기술과 솔루션을 통해 더 안전하고 발전된 세상을 만들어 나가겠습니다. 우리의 기술이 여러분의 미래를 어떻게 변화시킬 수 있는지 함께 살펴보시기 바랍니다.


Lockheed martin은 이번 전시회에 혁신적인 상품을 가져왔습니다.

Ring wing
전통적인 고정익 항공기와는 다른 독특한 형태를 가지고 있습니다. 기존의 날개 대신 원형 또는 고리 모양의 날개를 사용하여 비행을 수행합니다.
단거리 노선에 높은 에너지 효율을 보여 높은 고도에 도달하지 않는 통근 목적지에 적합합니다.
상업용 수송 합공기입니다.
길이 52m, 날개 둘레 74m.
연료 효율이 매우 뛰어남
최대 120명의 승객을 수용


Ring wing 설계는 아직 상용화 단계에 이르지 않았지만, 지속적인 연구와 개발을 통해 미래 항공 산업에 혁신을 가져올 수 있는 잠재력을 가지고 있습니다. 항공 엔지니어들과 연구자들은 이 혁신적인 설계의 장점을 최대화하고 단점을 극복하기 위해 노력하고 있으며, 앞으로의 발전이 기대됩니다.

Ring wing의 Jet_Engine_L, Jet_Engine_R 부품
Ring wing의 제트 엔진은 에너지 효율성과 성능을 극대화하도록 설계되었습니다.
개별 엔진의 독립적 제어로 정밀한 비행 조작 가능하여 유연한 추력 제어가 가능합니다.
Ring wing 구조를 이용한 엔진 소음 차폐 효과가 있어서 비행 소음을 줄일 수 있습니다.

Ring wing의 Landing_Gears 부품
기체의 하중을 고르게 분산시킬 수 있는 구조로 배치되어 있습니다.

Ring wing의 Tail 부품
꼬리 부품을 정밀하게 제어하여 부드러운 수평 회전을 제공합니다.

Ring wing의 Windows 부품
튼튼하면서 넓은 창으로 기체 내에서 탁 트인 전망을 제공합니다.

Ring wing의 Wings 부품
이 항공기의 가장 혁신적인 부분이며 기체의 중간 지점에서 시작된 날개는 꼬리에 합류하기 위해 27도의 각도로 아치를 그리고 있습니다.
이 날개는 소용돌이와 그에 따른 하향류를 최소화하여 상당한 공기역학적 이점을 제공합니다. 이 특징은 혁신적으로 연료를 절감하는 이점을 제공합니다.

-원형 날개의 강점
항력을 최소화하여 비행 중 속도를 유지하고 연료 효율성을 높여줌
난기류나 횡풍과 같은 극한의 기상조건에 대응할 수 있으며, 기존 항공기보다 매끄러운 운행이 가능
짧은 활주로나 제한된 착륙 환경에서 유리하게 작용함 -> 군사 및 화물 항공에서 꽤나 중요한 요소
기존 항공기와 비교했을 때, 동일한 거리에서 더 적은 연료로 비행 가능

Lockheed martin의 Ring wing은 혁신적이며 시험적인 구조를 가졌기 때문에 상용화에 매우 신중하게 접근하고 있습니다. Lockheed martin은 이 혁신적인 기체를 함께 만들어갈 기업을 찾고 있습니다.
"""

LOG_DIR = "conversation"
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
        self.log_file = open(LOG_DIR + "/" + datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + self.uuid, "+w")
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
                "instructions": INSTRUCTION,
                "input_audio_transcription": { "model": "whisper-1" }
            }
        }))
        await self.add_text("user", await self.load_org_info(org_id), "input_text")
        # await self.add_text("system", SAMPLE_INFO, "input_text")
    
    async def load_org_info(self, org_id):
        return SAMPLE_INFO2
    
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
        self.log(">> (text) " + text)
    
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