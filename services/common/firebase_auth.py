"""
Firebase Admin SDK wrapper for verifying client-issued ID tokens.

The frontend obtains a Firebase ID token via the Web SDK after a successful
sign-in (Google / Apple / Facebook) and sends it on every API request as
`Authorization: Bearer <token>`. This module verifies that token using the
service-account credentials in `FIREBASE_SERVICE_ACCOUNT_PATH`.
"""
from __future__ import annotations

import logging
import os
import threading
from typing import Optional

import firebase_admin
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth_sdk
from firebase_admin import credentials

logger = logging.getLogger(__name__)

_init_lock = threading.Lock()
_initialized = False


def _ensure_initialized() -> None:
    """Initialize the default Firebase app exactly once, lazily."""
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        sa_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
        if not sa_path:
            raise RuntimeError(
                "FIREBASE_SERVICE_ACCOUNT_PATH is not set. "
                "Point it at the Firebase Admin SDK service-account JSON."
            )
        if not os.path.isfile(sa_path):
            raise RuntimeError(
                f"FIREBASE_SERVICE_ACCOUNT_PATH points at '{sa_path}' "
                f"but no file exists there."
            )
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)
        _initialized = True
        logger.info(f"[firebase_auth] initialized from {sa_path}")


def verify_id_token(token: str) -> dict:
    """
    Verify a Firebase ID token. On success returns the decoded claims dict
    (contains at least `uid`, optionally `email`). On any verification
    failure raises HTTPException 401.
    """
    _ensure_initialized()
    try:
        return firebase_auth_sdk.verify_id_token(token)
    except firebase_auth_sdk.ExpiredIdTokenError:
        logger.info("[firebase_auth] expired id token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth_sdk.RevokedIdTokenError:
        logger.info("[firebase_auth] revoked id token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except firebase_auth_sdk.InvalidIdTokenError as exc:
        logger.warning(f"[firebase_auth] invalid id token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def parse_bearer_header(authorization: Optional[str]) -> str:
    """Extract the raw token from a `Bearer <token>` header, or 401 if malformed."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token
