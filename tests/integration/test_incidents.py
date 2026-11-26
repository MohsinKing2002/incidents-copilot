import uuid

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Incident, IncidentEvent, IncidentLog


# Test database connection
@pytest.mark.asyncio
async def test_database_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


# Test creating an incident
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


# Test creating multiple incident logs
@pytest.mark.asyncio
async def test_create_multiple_incident_logs(db_session: AsyncSession):
    # 1. Create an incident
    incident = Incident(
        title="Payment service unavailable",
        service_name="payment-service",
        environment="production",
        severity="critical",
    )

    # 2. Create multiple logs
    log1 = IncidentLog(
        message="Payment API returned 503",
        source="api-gateway",
        level="ERROR",
    )

    log2 = IncidentLog(
        message="Database connection timeout",
        source="payment-service",
        level="ERROR",
    )

    log3 = IncidentLog(
        message="Connection pool exhausted",
        source="payment-service",
        level="CRITICAL",
    )

    # 3. associates log with the incident
    incident.logs.extend([log1, log2, log3])

    # 4. Persist everything
    db_session.add(incident)
    await db_session.commit()

    # 5. Verify foreign key relationships
    assert log1.incident_id == incident.id
    assert log2.incident_id == incident.id
    assert log3.incident_id == incident.id

    # 6. retrieve incident with logs
    result = await db_session.execute(
        select(Incident)
        .options(selectinload(Incident.logs))
        .where(Incident.id == incident.id)
    )

    saved_incident = result.scalar_one()

    # 7. verify persisted relationships
    assert len(saved_incident.logs) == 3
    assert {log.message for log in saved_incident.logs} == {
        "Payment API returned 503",
        "Database connection timeout",
        "Connection pool exhausted",
    }


# Test creating multiple incident events
@pytest.mark.asyncio
async def test_create_multiple_incident_event(db_session: AsyncSession):
    # 1. Create an incident
    incident = Incident(
        title="Payment service outage",
        service_name="payment-service",
        environment="production",
        severity="critical",
    )

    db_session.add(incident)
    await db_session.flush()  # Flush to get the incident ID before creating events

    # 2. Create lifecycle events
    events = [
        IncidentEvent(
            incident_id=incident.id,
            event_type="status_changed",
            old_value=None,
            new_value="open",
            details="Incident created",
            actor="system",
        ),
        IncidentEvent(
            incident_id=incident.id,
            event_type="status_changed",
            old_value="open",
            new_value="investigating",
            details="Engineer started investigation",
            actor="engineer@example.com",
        ),
        IncidentEvent(
            incident_id=incident.id,
            event_type="status_changed",
            old_value="investigating",
            new_value="resolved",
            details="Database connection issue fixed",
            actor="engineer@example.com",
        ),
    ]

    # 3. associates events with the incident
    db_session.add_all(events)
    await db_session.commit()

    # 4. retrieve incident with events
    result = await db_session.execute(
        select(Incident)
        .options(selectinload(Incident.events))
        .where(Incident.id == incident.id)
    )

    saved_incident = result.scalar_one()

    # 5. verify
    assert len(saved_incident.events) == 3

    assert saved_incident.events[0].old_value is None
    assert saved_incident.events[1].new_value == "investigating"
    assert saved_incident.events[2].new_value == "resolved"

    assert all(event.incident_id == incident.id for event in saved_incident.events)


# Test handling of invalid incident foreign key
@pytest.mark.asyncio
async def test_invalid_incident_foreign_key(db_session: AsyncSession):
    # Generate a random UUID that doesn't exist in the database
    invalid_incident_id = uuid.uuid4()

    # Attempt to create a log for the invalid incident
    invalid_log = IncidentLog(
        incident_id=invalid_incident_id,
        message="This log references a non-existent incident",
        source="payment-service",
        level="ERROR",
    )

    db_session.add(invalid_log)

    with pytest.raises(IntegrityError):
        await db_session.flush()

    # recover the session after failed flush
    await db_session.rollback()


# Test invalid incident fields (3 tests)
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("environment", "invalid-env"),
        ("severity", "invalid-severity"),
        ("status", "invalid-status"),
    ],
)
async def test_invalid_incident_check_constraints(
    db_session: AsyncSession, field: str, invalid_value: str
):
    incident_data = {
        "title": "Invalid incident",
        "service_name": "payment-service",
        "environment": "production",
        "severity": "high",
        "status": "open",
    }

    # override one field with invalid value
    incident_data[field] = invalid_value

    incident = Incident(**incident_data)

    db_session.add(incident)

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


# Test cascading delete of child records
@pytest.mark.asyncio
async def test_cascade_delete_incident(db_session: AsyncSession):
    # 1. create parent incident
    incident = Incident(
        title="Payment service outage",
        service_name="payment-service",
        environment="production",
        severity="critical",
    )

    db_session.add(incident)
    await db_session.flush()  # Flush to get the incident ID before creating logs/events

    # 2. create child records using foreign key
    logs = [
        IncidentLog(
            incident_id=incident.id,
            message=f"Error log {i}",
            source="payment-service",
            level="ERROR",
        )
        for i in range(3)
    ]

    events = [
        IncidentEvent(
            incident_id=incident.id,
            event_type="status_changed",
            old_value="open",
            new_value="investigating",
            actor="engineer@example.com",
        ),
        IncidentEvent(
            incident_id=incident.id,
            event_type="status_changed",
            old_value="investigating",
            new_value="resolved",
            actor="engineer@example.com",
        ),
    ]

    db_session.add_all(logs + events)
    await db_session.commit()

    # 3. delete parent incident
    await db_session.delete(incident)
    await db_session.commit()

    # 4. verify parent deletion
    result = await db_session.execute(
        select(Incident).where(Incident.id == incident.id)
    )

    assert result.scalar_one_or_none() is None

    # 5. verify child records are also deleted
    logs_count = await db_session.scalar(
        select(func.count())
        .select_from(IncidentLog)
        .where(IncidentLog.incident_id == incident.id)
    )

    events_count = await db_session.scalar(
        select(func.count())
        .select_from(IncidentEvent)
        .where(IncidentEvent.incident_id == incident.id)
    )

    assert logs_count == 0
    assert events_count == 0


@pytest.mark.asyncio
async def test_transaction_rollback(db_session: AsyncSession):
    # 1. create indicent
    incident = Incident(
        title="Temporary outage",
        service_name="payment-service",
        environment="production",
        severity="high",
    )

    db_session.add(incident)

    # 2. Flush insert to PostgreSQL
    await db_session.flush()

    incident_id = incident.id

    # 3. incident existance verify
    result = await db_session.execute(
        select(Incident).where(Incident.id == incident_id)
    )

    assert result.scalar_one_or_none() is not None

    # 4. rollback the session transaction
    await db_session.rollback()

    # 5. verify incident - no longer exists
    result = await db_session.execute(
        select(Incident).where(Incident.id == incident_id)
    )

    assert result.scalar_one_or_none() is None
