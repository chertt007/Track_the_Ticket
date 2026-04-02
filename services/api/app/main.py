from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.logging_config import setup_logging, get_logger
from app.middleware import RequestLoggingMiddleware
from app.routers import subscriptions
from app.tracing import setup_tracing

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize structured logging before anything else
    setup_logging(
        environment=settings.environment,
        log_level="DEBUG" if settings.environment == "local" else "INFO",
    )
    logger.info(
        "🚀 application starting",
        extra={"environment": settings.environment},
    )
    setup_tracing(environment=settings.environment)
    await engine.connect()
    yield
    logger.info("🛑 application shutting down")
    await engine.dispose()


app = FastAPI(
    title="TrackTheTicket API",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "prod" else None,
    lifespan=lifespan,
)

# Request logging middleware (must be added before CORS)
app.add_middleware(RequestLoggingMiddleware)

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
