import asyncio
from uuid import uuid4
from EventHandler import EventHandler
from RealtimeClient import RealtimeClient
from fastapi import WebSocket

ERR_FATAL = 1
ERR_FAIL_CREATE_ROOM = 2
ERR_FAIL_JOIN_ROOM = 3
ERR_FAIL_EXIT_ROOM = 4
ERR_FAIL_APPROVE_SPEECH = 5
ERR_FAIL_SPEECH = 6

class Manager:
    def __init__(self):
        self.rooms: list[Room] = []

    async def accept(self, websocket: WebSocket) -> 'User':
        await websocket.accept()
        user = User(Connection(websocket))
        user.set_observer(self)
        return user

    async def onmessage(self, user: 'User', message):
        type = message.get("type", "")
        if type == "disconnected":
            pass
        elif type == "room.create":
            lang = message.get("lang", None)
            userid = message.get("userid", None)
            roomid = message.get("roomid", None)
            if lang is None or userid is None:
                await user.send_error(ERR_FAIL_CREATE_ROOM)
                return
            user.id = userid
            new_room = self.create_room(roomid)
            if new_room is None:
                await user.send_error(ERR_FAIL_CREATE_ROOM)
                return
            await new_room.join(user)
        elif type == "room.join":
            lang = message.get("lang", None)
            roomid = message.get("roomid", None)
            userid = message.get("userid", None)
            if lang is None or userid is None:
                await user.send_error(ERR_FAIL_CREATE_ROOM)
                return
            for room in self.rooms:
                if room.uuid == roomid:
                    await room.join(user)
                    return
            await user.send_error(ERR_FAIL_JOIN_ROOM)
        else:
            await user.send_error(ERR_FATAL)
            return
    
    def create_room(self, roomid = None) -> 'Room':
        new_room = Room(self, roomid)
        for room in self.rooms:
            if room.uuid == new_room.uuid:
                return None
        self.rooms.append(new_room)
        return new_room

    def destroy_room(self, room: 'Room'):
        room.free()
        self.rooms.remove(room)

    async def broadcast(self, conns: list['Connection'], json_data: dict):
        await asyncio.gather(*[conn.send(json_data) for conn in conns], return_exceptions=True)

class Room:
    def __init__(self, manager: Manager, id = None):
        self.manager = manager
        if id is None or not id:
            id = str(uuid4())
        self.uuid = id
        self.ready = False
        self.users: list[User] = []
        self.order = 0
        self.speech = None

    async def join(self, user: 'User'):
        self.users.append(user)
        user.set_observer(self)
        await user.send_join(self.uuid, self.users)
        await self.broadcast_update()

    async def onmessage(self, user: 'User', message):
        type = message.get("type", "")
        if type == "disconnected":
            if self.speech == user:
                self.speech = None
            self.users.remove(user)
            user.set_observer(self.manager)
            await self.broadcast_update()
            if len(self.users) == 0:
                self.manager.destroy_room(self)
        elif type == "room.leave":
            await user.send_bye()
            await user.conn.disconnect()
        elif type == "conversation.request_speech":
            if self.speech is None:
                self.speech = user
                self.order += 1
                await self.broadcast_approve(self.order, self.speech, "")
            else:
                await user.send_error(ERR_FAIL_APPROVE_SPEECH)
        elif type == "conversation.buffer.add_audio":
            if self.speech != user:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            # TODO: add audio source to realtime-api
            pass
        elif type == "conversation.buffer.clear_audio":
            if self.speech != user:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            self.speech = None
        elif type == "conversation.done_speech":
            if self.speech != user:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            self.speech = None
        else:
            await user.send_error(ERR_FATAL)
            return

    def free(self):
        # TODO: disconnect realtime-api
        pass

    async def broadcast(self, json_data: dict):
        await asyncio.gather(*[user.send(json_data) for user in self.users], return_exceptions=True)

    async def broadcast_approve(self, order, user: 'User', trans):
        await self.broadcast({
            "type": "conversation.approved_speech",
            "order": order,
            "userid": user.id,
            "lang": user.lang,
            "trans": trans,
        })

    async def broadcast_update(self):
        await self.broadcast({
            "type": "room.updated",
            "roomid": self.uuid,
            "ready": self.ready,
            "users": [{"userid": user.id, "lang": user.lang} for user in self.users],
        })

    async def broadcast_text_delta(self, order, delta):
        await self.broadcast({
            "type": "conversation.text.delta",
            "order": order,
            "delta": delta,
        })
        
    async def broadcast_text_done(self, order, text):
        await self.broadcast({
            "type": "conversation.text.done",
            "order": order,
            "text": text,
        })

    async def broadcast_audio_delta(self, order, delta):
        await self.broadcast({
            "type": "conversation.audio.delta",
            "order": order,
            "delta": delta,
        })

    async def broadcast_audio_done(self, order):
        await self.broadcast({
            "type": "conversation.audio.done",
            "order": order,
        })

class User:
    def __init__(self, conn: 'Connection', lang: str = None, id: str = None):
        self.observer = None
        conn.observe_disconnect(self)
        self.conn = conn
        self.conn.on("*", self.onmessage)
        if lang is None:
            lang = "en"
        if id is None:
            id = str(uuid4())
        self.lang = lang
        self.id = id

    def set_observer(self, observer):
        self.observer = observer

    async def disconnected(self, _):
        await self.onmessage({"type":"disconnected"})

    async def onmessage(self, message):
        if self.observer is not None:
            await self.observer.onmessage(self, message)
            
    async def send(self, json_data):
        await self.conn.send(json_data)
    
    async def send_error(self, code):
        await self.send({ "type": "server.error", "code": code })

    async def send_join(self, room_id, users: list['User']):
        await self.send({
            "type": "room.joined",
            "roomid": room_id,
            "users": [{"userid": user.id, "lang": user.lang} for user in users],
        })

    async def send_bye(self):
        await self.send({
            "type": "room.bye",
        })
    
class Connection(EventHandler):
    def __init__(self, websocket: WebSocket):
        super().__init__()
        self.ws = websocket
        self.disconnect_observers = []

    async def loop_until_close(self):
        try:
            while True:
                data = await self.ws.receive_json()
                type = data.get("type", "")
                callbacks = [ callback(data) for callback in self.get_callbacks(type) ]
                await asyncio.gather(*callbacks, return_exceptions=True)
        except:
            await self.disconnect()

    def observe_disconnect(self, observer):
        self.disconnect_observers.append(observer)

    async def disconnect(self):
        for ob in self.disconnect_observers:
            await ob.disconnected(self)
    
    async def send(self, json_data):
        await self.ws.send_json(json_data)
