import asyncio
from uuid import uuid4
from EventHandler import EventHandler
from RealtimeClient import RealtimeClient
from fastapi import WebSocket
from prompt import translation

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
            user.lang = lang
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
            user.id = userid
            user.lang = lang
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

    async def destroy_room(self, room: 'Room'):
        self.rooms.remove(room)
        await room.free()

    async def broadcast(self, conns: list['Connection'], json_data: dict):
        await asyncio.gather(*[conn.send(json_data) for conn in conns], return_exceptions=True)

class Room:
    def __init__(self, manager: Manager, id = None):
        self.realtime = RealtimeClient()
        self.realtime.on("*", self.onrealtime)
        self.manager = manager
        if id is None or not id:
            id = str(uuid4())
        self.uuid = id
        self.ready = False
        self.users: list[User] = []
        self.order = 0
        self.speech = None
        self.langs = []

    async def join(self, user: 'User'):
        self.users.append(user)
        user.set_observer(self)
        await user.send_join(self.uuid, self.users)
        self.langs = list(set([user.lang for user in self.users]))
        if len(self.users) > 1 and self.realtime.is_usable() == False and len(self.langs) > 1:
            await self.realtime.connect()
            instructions = translation.CONTENT.format(lang1=self.langs[0], lang2=self.langs[1])
            await self.realtime.send({
                "type": "session.update",
                "session": { "instructions": instructions }
            })
            self.ready = True
        await self.broadcast_update()

    async def onrealtime(self, json_data):
        type = json_data.get("type", "")
        if type == "error":
            print(json_data, flush=True)
        elif type == "response.text.delta":
            await self.broadcast_text_delta(self.order, json_data.get("delta", ""))
        elif type == "response.text.done":
            await self.broadcast_text_done(self.order, json_data.get("text", ""))
        elif type == "response.audio_transcript.delta":
            await self.broadcast_text_delta(self.order, json_data.get("delta", ""))
        elif type == "response.audio_transcript.done":
            await self.broadcast_text_done(self.order, json_data.get("transcript", ""))
        elif type == "response.audio.delta":
            await self.broadcast_audio_delta(self.order, json_data.get("delta", ""))
        elif type == "response.audio.done":
            await self.broadcast_audio_done(self.order)

    async def onmessage(self, user: 'User', message):
        type = message.get("type", "")
        if type == "disconnected":
            if self.speech == user:
                self.speech = None
            self.users.remove(user)
            user.set_observer(self.manager)
            await self.broadcast_update()
            if len(self.users) == 0:
                await self.manager.destroy_room(self)
        elif type == "room.leave":
            await user.send_bye()
            await user.conn.disconnect()
        elif type == "conversation.request_speech":
            if self.speech is None:
                self.speech = user
                self.order += 1
                trans = self.langs[0] if self.speech.lang != self.langs[0] else self.langs[1]
                await self.broadcast_approve(self.order, self.speech, "" if trans is None else trans)
            else:
                await user.send_error(ERR_FAIL_APPROVE_SPEECH)
        elif type == "conversation.buffer.add_audio":
            audio = message.get("audio", None)
            if audio is None:
                print("debug: conversation.buffer.add_audio - no audio field", flush=True)
                await user.send_error(ERR_FAIL_SPEECH)
                return
            if self.speech != user:
                print("debug: conversation.buffer.add_audio - no speech", flush=True)
                await user.send_error(ERR_FAIL_SPEECH)
                return
            if self.realtime.is_usable() == False:
                print("debug: conversation.buffer.add_audio - no realtime", flush=True)
                await user.send_error(ERR_FAIL_SPEECH)
                return
            await self.realtime.send({
                "type": "input_audio_buffer.append",
                "audio": audio
            })
        elif type == "conversation.buffer.clear_audio":
            if self.speech != user:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            self.speech = None
            if self.realtime.is_usable() == False:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            await self.ready.send({
                "type": "input_audio_buffer.clear"
            })
        elif type == "conversation.done_speech":
            if self.speech != user:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            self.speech = None
            if self.realtime.is_usable() == False:
                await user.send_error(ERR_FAIL_SPEECH)
                return
            await self.realtime.send({
                "type": "input_audio_buffer.commit"
            })
            await self.realtime.send({
                "type": "response.create"
            })

        else:
            await user.send_error(ERR_FATAL)
            return

    async def free(self):
        await self.realtime.disconnect()

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
        except Exception as e:
            print(e, flush=True)
            await self.disconnect()

    def observe_disconnect(self, observer):
        self.disconnect_observers.append(observer)

    async def disconnect(self):
        for ob in self.disconnect_observers:
            await ob.disconnected(self)
    
    async def send(self, json_data):
        await self.ws.send_json(json_data)
