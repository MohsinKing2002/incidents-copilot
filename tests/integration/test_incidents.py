import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Incident


@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_create_incident(db_session: AsyncSession):
    incident = Incident(
        title="Payment service unavailable",
        description="Payment API returning 503 errors",
        service_name="payment-service",
        environment="production",
        severity="critical",
        status="open",
    )

    db_session.add(incident)
    await db_session.commit()

    result = await db_session.execute(
        select(Incident).where(Incident.id == incident.id)
    )

    saved_incident = result.scalar_one()

    assert saved_incident.id == incident.id
    assert saved_incident.title == "Payment service unavailable"
    assert saved_incident.severity == "critical"
    assert saved_incident.status == "open"
    assert saved_incident.created_at is not None
