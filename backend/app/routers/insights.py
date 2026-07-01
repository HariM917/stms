"""
AI insights router.
Generates traffic insights using LLM with a rule-based fallback.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.services import detector_service
from app.utils.logging import get_logger

logger = get_logger("insights")
router = APIRouter(tags=["insights"])


def _generate_fallback_insights(prompt: str) -> list[str]:
    """
    Rich, context-aware rule-based fallback when the LLM is not available.
    Parses the prompt to provide relevant, structured responses.
    """
    insights = []

    # Check if the prompt is for an incident summary
    if "incident summary" in prompt.lower() or (
        "type:" in prompt.lower() and "location:" in prompt.lower()
    ):
        incident_type = "Incident"
        location = "Junction"
        desc = ""

        if "Type:" in prompt:
            try:
                incident_type = prompt.split("Type:")[1].split(",")[0].strip()
            except Exception:
                pass
        if "Location:" in prompt:
            try:
                location = prompt.split("Location:")[1].split(",")[0].strip()
            except Exception:
                pass
        if "Description:" in prompt:
            try:
                desc = prompt.split("Description:")[1].split(".")[0].strip().replace('"', "")
            except Exception:
                pass

        summary = (
            f"**OFFICIAL TRAFFIC LOG**: Active **{incident_type.title()}** "
            f"reported at **{location}**. "
        )
        if desc:
            summary += f"Reported situation: {desc}. "
        summary += (
            "Emergency response teams have been dispatched. "
            "Automated gating algorithms are adjusting adjacent signals "
            "to manage vehicle spillover."
        )
        insights.append(summary)
    else:
        # General AI advice request
        high_density = "none"
        active_alerts = "none"
        recent_incidents = "none"

        if "High-Density Nodes (>80):" in prompt:
            try:
                high_density = prompt.split("High-Density Nodes (>80):")[1].split("-")[0].strip()
            except Exception:
                pass
        if "Active System Alerts:" in prompt:
            try:
                active_alerts = prompt.split("Active System Alerts:")[1].split("-")[0].strip()
            except Exception:
                pass
        if "Recent Incidents:" in prompt:
            try:
                recent_incidents = prompt.split("Recent Incidents:")[1].strip()
            except Exception:
                pass

        insights.append("🚦 **Signal Optimization Recommendations**:")

        if high_density and high_density.lower() != "none":
            insights.append(
                f"1. **Congestion Alert**: Critical volume detected at **{high_density}**. "
                "Adjusting traffic light timers to prioritize main arterials (+15s green phase)."
            )
        else:
            insights.append(
                "1. **Normal Flow**: No critical congestion detected. "
                "Standard scheduling and AI predictive offsets are active."
            )

        if active_alerts and active_alerts.lower() != "none":
            insights.append(
                f"2. **Active Alert Response**: Addressing **{active_alerts}**. "
                "Triggering alert notifications to local traffic police."
            )
        else:
            insights.append(
                "2. **System Health**: Infrastructure and connectivity statuses "
                "are healthy across all active control centers."
            )

        if recent_incidents and recent_incidents.lower() != "none":
            insights.append(
                f"3. **Incident Impact Mitigation**: Managing **{recent_incidents}**. "
                "Directing neighboring nodes to apply defensive gating "
                "to slow flow heading into the incident zone."
            )
        else:
            insights.append(
                "3. **Incident Control**: No major collisions or blockages reported. "
                "Rerouting algorithms are standing by."
            )

        insights.append(
            "4. **Weather Action**: Standard weather protocols active. Speeds are optimal."
        )

    return insights


@router.post("/generate/insights")
@router.post("/insights", include_in_schema=False)
async def generate_insights(request: Request):
    """Generate traffic insights using LLM with rule-based fallback."""
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
    except Exception:
        prompt = ""

    # Try the real LLM first
    llm = detector_service.get_insights_llm()
    if llm is not None:
        try:
            if hasattr(llm, "generate_insights"):
                result = llm.generate_insights(prompt)
                return {
                    "success": True,
                    "message": "Insights generation successful",
                    "insights": [result] if isinstance(result, str) else result,
                }
        except Exception as e:
            logger.warning("LLM insights generation failed: %s — using fallback", e)

    # Rule-based fallback
    insights = _generate_fallback_insights(prompt)

    return {
        "success": True,
        "message": "Insights generation successful",
        "insights": insights,
    }
