"""
NeuroSync — Insights Engine (Phase 3.2)

SWOT-style structured analysis. Each insight carries:
  type, claim, evidence, confidence, action_item

Input: structured pipeline outputs from IntelligenceEngine.
Output: InsightsResult with strengths, weaknesses, opportunities, threats.

Doc 12 Rule 1: IntelligenceEngine is the ONLY orchestrator. This engine is
a pure function (no state, no I/O) called from within analyze().
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.models.domain import ExtractionResult, Skill
from app.models.enums import GapPriority, SkillCategory
from app.services.skill_gap_analyzer import GapAnalysisResult

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    OPPORTUNITY = "opportunity"
    THREAT = "threat"


class Insight(BaseModel):
    """A single structured SWOT insight."""
    type: InsightType
    claim: str                         # The assertion (non-template, data-driven)
    evidence: str                      # Specific data point backing the claim
    confidence: float = Field(ge=0.0, le=1.0)
    action_item: Optional[str] = None  # What to do about this insight


class InsightsResult(BaseModel):
    """Full SWOT-style insights output."""
    strengths: list[Insight] = Field(default_factory=list)
    weaknesses: list[Insight] = Field(default_factory=list)
    opportunities: list[Insight] = Field(default_factory=list)
    threats: list[Insight] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "strengths": [i.model_dump() for i in self.strengths],
            "weaknesses": [i.model_dump() for i in self.weaknesses],
            "opportunities": [i.model_dump() for i in self.opportunities],
            "threats": [i.model_dump() for i in self.threats],
        }

    def top_strengths_as_list(self) -> list[str]:
        return [s.claim for s in self.strengths[:5]]

    def top_weaknesses_as_list(self) -> list[str]:
        return [w.claim for w in self.weaknesses[:5]]


# Skills that often appear on resumes but are generic/low-signal for most tech JDs
_LOW_SIGNAL_SKILLS = {
    "communication", "teamwork", "leadership", "problem solving",
    "time management", "attention to detail", "microsoft office", "excel",
}


class InsightsEngine:
    """
    Generates evidence-backed SWOT insights from pipeline outputs.

    Each insight references at least one measured data point.
    No template fill-in: output varies meaningfully with input.
    """

    def generate(
        self,
        *,
        overall_score: float,
        fit_level: str,
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
        gap_result: GapAnalysisResult,
        semantic_score: Optional[float] = None,
    ) -> InsightsResult:
        """Generate full SWOT insights for this analysis."""

        strengths = self._generate_strengths(
            resume_result=resume_result,
            jd_result=jd_result,
            gap_result=gap_result,
            semantic_score=semantic_score,
        )

        weaknesses = self._generate_weaknesses(
            gap_result=gap_result,
            semantic_score=semantic_score,
            overall_score=overall_score,
        )

        opportunities = self._generate_opportunities(
            gap_result=gap_result,
            resume_result=resume_result,
        )

        threats = self._generate_threats(
            gap_result=gap_result,
            semantic_score=semantic_score,
        )

        return InsightsResult(
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
        )

    # ─────────────────────────────────────────────────────────
    # STRENGTHS — what the candidate does well for THIS JD
    # ─────────────────────────────────────────────────────────

    def _generate_strengths(
        self,
        *,
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
        gap_result: GapAnalysisResult,
        semantic_score: Optional[float],
    ) -> list[Insight]:
        insights: list[Insight] = []

        # S1: High skill overlap
        if gap_result.overlap_score >= 0.65:
            matched = gap_result.matched_count
            total = gap_result.matched_count + gap_result.missing_count
            insights.append(Insight(
                type=InsightType.STRENGTH,
                claim=f"Strong requirement coverage ({matched}/{total} JD requirements met)",
                evidence=f"Overlap score {gap_result.overlap_score:.0%} with {matched} direct matches",
                confidence=0.90,
                action_item=None,
            ))

        # S2: High-confidence matched skills
        jd_names = {s.canonical.lower() for s in jd_result.skills}
        matched_skills = [
            s for s in resume_result.skills
            if s.canonical.lower() in jd_names and s.confidence >= 0.75
        ]
        if matched_skills:
            top = matched_skills[:3]
            insights.append(Insight(
                type=InsightType.STRENGTH,
                claim=f"High-confidence match on key skills: {', '.join(s.canonical for s in top)}",
                evidence=f"Average confidence {sum(s.confidence for s in top) / len(top):.0%} on verified matches",
                confidence=0.85,
                action_item="Highlight these skills prominently in your resume summary and cover letter.",
            ))

        # S3: Semantic alignment
        if semantic_score is not None and semantic_score >= 0.55:
            insights.append(Insight(
                type=InsightType.STRENGTH,
                claim=f"Resume language aligns well with JD vocabulary ({int(semantic_score * 100)}%)",
                evidence=f"Sentence-transformer cosine similarity: {semantic_score:.3f}",
                confidence=0.80,
                action_item="Language alignment is already good. Keep JD keywords in your application.",
            ))

        # S4: Implied skill resolution (graph reasoning)
        if gap_result.coverage.implied_matches:
            pairs = list(gap_result.coverage.implied_matches.items())[:3]
            claim_parts = [f"{req} (via {skill})" for req, skill in pairs]
            insights.append(Insight(
                type=InsightType.STRENGTH,
                claim=f"Skill graph resolved {len(gap_result.coverage.implied_matches)} requirement(s) through related skills",
                evidence="; ".join(claim_parts),
                confidence=0.75,
                action_item="These implied skills satisfy requirements — explicitly mention them in your application.",
            ))

        # S5: High proficiency on matched skills
        expert_skills = [
            s for s in matched_skills if s.proficiency_score >= 0.8
        ]
        if expert_skills:
            top_expert = expert_skills[:2]
            insights.append(Insight(
                type=InsightType.STRENGTH,
                claim=f"Expert-level proficiency detected on {', '.join(s.canonical for s in top_expert)}",
                evidence=f"Proficiency scores: {', '.join(f'{s.canonical}={s.proficiency_score:.0%}' for s in top_expert)}",
                confidence=0.80,
                action_item="Quantify your impact with these skills in job applications.",
            ))

        return insights[:6]

    # ─────────────────────────────────────────────────────────
    # WEAKNESSES — where the candidate falls short
    # ─────────────────────────────────────────────────────────

    def _generate_weaknesses(
        self,
        *,
        gap_result: GapAnalysisResult,
        semantic_score: Optional[float],
        overall_score: float,
    ) -> list[Insight]:
        insights: list[Insight] = []

        # W1: Critical skill gaps
        critical = [g for g in gap_result.gaps if g.priority.value == "critical"]
        if critical:
            top_critical = critical[:3]
            insights.append(Insight(
                type=InsightType.WEAKNESS,
                claim=f"Missing {len(critical)} critical skill(s): {', '.join(g.skill for g in top_critical)}",
                evidence=f"These are non-optional JD requirements with no partial coverage detected",
                confidence=0.92,
                action_item=f"Prioritise learning {top_critical[0].skill} first (highest gap impact).",
            ))

        # W2: Low semantic alignment
        if semantic_score is not None and semantic_score < 0.40:
            insights.append(Insight(
                type=InsightType.WEAKNESS,
                claim=f"Resume language is poorly aligned with JD vocabulary ({int(semantic_score * 100)}%)",
                evidence=f"Semantic similarity score: {semantic_score:.3f} — below the 0.40 threshold",
                confidence=0.82,
                action_item="Mirror more JD terminology in your resume. Tailor each application.",
            ))

        # W3: Thin resume skills vs JD breadth
        resume_count = len(gap_result.coverage.resume_skills_set) if hasattr(gap_result.coverage, 'resume_skills_set') else 0
        jd_count = gap_result.matched_count + gap_result.missing_count
        if gap_result.missing_count > gap_result.matched_count and jd_count > 0:
            insights.append(Insight(
                type=InsightType.WEAKNESS,
                claim=f"More gaps than matches ({gap_result.missing_count} unmet vs {gap_result.matched_count} met)",
                evidence=f"Requirement coverage: {gap_result.overlap_score:.0%}",
                confidence=0.88,
                action_item="Consider whether this role is appropriately levelled for your current profile.",
            ))

        # W4: Overall score below competitive threshold
        if overall_score < 55:
            insights.append(Insight(
                type=InsightType.WEAKNESS,
                claim=f"Overall fit score ({overall_score:.1f}) is below the competitive shortlist band (≥65)",
                evidence=f"Score breakdown: skill={gap_result.overlap_score:.0%}, gap penalty applied",
                confidence=0.85,
                action_item="Address top 2-3 gaps from the improvement path before applying.",
            ))

        return insights[:5]

    # ─────────────────────────────────────────────────────────
    # OPPORTUNITIES — skills close to qualifying
    # ─────────────────────────────────────────────────────────

    def _generate_opportunities(
        self,
        *,
        gap_result: GapAnalysisResult,
        resume_result: ExtractionResult,
    ) -> list[Insight]:
        insights: list[Insight] = []

        # O1: Low-time gaps (quick wins)
        quick_wins = [
            g for g in gap_result.gaps
            if g.learning_time_estimate and "week" in g.learning_time_estimate.lower()
            and not g.optional
        ]
        if quick_wins:
            top = quick_wins[:3]
            insights.append(Insight(
                type=InsightType.OPPORTUNITY,
                claim=f"{len(quick_wins)} short-cycle gap(s) closeable within weeks: {', '.join(g.skill for g in top)}",
                evidence=f"Estimated learning times: {', '.join(f'{g.skill}~{g.learning_time_estimate}' for g in top)}",
                confidence=0.78,
                action_item="These quick wins can meaningfully improve your score before applying.",
            ))

        # O2: Skills that have related present (partial credit possible)
        partial_credit = [
            g for g in gap_result.gaps if g.related_present
        ]
        if partial_credit:
            top_partial = partial_credit[:2]
            insights.append(Insight(
                type=InsightType.OPPORTUNITY,
                claim=f"{len(partial_credit)} missing skill(s) have related skills already on your resume",
                evidence=f"Partial credit available for: {', '.join(g.skill for g in top_partial)}",
                confidence=0.72,
                action_item="Bridge these gaps by explicitly mentioning transferable experience in your application.",
            ))

        # O3: Optional requirements already met
        optional_met = [
            g for g in gap_result.gaps if g.optional
        ]
        satisfied_optional = [
            g for g in optional_met if g.priority.value in ("low",)
        ]
        if optional_met and not satisfied_optional:
            insights.append(Insight(
                type=InsightType.OPPORTUNITY,
                claim=f"{len(optional_met)} optional JD requirement(s) could differentiate your application",
                evidence=f"Optional skills: {', '.join(g.skill for g in optional_met[:3])}",
                confidence=0.65,
                action_item="Adding any of these optional skills would put you ahead of competing candidates.",
            ))

        return insights[:4]

    # ─────────────────────────────────────────────────────────
    # THREATS — risk factors (skills becoming less relevant, etc.)
    # ─────────────────────────────────────────────────────────

    def _generate_threats(
        self,
        *,
        gap_result: GapAnalysisResult,
        semantic_score: Optional[float],
    ) -> list[Insight]:
        insights: list[Insight] = []

        # T1: High gap count is a competitive disadvantage
        if gap_result.missing_count >= 5:
            insights.append(Insight(
                type=InsightType.THREAT,
                claim=f"{gap_result.missing_count} unmet requirements is high — competing candidates likely have fewer gaps",
                evidence=f"Industry shortlisting typically drops candidates with >30% unmet requirements",
                confidence=0.70,
                action_item="Prioritise closing the top-ranked gaps from the improvement path.",
            ))

        # T2: Degraded semantic model means score may be conservative
        if semantic_score is None:
            insights.append(Insight(
                type=InsightType.THREAT,
                claim="Semantic similarity scoring unavailable — score is skill-match only, may be pessimistic",
                evidence="Semantic engine degraded; holistic language alignment not measured",
                confidence=0.65,
                action_item="If your resume's language strongly mirrors the JD, actual fit may be higher than scored.",
            ))

        return insights[:3]
