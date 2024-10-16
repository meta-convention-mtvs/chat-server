class LLMConsole:
    STATUS_WAIT = 0
    STATUS_RUN = 1
    
    def __init__(self, ws, org):
        self.ws = ws
        self.org = org
        self.status = LLMConsole.STATUS_WAIT
    
    async def add_audio(self, buffer):
        pass
    
    async def clear_audio(self):
        pass
    
    async def add_text(self, text):
        pass
    
    async def generate(self, type=["text", "audio"]):
        pass
    
    async def cancel():
        pass
