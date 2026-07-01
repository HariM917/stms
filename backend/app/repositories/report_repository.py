"""
Traffic report repository — async CRUD operations for TrafficReport model.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.db.traffic_report import TrafficReport


async def create_report(
    db: AsyncSession,
    *,
    user_id: str,
    junction_id: str,
    weather_condition: str | None = None,
    congestion_level: float | None = None,
    vehicle_count: int | None = None,
    pedestrian_count: int | None = None,
    railway_crossing_active: bool = False,
    notes: str | None = None,
) -> TrafficReport:
    """Create a new traffic report."""
    report = TrafficReport(
        user_id=user_id,
        junction_id=junction_id,
        weather_condition=weather_condition,
        congestion_level=congestion_level,
        vehicle_count=vehicle_count,
        pedestrian_count=pedestrian_count,
        railway_crossing_active=railway_crossing_active,
        notes=notes,
    )
    db.add(report)
    await db.flush()
    return report


async def get_report_by_id(db: AsyncSession, report_id: str) -> TrafficReport | None:
    """Look up a report by primary key."""
    result = await db.execute(
        select(TrafficReport)
        .options(joinedload(TrafficReport.user))
        .where(TrafficReport.id == report_id)
    )
    return result.scalar_one_or_none()


async def list_reports(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[TrafficReport]:
    """
    List traffic reports with optional user filter and pagination.
    If user_id is None, returns all reports (admin view).
    """
    query = (
        select(TrafficReport)
        .options(joinedload(TrafficReport.user))
        .order_by(TrafficReport.report_time.desc())
    )
    if user_id is not None:
        query = query.where(TrafficReport.user_id == user_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return list(result.scalars().unique().all())


async def count_reports(
    db: AsyncSession,
    *,
    user_id: str | None = None,
) -> int:
    """Count total reports, optionally filtered by user."""
    query = select(func.count(TrafficReport.id))
    if user_id is not None:
        query = query.where(TrafficReport.user_id == user_id)
    result = await db.execute(query)
    return result.scalar_one()


async def get_recent_reports(
    db: AsyncSession,
    *,
    user_id: str | None = None,
    limit: int = 10,
) -> list[TrafficReport]:
    """Get the most recent reports (shorthand for list_reports with small limit)."""
    return await list_reports(db, user_id=user_id, limit=limit, offset=0)
