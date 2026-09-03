from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from app.core.events import event_manager
from app.core.database import get_db
from app.core.security import decode_token
from app.models.booking import Booking
from app.models.provider import ProviderProfile
from app.models.user import User
from app.models.enums import UserRole
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def _authenticated_user(websocket: WebSocket, db):
    token = websocket.query_params.get("token")
    if not token:
        authorization = websocket.headers.get("authorization", "")
        if authorization.lower().startswith("bearer "):
            token = authorization[7:]
    payload = decode_token(token) if token else None
    if not payload or payload.get("type") != "access" or not payload.get("sub"):
        return None
    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        return None
    return db.query(User).filter(
        User.id == user_id, User.is_active.is_(True), User.is_suspended.is_(False)
    ).first()


@router.websocket("/bookings/{booking_id}")
async def booking_websocket_endpoint(websocket: WebSocket, booking_id: str, db=Depends(get_db)):
    user = _authenticated_user(websocket, db)
    try:
        booking_uuid = uuid.UUID(booking_id)
    except ValueError:
        booking_uuid = None
    booking = db.query(Booking).filter(Booking.id == booking_uuid).first() if booking_uuid else None
    authorized = bool(user and booking and (
        user.role == UserRole.ADMIN
        or (user.role == UserRole.CUSTOMER and booking.customer_id == user.id)
        or (user.role == UserRole.PROVIDER and booking.provider and booking.provider.user_id == user.id)
    ))
    if not authorized:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
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
async def provider_websocket_endpoint(websocket: WebSocket, provider_id: str, db=Depends(get_db)):
    user = _authenticated_user(websocket, db)
    try:
        provider_uuid = uuid.UUID(provider_id)
    except ValueError:
        provider_uuid = None
    provider = db.query(ProviderProfile).filter(ProviderProfile.id == provider_uuid).first() if provider_uuid else None
    if not user or not provider or not (
        user.role == UserRole.ADMIN
        or (user.role == UserRole.PROVIDER and provider.user_id == user.id)
    ):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
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
