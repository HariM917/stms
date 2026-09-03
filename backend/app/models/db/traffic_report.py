"""
Traffic report ORM model.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TrafficReport(Base):
    """Traffic condition report submitted by a user."""

    __tablename__ = "traffic_reports"
    __table_args__ = (
        Index("ix_traffic_reports_user_report_time", "user_id", "report_time"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: f"rpt_{uuid.uuid4().hex[:12]}"
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    junction_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    report_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False, index=True
    )
    weather_condition: Mapped[str | None] = mapped_column(String(50), nullable=True)
    congestion_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    vehicle_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pedestrian_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    railway_crossing_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    # Relationship
    user = relationship("User", back_populates="reports")

    def __repr__(self) -> str:
        return f"<TrafficReport(id={self.id!r}, junction={self.junction_id!r})>"
