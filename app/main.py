from fastapi import FastAPI

app = FastAPI(
    title="AI Incident Management Copilot",
    description="AI-powered incident investigation and management platform",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Welcome to the AI Incident Management Copilot"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "incident-copilot"}
