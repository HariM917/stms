"""
Image processing service.
Handles reading uploaded images and encoding visualizations with strict security controls.
"""
import base64
import io

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("image_service")

# Safe MIME signatures
ALLOWED_MAGIC_SIGNATURES = [
    (b"\xff\xd8\xff", "image/jpeg"),               # JPEG
    (b"\x89PNG\r\n\x1a\n", "image/png"),           # PNG
    (b"RIFF", "image/webp"),                       # WebP (checked further below)
]


def _validate_image_signature(header_bytes: bytes) -> bool:
    """Validate true image file signature from initial magic bytes."""
    if len(header_bytes) < 12:
        return False
    return (
        header_bytes.startswith(b"\xff\xd8\xff")
        or header_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or (header_bytes.startswith(b"RIFF") and header_bytes[8:12] == b"WEBP")
    )


HTTP_413_PAYLOAD_TOO_LARGE: int = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)


async def read_image_file(file: UploadFile) -> np.ndarray:
    """
    Read an uploaded image file securely and convert to OpenCV BGR format.

    Security features:
    - Streaming chunked read to prevent memory exhaustion (DoS)
    - Rejection of oversized files with HTTP 413
    - Magic byte / file signature validation (ignores untrusted client Content-Type)
    - Image dimension and pixel count bounds (decompression bomb protection)
    - Safe decoding with malformed image handling (HTTP 422)
    """
    settings = get_settings()
    max_bytes = settings.max_upload_size_bytes

    # 1. Chunked streaming read
    chunk_size = 64 * 1024  # 64 KB
    total_size = 0
    chunks = []

    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_bytes:
                raise HTTPException(
                    status_code=HTTP_413_PAYLOAD_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed limit of {max_bytes // (1024 * 1024)}MB.",
                )
            chunks.append(chunk)
    finally:
        await file.close()

    contents = b"".join(chunks)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded.",
        )

    # 2. Magic byte signature verification
    if not _validate_image_signature(contents[:16]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image format or signature. Allowed formats: JPEG, PNG, WebP.",
        )

    # 3. Pillow integrity & dimension verification (decompression bomb defense)
    try:
        with Image.open(io.BytesIO(contents)) as pil_img:
            # Check format is allowed by Pillow
            if pil_img.format not in ("JPEG", "PNG", "WEBP"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported image format '{pil_img.format}'. Allowed: JPEG, PNG, WebP.",
                )
            w, h = pil_img.size
            if w > settings.max_image_dimension or h > settings.max_image_dimension:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image dimensions ({w}x{h}) exceed maximum allowed dimension ({settings.max_image_dimension}px).",
                )
            if (w * h) > settings.max_image_pixels:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Image pixel count ({w * h}) exceeds maximum limit ({settings.max_image_pixels}).",
                )
            pil_img.verify()
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Pillow image verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Malformed or corrupted image file.",
        ) from e

    # 4. Safe OpenCV decoding
    try:
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to decode image data.",
            )
        logger.debug("Image decoded successfully: shape=%s, size=%d bytes", img.shape, total_size)
        return img
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OpenCV decoding error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Failed to process image file.",
        ) from e


def encode_image_to_base64(image: np.ndarray) -> str:
    """Encode an OpenCV image to a base64 PNG string for web display."""
    try:
        _, buffer = cv2.imencode(".png", image)
        return base64.b64encode(buffer.tobytes()).decode("utf-8")
    except Exception as e:
        logger.error("Error encoding image to base64: %s", e)
        return ""


def draw_detections(
    image: np.ndarray,
    detections: list[dict],
    color: tuple[int, int, int] = (0, 255, 0),
    label_key: str = "class",
) -> np.ndarray:
    """
    Draw bounding boxes and labels on an image copy.

    Args:
        image: Source image (BGR).
        detections: List of dicts with 'bbox', 'confidence', and optionally label_key.
        color: BGR color tuple for boxes and text.
        label_key: Key in detection dict to use as label text.

    Returns:
        A copy of the image with drawn annotations.
    """
    visualization = image.copy()
    for det in detections:
        try:
            bbox = det.get("bbox", [])
            if len(bbox) < 4:
                continue

            x1, y1, x2, y2 = [int(float(c)) for c in bbox[:4]]
            label_text = str(det.get(label_key, "unknown"))
            confidence = float(det.get("confidence", 0.0))

            cv2.rectangle(visualization, (x1, y1), (x2, y2), color, 2)
            label = f"{label_text}: {confidence:.2f}"
            cv2.putText(
                visualization, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2,
            )
        except Exception as e:
            logger.warning("Error drawing detection: %s", e)
            continue

    return visualization
