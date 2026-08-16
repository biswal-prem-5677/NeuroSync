"""
NeuroSync — Tests for Phase 3 Intelligence Expansion Services.
Tests ReasoningEngine, InsightsEngine, FeedbackProcessor, and /feedback/process.
"""
from __future__ import annotations

import pytest
from app.config import get_settings
from app.models.domain import ExtractionResult, Skill, ScoringBreakdown
from app.models.enums import FitLevel, GapPriority, MatchMethod, SkillCategory
from app.services.reasoning_engine import ReasoningEngine
from app.services.insights_engine import InsightsEngine, InsightType
from app.services.feedback_processor import FeedbackProcessor
from app.services.skill_gap_analyzer import GapAnalysisResult, SkillGapItem, RequirementSet, CoverageResult
from app.state.memory_state import MemoryState
from app.state.base import FeedbackRecord


def _make_dummy_extraction():
    skill1 = Skill(name="Python", canonical="Python", category=SkillCategory.PROGRAMMING, confidence=0.9, proficiency_score=0.85, matched_by=MatchMethod.TAXONOMY)
    skill2 = Skill(name="Docker", canonical="Docker", category=SkillCategory.DEVOPS, confidence=0.8, proficiency_score=0.75, matched_by=MatchMethod.TAXONOMY)
    return ExtractionResult(skills=[skill1, skill2])



def _make_dummy_gap_result():
    g1 = SkillGapItem(skill="Kubernetes", category=SkillCategory.DEVOPS, priority=GapPriority.CRITICAL, reasoning="Required for deployment", learning_time_estimate="2-3 weeks")
    req_set = RequirementSet()
    coverage = CoverageResult(satisfied_count=2, unmet_count=1)
    return GapAnalysisResult(gaps=[g1], matched_count=2, missing_count=1, overlap_score=0.67, requirements=req_set, coverage=coverage)



def test_reasoning_engine():
    engine = ReasoningEngine()
    scoring = ScoringBreakdown(semantic_score=0.75, skill_overlap_score=67.0, gap_penalty=10.0, final_score=72.0)
    resume_ext = _make_dummy_extraction()
    jd_ext = _make_dummy_extraction()
    gap_res = _make_dummy_gap_result()

    output = engine.synthesize(
        overall_score=72.0,
        fit_level="strong_fit",
        recommendation="apply",
        confidence=0.85,
        shortlist_probability=0.78,
        scoring=scoring,
        resume_result=resume_ext,
        jd_result=jd_ext,
        gap_result=gap_res,
        strengths=["Python", "Docker"],
        weaknesses=["Kubernetes"],
        semantic_score=0.75,
    )

    assert "72.0/100" in output.summary
    assert "Python" in output.strengths_rationale
    assert "Kubernetes" in output.gaps_rationale
    assert output.to_single_paragraph() is not None


def test_insights_engine_swot():
    engine = InsightsEngine()
    resume_ext = _make_dummy_extraction()
    jd_ext = _make_dummy_extraction()
    gap_res = _make_dummy_gap_result()

    insights = engine.generate(
        overall_score=72.0,
        fit_level="strong_fit",
        resume_result=resume_ext,
        jd_result=jd_ext,
        gap_result=gap_res,
        semantic_score=0.75,
    )

    assert len(insights.strengths) > 0
    assert len(insights.weaknesses) > 0
    assert len(insights.opportunities) > 0
    
    # Verify SWOT data structure integrity
    s0 = insights.strengths[0]
    assert s0.type == InsightType.STRENGTH
    assert s0.claim is not None
    assert s0.evidence is not None


@pytest.mark.anyio
async def test_feedback_processor():
    config = get_settings()
    taxonomy = None  # Mock/None
    processor = FeedbackProcessor(config, taxonomy)
    state = MemoryState()

    # Empty state test
    result_empty = await processor.process(state)
    assert result_empty.feedback_count == 0

    # Add dummy feedback records
    state.store_feedback(FeedbackRecord(
        feedback_id="f1",
        analysis_id="a1",
        outcome="interview",
        score=75.0,
        shortlist_probability=0.70,
        confidence=0.85,
    ))
    state.store_feedback(FeedbackRecord(
        feedback_id="f2",
        analysis_id="a2",
        outcome="hired",
        score=82.0,
        shortlist_probability=0.80,
        confidence=0.90,
    ))

    result = await processor.process(state)
    assert result.feedback_count == 2
    assert result.drift.positive_outcomes == 2
    assert result.drift.actual_positive_rate == 1.0


@pytest.mark.anyio
async def test_process_feedback_endpoint(client):
    res = client.post("/api/v1/feedback/process")
    assert res.status_code == 200
    data = res.json()
    assert "feedback_count" in data
    assert "drift" in data
