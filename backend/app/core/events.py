import asyncio
import logging
from typing import Dict, Any, Optional

from app.core.websocket_manager import ws_manager
from app.services.cache_service import data_cache

logger = logging.getLogger("stocksense.events")


def broadcast_live_event(event_type: str, data: Optional[Dict[str, Any]] = None):
    """
    Invalidates in-memory caches and dispatches a live real-time event to all connected
    WebSocket clients without blocking the current synchronous database transaction.
    """
    # 1. Invalidate stale dashboard and analytics caches
    data_cache.invalidate()

    payload = data or {}
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(ws_manager.broadcast(event_type, payload))
    except RuntimeError:
        # In background threads or scripts without active running loop
        logger.debug(f"No running asyncio loop to broadcast {event_type} event.")
