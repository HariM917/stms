"""
Tests for the optimization endpoint and domain constraints.
"""
import pytest


@pytest.mark.asyncio
async def test_optimize_signals_unauthenticated(client):
    """Anonymous user must be rejected from signal optimization."""
    client.cookies.clear()
    response = await client.post("/api/v1/optimize/signals", json={"junction_id": "Junction-1"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_optimize_signals_normal_user_forbidden(client, registered_user):
    """Normal user must be forbidden from signal optimization."""
    client.cookies.clear()
    response = await client.post(
        "/api/v1/optimize/signals",
        json={"junction_id": "Junction-1"},
        headers=registered_user["headers"],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_optimize_signals_operator_allowed(client, operator_user):
    """Operator should be allowed to run signal optimization and get valid domain timings."""
    client.cookies.clear()
    response = await client.post(
        "/api/v1/optimize/signals",
        json={
            "junction_id": "Junction-A4",
            "traffic_data": {
                "vehicle_count": 50,
                "pedestrian_count": 10,
            },
            "weather_data": {
                "condition": "rainy",
            },
        },
        headers=operator_user["headers"],
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "signal_timings" in data
    assert "congestion_level" in data

    timings = data["signal_timings"]
    # Verify domain constraints
    ns_green = timings["north_south"]["green"]
    assert 15 <= ns_green <= 90
    ped_time = timings["pedestrian"]["crossing_time"]
    assert 12 <= ped_time <= 40
    cycle_length = timings["cycle_length"]
    assert 40 <= cycle_length <= 180

