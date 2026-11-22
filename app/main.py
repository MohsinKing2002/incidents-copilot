from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.dependencies import get_db
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    await engine.dispose()


app = FastAPI(
    title="AI Incident Management Copilot",
    description="AI-powered incident investigation and management platform",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Incident Management Copilot"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "incident-copilot"}


@app.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    result = await db.execute(text("SELECT 1"))

    return {"status": "connected", "database": "postgresql", "result": result.scalar()}
