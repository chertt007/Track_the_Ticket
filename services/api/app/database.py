import ssl

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# RDS requires SSL in production; asyncpg does not enable it by default.
_connect_args: dict = {}
if settings.environment == "prod":
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE  # RDS uses AWS-managed cert; skip hostname check
    _connect_args["ssl"] = _ssl_ctx

engine = create_async_engine(
    settings.database_url,
    echo=False,  # never log SQL in production (contains sensitive data)
    pool_size=5,
    max_overflow=10,
    connect_args=_connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
