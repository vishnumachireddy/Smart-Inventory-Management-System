import json
import logging
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("stocksense.websocket")


class WebSocketConnectionManager:
    """
    Centralized WebSocket manager handling client connections, authentication,
    heartbeats, and real-time inventory event broadcasting.
    """

    def __init__(self):
        # Active connections mapped by connection id or set
        self.active_connections: Set[WebSocket] = set()
        self.user_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """Accepts and registers a new authenticated client connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(websocket)
        logger.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None):
        """Removes a disconnected websocket client."""
        self.active_connections.discard(websocket)
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info(f"WebSocket client disconnected. Total active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Sends a JSON message to a specific connection."""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.warning(f"Failed to send personal WebSocket message: {e}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """
        Broadcasts an event message to all connected clients.
        Automatically cleans up stale or disconnected sockets.
        """
        if not self.active_connections:
            return

        message = {
            "type": event_type,
            "data": data
        }
        raw_message = json.dumps(message, default=str)
        dead_sockets = []

        for connection in list(self.active_connections):
            try:
                await connection.send_text(raw_message)
            except Exception as e:
                logger.warning(f"Error broadcasting to client: {e}. Marking for cleanup.")
                dead_sockets.append(connection)

        for dead in dead_sockets:
            self.disconnect(dead)


# Global singleton instance
ws_manager = WebSocketConnectionManager()
