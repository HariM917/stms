"""
Traffic reports router — CRUD for traffic condition reports.
Ported from the Node.js auth-server.js into the Python backend.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth_middleware import get_current_user, require_role
from app.models.db.user import User
from app.models.db.traffic_report import TrafficReport
from app.repositories import report_repository
from app.utils.logging import get_logger
from pydantic import BaseModel, Field
from typing import Optional

logger = get_logger("reports")
router = APIRouter(prefix="/reports", tags=["traffic reports"])


# ---- Request/Response Models ----

class CreateReportRequest(BaseModel):
    """Request body for creating a traffic report."""
    junction_id: str = Field(..., min_length=1, max_length=100)
    weather_condition: Optional[str] = Field(None, max_length=50)
    congestion_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    vehicle_count: Optional[int] = Field(None, ge=0)
    pedestrian_count: Optional[int] = Field(None, ge=0)
    railway_crossing_active: bool = False
    notes: Optional[str] = None


class ReportResponse(BaseModel):
    """Single report in API responses."""
    id: str
    junction_id: str
    report_time: str
    weather_condition: Optional[str] = None
    congestion_level: Optional[float] = None
    vehicle_count: Optional[int] = None
    pedestrian_count: Optional[int] = None
    railway_crossing_active: bool = False
    notes: Optional[str] = None
    reporter_name: Optional[str] = None
    type: Optional[str] = None
    status: Optional[str] = None


def _report_to_response(report: TrafficReport) -> ReportResponse:
    """Convert a TrafficReport ORM instance to a response model."""
    # Determine report type from data
    report_type = "Traffic Sign"
    if report.railway_crossing_active:
        report_type = "Railway Crossing"
    elif report.weather_condition and report.weather_condition.lower() != "clear":
        report_type = "Weather"
    elif report.notes and "pothole" in report.notes.lower():
        report_type = "Pothole"

    # Determine status based on age
    report_status = "New"
    if report.report_time:
        hours_ago = (datetime.now(timezone.utc) - report.report_time.replace(tzinfo=timezone.utc if report.report_time.tzinfo is None else report.report_time.tzinfo)).total_seconds() / 3600
        if hours_ago > 3:
            report_status = "Resolved"
        elif hours_ago > 1:
            report_status = "In Progress"

    reporter_name = report.user.name if report.user else None

    return ReportResponse(
        id=report.id,
        junction_id=report.junction_id,
        report_time=report.report_time.isoformat() if report.report_time else "",
        weather_condition=report.weather_condition,
        congestion_level=report.congestion_level,
        vehicle_count=report.vehicle_count,
        pedestrian_count=report.pedestrian_count,
        railway_crossing_active=report.railway_crossing_active,
        notes=report.notes,
        reporter_name=reporter_name,
        type=report_type,
        status=report_status,
    )


# ---- Endpoints ----

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_report(
    body: CreateReportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new traffic report (authenticated)."""
    report = await report_repository.create_report(
        db,
        user_id=user.id,
        junction_id=body.junction_id,
        weather_condition=body.weather_condition,
        congestion_level=body.congestion_level,
        vehicle_count=body.vehicle_count,
        pedestrian_count=body.pedestrian_count,
        railway_crossing_active=body.railway_crossing_active,
        notes=body.notes,
    )

    logger.info("Report created by %s: junction=%s", user.email, body.junction_id)
    return {
        "success": True,
        "message": "Traffic report saved successfully",
        "report": {"id": report.id, "report_time": report.report_time.isoformat()},
    }


@router.get("")
async def list_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    List traffic reports with pagination.
    Admins see all reports; regular users see only their own.
    """
    user_filter = None if user.role == "admin" else user.id

    reports = await report_repository.list_reports(
        db, user_id=user_filter, limit=limit, offset=offset
    )
    total = await report_repository.count_reports(db, user_id=user_filter)

    return {
        "success": True,
        "message": "Reports retrieved successfully",
        "reports": [_report_to_response(r) for r in reports],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total,
        },
    }


@router.get("/recent")
async def recent_reports(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=10, ge=1, le=50),
):
    """Get the most recent traffic reports."""
    user_filter = None if user.role == "admin" else user.id
    reports = await report_repository.get_recent_reports(
        db, user_id=user_filter, limit=limit
    )
    return {
        "success": True,
        "reports": [_report_to_response(r) for r in reports],
    }
