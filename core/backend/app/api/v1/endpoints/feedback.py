"""NeuroSync — /feedback endpoint.
Records analysis outcomes for the learning loop.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import FeedbackRequest
from app.api.deps import get_intelligence_engine, get_state_backend, get_feedback_processor

router = APIRouter()


@router.post("/feedback", summary="Record analysis outcome feedback")
async def record_feedback(body: FeedbackRequest):
    """
    Record what happened after the user followed our recommendation.
    Feeds the learning loop for future weight calibration.

    Requires a valid `analysis_id` from a previous /analyze call. If that
    analysis is not in the store, the outcome is still recorded against a stub
    decision (doc 08 §3.2 `decision_found: false`) — an unrecognised id is a
    reason to record less, not to record nothing.
    """
    intelligence = get_intelligence_engine()
    if not intelligence:
        raise HTTPException(status_code=503, detail="Intelligence engine unavailable")

    from app.services.intelligence_engine import Decision, Recommendation
    from app.models.enums import FitLevel
    from app.models.domain import ScoringBreakdown

    record = get_state_backend().get_analysis(body.analysis_id)

    if record is None:
        # Unknown analysis — record the outcome for aggregate stats only.
        decision = Decision(
            recommendation=Recommendation.APPLY,
            confidence=0.0,
            shortlist_probability=0.0,
            fit_level=FitLevel.POTENTIAL_FIT,
            overall_score=0.0,
            reasoning="feedback-only entry (analysis not found in state)",
            scoring=ScoringBreakdown(),
        )
        analysis_id = None
        found = False
    else:
        # Rebuild the decision that was actually made. The persisted columns
        # carry exactly the fields the learning loop calibrates against.
        decision = Decision(
            recommendation=Recommendation(record.recommendation),
            confidence=record.confidence,
            shortlist_probability=record.shortlist_probability,
            fit_level=FitLevel(record.fit_level),
            overall_score=record.overall_score,
            reasoning=record.reasoning,
            scoring=ScoringBreakdown(
                semantic_score=record.semantic_score,
                skill_overlap_score=record.skill_overlap_score,
                gap_penalty=record.gap_penalty,
                final_score=record.overall_score,
                confidence=record.confidence,
                explanation=record.scoring_explanation,
            ),
        )
        analysis_id = record.analysis_id
        found = True

    intelligence.record_feedback(
        decision=decision,
        outcome=body.outcome,
        user_notes=body.notes or "",
        analysis_id=analysis_id,
    )

    return {
        "status": "recorded",
        "analysis_id": body.analysis_id,
        "outcome": body.outcome,
        "decision_found": found,
        "feedback_stats": intelligence.get_feedback_stats().as_response(),
    }


@router.post("/feedback/process", summary="Run feedback learning loop (Phase 3.3)")
async def process_feedback():
    """
    Run the FeedbackProcessor learning loop over all accumulated feedback.

    Returns:
    - Drift report: predicted vs actual shortlist probability
    - Proposed weight adjustments
    - New skills discovered
    - Calibration recommendation
    """
    processor = get_feedback_processor()
    state = get_state_backend()
    result = await processor.process(state)
    return result.to_dict()
