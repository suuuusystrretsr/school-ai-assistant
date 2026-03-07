from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import SessionLocal, engine
from app.models.base import Base
from app.ws.manager import room_connection_manager

settings = get_settings()

app = FastAPI(title=settings.app_name)

origins = [origin.strip() for origin in settings.cors_origins.split(',') if origin.strip()]
allow_all = '*' in origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if allow_all else origins,
    allow_credentials=False if allow_all else True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.on_event('startup')
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get('/health')
def health() -> dict:
    with SessionLocal() as db:
        db.execute(text('SELECT 1'))
    return {'status': 'ok', 'app': settings.app_name}


@app.websocket('/ws/rooms/{room_id}')
async def room_ws(websocket: WebSocket, room_id: int):
    user_id = websocket.query_params.get('user_id', 'anonymous')
    await room_connection_manager.connect(room_id, websocket)
    await room_connection_manager.broadcast(
        room_id,
        {'type': 'presence', 'event': 'join', 'room_id': room_id, 'user_id': user_id},
    )

    try:
        while True:
            payload = await websocket.receive_json()
            await room_connection_manager.broadcast(
                room_id,
                {
                    'type': payload.get('type', 'chat'),
                    'room_id': room_id,
                    'user_id': user_id,
                    'content': payload.get('content', ''),
                },
            )
    except WebSocketDisconnect:
        room_connection_manager.disconnect(room_id, websocket)
        await room_connection_manager.broadcast(
            room_id,
            {'type': 'presence', 'event': 'leave', 'room_id': room_id, 'user_id': user_id},
        )
