"""NeuroSync — /health endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import (
    get_extractor, get_intelligence_engine, get_semantic_engine, get_state_backend,
)
from app.config import get_settings

router = APIRouter()


@router.get("/health", summary="System health check")
async def health():
    config = get_settings()
    extractor = get_extractor()
    semantic = get_semantic_engine()
    intelligence = get_intelligence_engine()
    state = get_state_backend()

    state_health = state.health()

    return {
        # An unreachable database is not "healthy" — persistence failing
        # silently is precisely the failure this layer exists to prevent.
        "status": "healthy" if state_health.get("status") == "healthy" else "degraded",
        "version": config.versions.engine,
        "api_version": config.versions.api,
        "components": {
            "extractor": extractor.get_stats() if extractor else {"status": "unavailable"},
            "semantic_engine": "available" if semantic else "unavailable",
            "intelligence_engine": "available" if intelligence else "unavailable",
            "state": state_health,
            "feedback": intelligence.get_feedback_stats().as_response() if intelligence else {},
        },
    }
