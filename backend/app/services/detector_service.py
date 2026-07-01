"""
Detector service — manages initialization and access to all detection modules.
Uses a singleton pattern so detectors are loaded once at startup.
"""
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from app.utils.logging import get_logger

logger = get_logger("detector_service")

# Module-level state
_detectors: Dict[str, Any] = {}
_optimizer: Optional[Any] = None
_insights_llm: Optional[Any] = None


# ---------------------------------------------------------------------------
# Mock detector (fallback when real detector modules fail to load)
# ---------------------------------------------------------------------------

class MockDetector:
    """Lightweight mock detector that returns realistic-looking results."""

    MOCK_RESULTS = {
        "object": [
            {"class": "car", "confidence": 0.92, "bbox": [100, 100, 300, 200]},
            {"class": "person", "confidence": 0.85, "bbox": [400, 300, 450, 500]},
        ],
        "pothole": [
            {"confidence": 0.75, "bbox": [200, 300, 300, 350]},
        ],
        "traffic_sign": [
            {"class": "stop", "confidence": 0.89, "bbox": [50, 100, 120, 170]},
        ],
        "railway_crossing": [
            {"confidence": 0.82, "bbox": [250, 200, 450, 350], "status": "closed"},
        ],
        "weather": {"condition": "cloudy", "confidence": 0.88, "impact_factor": 0.3},
    }

    def __init__(self, name: str):
        self.name = name
        self._is_mock = True

    def detect(self, image):
        logger.debug("Mock %s detection on image", self.name)
        return {"mock": True, "image_shape": image.shape if hasattr(image, "shape") else None}

    def postprocess(self, results, image=None):
        return self.MOCK_RESULTS.get(self.name, [])


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def _try_import_detectors():
    """Attempt to import detector classes from the detectors package."""
    # Ensure parent directories are on the path
    root_dir = Path(__file__).resolve().parent.parent.parent
    for p in [str(root_dir), str(root_dir / "backend")]:
        if p not in sys.path:
            sys.path.insert(0, p)

    classes = {}
    # Try backend.detectors first, then plain detectors
    for prefix in ("backend.detectors", "detectors"):
        try:
            mod_obj = __import__(f"{prefix}.object_detector", fromlist=["ObjectDetector"])
            classes["object"] = mod_obj.ObjectDetector

            mod_pot = __import__(f"{prefix}.pothole_detector", fromlist=["PotholeDetector"])
            classes["pothole"] = mod_pot.PotholeDetector

            mod_wea = __import__(f"{prefix}.weather_detector", fromlist=["WeatherDetector"])
            classes["weather"] = mod_wea.WeatherDetector

            mod_ts = __import__(f"{prefix}.traffic_sign_detector", fromlist=["TrafficSignDetector"])
            classes["traffic_sign"] = mod_ts.TrafficSignDetector

            mod_rc = __import__(f"{prefix}.railway_crossing_detector", fromlist=["RailwayCrossingDetector"])
            classes["railway_crossing"] = mod_rc.RailwayCrossingDetector

            logger.info("Detector modules imported from '%s'", prefix)
            return classes
        except ImportError:
            continue

    logger.warning("Could not import detector modules from any path")
    return {}


def _try_import_extras():
    """Attempt to import optimizer and LLM modules."""
    optimizer_cls = None
    llm_cls = None

    for prefix in ("backend.optimization", "optimization"):
        try:
            mod = __import__(f"{prefix}.traffic_optimizer", fromlist=["TrafficSignalOptimizer"])
            optimizer_cls = mod.TrafficSignalOptimizer
            break
        except ImportError:
            continue

    for prefix in ("backend.llm", "llm"):
        try:
            mod = __import__(f"{prefix}.traffic_insights", fromlist=["TrafficInsightsLLM"])
            llm_cls = mod.TrafficInsightsLLM
            break
        except ImportError:
            continue

    return optimizer_cls, llm_cls


def initialize_all():
    """
    Initialize all detectors, the optimizer, and the LLM module.
    Called once during application startup (lifespan).
    Falls back to mock detectors on failure.
    """
    global _detectors, _optimizer, _insights_llm

    logger.info("Initializing detection services...")

    # Start with mocks for all detector types
    detector_names = ["object", "pothole", "weather", "traffic_sign", "railway_crossing"]
    _detectors = {name: MockDetector(name) for name in detector_names}

    # Try loading real detectors
    detector_classes = _try_import_detectors()
    for name, cls in detector_classes.items():
        try:
            detector = cls()
            # Check if the model actually loaded
            if hasattr(detector, "model") and detector.model is None:
                logger.warning("%s detector model is None — keeping mock", name)
            else:
                _detectors[name] = detector
                logger.info("✓ %s detector initialized", name)
        except Exception as e:
            logger.warning("✗ %s detector failed: %s — using mock", name, e)

    # Try loading optimizer and LLM
    optimizer_cls, llm_cls = _try_import_extras()

    if optimizer_cls:
        try:
            _optimizer = optimizer_cls()
            logger.info("✓ Traffic signal optimizer initialized")
        except Exception as e:
            logger.warning("✗ Optimizer failed: %s", e)

    if llm_cls:
        try:
            _insights_llm = llm_cls()
            logger.info("✓ Traffic insights LLM initialized")
        except Exception as e:
            logger.warning("✗ LLM failed: %s", e)

    logger.info(
        "Initialization complete — %d detectors loaded (%d real, %d mock)",
        len(_detectors),
        sum(1 for d in _detectors.values() if not getattr(d, "_is_mock", False)),
        sum(1 for d in _detectors.values() if getattr(d, "_is_mock", False)),
    )


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_detector(name: str):
    """Get a detector by name. Returns None if not available."""
    return _detectors.get(name)


def get_optimizer():
    return _optimizer


def get_insights_llm():
    return _insights_llm


def get_detector_status() -> dict:
    """Return a dict of detector availability for the health endpoint."""
    return {
        name: not getattr(det, "_is_mock", False)
        for name, det in _detectors.items()
    }
