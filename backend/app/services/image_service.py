"""
Image processing service.
Handles reading uploaded images and encoding visualizations.
"""
import cv2
import numpy as np
import base64
from fastapi import UploadFile, HTTPException

from app.utils.logging import get_logger

logger = get_logger("image_service")


async def read_image_file(file: UploadFile) -> np.ndarray:
    """
    Read an uploaded image file and convert to OpenCV BGR format.

    Raises:
        HTTPException 400: if file is empty or not a valid image format
        HTTPException 422: if decoding fails
    """
    # Validate content type
    valid_mime_types = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
    if file.content_type and file.content_type not in valid_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format '{file.content_type}'. Accepted: JPG, PNG, WebP.",
        )

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        nparr = np.frombuffer(contents, np.uint8)
        if nparr.size == 0:
            raise HTTPException(status_code=400, detail="Invalid image data.")

        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(
                status_code=422,
                detail="Failed to decode image. File may be corrupted or unsupported.",
            )

        logger.debug("Image read successfully: shape=%s", img.shape)
        return img

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error reading image file: %s", e)
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")


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
