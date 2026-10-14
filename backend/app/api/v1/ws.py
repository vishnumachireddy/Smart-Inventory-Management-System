import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import jwt

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.websocket_manager import ws_manager
from app.services.analytics_service import AnalyticsService
from app.services.inventory_alert_service import InventoryAlertService

logger = logging.getLogger("stocksense.websocket")
router = APIRouter()


def decode_jwt_token(token: Optional[str]) -> Optional[Dict[str, Any]]:
    """Decodes and validates JWT bearer token without hitting database."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            return None
        return {
            "id": int(user_id_str),
            "role": payload.get("role", "staff"),
        }
    except Exception as e:
        logger.debug(f"WebSocket token validation failed: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """
    Real-time bi-directional WebSocket connection for instant inventory updates,
    dashboard KPIs, and alert notifications.
    """
    # Accept handshake immediately to prevent client-side timeouts
    await websocket.accept()

    user_info = decode_jwt_token(token)
    user_id = user_info["id"] if user_info else None

    # Register in manager
    ws_manager.active_connections.add(websocket)
    if user_id:
        if user_id not in ws_manager.user_connections:
            ws_manager.user_connections[user_id] = set()
        ws_manager.user_connections[user_id].add(websocket)

    logger.info(f"WebSocket client connected (user_id={user_id}). Active: {len(ws_manager.active_connections)}")

    # 1. Send immediate ACK
    await ws_manager.send_personal_message(
        {
            "type": "CONNECTED",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "user_id": user_id,
                "role": user_info["role"] if user_info else "anonymous",
                "timezone": settings.APP_TIMEZONE,
                "message": "StockSense live WebSocket feed established."
            }
        },
        websocket
    )

    # 2. Asynchronously dispatch initial state in worker thread (non-blocking)
    async def dispatch_initial_state():
        def _load_data():
            db = SessionLocal()
            try:
                kpis = AnalyticsService.get_dashboard_summary(db)
                alerts_summary = InventoryAlertService.get_inventory_summary(db)
                return kpis.model_dump(mode="json"), alerts_summary["summary"]
            finally:
                db.close()

        try:
            kpis_dict, alerts_dict = await asyncio.to_thread(_load_data)
            if websocket in ws_manager.active_connections:
                await ws_manager.send_personal_message(
                    {
                        "type": "INITIAL_STATE",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "data": {
                            "kpis": kpis_dict,
                            "alerts_summary": alerts_dict,
                            "timezone": settings.APP_TIMEZONE
                        }
                    },
                    websocket
                )
        except Exception as e:
            logger.warning(f"Could not dispatch initial WebSocket state: {e}")

    asyncio.create_task(dispatch_initial_state())

    # 3. Main receive loop for client heartbeats and requests
    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
                msg_type = msg.get("type", "").upper()

                if msg_type == "PING":
                    await ws_manager.send_personal_message(
                        {"type": "PONG", "timestamp": datetime.now(timezone.utc).isoformat()},
                        websocket
                    )

                elif msg_type == "REQUEST_KPIS":
                    def _load_kpis():
                        db = SessionLocal()
                        try:
                            return AnalyticsService.get_dashboard_summary(db).model_dump(mode="json")
                        finally:
                            db.close()

                    kpis_dict = await asyncio.to_thread(_load_kpis)
                    if websocket in ws_manager.active_connections:
                        await ws_manager.send_personal_message(
                            {"type": "KPIS_UPDATE", "data": kpis_dict},
                            websocket
                        )

                elif msg_type == "REQUEST_ALERTS":
                    def _load_alerts():
                        db = SessionLocal()
                        try:
                            return InventoryAlertService.get_inventory_summary(db)["summary"]
                        finally:
                            db.close()

                    alerts_dict = await asyncio.to_thread(_load_alerts)
                    if websocket in ws_manager.active_connections:
                        await ws_manager.send_personal_message(
                            {"type": "ALERTS_UPDATE", "data": alerts_dict},
                            websocket
                        )

            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id=user_id)
    except Exception as e:
        logger.warning(f"WebSocket client loop exception: {e}")
        ws_manager.disconnect(websocket, user_id=user_id)
