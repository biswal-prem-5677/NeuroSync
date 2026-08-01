"""
NeuroSync — /analyze endpoint.
The main pipeline: resume + JD → Decision.
"""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import AnalyzeRequest
from app.api.deps import (
    get_extractor, get_gap_analyzer,
    get_semantic_engine, get_intelligence_engine,
    get_state_backend,
)
from app.state.base import AnalysisRecord

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", summary="Full resume-to-JD analysis")
async def analyze(request: Request, body: AnalyzeRequest):
    """
    Complete analysis pipeline:
    1. Extract skills from resume + JD (4-layer hybrid)
    2. Compute semantic similarity (section-aware)
    3. Analyze skill gaps (cluster-based reasoning)
    4. Produce decision (recommendation + simulations + improvement path)
    """
    analysis_id = str(uuid.uuid4())[:12]
    rid = getattr(request.state, "request_id", "?")
    start = time.perf_counter()

    logger.info("[%s] Analysis started (id=%s)", rid, analysis_id)

    try:
        extractor = get_extractor()
        gap_analyzer = get_gap_analyzer()
        semantic_engine = get_semantic_engine()
        intelligence = get_intelligence_engine()

        # Step 1: Extract skills
        resume_result = await extractor.extract_async(body.resume_text)
        jd_result = await extractor.extract_async(body.jd_text)

        # Step 1b: Cross-document semantic skill matching
        cross_doc_skills = extractor.extract_cross_document(
            body.resume_text, body.jd_text, resume_result, jd_result
        )
        if cross_doc_skills:
            from app.models.domain import ExtractionResult
            resume_result = ExtractionResult(
                skills=resume_result.skills + cross_doc_skills,
                extraction_methods_used=resume_result.extraction_methods_used + ["semantic"],
                degraded=resume_result.degraded,
                failed_layers=resume_result.failed_layers,
                processing_time_ms=resume_result.processing_time_ms,
            )

        # Step 2: Semantic similarity
        semantic_result = None
        semantic_score = None
        if semantic_engine:
            semantic_result = await semantic_engine.compute_similarity_async(
                body.resume_text, body.jd_text, resume_result, jd_result,
            )
            semantic_score = semantic_result.overall_score

        # Step 3: Gap analysis
        gap_result = gap_analyzer.analyze(resume_result, jd_result, body.jd_text)

        # Step 4: Decision
        decision = intelligence.decide(
            semantic_score=semantic_score,
            resume_result=resume_result,
            jd_result=jd_result,
            gap_result=gap_result,
        )

        elapsed = (time.perf_counter() - start) * 1000

        # Build response
        response = {
            "analysis_id": analysis_id,
            "decision": {
                "recommendation": decision.recommendation.value,
                "confidence": decision.confidence,
                "shortlist_probability": decision.shortlist_probability,
                "fit_level": decision.fit_level.value,
                "overall_score": decision.overall_score,
                "reasoning": decision.reasoning,
            },
            "scoring": {
                "semantic_score": decision.scoring.semantic_score,
                "skill_overlap_score": decision.scoring.skill_overlap_score,
                "gap_penalty": decision.scoring.gap_penalty,
                "final_score": decision.scoring.final_score,
                "explanation": decision.scoring.explanation,
            },
            "skills": {
                "resume_count": len(resume_result.skills),
                "jd_count": len(jd_result.skills),
                "matched": gap_result.matched_count,
                "missing": gap_result.missing_count,
                "overlap_score": gap_result.overlap_score,
                # Requirements the resume satisfies through a skill that
                # subsumes them, e.g. {"SQL": "PostgreSQL"}.
                "implied_matches": gap_result.coverage.implied_matches,
                "resume_skills": [
                    {
                        "name": s.canonical,
                        "category": s.category.value,
                        "confidence": s.confidence,
                        "proficiency": s.proficiency_score,
                        "evidence_strength": s.evidence_strength,
                        "occurrences": s.occurrence_count,
                        "matched_by": s.matched_by.value,
                        "sections": s.found_in_sections,
                    }
                    for s in resume_result.skills
                ],
            },
            "requirements": {
                "total": len(gap_result.requirements.groups),
                "alternative": gap_result.requirements.alternative_count,
                "optional": gap_result.requirements.optional_count,
                "satisfied": gap_result.coverage.satisfied_count,
                "unmet": gap_result.coverage.unmet_count,
            },
            "gaps": [
                {
                    "skill": g.skill,
                    "category": g.category.value,
                    "priority": g.priority.value,
                    "reasoning": g.reasoning,
                    "learning_time": g.learning_time_estimate,
                    "related_present": g.related_present,
                    "confidence": g.confidence,
                    # Other skills that would satisfy the same requirement —
                    # non-empty only for "A or B" JD lines.
                    "alternatives": g.alternatives,
                    "optional": g.optional,
                }
                for g in gap_result.gaps
            ],
            "improvement_path": [
                {
                    "rank": a.roi_rank,
                    "skill": a.skill,
                    "impact": a.impact_score_delta,
                    "learning_time": a.learning_time,
                    "reasoning": a.reasoning,
                }
                for a in decision.improvement_path
            ],
            "strengths": decision.strengths,
            "weaknesses": decision.weaknesses,
        }

        # Optional: simulations
        if body.include_simulations and decision.top_simulations:
            response["simulations"] = [
                {
                    "skill_added": s.skill_added,
                    "current_score": s.current_score,
                    "projected_score": s.projected_score,
                    "delta": s.delta,
                    "new_fit_level": s.new_fit_level.value,
                    "new_shortlist_probability": s.new_shortlist_probability,
                }
                for s in decision.top_simulations
            ]

        # Optional: evidence
        if body.include_evidence and decision.evidence:
            response["evidence"] = [
                {
                    "source": e.source,
                    "claim": e.claim,
                    "weight": e.weight,
                    "confidence": e.confidence,
                }
                for e in decision.evidence
            ]

        # Semantic details
        if semantic_result:
            response["semantic"] = {
                "overall": semantic_result.overall_score,
                "chunk_max": semantic_result.chunk_level_max,
                "chunk_mean": semantic_result.chunk_level_mean,
                "skill_alignment": semantic_result.skill_alignment_score,
                "confidence": semantic_result.confidence,
                "degraded": semantic_result.degraded,
                "sections": [
                    {"section": s.section, "score": s.score, "weight": s.weight}
                    for s in semantic_result.section_scores[:5]
                ],
            }

        response["meta"] = {
            "processing_time_ms": round(elapsed, 1),
            "extraction_degraded": resume_result.degraded or jd_result.degraded,
            "semantic_available": semantic_engine is not None,
        }

        # Persist through StateBackend (doc 12 §4 Rule 5) so /feedback can find
        # the real decision later. A storage failure must not lose the user's
        # analysis: the result is already computed and is still returned.
        try:
            get_state_backend().store_analysis(AnalysisRecord(
                analysis_id=analysis_id,
                resume_text=body.resume_text,
                jd_text=body.jd_text,
                recommendation=decision.recommendation.value,
                fit_level=decision.fit_level.value,
                overall_score=decision.overall_score,
                shortlist_probability=decision.shortlist_probability,
                confidence=decision.confidence,
                reasoning=decision.reasoning,
                semantic_score=decision.scoring.semantic_score,
                skill_overlap_score=decision.scoring.skill_overlap_score or 0.0,
                gap_penalty=decision.scoring.gap_penalty or 0.0,
                scoring_explanation=decision.scoring.explanation,
                payload=response,
                processing_time_ms=elapsed,
            ))
        except Exception as e:
            logger.error("[%s] Analysis %s not persisted: %s", rid, analysis_id, e,
                         exc_info=True)

        logger.info("[%s] Analysis complete in %.1fms (score=%.1f, rec=%s)",
                    rid, elapsed, decision.overall_score, decision.recommendation.value)

        return response

    except Exception as e:
        logger.error("[%s] Analysis failed: %s", rid, e, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
