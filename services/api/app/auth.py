import base64

import httpx
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
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


def _rsa_jwk_to_pem(key: dict) -> bytes:
    """Convert a Cognito RSA JWK to PEM bytes.

    python-jose's jwk.construct() returns a jose.jwk.RSAKey object, but
    jwt.decode() internally calls RSAAlgorithm.prepare_key() which only accepts
    PEM bytes (str/bytes) or a native cryptography.RSAPublicKey — not a jose.jwk.RSAKey.
    Passing the wrong type raises InvalidKeyError, silently wrapped into JWTError,
    causing a spurious 401. We convert the JWK directly to PEM to avoid this.
    """

    def _b64url_to_int(s: str) -> int:
        s += "=" * (-len(s) % 4)
        return int.from_bytes(base64.urlsafe_b64decode(s), "big")

    public_key = RSAPublicNumbers(
        e=_b64url_to_int(key["e"]),
        n=_b64url_to_int(key["n"]),
    ).public_key(default_backend())

    return public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        logger.info(f"Fetching JWKS from Cognito | url={JWKS_URL}")
        async with httpx.AsyncClient() as client:
            response = await client.get(JWKS_URL)
            response.raise_for_status()
            _jwks_cache = response.json()
        available_kids = [k["kid"] for k in _jwks_cache.get("keys", [])]
        logger.info(f"JWKS fetched | available_kids={available_kids}")
    return _jwks_cache


async def _decode_token(token: str) -> dict:
    token_preview = token[:40] + "..." if len(token) > 40 else token

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        logger.warning(
            f"Token is malformed | error={exc!s} | token_preview={token_preview}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is malformed",
        )

    kid = unverified_header.get("kid")
    alg = unverified_header.get("alg")
    logger.info(f"Token header parsed | kid={kid} | alg={alg}")

    jwks = await _get_jwks()
    available_kids = [k["kid"] for k in jwks.get("keys", [])]

    matched_key = None
    for key in jwks["keys"]:
        if key["kid"] == kid:
            matched_key = key
            break

    if matched_key is None:
        logger.warning(
            f"No matching public key | token_kid={kid} | available_kids={available_kids}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Public key not found",
        )

    logger.info(f"Matched public key | kid={kid}")

    try:
        pem_key = _rsa_jwk_to_pem(matched_key)
    except Exception as exc:
        logger.warning(
            f"JWK to PEM conversion failed | error_type={type(exc).__name__} | error={exc!s} | kid={kid}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to load public key",
        )

    try:
        payload = jwt.decode(
            token,
            pem_key,
            algorithms=["RS256"],
            options={
                "verify_aud": False,
                "verify_at_hash": False,  # ID token contains at_hash; we don't pass access_token, so skip this check
            },
        )
    except JWTError as exc:
        logger.warning(
            f"Token decode failed | error_type={type(exc).__name__} | error={exc!s} | kid={kid}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired",
        )

    logger.info(f"Token decoded successfully | sub={payload.get('sub')} | email={payload.get('email')}")
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
        logger.warning(f"Token payload missing sub | payload_keys={list(payload.keys())}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    result = await db.execute(select(User).where(User.cognito_id == cognito_id))
    user = result.scalar_one_or_none()

    if user is None:
        logger.info(f"Creating new user | cognito_id={cognito_id} | email={email}")
        user = User(cognito_id=cognito_id, email=email)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        logger.info(f"User found | user_id={user.id} | cognito_id={cognito_id}")

    return user
