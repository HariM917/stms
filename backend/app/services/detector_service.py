"""
Detector service — manages initialization and access to all detection modules.
Uses a singleton pattern so detectors are loaded once at startup.
"""
import sys
from pathlib import Path
from typing import Any

from app.utils.logging import get_logger

logger = get_logger("detector_service")

# Module-level state
_detectors: dict[str, Any] = {}
_optimizer: Any | None = None
_insights_llm: Any | None = None


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
    Mock detectors are strictly prohibited in production and only permitted
    when ENVIRONMENT=development and ALLOW_MOCK_MODELS=true.
    """
    global _detectors, _optimizer, _insights_llm
    from app.config import get_settings
    settings = get_settings()

    logger.info("Initializing detection services (environment=%s)...", settings.environment)

    allow_mocks = (not settings.is_production) and settings.allow_mock_models
    detector_names = ["object", "pothole", "weather", "traffic_sign", "railway_crossing"]
    _detectors = {name: None for name in detector_names}

    # Try loading real detectors
    detector_classes = _try_import_detectors()
    for name in detector_names:
        cls = detector_classes.get(name)
        if cls:
            try:
                detector = cls()
                # Check if model loaded successfully
                if hasattr(detector, "model") and detector.model is None:
                    if allow_mocks:
                        _detectors[name] = MockDetector(name)
                        logger.warning("DEV: %s model is None — using mock (ALLOW_MOCK_MODELS=true)", name)
                    else:
                        _detectors[name] = None
                        logger.warning("PROD/SAFE: %s model is None — mock disabled", name)
                else:
                    _detectors[name] = detector
                    logger.info("✓ %s detector initialized successfully", name)
            except Exception as e:
                logger.error("Error initializing %s detector: %s", name, e)
                if allow_mocks:
                    _detectors[name] = MockDetector(name)
                    logger.warning("DEV: Using mock for %s because ALLOW_MOCK_MODELS=true", name)
                else:
                    _detectors[name] = None
        else:
            if allow_mocks:
                _detectors[name] = MockDetector(name)
                logger.warning("DEV: %s class not found — using mock (ALLOW_MOCK_MODELS=true)", name)
            else:
                _detectors[name] = None
                logger.error("PROD/SAFE: %s class not found — mock disabled", name)

    # Try loading optimizer and LLM
    optimizer_cls, llm_cls = _try_import_extras()

    if optimizer_cls:
        try:
            _optimizer = optimizer_cls()
            logger.info("✓ Traffic signal optimizer initialized")
        except Exception as e:
            logger.error("Optimizer initialization failed: %s", e)
            _optimizer = None
    else:
        _optimizer = None

    if llm_cls:
        try:
            _insights_llm = llm_cls()
            logger.info("✓ Traffic insights LLM initialized")
        except Exception as e:
            logger.error("LLM initialization failed: %s", e)
            _insights_llm = None
    else:
        _insights_llm = None

    real_count = sum(1 for d in _detectors.values() if d is not None and not getattr(d, "_is_mock", False))
    mock_count = sum(1 for d in _detectors.values() if d is not None and getattr(d, "_is_mock", False))
    none_count = sum(1 for d in _detectors.values() if d is None)

    logger.info(
        "Initialization complete — %d real detectors, %d mock detectors, %d unavailable",
        real_count,
        mock_count,
        none_count,
    )


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_detector(name: str):
    """Get a detector by name. Returns None if not available."""
    return _detectors.get(name)


def is_mock(detector) -> bool:
    """Check if a detector instance is a mock."""
    return bool(getattr(detector, "_is_mock", False))


def is_mock_allowed() -> bool:
    """Check if mock models are currently allowed by configuration."""
    from app.config import get_settings
    settings = get_settings()
    return (not settings.is_production) and settings.allow_mock_models


def get_optimizer():
    return _optimizer


def get_insights_llm():
    return _insights_llm


def get_detector_status() -> dict:
    """Return a dict of detector availability for health and readiness endpoints."""
    return {
        name: (det is not None and not getattr(det, "_is_mock", False))
        for name, det in _detectors.items()
    }

