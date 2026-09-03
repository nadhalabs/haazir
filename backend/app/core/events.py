import asyncio
import json
import logging
from typing import Dict, Set, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages active WebSocket client connections for customers and providers.
    Supports channel subscription per booking and provider.
    """
    def __init__(self):
        # Map channel_name -> Set[WebSocket]
        # Channels:
        # "booking:{booking_id}"
        # "provider:{provider_id}"
        self.active_channels: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if channel not in self.active_channels:
                self.active_channels[channel] = set()
            self.active_channels[channel].add(websocket)
        logger.info(f"Client connected to channel: {channel}")

    async def disconnect(self, channel: str, websocket: WebSocket):
        async with self._lock:
            if channel in self.active_channels:
                self.active_channels[channel].discard(websocket)
                if not self.active_channels[channel]:
                    del self.active_channels[channel]
        logger.info(f"Client disconnected from channel: {channel}")

    async def broadcast(self, channel: str, event_type: str, data: Dict[str, Any]):
        """
        Broadcasts an event to all connected sockets on a channel.
        Normal REST endpoints remain the authoritative source of truth.
        """
        payload = json.dumps({"event": event_type, "data": data})
        async with self._lock:
            targets = list(self.active_channels.get(channel, []))

        for ws in targets:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"Failed to send to websocket on {channel}: {e}")
                await self.disconnect(channel, ws)


event_manager = ConnectionManager()
