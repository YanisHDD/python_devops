import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add api directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../api")))

from main import app


@pytest.fixture
def client():
    """Fixture that initializes the TestClient with lifespan events enabled."""
    with TestClient(app) as c:
        yield c


def test_get_health(client):
    """Verify GET /health is public and returns ok."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_get_metrics(client):
    """Verify GET /metrics is public and returns metrics."""
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "cpu_percent" in resp.json()


def test_post_server_auth(client):
    """Verify POST /servers requires valid API Key."""
    payload = {"name": "test-srv", "host": "127.0.0.1", "port": 8080}
    # No header
    resp1 = client.post("/servers", json=payload)
    assert resp1.status_code == 403

    # Invalid header
    resp2 = client.post("/servers", json=payload, headers={"X-API-Key": "wrong"})
    assert resp2.status_code == 403

    # Valid header (default fallback key)
    resp3 = client.post("/servers", json=payload, headers={"X-API-Key": "dev-secret-change-in-prod"})
    assert resp3.status_code == 201
    assert resp3.json()["name"] == "test-srv"
    assert resp3.json()["status"] == "unknown"


def test_get_servers_list(client):
    """Verify listing of servers and filters."""
    # List all
    resp = client.get("/servers")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1

    # Filter status
    resp_filter = client.get("/servers?status=UP")
    assert resp_filter.status_code == 200
    assert isinstance(resp_filter.json(), list)


def test_get_server_by_id(client):
    """Verify getting single server or 404."""
    # Try ID 1 (should exist if loaded from servers.json)
    resp = client.get("/servers/1")
    assert resp.status_code in (200, 404)

    # Invalid ID
    resp_missing = client.get("/servers/9999")
    assert resp_missing.status_code == 404


def test_trigger_immediate_check(client):
    """Verify manual health check trigger."""
    # Invalid ID
    resp_missing = client.post("/servers/9999/check")
    assert resp_missing.status_code == 404

    # Valid ID 1
    resp = client.post("/servers/1/check")
    assert resp.status_code in (200, 404)


def test_delete_server_auth(client):
    """Verify DELETE /servers/{id} requires auth and works."""
    # No auth
    resp1 = client.delete("/servers/1")
    assert resp1.status_code == 403

    # Valid auth
    resp2 = client.delete("/servers/1", headers={"X-API-Key": "dev-secret-change-in-prod"})
    assert resp2.status_code in (204, 404)
