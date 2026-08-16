"""
NeuroSync — Authentication Service.
Magic-link token generation, verification, and JWT session management.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt

from app.config import get_settings

logger = logging.getLogger(__name__)


class AuthError(ValueError):
    """Raised when token is invalid or expired."""
    pass


class AuthService:
    """Handles JWT creation and verification for magic links and user sessions."""

    def __init__(self, secret_key: Optional[str] = None):
        config = get_settings()
        self._secret = secret_key or config.secret_key
        self._algorithm = "HS256"
        self._access_ttl_days = config.token_expire_days
        self._magic_ttl_min = config.magic_link_expire_minutes

    def create_magic_link_token(self, email: str) -> str:
        """Create a short-lived magic link token for email authentication."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": email.strip().lower(),
            "type": "magic_link",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._magic_ttl_min)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_magic_link_token(self, token: str) -> str:
        """Verify magic link token and return normalized user email."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            if payload.get("type") != "magic_link":
                raise AuthError("Invalid token type")
            email = payload.get("sub")
            if not email:
                raise AuthError("Token payload missing subject")
            return email
        except jwt.ExpiredSignatureError:
            raise AuthError("Magic link has expired")
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {str(e)}")

    def create_access_token(self, email: str) -> str:
        """Create a 7-day session JWT access token."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": email.strip().lower(),
            "type": "access_token",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=self._access_ttl_days)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_access_token(self, token: str) -> str:
        """Verify access token and return user email."""
        try:
            payload = jwt.decode(token, self._secret, algorithms=[self._algorithm])
            if payload.get("type") != "access_token":
                raise AuthError("Invalid token type")
            email = payload.get("sub")
            if not email:
                raise AuthError("Token payload missing subject")
            return email
        except jwt.ExpiredSignatureError:
            raise AuthError("Session token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {str(e)}")
