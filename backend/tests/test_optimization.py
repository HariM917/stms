"""
Tests for the optimization endpoint.
"""
import pytest


@pytest.mark.asyncio
async def test_optimize_signals_default(client):
    """Optimization endpoint should return signal timings even without input data."""
    response = await client.post("/api/v1/optimize/signals", json={})
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "signal_timings" in data
    assert "congestion_level" in data


@pytest.mark.asyncio
async def test_optimize_signals_with_data(client):
    """Optimization endpoint should accept traffic data."""
    response = await client.post("/api/v1/optimize/signals", json={
        "junction_id": "Junction-A4",
        "traffic_data": {
            "vehicle_count": 50,
            "pedestrian_count": 10,
        },
        "weather_data": {
            "condition": "rainy",
        },
    })
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "signal_timings" in data
