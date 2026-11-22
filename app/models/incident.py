import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"

    __table_args__ = (
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_incidents_severity",
        ),
        CheckConstraint(
            "status IN ('open', 'acknowledged', 'investigating', 'resolved', 'closed')",
            name="ck_incidents_status",
        ),
        CheckConstraint(
            "environment IN ('production', 'staging', 'development')",
            name="ck_incidents_environment",
        ),
        Index(
            "idx_incidents_status_severity_created", "status", "severity", "created_at"
        ),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Incident information
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="open", server_default=text("'open'")
    )
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    logs: Mapped[list["IncidentLog"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan", passive_deletes=True
    )

    events: Mapped[list["IncidentEvent"]] = relationship(
        back_populates="incident", cascade="all, delete-orphan", passive_deletes=True
    )
