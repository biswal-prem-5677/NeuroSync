"""NeuroSync — Social, Identity & Portfolio API Endpoint Router."""

from fastapi import APIRouter
from typing import Dict, List, Any
from app.services.social_profile_engine import (
    social_profile_engine,
    UnifiedProfile,
    AchievementPost
)

router = APIRouter(prefix="/social", tags=["Social, Identity & Portfolio"])


@router.get("/profile", response_model=UnifiedProfile, summary="Get user unified public profile")
async def get_profile(user_id: str = "usr_biswal"):
    """Retrieve user's public achievement profile & portfolio projects."""
    return social_profile_engine.get_profile(user_id)


@router.get("/feed", response_model=List[AchievementPost], summary="Get public community achievement feed")
async def get_feed():
    """Retrieve public achievement feed."""
    return social_profile_engine.get_community_feed()


@router.post("/post", response_model=AchievementPost, summary="Post an achievement to public feed")
async def create_post(post: AchievementPost):
    """Publish a new project/certificate achievement to the community feed."""
    return social_profile_engine.create_post(post)
