"""
Live dashboard feed. Single-process connection manager — fine for one API
instance; if you scale the API horizontally, swap the in-memory `connections`
list for a pub/sub mechanism (Redis, or your cloud provider's equivalent) so
every instance can broadcast to every connected dashboard client.
"""
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self.connections:
            self.connections.remove(ws)

    async def broadcast(self, event: dict) -> None:
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(json.dumps(event))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/dashboard")
async def dashboard_feed(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            # Dashboard clients don't need to send anything; this just keeps
            # the connection open and detects disconnects.
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(ws)
