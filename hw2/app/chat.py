import random
import string
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict

chat_rooms: Dict[str, 'ConnectionManager'] = {}


def generate_username() -> str:
    return ''.join(random.choices(string.ascii_letters, k=8))


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


async def websocket_endpoint(websocket: WebSocket, chat_name: str):
    if chat_name not in chat_rooms:
        chat_rooms[chat_name] = ConnectionManager()

    manager = chat_rooms[chat_name]
    await manager.connect(websocket)

    username = generate_username()

    try:
        while True:
            data = await websocket.receive_text()
            broadcast_message = f"{username} :: {data}"
            await manager.broadcast(broadcast_message)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"{username} has left the chat")
