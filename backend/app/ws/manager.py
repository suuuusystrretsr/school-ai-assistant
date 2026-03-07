from collections import defaultdict

from fastapi import WebSocket


class RoomConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[int, list[WebSocket]] = defaultdict(list)

    async def connect(self, room_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: int, websocket: WebSocket) -> None:
        if room_id in self.rooms and websocket in self.rooms[room_id]:
            self.rooms[room_id].remove(websocket)

    async def broadcast(self, room_id: int, message: dict) -> None:
        dead_sockets: list[WebSocket] = []
        for connection in self.rooms.get(room_id, []):
            try:
                await connection.send_json(message)
            except RuntimeError:
                dead_sockets.append(connection)
        for dead in dead_sockets:
            self.disconnect(room_id, dead)


room_connection_manager = RoomConnectionManager()
