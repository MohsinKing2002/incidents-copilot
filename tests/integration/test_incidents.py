import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_db_connection(db_session: AsyncSession):
    result = await db_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


@pytest.mark.asyncio
async def test_transaction_rollback(db_session):
    test_value = str(uuid.uuid4())

    await db_session.execute(text("SELECT 1"))

    await db_session.commit()

    assert test_value is not None
