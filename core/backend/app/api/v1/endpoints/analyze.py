"""
NeuroSync — /analyze endpoint.
Thin controller delegating to IntelligenceEngine (doc 12 Rule 1 & Rule 3).
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import AnalyzeRequest
from app.api.deps import get_intelligence_engine

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", summary="Full resume-to-JD analysis")
async def analyze(request: Request, body: AnalyzeRequest):
    """
    Complete analysis pipeline: resume + JD → Decision.
    All orchestration is owned by IntelligenceEngine (doc 12 Rule 1).
    """
    rid = getattr(request.state, "request_id", "?")
    logger.info("[%s] POST /analyze request received", rid)

    intelligence = get_intelligence_engine()
    if not intelligence:
        raise HTTPException(status_code=503, detail="Intelligence Engine unavailable")

    try:
        response = await intelligence.analyze(
            resume_text=body.resume_text,
            jd_text=body.jd_text,
            include_simulations=body.include_simulations,
            include_evidence=body.include_evidence,
        )
        return response
    except Exception as e:
        logger.error("[%s] Analysis failed: %s", rid, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

