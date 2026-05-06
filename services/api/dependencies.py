"""FastAPI dependencies shared across routes."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from common.database import get_db
from common.db_models import User
from common.firebase_auth import parse_bearer_header, verify_id_token
from common.queries import upsert_user

logger = logging.getLogger(__name__)


def current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency that resolves the authenticated user from the
    `Authorization: Bearer <firebase_id_token>` header.

    On the user's first authenticated request a row is lazily created in
    the `users` table (Firebase UID becomes the primary key). Any
    verification failure raises HTTPException 401.
    """
    token = parse_bearer_header(authorization)
    claims = verify_id_token(token)
    uid: str = claims["uid"]
    email: Optional[str] = claims.get("email")
    return upsert_user(db, uid, email)
