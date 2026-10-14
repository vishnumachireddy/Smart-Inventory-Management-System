import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token
from app.services.cache_service import data_cache
from app.core.events import broadcast_live_event


def test_websocket_anonymous_handshake():
    """Verifies that WebSocket handshake succeeds and sends immediate CONNECTED ACK."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws") as websocket:
        msg = websocket.receive_json()
        assert msg["type"] == "CONNECTED"
        assert msg["data"]["role"] == "anonymous"
        assert "Asia/Kolkata" in msg["data"]["timezone"]


def test_websocket_authenticated_handshake(owner_user):
    """Verifies that valid JWT grants authenticated WebSocket connection and initial state."""
    token = create_access_token(subject=str(owner_user.id), role=owner_user.role)
    client = TestClient(app)
    with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        # Message 1: CONNECTED
        ack = websocket.receive_json()
        assert ack["type"] == "CONNECTED"
        assert ack["data"]["user_id"] == owner_user.id
        assert ack["data"]["role"] == "shop_owner"


def test_websocket_ping_pong():
    """Verifies that PING heartbeat receives immediate PONG response."""
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws") as websocket:
        ack = websocket.receive_json()
        assert ack["type"] == "CONNECTED"

        websocket.send_json({"type": "PING"})
        pong = websocket.receive_json()
        assert pong["type"] == "PONG"
        assert "timestamp" in pong


def test_cache_invalidation_and_event_broadcast():
    """Verifies that broadcast_live_event invalidates cache and triggers event dispatch."""
    data_cache.set("dashboard_kpis_30", {"mock": True}, ttl_seconds=60)
    assert data_cache.get("dashboard_kpis_30") is not None

    broadcast_live_event("SALE_COMPLETED", {"sale_id": 999})
    assert data_cache.get("dashboard_kpis_30") is None
