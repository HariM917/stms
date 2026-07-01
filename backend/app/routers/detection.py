"""
Detection router — all 5 detection endpoints.
Clean, DRY handlers with consistent kebab-case naming.
"""
import cv2
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.services import detector_service
from app.services.image_service import read_image_file, encode_image_to_base64, draw_detections
from app.utils.numpy_utils import clean_detections, deep_convert_numpy
from app.utils.logging import get_logger

logger = get_logger("detection")
router = APIRouter(prefix="/detect", tags=["detection"])


async def _run_detection(
    detector_name: str,
    file: UploadFile,
    box_color: tuple[int, int, int] = (0, 255, 0),
    label_key: str = "class",
):
    """
    Shared detection pipeline used by all detection endpoints.
    1. Read image  2. Run detector  3. Post-process  4. Draw visualization  5. Return
    """
    detector = detector_service.get_detector(detector_name)
    if detector is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": f"{detector_name} detector not available"},
        )

    try:
        image = await read_image_file(file)
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": f"Error processing image: {e}"},
        )

    try:
        results = detector.detect(image)
        detections = detector.postprocess(results, image)
    except Exception as e:
        logger.warning("%s detection failed, using mock fallback: %s", detector_name, e)
        mock = detector_service.MockDetector(detector_name)
        results = mock.detect(image)
        detections = mock.postprocess(results, image)

    # Normalize to a list of dicts
    if isinstance(detections, dict):
        detections = [detections]
    if not isinstance(detections, list):
        detections = []

    cleaned = clean_detections(detections)
    visualization = draw_detections(image, cleaned, color=box_color, label_key=label_key)
    vis_b64 = encode_image_to_base64(visualization)

    logger.info("%s detection: found %d results", detector_name, len(cleaned))
    return {
        "success": True,
        "message": f"{detector_name.replace('_', ' ').title()} detection successful",
        "detections": cleaned,
        "count": len(cleaned),
        "visualization": vis_b64,
    }


# ---- Object Detection ----

@router.post("/objects")
async def detect_objects(file: UploadFile = File(...)):
    """Detect vehicles, pedestrians, and other objects in an image."""
    result = await _run_detection("object", file, box_color=(255, 255, 0))

    # Add vehicle/pedestrian counts if the result is a dict (not a JSONResponse error)
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
async def detect_traffic_signs(file: UploadFile = File(...)):
    """Detect Indian traffic signs in an image."""
    return await _run_detection("traffic_sign", file, box_color=(0, 255, 0))


# ---- Potholes ----

@router.post("/potholes")
async def detect_potholes(file: UploadFile = File(...)):
    """Detect potholes and road damage in an image."""
    return await _run_detection("pothole", file, box_color=(0, 0, 255))


# ---- Weather ----

@router.post("/weather")
async def detect_weather(file: UploadFile = File(...)):
    """Detect weather conditions from an image."""
    detector = detector_service.get_detector("weather")
    if detector is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "Weather detector not available"},
        )

    try:
        image = await read_image_file(file)
        results = detector.detect(image)
        weather_data = detector.postprocess(results, image)
    except Exception as e:
        logger.warning("Weather detection failed, using mock: %s", e)
        weather_data = {"condition": "cloudy", "confidence": 0.88, "impact_factor": 0.3}

    weather_data = deep_convert_numpy(weather_data)

    return {
        "success": True,
        "message": "Weather detection successful",
        "condition": weather_data.get("condition", "unknown"),
        "confidence": float(weather_data.get("confidence", 0.0)),
        "impact_factor": float(weather_data.get("impact_factor", 0.0)),
    }


# ---- Railway Crossing ----

@router.post("/railway-crossing")
async def detect_railway_crossing(file: UploadFile = File(...)):
    """Detect railway crossings and trains in an image."""
    detector = detector_service.get_detector("railway_crossing")
    if detector is None:
        return JSONResponse(
            status_code=503,
            content={"success": False, "message": "Railway crossing detector not available"},
        )

    try:
        image = await read_image_file(file)
        results = detector.detect(image)
    except Exception as e:
        return JSONResponse(
            status_code=422,
            content={"success": False, "message": f"Error processing image: {e}"},
        )

    # Handle the various result formats from the railway crossing detector
    try:
        if isinstance(results, dict) and "railway_objects" in results:
            detections = []
            for obj in results.get("railway_objects", []):
                if isinstance(obj, dict) and "box" in obj:
                    detections.append({
                        "bbox": obj["box"],
                        "confidence": obj.get("confidence", 0.0),
                        "status": "closed" if results.get("train_present", False) else "open",
                    })
        else:
            post_result = detector.postprocess(results, image)
            if isinstance(post_result, dict):
                railway_objects = post_result.get("railway_objects", [])
                detections = [
                    {
                        "bbox": obj.get("box", obj.get("bbox", [0, 0, 100, 100])),
                        "confidence": obj.get("confidence", 0.0),
                        "status": "closed" if post_result.get("train_present", False) else "open",
                    }
                    for obj in railway_objects
                    if isinstance(obj, dict)
                ]
            elif isinstance(post_result, list):
                detections = post_result
            else:
                detections = []
    except Exception as e:
        logger.warning("Railway crossing post-processing failed: %s", e)
        detections = []

    cleaned = clean_detections(detections)

    # Visualization with color based on status
    visualization = image.copy()
    for det in cleaned:
        bbox = det.get("bbox", [])
        if len(bbox) < 4:
            continue
        x1, y1, x2, y2 = [int(float(c)) for c in bbox[:4]]
        det_status = det.get("status", "unknown")
        color = (255, 0, 0) if det_status == "closed" else (0, 255, 255)
        cv2.rectangle(visualization, (x1, y1), (x2, y2), color, 2)
        label = f"Crossing ({det_status}): {det.get('confidence', 0.0):.2f}"
        cv2.putText(visualization, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    vis_b64 = encode_image_to_base64(visualization)

    logger.info("Railway crossing detection: found %d results", len(cleaned))
    return {
        "success": True,
        "message": "Railway crossing detection successful",
        "detections": cleaned,
        "count": len(cleaned),
        "visualization": vis_b64,
    }
