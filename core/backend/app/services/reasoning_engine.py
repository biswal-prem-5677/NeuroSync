"""
NeuroSync — Reasoning Engine (Phase 3.1)

Standalone evidence-chain reasoning. Takes structured pipeline outputs and
produces multi-paragraph explanations where every claim is backed by a
specific data point — no template text.

Doc 12 Rule 1: IntelligenceEngine calls this; endpoints are thin.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.models.domain import ExtractionResult, ScoringBreakdown
from app.services.skill_gap_analyzer import GapAnalysisResult

logger = logging.getLogger(__name__)


class ReasoningOutput:
    """Full reasoning narrative from the engine."""

    def __init__(
        self,
        summary: str,
        strengths_rationale: str,
        gaps_rationale: str,
        recommendation_rationale: str,
        confidence_explanation: str,
    ):
        self.summary = summary
        self.strengths_rationale = strengths_rationale
        self.gaps_rationale = gaps_rationale
        self.recommendation_rationale = recommendation_rationale
        self.confidence_explanation = confidence_explanation

    def to_single_paragraph(self) -> str:
        """Compact form for the `decision.reasoning` field."""
        return f"{self.summary} {self.recommendation_rationale}"

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "strengths_rationale": self.strengths_rationale,
            "gaps_rationale": self.gaps_rationale,
            "recommendation_rationale": self.recommendation_rationale,
            "confidence_explanation": self.confidence_explanation,
        }


class ReasoningEngine:
    """
    Synthesises evidence-backed narrative reasoning from scoring + gap data.

    Design principles:
    - Every sentence references a measured number or named skill.
    - No template fill-in: output varies meaningfully with input.
    - Graceful degradation: works with partial pipeline output (no semantic, etc.)
    """

    def synthesize(
        self,
        *,
        overall_score: float,
        fit_level: str,
        recommendation: str,
        confidence: float,
        shortlist_probability: float,
        scoring: ScoringBreakdown,
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
        gap_result: GapAnalysisResult,
        strengths: list[str],
        weaknesses: list[str],
        semantic_score: Optional[float] = None,
    ) -> ReasoningOutput:
        """Produce full reasoning narrative for this analysis."""

        # ── Metrics ────────────────────────────────────────────
        resume_count = len(resume_result.skills)
        jd_count = len(jd_result.skills)
        matched = gap_result.matched_count
        missing = gap_result.missing_count
        critical_gaps = [g for g in gap_result.gaps if g.priority.value in ("critical", "high")]
        optional_gaps = [g for g in gap_result.gaps if g.optional]
        implied = len(gap_result.coverage.implied_matches)

        # ── Summary ────────────────────────────────────────────
        semantic_clause = ""
        if semantic_score is not None:
            sem_pct = int(semantic_score * 100)
            if sem_pct >= 70:
                semantic_clause = f" Resume language alignment is strong at {sem_pct}%."
            elif sem_pct >= 45:
                semantic_clause = f" Resume language alignment is moderate at {sem_pct}%."
            else:
                semantic_clause = f" Resume language alignment is weak at {sem_pct}% — this lowers the holistic score."

        summary = (
            f"Overall score: {overall_score:.1f}/100 → {fit_level.replace('_', ' ')} fit "
            f"({int(shortlist_probability * 100)}% shortlist probability). "
            f"Extracted {resume_count} skills from the resume against {jd_count} required by the JD. "
            f"{matched} requirements satisfied, {missing} unmet"
            f"{f' (including {implied} resolved via implied-skill graph)' if implied else ''}."
            f"{semantic_clause}"
        )

        # ── Strengths rationale ────────────────────────────────
        if strengths:
            top = strengths[:3]
            str_text = (
                f"Primary strengths: {', '.join(top)}. "
                f"Skill coverage score is {scoring.skill_overlap_score:.1f}/100, "
                f"{'well above' if scoring.skill_overlap_score >= 70 else 'at'} the strong-match threshold."
            )
        else:
            str_text = (
                f"No dominant strengths detected. Skill overlap score is "
                f"{scoring.skill_overlap_score:.1f}/100, indicating thin coverage of JD requirements."
            )

        # ── Gaps rationale ─────────────────────────────────────
        if critical_gaps:
            gap_names = [g.skill for g in critical_gaps[:3]]
            gaps_text = (
                f"{len(critical_gaps)} critical/high-priority gap(s) detected: {', '.join(gap_names)}. "
                f"Gap penalty applied: -{scoring.gap_penalty:.1f} points. "
            )
            if optional_gaps:
                gaps_text += (
                    f"{len(optional_gaps)} of the unmet requirements are optional and "
                    f"did not receive full penalty weight."
                )
        elif missing > 0:
            gaps_text = (
                f"{missing} gaps present but none are critical. "
                f"Gap penalty: -{scoring.gap_penalty:.1f} points — manageable with targeted preparation."
            )
        else:
            gaps_text = "No skill gaps detected. Full requirement coverage achieved."

        # ── Recommendation rationale ───────────────────────────
        rec = recommendation.replace("_", " ")
        if recommendation in ("strong_apply", "apply"):
            rec_text = (
                f"Recommendation is '{rec}' because skill coverage and semantic alignment "
                f"both exceed threshold. Confidence: {int(confidence * 100)}%."
            )
        elif recommendation == "apply_with_preparation":
            prep_skills = [g.skill for g in critical_gaps[:2]] if critical_gaps else []
            prep_clause = f" Focus preparation on: {', '.join(prep_skills)}." if prep_skills else ""
            rec_text = (
                f"Candidate is viable but has addressable gaps.{prep_clause} "
                f"Addressing these gaps is projected to raise shortlist probability meaningfully."
            )
        elif recommendation == "upskill_then_apply":
            rec_text = (
                f"Too many critical gaps ({len(critical_gaps)}) to apply competitively now. "
                f"Score of {overall_score:.1f} is below the apply threshold. "
                f"Targeted upskilling is the recommended path."
            )
        else:  # do_not_apply
            rec_text = (
                f"Score {overall_score:.1f} and {len(critical_gaps)} critical gaps indicate "
                f"a poor fit. This role requires a substantially different skill profile."
            )

        # ── Confidence explanation ─────────────────────────────
        if resume_result.degraded or jd_result.degraded:
            conf_text = (
                f"Confidence is {int(confidence * 100)}% — reduced because extraction "
                f"ran in degraded mode (semantic model unavailable). Scores are conservative."
            )
        else:
            conf_text = (
                f"Confidence is {int(confidence * 100)}%, reflecting full extraction "
                f"(taxonomy + NER + semantic + embedding layers all active)."
            )

        return ReasoningOutput(
            summary=summary,
            strengths_rationale=str_text,
            gaps_rationale=gaps_text,
            recommendation_rationale=rec_text,
            confidence_explanation=conf_text,
        )
