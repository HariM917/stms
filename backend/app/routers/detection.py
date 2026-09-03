"""
Detection router — all 5 detection endpoints with authentication and production safety.
"""
import cv2
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.middleware.auth_middleware import get_current_user
from app.models.db.user import User
from app.services import detector_service
from app.services.image_service import (
    draw_detections,
    encode_image_to_base64,
    read_image_file,
)
from app.utils.logging import get_logger
from app.utils.numpy_utils import clean_detections, deep_convert_numpy

logger = get_logger("detection")
router = APIRouter(prefix="/detect", tags=["detection"])


async def _run_detection(
    detector_name: str,
    file: UploadFile,
    box_color: tuple[int, int, int] = (0, 255, 0),
    label_key: str = "class",
):
    """
    Shared detection pipeline used by detection endpoints.
    1. Read image safely  2. Run detector  3. Post-process  4. Draw visualization  5. Return
    """
    detector = detector_service.get_detector(detector_name)
    if detector is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"success": False, "message": f"{detector_name.replace('_', ' ').title()} detector temporarily unavailable"},
        )

    image = await read_image_file(file)

    is_mock = detector_service.is_mock(detector)

    try:
        results = detector.detect(image)
        detections = detector.postprocess(results, image)
    except Exception as e:
        logger.error("%s detection failed during inference: %s", detector_name, e)
        if detector_service.is_mock_allowed():
            logger.warning("%s using mock fallback because ALLOW_MOCK_MODELS=true", detector_name)
            mock = detector_service.MockDetector(detector_name)
            results = mock.detect(image)
            detections = mock.postprocess(results, image)
            is_mock = True
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"success": False, "message": f"{detector_name.replace('_', ' ').title()} detection service error"},
            )

    # Normalize to a list of dicts
    if isinstance(detections, dict):
        detections = [detections]
    if not isinstance(detections, list):
        detections = []

    cleaned = clean_detections(detections)

    # Filter out malformed detections without valid bboxes
    valid_cleaned = []
    for d in cleaned:
        box = d.get("bbox", d.get("box"))
        if box and len(box) >= 4:
            x1, y1, x2, y2 = box[:4]
            if x2 > x1 and y2 > y1:
                valid_cleaned.append(d)
        elif "condition" in d or "status" in d:
            valid_cleaned.append(d)

    visualization = draw_detections(image, valid_cleaned, color=box_color, label_key=label_key)
    vis_b64 = encode_image_to_base64(visualization)

    response_data = {
        "success": True,
        "message": f"{detector_name.replace('_', ' ').title()} detection successful",
        "detections": valid_cleaned,
        "count": len(valid_cleaned),
        "visualization": vis_b64,
    }
    if is_mock:
        response_data["mock"] = True

    logger.info("%s detection: found %d valid results (mock=%s)", detector_name, len(valid_cleaned), is_mock)
    return response_data


# ---- Object Detection ----

@router.post("/objects")
async def detect_objects(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Detect vehicles, pedestrians, and other objects in an image (authenticated)."""
    result = await _run_detection("object", file, box_color=(255, 255, 0))

    if isinstance(result, dict) and result.get("success"):
        detections = result["detections"]
        vehicle_count = sum(
            1 for d in detections
            if str(d.get("class", "")).lower() in ("car", "truck", "bus", "motorcycle", "vehicle")
        )
        pedestrian_count = sum(
            1 for d in detections
            if str(d.get("class", "")).lower() in ("person", "pedestrian")
        )
        result["vehicle_count"] = vehicle_count
        result["pedestrian_count"] = pedestrian_count

    return result


# ---- Traffic Signs ----

@router.post("/traffic-signs")
async def detect_traffic_signs(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Detect Indian traffic signs in an image (authenticated)."""
    return await _run_detection("traffic_sign", file, box_color=(0, 255, 0))


# ---- Potholes ----

@router.post("/potholes")
async def detect_potholes(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Detect potholes and road damage in an image (authenticated)."""
    return await _run_detection("pothole", file, box_color=(0, 0, 255))


# ---- Weather ----

@router.post("/weather")
async def detect_weather(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Detect weather conditions from an image (authenticated)."""
    detector = detector_service.get_detector("weather")
    if detector is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"success": False, "message": "Weather detector temporarily unavailable"},
        )

    image = await read_image_file(file)
    is_mock = detector_service.is_mock(detector)

    try:
        results = detector.detect(image)
        weather_data = detector.postprocess(results, image)
    except Exception as e:
        logger.error("Weather detection failed: %s", e)
        if detector_service.is_mock_allowed():
            weather_data = {"condition": "cloudy", "confidence": 0.88, "impact_factor": 0.3}
            is_mock = True
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"success": False, "message": "Weather detection service error"},
            )

    weather_data = deep_convert_numpy(weather_data)

    response_data = {
        "success": True,
        "message": "Weather detection successful",
        "condition": weather_data.get("condition", "unknown"),
        "confidence": float(weather_data.get("confidence", 0.0)),
        "impact_factor": float(weather_data.get("impact_factor", 0.0)),
    }
    if is_mock:
        response_data["mock"] = True

    return response_data


# ---- Railway Crossing ----

@router.post("/railway-crossing")
async def detect_railway_crossing(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """Detect railway crossings and trains in an image (authenticated)."""
    detector = detector_service.get_detector("railway_crossing")
    if detector is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"success": False, "message": "Railway crossing detector temporarily unavailable"},
        )

    image = await read_image_file(file)
    is_mock = detector_service.is_mock(detector)

    try:
        results = detector.detect(image)
        post_result = detector.postprocess(results, image)
    except Exception as e:
        logger.error("Railway crossing detection failed: %s", e)
        if detector_service.is_mock_allowed():
            post_result = {"railway_objects": [], "train_present": False, "status": "open"}
            is_mock = True
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"success": False, "message": "Railway crossing detection service error"},
            )

    detections = []
    if isinstance(post_result, dict):
        railway_objs = post_result.get("railway_objects")
        if isinstance(railway_objs, list):
            for obj in railway_objs:
                if isinstance(obj, dict):
                    bbox = obj.get("bbox", obj.get("box"))
                    if isinstance(bbox, (list, tuple)) and len(bbox) >= 4 and bbox[2] > bbox[0] and bbox[3] > bbox[1]:
                        detections.append({
                            "bbox": list(bbox),
                            "confidence": float(obj.get("confidence", 0.0)),
                            "status": str(obj.get("status", post_result.get("status", "unknown"))),
                        })
    elif isinstance(post_result, list):
        for obj in post_result:
            if isinstance(obj, dict):
                bbox = obj.get("bbox", obj.get("box"))
                if isinstance(bbox, (list, tuple)) and len(bbox) >= 4:
                    detections.append(obj)

    cleaned = clean_detections(detections)

    # Visualization
    visualization = image.copy()
    for det in cleaned:
        bbox = det.get("bbox", [])
        if len(bbox) >= 4:
            x1, y1, x2, y2 = [int(float(c)) for c in bbox[:4]]
            det_status = det.get("status", "unknown")
            color = (255, 0, 0) if det_status == "closed" else (0, 255, 255)
            cv2.rectangle(visualization, (x1, y1), (x2, y2), color, 2)
            label = f"Crossing ({det_status}): {det.get('confidence', 0.0):.2f}"
            cv2.putText(visualization, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    vis_b64 = encode_image_to_base64(visualization)

    response_data = {
        "success": True,
        "message": "Railway crossing detection successful",
        "detections": cleaned,
        "count": len(cleaned),
        "visualization": vis_b64,
    }
    if is_mock:
        response_data["mock"] = True

    return response_data

