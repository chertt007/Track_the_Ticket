from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.routers import subscriptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    await engine.connect()
    yield
    await engine.dispose()


app = FastAPI(
    title="TrackTheTicket API",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "prod" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(subscriptions.router)


@app.get("/health")
async def health():
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok", "environment": settings.environment}
