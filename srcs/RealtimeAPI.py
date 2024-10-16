from fastapi import WebSocket
import asyncio

class LLMConsole:
    STATUS_WAIT = 0
    STATUS_RUN = 1
    
    def __init__(self, ws: WebSocket, org):
        self.ws = ws
        self.org = org
        self.status = LLMConsole.STATUS_WAIT
        self.generate_type = None
    
    async def add_audio(self, buffer):
        pass
    
    async def clear_audio(self):
        pass
    
    async def add_text(self, text):
        pass
    
    async def generate(self, type=["text", "audio"]):
        self.generate_type = type
        self.status = LLMConsole.STATUS_RUN
        await asyncio.sleep(0.016)
        async def send_text(text):
            if self.status == LLMConsole.STATUS_RUN and "text" in self.generate_type:
                await self.ws.send_json({ "type": "generated.text.delta", "delta": text })
                await asyncio.sleep(0.016)
        async def send_audio(file_name):
            with open(file_name) as file:
                content = file.read()
            await self.ws.send_json({ "type": "generated.audio.delta", "delta": content })
            await asyncio.sleep(0.016)
        send_text("메타")
        send_text(" 컨벤션")
        send_audio("srcs/sample/pcm_file_0.txt")
        send_audio("srcs/sample/pcm_file_1.txt")
        send_audio("srcs/sample/pcm_file_2.txt")
        send_text("에")
        send_text(" 오신")
        send_text(" 것")
        send_audio("srcs/sample/pcm_file_3.txt")
        send_audio("srcs/sample/pcm_file_4.txt")
        send_audio("srcs/sample/pcm_file_5.txt")
        send_text("을")
        send_text(" 환영")
        send_text("합니다")
        send_text(".")
        if self.status == LLMConsole.STATUS_RUN and "text" in self.generate_type:
            await self.ws.send_json({ "type": "generated.text.done" })
            await asyncio.sleep(0.016)
        send_audio("srcs/sample/pcm_file_6.txt")
        send_audio("srcs/sample/pcm_file_7.txt")
        send_audio("srcs/sample/pcm_file_8.txt")
        send_audio("srcs/sample/pcm_file_9.txt")
        if self.status == LLMConsole.STATUS_RUN and "audio" in self.generate_type:
            await self.ws.send_json({ "type": "generated.audio.done" })
            await asyncio.sleep(0.016)

    async def cancel(self):
        if self.status == LLMConsole.STATUS_WAIT:
            return
        self.status = LLMConsole.STATUS_WAIT
        if "text" in self.generate_type:
            self.ws.send_json({ "type": "generated.text.canceled" })
        if "audio" in self.generate_type:
            self.ws.send_json({ "type": "generated.audio.canceled" })
