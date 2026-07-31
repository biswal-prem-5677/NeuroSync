"""NeuroSync — /feedback endpoint.
Records analysis outcomes for the learning loop.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import FeedbackRequest
from app.api.deps import get_intelligence_engine, get_cached_analysis

router = APIRouter()


@router.post("/feedback", summary="Record analysis outcome feedback")
async def record_feedback(body: FeedbackRequest):
    """
    Record what happened after the user followed our recommendation.
    Feeds the learning loop for future weight calibration.

    Requires a valid `analysis_id` from a previous /analyze call.
    If the analysis is no longer in cache, records a lightweight entry
    with a stub decision (still useful for aggregate statistics).
    """
    intelligence = get_intelligence_engine()
    if not intelligence:
        raise HTTPException(status_code=503, detail="Intelligence engine unavailable")

    # Try to find the real decision from the analysis cache
    decision = get_cached_analysis(body.analysis_id)

    if decision is None:
        # Analysis expired from cache — create a minimal stub
        # This still records the outcome for aggregate stats
        from app.services.intelligence_engine import Decision, Recommendation
        from app.models.enums import FitLevel
        from app.models.domain import ScoringBreakdown

        decision = Decision(
            recommendation=Recommendation.APPLY,
            confidence=0.0,
            shortlist_probability=0.0,
            fit_level=FitLevel.POTENTIAL_FIT,
            overall_score=0.0,
            reasoning="feedback-only entry (original analysis expired from cache)",
            scoring=ScoringBreakdown(),
        )
        cache_hit = False
    else:
        cache_hit = True

    intelligence.record_feedback(
        decision=decision,
        outcome=body.outcome,
        user_notes=body.notes or "",
    )

    stats = intelligence.get_feedback_stats()

    return {
        "status": "recorded",
        "analysis_id": body.analysis_id,
        "outcome": body.outcome,
        "decision_found": cache_hit,
        "feedback_stats": stats,
    }
