"""
Tests for the health check endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_health_returns_200(client):
    """Health endpoint should return 200 with system status."""
    response = await client.get("/api/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_health_contains_detector_status(client):
    """Health endpoint should report detector availability."""
    response = await client.get("/api/health")
    data = response.json()

    services = data["services"]
    assert "detectors" in services
    assert "database" in services


@pytest.mark.asyncio
async def test_liveness_probe(client):
    """Liveness probe should return status alive."""
    response = await client.get("/api/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_readiness_probe(client):
    """Readiness probe should return ready: true when DB is available."""
    response = await client.get("/api/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """Root endpoint should return app info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "docs" in data
