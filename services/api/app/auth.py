import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.models.user import User
from sqlalchemy import select

JWKS_URL = (
    f"https://cognito-idp.{settings.cognito_region}.amazonaws.com"
    f"/{settings.cognito_user_pool_id}/.well-known/jwks.json"
)

_jwks_cache: dict | None = None

bearer_scheme = HTTPBearer()


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


async def _decode_token(token: str) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is malformed",
        )

    jwks = await _get_jwks()
    kid = unverified_header.get("kid")

    public_key = None
    for key in jwks["keys"]:
        if key["kid"] == kid:
            public_key = jwk.construct(key)
            break

    if public_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public key not found",
        )

    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = await _decode_token(token)

    cognito_id: str = payload.get("sub")
    email: str = payload.get("email", "")

    if not cognito_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.cognito_id == cognito_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(cognito_id=cognito_id, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
