import websockets
import asyncio
import json
import os
from EventHandler import EventHandler

class DisconnectedError(Exception):
    """OpenAI의 RealtimeAPI와 연결이 끊겼거나 연결이 되어 있지 않음"""

class RealtimeClient(EventHandler):
    model = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "OpenAI-Beta": "realtime=v1",
    }
    def __init__(self):
        super().__init__()
        self.ws: websockets.client.WebSocketClientProtocol = None
        self.usable = False
        self.listen_task = None
    
    def log(self, message):
        print(">", message, flush=True)

    async def connect(self):
        self.ws = await websockets.connect(RealtimeClient.model, extra_headers=RealtimeClient.headers)
        loop = asyncio.get_event_loop()
        self.listen_task = loop.create_task(self.onmessage())
        self.usable = True

    async def disconnect(self):
        self.usable = False
        if self.ws.close_code is None:
            await self.ws.close()

    async def send(self, json_data):
        if self.ws is None:
            raise DisconnectedError()
        await self.ws.send(json.dumps(json_data))

    async def onmessage(self):
        while True:
            try:
                raw = await self.ws.recv()
                json_data = json.loads(raw)
                type = json_data["type"]
                callbacks = [callback(json_data) for callback in self.get_callbacks(type)]
                await asyncio.gather(*callbacks, return_exceptions=True)
            except websockets.exceptions.ConnectionClosed:
                self.usable = False
                return

    def is_usable(self):
        return self.usable

class RealtimeDebugger:
    def __init__(self, client: RealtimeClient):
        self.client = client
        self.client.on("*", self.onevent)
    
    async def send2server(self, json_data):
        await self.client.send(json_data)
    
    async def onevent(self, json_data):
        print(json_data, flush=True)