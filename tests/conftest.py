import pytest_asyncio
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings


@pytest_asyncio.fixture
async def db_session():
    # Safety guard: never run tests against development DB
    database_url = make_url(settings.TEST_DATABASE_URL)

    if database_url.database != "incident_copilot_test":
        raise RuntimeError("Tests must run against test db('incident_copilot_test')")

    # create an engine for this test
    engine = create_async_engine(
        settings.TEST_DATABASE_URL, echo=False, pool_pre_ping=True
    )

    try:
        async with engine.connect() as connection:
            # start outer transaction
            transaction = await connection.begin()

            # create session bound to the connection
            session = AsyncSession(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            )

            try:
                yield session

            finally:
                # close the session and rollback outer transaction
                await session.close()

                if transaction.is_active:
                    await transaction.rollback()

    finally:
        await engine.dispose()
