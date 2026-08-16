"""NeuroSync — API v1 Router."""
from fastapi import APIRouter

from app.api.v1.endpoints import analyze, analyze_file, auth, health, feedback, behavior, market

router = APIRouter(tags=["v1"])

router.include_router(analyze.router)
router.include_router(analyze_file.router)
router.include_router(auth.router)
router.include_router(health.router)
router.include_router(feedback.router)
router.include_router(behavior.router)
router.include_router(market.router)




