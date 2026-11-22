import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentLog(Base):
    __tablename__ = "incident_logs"

    __table_args__ = (
        Index("idx_incident_logs_incident_logged_at", "incident_id", "logged_at"),
    )

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign key to the incident
    incident_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Log information
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Timestamp
    logged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(back_populates="logs")
