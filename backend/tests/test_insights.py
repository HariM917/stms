"""
Tests for LLM traffic insights and safety guarantees.
"""
import pytest


@pytest.mark.asyncio
async def test_insights_unauthenticated(client):
    """Anonymous user must be rejected from requesting insights."""
    client.cookies.clear()
    response = await client.post("/api/v1/generate/insights", json={"prompt": "Analyze traffic"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_insights_normal_user_forbidden(client, registered_user):
    """Normal user must be forbidden from requesting insights."""
    client.cookies.clear()
    response = await client.post(
        "/api/v1/generate/insights",
        json={"prompt": "Analyze traffic"},
        headers=registered_user["headers"],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_insights_operator_allowed_and_no_fake_dispatch(client, operator_user):
    """Operator should get valid advisory with no false emergency dispatch claims."""
    client.cookies.clear()
    response = await client.post(
        "/api/v1/generate/insights",
        json={"prompt": "Type: Accident, Location: Silk Board Junction, Description: Collision on ramp"},
        headers=operator_user["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "insights" in data
    assert len(data["insights"]) > 0

    # Ensure no fabricated dispatch claims
    all_text = " ".join(data["insights"])
    assert "Emergency response teams have been dispatched" not in all_text
    assert "disclaimer" in data


@pytest.mark.asyncio
async def test_insights_prompt_too_long(client, operator_user):
    """Prompts exceeding 4000 characters must be rejected with 422."""
    client.cookies.clear()
    response = await client.post(
        "/api/v1/generate/insights",
        json={"prompt": "A" * 4500},
        headers=operator_user["headers"],
    )
    assert response.status_code == 422
