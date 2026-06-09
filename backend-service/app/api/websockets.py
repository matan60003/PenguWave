from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.websockets import manager
import logging

logger = logging.getLogger("penguwave")
router = APIRouter(tags=["WebSockets"])

@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We wait for messages to keep the connection open and handle disconnects
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
