"""
Tests for the traffic reports endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_create_report(client, auth_headers):
    """Authenticated user should be able to create a traffic report."""
    response = await client.post("/api/v1/reports", json={
        "junction_id": "Junction-A4",
        "weather_condition": "Rainy",
        "congestion_level": 0.8,
        "vehicle_count": 45,
        "pedestrian_count": 12,
        "railway_crossing_active": False,
        "notes": "Heavy congestion near the intersection due to rain.",
    }, headers=auth_headers)
    assert response.status_code == 201

    data = response.json()
    assert data["success"] is True
    assert "report" in data
    assert "id" in data["report"]


@pytest.mark.asyncio
async def test_create_report_unauthorized(client):
    """Creating a report without auth should return 401."""
    response = await client.post("/api/v1/reports", json={
        "junction_id": "Junction-A4",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_reports(client, auth_headers):
    """Should be able to list reports with pagination."""
    # Create a report first
    await client.post("/api/v1/reports", json={
        "junction_id": "Junction-B1",
        "congestion_level": 0.5,
    }, headers=auth_headers)

    response = await client.get("/api/v1/reports", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "reports" in data
    assert "pagination" in data
    assert isinstance(data["reports"], list)
    assert len(data["reports"]) >= 1


@pytest.mark.asyncio
async def test_recent_reports(client, auth_headers):
    """Should be able to get recent reports."""
    # Create a couple of reports
    for i in range(3):
        await client.post("/api/v1/reports", json={
            "junction_id": f"Junction-C{i}",
        }, headers=auth_headers)

    response = await client.get("/api/v1/reports/recent?limit=2", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert len(data["reports"]) <= 2


@pytest.mark.asyncio
async def test_report_validation(client, auth_headers):
    """Report with invalid congestion_level should return 422."""
    response = await client.post("/api/v1/reports", json={
        "junction_id": "Junction-A4",
        "congestion_level": 5.0,  # Must be 0.0 - 1.0
    }, headers=auth_headers)
    assert response.status_code == 422
