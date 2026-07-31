"""NeuroSync — /health endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import get_extractor, get_intelligence_engine, get_semantic_engine
from app.config import get_settings

router = APIRouter()


@router.get("/health", summary="System health check")
async def health():
    config = get_settings()
    extractor = get_extractor()
    semantic = get_semantic_engine()
    intelligence = get_intelligence_engine()

    return {
        "status": "healthy",
        "version": config.versions.engine,
        "api_version": config.versions.api,
        "components": {
            "extractor": extractor.get_stats() if extractor else {"status": "unavailable"},
            "semantic_engine": "available" if semantic else "unavailable",
            "intelligence_engine": "available" if intelligence else "unavailable",
            "feedback": intelligence.get_feedback_stats() if intelligence else {},
        },
    }
