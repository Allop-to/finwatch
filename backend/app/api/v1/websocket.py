from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: Dict[int, WebSocket] = {}

    async def connect(self, ws: WebSocket, user_id: int = 1):
        await ws.accept()
        self.active[user_id] = ws

    def disconnect(self, user_id: int = 1):
        self.active.pop(user_id, None)

    async def broadcast(self, event: dict, user_id: int = 1):
        ws = self.active.get(user_id)
        if ws:
            await ws.send_json(event)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
            await ws.send_json({"type": "system.health", "data": "ok"})
    except WebSocketDisconnect:
        manager.disconnect()
