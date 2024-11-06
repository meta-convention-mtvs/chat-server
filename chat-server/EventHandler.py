class EventHandler:
    def __init__(self):
        self.callbacks: dict[str, list] = {}
        self.clear()

    def clear(self):
        self.callbacks = { "*": [ ]}

    def on(self, type: str, callback: callable):
        if type is None or not type:
            raise Exception()
        if type not in self.callbacks:
            self.callbacks[type] = []
        self.callbacks[type].append(callback)

    def off(self, type: str, callback: callable):
        if type is None or not type:
            raise Exception()
        if type not in self.callbacks:
            return
        self.callbacks[type].remove(callback)

    def get_callbacks(self, type) -> list:
        if type is None or not type:
            raise Exception()
        res = []
        res += self.callbacks.get("*", [])
        res += self.callbacks.get(type, [])
        return res