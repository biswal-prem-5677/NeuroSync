"""
NeuroSync — Auth Endpoints.
Magic link authentication and user session management.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field

from app.services.auth_service import AuthService, AuthError

logger = logging.getLogger(__name__)
router = APIRouter()
_auth_service = AuthService()


class MagicLinkRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class VerifyTokenRequest(BaseModel):
    token: str = Field(..., description="Magic link token")


class UserProfileResponse(BaseModel):
    email: str
    authenticated: bool = True


@router.post("/auth/magic-link", summary="Request magic link for email login")
async def request_magic_link(body: MagicLinkRequest):
    """
    Generate a magic link token for email login.
    In dev mode, the token is returned directly in the response payload.
    """
    email = body.email.strip().lower()
    token = _auth_service.create_magic_link_token(email)
    logger.info("Magic link requested for %s", email)

    return {
        "status": "success",
        "message": f"Magic link generated for {email}",
        "dev_magic_link": f"/auth/verify?token={token}",
        "token": token,
    }


@router.post("/auth/verify", summary="Verify magic link token and obtain access token")
async def verify_magic_link(body: VerifyTokenRequest):
    """Verify magic link token and return JWT access token."""
    try:
        email = _auth_service.verify_magic_link_token(body.token)
        access_token = _auth_service.create_access_token(email)
        logger.info("User authenticated via magic link: %s", email)
        return {
            "status": "authenticated",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {"email": email},
        }
    except AuthError as e:
        logger.warning("Magic link verification failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/auth/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_current_user_profile(authorization: Optional[str] = Header(None)):
    """Return user profile from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Bearer token")

    token = authorization.split(" ")[1]
    try:
        email = _auth_service.verify_access_token(token)
        return UserProfileResponse(email=email, authenticated=True)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))
