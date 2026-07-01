"""
Tests for the detection endpoints (using mock detectors).
"""
import io
import pytest
import numpy as np
import cv2


def _create_test_image() -> bytes:
    """Create a minimal test image as bytes."""
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[25:75, 25:75] = (0, 255, 0)  # Green square
    _, buffer = cv2.imencode(".png", img)
    return buffer.tobytes()


@pytest.mark.asyncio
async def test_detect_objects(client):
    """Object detection endpoint should accept an image and return detections."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/objects",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "detections" in data
    assert "count" in data
    assert isinstance(data["detections"], list)


@pytest.mark.asyncio
async def test_detect_traffic_signs(client):
    """Traffic sign detection endpoint should accept an image."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/traffic-signs",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_detect_potholes(client):
    """Pothole detection endpoint should accept an image."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/potholes",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_detect_weather(client):
    """Weather detection endpoint should accept an image and return conditions."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/weather",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "condition" in data
    assert "confidence" in data


@pytest.mark.asyncio
async def test_detect_railway_crossing(client):
    """Railway crossing detection endpoint should accept an image."""
    image_bytes = _create_test_image()
    response = await client.post(
        "/api/v1/detect/railway-crossing",
        files={"file": ("test.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_detect_empty_file(client):
    """Uploading an empty file should return an error."""
    response = await client.post(
        "/api/v1/detect/objects",
        files={"file": ("empty.png", io.BytesIO(b""), "image/png")},
    )
    # Should get a 400 or 422 error
    assert response.status_code in (400, 422)
