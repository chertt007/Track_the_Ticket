import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db
from app.logging_config import get_logger
from app.models.user import User
from sqlalchemy import select

logger = get_logger(__name__)

JWKS_URL = (
    f"https://cognito-idp.{settings.cognito_region}.amazonaws.com"
    f"/{settings.cognito_user_pool_id}/.well-known/jwks.json"
)

_jwks_cache: dict | None = None

bearer_scheme = HTTPBearer()


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        logger.info("Fetching JWKS from Cognito", extra={"url": JWKS_URL})
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            _jwks_cache = response.json()
        logger.info(
            "JWKS fetched successfully",
            extra={"key_ids": [k["kid"] for k in _jwks_cache.get("keys", [])]},
        )
    else:
        logger.debug("Using cached JWKS")
    return _jwks_cache


async def _decode_token(token: str) -> dict:
    # Log the token prefix so we can identify it without exposing the full value
    token_preview = token[:40] + "..." if len(token) > 40 else token
    logger.debug("Decoding token", extra={"token_preview": token_preview})

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        logger.warning(
            "Failed to parse token header — token is malformed",
            extra={"error": str(exc), "token_preview": token_preview},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is malformed",
        )

    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg")
    logger.debug("Token header parsed", extra={"kid": kid, "alg": alg})

    jwks = await _get_jwks()
    available_kids = [k["kid"] for k in jwks.get("keys", [])]

    public_key = None
    for key in jwks["keys"]:
        if key["kid"] == kid:
            public_key = jwk.construct(key)
            logger.debug("Matched public key", extra={"kid": kid, "kty": key.get("kty")})
            break

    if public_key is None:
        logger.warning(
            "No matching public key found for token",
            extra={"token_kid": kid, "available_kids": available_kids},
        )
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
        logger.info(
            "Token decoded successfully",
            extra={"sub": payload.get("sub"), "email": payload.get("email")},
        )
    except JWTError as exc:
        logger.warning(
            "Token decode failed",
            extra={
                "error_type": type(exc).__name__,
                "error_detail": str(exc),
                "kid": kid,
                "token_preview": token_preview,
            },
        )
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
        logger.warning("Token payload missing 'sub' field", extra={"payload_keys": list(payload.keys())})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.cognito_id == cognito_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.info("Creating new user from Cognito", extra={"cognito_id": cognito_id, "email": email})
        user = User(cognito_id=cognito_id, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        logger.debug("User found in DB", extra={"user_id": user.id, "cognito_id": cognito_id})

    return user
