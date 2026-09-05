"""
Tests for the detection endpoints (using mock detectors).
"""
import io

import cv2
import numpy as np
import pytest


def _create_test_image() -> bytes:
    """Create a minimal test image as bytes."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[25:75, 25:75] = (0, 255, 0)  # Green square
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()


@pytest.mark.asyncio
async def test_detect_objects(client, auth_headers):
    """Object detection endpoint should accept an image and return detections for authenticated user."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/objects",
        headers=auth_headers,
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "detections" in data
    assert "count" in data
    assert isinstance(data["detections"], list)


@pytest.mark.asyncio
async def test_detect_objects_unauthenticated(client):
    """Detection endpoint must reject anonymous requests."""
    client.cookies.clear()
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/objects",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_detect_traffic_signs(client, auth_headers):
    """Traffic sign detection endpoint should accept an image."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/traffic-signs",
        headers=auth_headers,
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_detect_potholes(client, auth_headers):
    """Pothole detection endpoint should accept an image."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/potholes",
        headers=auth_headers,
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_detect_weather(client, auth_headers):
    """Weather detection endpoint should accept an image and return conditions."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/weather",
        headers=auth_headers,
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "condition" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_detect_railway_crossing(client, auth_headers):
    """Railway crossing detection endpoint should accept an image."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/railway-crossing",
        headers=auth_headers,
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_detect_empty_file(client, auth_headers):
    """Uploading an empty file should return an error."""
    response = await client.post(
        "/api/v1/detect/objects",
        headers=auth_headers,
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    # Should get a 400 or 422 error
    assert response.status_code in (400, 422)

