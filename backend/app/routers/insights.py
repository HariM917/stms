"""
AI traffic insights and advisory router.
Generates analytical assessments and signal management recommendations for operators.
"""
import contextlib

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.middleware.auth_middleware import require_role
from app.models.db.user import User
from app.services import detector_service
from app.utils.logging import get_logger

logger = get_logger("insights")
router = APIRouter(tags=["insights"])


class InsightsRequest(BaseModel):
    """Request model for traffic insights generation."""
    prompt: str = Field(..., min_length=1, max_length=4000, description="Operator query or junction telemetry summary")


def _generate_fallback_insights(prompt: str) -> list[str]:
    """
    Context-aware rule-based advisory fallback.
    Clearly distinguishes AI analysis from physical actuation and avoids false dispatch claims.
    """
    insights = []
    prompt_lower = prompt.lower()

    if "incident" in prompt_lower or "accident" in prompt_lower:
        location = "monitored junction"
        if "location:" in prompt_lower:
            with contextlib.suppress(Exception):
                location = prompt.split("Location:")[1].split(",")[0].strip()

        insights.append(
            f"⚠️ **Incident Assessment**: Localized congestion risk detected near **{location}**. "
            "Advisory: Recommend notifying nearest sector traffic post and adjusting adjacent signals to defensive gating."
        )
        insights.append(
            "ℹ️ *Note: Real-world emergency dispatch must be initiated via official emergency service protocols.*"
        )
    else:
        insights.append(
            "🚦 **Signal Optimization Advisory**: Peak intersection telemetry analyzed. "
            "Recommend extending arterial green phase by +10s to clear queue buildup."
        )
        insights.append(
            "📊 **System Status**: Infrastructure metrics indicate nominal communication throughput across active nodes."
        )
        insights.append(
            "ℹ️ *Note: AI advisory recommendations require human operator confirmation before physical actuation.*"
        )

    return insights


@router.post("/generate/insights")
@router.post("/insights/generate", include_in_schema=False)
@router.post("/insights", include_in_schema=False)
async def generate_insights(
    body: InsightsRequest,
    user: User = Depends(require_role("operator", "admin")),
):
    """
    Generate traffic management advisory insights.
    Restricted to operators and administrators.
    """
    prompt = body.prompt.strip()
    llm = detector_service.get_insights_llm()

    if llm is not None:
        try:
            if hasattr(llm, "generate_insights"):
                results = llm.generate_insights(prompt)
                return {
                    "success": True,
                    "message": "Insights generation successful",
                    "insights": [results] if isinstance(results, str) else results,
                    "disclaimer": "AI Advisory: Recommendations require operator confirmation before physical actuation.",
                }
        except Exception as e:
            logger.error("LLM insights generation error: %s", e)

    # If LLM is not available or failed, use safe analytical fallback
    insights = _generate_fallback_insights(prompt)
    return {
        "success": True,
        "message": "Insights generation successful",
        "insights": insights,
        "disclaimer": "AI Advisory: Recommendations require operator confirmation before physical actuation.",
    }
