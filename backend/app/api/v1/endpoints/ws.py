from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.events import event_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/bookings/{booking_id}")
async def booking_websocket_endpoint(websocket: WebSocket, booking_id: str):
    channel = f"booking:{booking_id}"
    await event_manager.connect(channel, websocket)
    try:
        while True:
            # Client can ping/listen for events
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        await event_manager.disconnect(channel, websocket)
    except Exception as e:
        logger.warning(f"WebSocket error on {channel}: {e}")
        await event_manager.disconnect(channel, websocket)


@router.websocket("/providers/{provider_id}")
async def provider_websocket_endpoint(websocket: WebSocket, provider_id: str):
    channel = f"provider:{provider_id}"
    await event_manager.connect(channel, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text('{"event": "pong"}')
    except WebSocketDisconnect:
        await event_manager.disconnect(channel, websocket)
    except Exception as e:
        logger.warning(f"WebSocket error on {channel}: {e}")
        await event_manager.disconnect(channel, websocket)
