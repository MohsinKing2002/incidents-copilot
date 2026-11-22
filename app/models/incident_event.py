import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    __table_args__ = Index(
        "idx_incident_events_incident_created", "incident_id", "created_at"
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

    # Event information
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    new_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    incident: Mapped["Incident"] = relationship(back_populates="events")
