"""NeuroSync — API v1 Router."""
from fastapi import APIRouter

from app.api.v1.endpoints import analyze, health, feedback

router = APIRouter(tags=["v1"])

router.include_router(analyze.router)
router.include_router(health.router)
router.include_router(feedback.router)
