"""
NeuroSync — Intelligence Engine.
The central brain that converts analysis into decisions.
Combines: semantic similarity + skill overlap + gap analysis → actionable outcome.
"""
from __future__ import annotations

import logging
import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.config import Settings
from app.models.domain import (
    CoverageResult, ExtractionResult, Skill, SkillGapItem, ScoringBreakdown,
    EvidenceItem, ReasoningTrace,
)
from app.models.enums import FitLevel, GapPriority, SkillCategory
from app.services.requirement_resolver import CoverageResolver
from app.services.skill_gap_analyzer import GapAnalysisResult
from app.state.base import FeedbackRecord, FeedbackStats, StateBackend
from app.utils.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)


# =========================================================================
# OUTPUT MODELS
# =========================================================================

class Recommendation(str, Enum):
    STRONG_APPLY = "strong_apply"          # Go for it — strong match
    APPLY = "apply"                        # Good match, apply
    APPLY_WITH_PREPARATION = "apply_with_preparation"  # Viable but fix gaps first
    UPSKILL_THEN_APPLY = "upskill_then_apply"          # Too many gaps now
    DO_NOT_APPLY = "do_not_apply"          # Poor fit


class ImprovementAction(BaseModel):
    """A single actionable improvement step."""
    skill: str
    priority: GapPriority
    impact_score_delta: float              # How much score improves if learned
    learning_time: str
    reasoning: str                         # Why THIS skill has highest ROI
    roi_rank: int                          # 1 = highest ROI action


class ScoreSimulation(BaseModel):
    """What-if simulation: if user learns skill X, what happens?"""
    skill_added: str
    current_score: float
    projected_score: float
    delta: float
    new_fit_level: FitLevel
    new_shortlist_probability: float


class Decision(BaseModel):
    """The final intelligence output — a career decision with evidence."""
    recommendation: Recommendation
    confidence: float = Field(ge=0.0, le=1.0)
    shortlist_probability: float = Field(ge=0.0, le=1.0)
    fit_level: FitLevel
    overall_score: float = Field(ge=0.0, le=100.0)

    # Multi-factor reasoning
    reasoning: str
    evidence: list[EvidenceItem] = Field(default_factory=list)

    # Scoring breakdown
    scoring: ScoringBreakdown

    # Actionable guidance
    improvement_path: list[ImprovementAction] = Field(default_factory=list)
    top_simulations: list[ScoreSimulation] = Field(default_factory=list)

    # Stats
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    processing_time_ms: float = 0.0


# =========================================================================
# INTELLIGENCE ENGINE
# =========================================================================

class IntelligenceEngine:
    """
    Central decision engine. Takes all analysis components and produces
    a single Decision with recommendation, confidence, and improvement path.

    Pipeline:
    1. Compute composite score (semantic + skill overlap - gap penalty)
    2. Determine fit level
    3. Estimate shortlist probability
    4. Simulate gap fixes (what-if analysis)
    5. Rank improvements by ROI
    6. Generate multi-factor reasoning
    7. Output Decision
    """

    def __init__(
        self,
        config: Settings,
        taxonomy: SkillTaxonomy,
        state: StateBackend,
        resolver: Optional[CoverageResolver] = None,
    ):
        self._config = config
        self._taxonomy = taxonomy
        # Used only to re-resolve coverage during what-if simulation, so a
        # projected score is computed the same way the real one was.
        self._resolver = resolver or CoverageResolver(config, taxonomy)
        # Doc 12 §4 Rule 5. Feedback used to accumulate in a list on this
        # object, which meant every recorded outcome died with the process
        # (doc 15 R3). The engine now owns no storage at all.
        self._state = state

    def decide(
        self,
        semantic_score: Optional[float],
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
        gap_result: GapAnalysisResult,
    ) -> Decision:
        """
        Produce the final decision from all analysis components.

        Args:
            semantic_score: cosine similarity between resume and JD (0-1), or None
            resume_result: extracted resume skills with intensity
            jd_result: extracted JD skills
            gap_result: gap analysis with prioritized gaps
        """
        start = time.perf_counter()

        weights = self._config.weights
        evidence: list[EvidenceItem] = []

        # ── Step 1: Compute component scores ─────────────────
        # Semantic — reported raw, scored calibrated (see config.semantic_floor)
        sem_score = semantic_score if semantic_score is not None else 0.0
        sem_available = semantic_score is not None
        sem_calibrated = self._calibrate_semantic(sem_score)

        if sem_available:
            evidence.append(EvidenceItem(
                source="semantic_engine",
                claim=(
                    f"Document-level semantic similarity is {sem_score:.2f} "
                    f"({sem_calibrated:.0%} of the model's usable range)"
                ),
                weight=weights.semantic,
                confidence=0.9,
            ))

        # Skill overlap — PROFICIENCY WEIGHTED, over requirement groups
        overlap_raw = gap_result.overlap_score
        overlap = self._compute_weighted_overlap(
            gap_result.coverage, resume_result, jd_result
        )
        evidence.append(EvidenceItem(
            source="skill_extractor",
            claim=(
                f"{gap_result.matched_count}/{gap_result.total_jd_skills} "
                f"required skills matched ({overlap_raw:.0%} raw, {overlap:.0%} proficiency-weighted)"
            ),
            weight=weights.skill,
            confidence=0.95,
        ))

        # Gap penalty
        gap_penalty = self._compute_gap_penalty(gap_result)
        evidence.append(EvidenceItem(
            source="gap_analyzer",
            claim=(
                f"{gap_result.missing_count} skills missing "
                f"({gap_result.critical_count} critical, {gap_result.high_count} high). "
                f"Gap penalty: -{gap_penalty:.2f}"
            ),
            weight=weights.gap,
            confidence=0.9,
        ))

        # ── Step 2: Composite score ──────────────────────────
        scoring = self._compute_score(
            sem_calibrated, sem_available, overlap, gap_penalty, weights, evidence,
            raw_semantic=sem_score,
        )

        # ── Step 3: Fit level ────────────────────────────────
        fit_level = self._score_to_fit(scoring.final_score)

        # ── Step 4: Shortlist probability ────────────────────
        shortlist_prob = self._estimate_shortlist_probability(
            scoring.final_score, gap_result, sem_calibrated, sem_available
        )

        # ── Step 5: Simulate improvements ────────────────────
        simulations = self._simulate_gap_fixes(
            scoring, gap_result, resume_result, jd_result, weights
        )

        # ── Step 6: Rank improvements by ROI ─────────────────
        improvement_path = self._build_improvement_path(
            gap_result, simulations
        )

        # ── Step 7: Strengths & weaknesses ───────────────────
        strengths, weaknesses = self._analyze_strengths_weaknesses(
            resume_result, jd_result, gap_result, sem_score, sem_available
        )

        # ── Step 8: Decision ─────────────────────────────────
        recommendation = self._make_recommendation(
            scoring.final_score, gap_result, shortlist_prob
        )

        # ── Step 9: Multi-factor reasoning ───────────────────
        reasoning = self._generate_decision_reasoning(
            recommendation, scoring, gap_result,
            shortlist_prob, strengths, weaknesses,
            improvement_path, sem_score, sem_available,
        )

        # ── Step 10: Confidence ──────────────────────────────
        confidence = self._compute_decision_confidence(
            sem_available, resume_result, jd_result, gap_result
        )

        elapsed = (time.perf_counter() - start) * 1000

        return Decision(
            recommendation=recommendation,
            confidence=round(confidence, 3),
            shortlist_probability=round(shortlist_prob, 3),
            fit_level=fit_level,
            overall_score=round(scoring.final_score, 2),
            reasoning=reasoning,
            evidence=evidence,
            scoring=scoring,
            improvement_path=improvement_path[:5],  # Top 5 actions
            top_simulations=simulations[:3],         # Top 3 what-ifs
            strengths=strengths,
            weaknesses=weaknesses,
            processing_time_ms=round(elapsed, 2),
        )

    # =========================================================================
    # SCORING
    # =========================================================================

    def _calibrate_semantic(self, raw: float) -> float:
        """
        Map raw semantic similarity onto its usable band (see config.semantic_floor).

        The semantic composite cannot reach 1.0 in practice — its three sub-signals
        are each compressed cosines — so consuming it as a raw percentage would put
        a hard ceiling on every score the system can produce.
        """
        floor = self._config.semantic_floor
        ceiling = self._config.semantic_ceiling
        if ceiling <= floor:
            return max(0.0, min(1.0, raw))
        return max(0.0, min(1.0, (raw - floor) / (ceiling - floor)))

    def _compute_score(
        self, sem_score, sem_available, overlap, gap_penalty, weights, evidence,
        raw_semantic: Optional[float] = None,
    ) -> ScoringBreakdown:
        """
        Compute weighted composite score.

        Formula:
          base = weighted_average(semantic, skill_overlap)   → 0-100 (positive signals)
          penalty = gap_penalty * gap_weight * 100            → 0-25  (deduction)
          final = base - penalty                              → clamped [0, 100]

        `sem_score` is the CALIBRATED semantic value; `raw_semantic` is the
        uncalibrated cosine, reported in the breakdown for transparency.

        The old formula treated gap_penalty as a negative additive in the weighted
        average, which caused catastrophic score collapse (e.g. 13/100 for a strong
        resume). This fix separates positive signals from penalty deductions.
        """
        # 1. Build positive component scores (0-100 scale)
        positive_components = {}
        positive_weights = {}

        if sem_available:
            positive_components["semantic"] = sem_score * 100
            positive_weights["semantic"] = weights.semantic

        positive_components["skill_overlap"] = overlap * 100
        positive_weights["skill_overlap"] = weights.skill

        # 2. Normalize positive weights to sum to 1.0
        total_pos_weight = sum(positive_weights.values())
        if total_pos_weight == 0:
            total_pos_weight = 1.0
        normalized_pos = {k: v / total_pos_weight for k, v in positive_weights.items()}

        # 3. Compute positive base score
        base_score = 0.0
        for key, weight in normalized_pos.items():
            base_score += positive_components[key] * weight

        # 4. Compute gap penalty deduction (separate from base)
        # gap_penalty is 0-1, scaled to a max deduction of gap_weight * 100
        # e.g., gap_weight=0.25, full penalty = 25 points off base
        gap_deduction = gap_penalty * weights.gap * 100

        # 5. Final score = base - gap deduction, clamped
        final = max(0.0, min(100.0, base_score - gap_deduction))

        # Build all weights for transparency
        all_weights = {**normalized_pos, "gap_penalty": weights.gap}

        # Explanation
        parts = []
        if sem_available:
            shown_raw = raw_semantic if raw_semantic is not None else sem_score
            parts.append(
                f"semantic={shown_raw:.2f} raw -> {sem_score:.2f} calibrated "
                f"(w={normalized_pos.get('semantic', 0):.2f})"
            )
        parts.append(f"skill_overlap={overlap:.2f} (w={normalized_pos.get('skill_overlap', 0):.2f})")
        parts.append(f"gap_deduction=-{gap_deduction:.1f}pts (penalty={gap_penalty:.2f}, w={weights.gap:.2f})")
        parts.append(f"base={base_score:.1f} - {gap_deduction:.1f} = {final:.1f}")

        reported_semantic = raw_semantic if raw_semantic is not None else sem_score

        return ScoringBreakdown(
            semantic_score=reported_semantic if sem_available else None,
            skill_overlap_score=overlap,
            gap_penalty=gap_penalty,
            weights_used=all_weights,
            final_score=final,
            confidence=0.85 if sem_available else 0.65,
            explanation=" | ".join(parts),
        )

    def _compute_gap_penalty(self, gap_result: GapAnalysisResult) -> float:
        """
        Gap penalty (0-1). Severity-weighted, normalized by what the JD asked
        for in total — NOT by the gaps alone.

        The old formula divided by the summed importance of the gaps only, so
        the denominator shrank with the numerator: one critical gap out of 25
        requirements scored the same ~1.0 penalty as twenty-five of them, and
        the full 25-point deduction landed on strong candidates. Normalizing
        against total requirement importance makes the penalty read as "how
        much of the role is uncovered" (tracker D1).
        """
        if gap_result.missing_count == 0:
            return 0.0

        multipliers = {
            GapPriority.CRITICAL: 1.0,
            GapPriority.HIGH: 0.6,
            GapPriority.MEDIUM: 0.3,
            GapPriority.LOW: 0.1,
        }

        penalty = 0.0
        for gap in gap_result.gaps:
            # gap.weight already discounts "nice to have" requirements.
            mass = gap.importance * gap.weight
            penalty += mass * multipliers.get(gap.priority, 0.2) * gap.confidence

        # Denominator: every requirement, met or not.
        total = gap_result.total_importance
        if total <= 0:
            # No requirement set (parser found nothing) — fall back to the
            # gap-only normalization so the penalty stays bounded.
            total = sum(g.importance * g.weight for g in gap_result.gaps)
        if total <= 0:
            return 0.0

        return min(1.0, penalty / total)

    def _compute_weighted_overlap(
        self,
        coverage: CoverageResult,
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
    ) -> float:
        """
        Proficiency-weighted coverage of the JD's requirements.

        Prefers the resolved coverage, which already understands that
        "Python, Go, or Java" is one requirement and that PostgreSQL is
        evidence of SQL. Falls back to a raw skill-set diff only when the
        requirement parser produced nothing to resolve against.
        """
        if coverage.coverages:
            return coverage.proficiency_weighted_score

        return self._raw_weighted_overlap(resume_result, jd_result)

    def _raw_weighted_overlap(
        self, resume_result: ExtractionResult, jd_result: ExtractionResult,
    ) -> float:
        """Legacy set-diff overlap — degraded path, no requirement semantics."""
        resume_skills = {s.canonical.lower(): s for s in resume_result.skills}
        jd_skills = {s.canonical.lower(): s for s in jd_result.skills}

        if not jd_skills:
            return 0.0

        total_jd_importance = 0.0
        weighted_match = 0.0

        for key, jd_skill in jd_skills.items():
            importance = self._taxonomy.get_importance(jd_skill.canonical)
            total_jd_importance += importance

            if key in resume_skills:
                prof = resume_skills[key].proficiency_score
                # Match value = importance * proficiency
                weighted_match += importance * prof

        if total_jd_importance == 0:
            return 0.0

        return weighted_match / total_jd_importance

    # =========================================================================
    # SHORTLIST PROBABILITY
    # =========================================================================

    def _estimate_shortlist_probability(
        self, score: float, gap_result: GapAnalysisResult,
        sem_score: float, sem_available: bool,
    ) -> float:
        """
        Estimate probability of being shortlisted (0-1).
        Based on: composite score, critical gap count, semantic alignment.

        `sem_score` is the CALIBRATED semantic value — the 0.80/0.50 thresholds
        below are band positions, not raw cosines, which no real resume reaches.

        This is a calibrated heuristic — designed to be replaced with
        learned probability once feedback data is available.
        """
        # Base probability from score (sigmoid-like curve)
        if score >= 85:
            base = 0.85 + (score - 85) * 0.01
        elif score >= 70:
            base = 0.55 + (score - 70) * 0.02
        elif score >= 55:
            base = 0.30 + (score - 55) * 0.017
        elif score >= 40:
            base = 0.10 + (score - 40) * 0.013
        else:
            base = score * 0.0025

        # Critical gap penalty: each critical gap reduces probability
        critical_penalty = gap_result.critical_count * 0.08
        base -= critical_penalty

        # Semantic boost: high semantic alignment = resume "speaks the language"
        if sem_available and sem_score >= 0.80:
            base += 0.05
        elif sem_available and sem_score < 0.50:
            base -= 0.05

        return max(0.0, min(0.99, base))

    # =========================================================================
    # WHAT-IF SIMULATION
    # =========================================================================

    def _simulate_gap_fixes(
        self, current_scoring: ScoringBreakdown,
        gap_result: GapAnalysisResult,
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
        weights,
    ) -> list[ScoreSimulation]:
        """
        REAL simulation: for each critical/high gap, recompute the full
        scoring pipeline as if the user had that skill at proficiency 0.7.
        """
        simulations: list[ScoreSimulation] = []
        current_score = current_scoring.final_score
        # scoring.semantic_score holds the RAW cosine; calibrate it the same way
        # decide() did, or projections land on a different scale than the baseline.
        sem_score = current_scoring.semantic_score
        sem_available = sem_score is not None
        sem_calibrated = self._calibrate_semantic(sem_score or 0.0)

        for gap in gap_result.gaps:
            if gap.priority not in (GapPriority.CRITICAL, GapPriority.HIGH):
                continue

            # Build simulated resume result: add the missing skill
            simulated_skill = Skill(
                name=gap.skill,
                canonical=gap.skill,
                category=gap.category,
                confidence=1.0,
                proficiency_score=0.7,   # Assume decent proficiency after learning
                evidence_strength=0.7,
                occurrence_count=1,
            )
            sim_resume = ExtractionResult(
                skills=resume_result.skills + [simulated_skill],
                extraction_methods_used=resume_result.extraction_methods_used,
                degraded=resume_result.degraded,
                failed_layers=resume_result.failed_layers,
            )

            # Re-resolve coverage against the same requirement set. Recomputing
            # rather than decrementing counters keeps the projected score on the
            # exact path the real score took — including the case where one new
            # skill satisfies several requirements at once.
            sim_coverage = self._resolver.resolve(
                sim_resume.skills, gap_result.requirements
            )
            new_overlap = self._compute_weighted_overlap(
                sim_coverage, sim_resume, jd_result
            )

            # Recompute gap penalty without the gaps this skill just closed
            still_unmet = {g.primary.lower() for g in sim_coverage.unmet}
            remaining = [g for g in gap_result.gaps if g.skill.lower() in still_unmet]
            sim_gap_result = GapAnalysisResult(
                gaps=remaining,
                matched_count=sim_coverage.satisfied_count,
                missing_count=sim_coverage.unmet_count,
                total_jd_skills=gap_result.total_jd_skills,
                overlap_score=sim_coverage.coverage_score,
                critical_count=sum(
                    1 for g in remaining if g.priority == GapPriority.CRITICAL
                ),
                high_count=sum(1 for g in remaining if g.priority == GapPriority.HIGH),
                requirements=gap_result.requirements,
                coverage=sim_coverage,
                total_importance=gap_result.total_importance,
            )
            new_penalty = self._compute_gap_penalty(sim_gap_result)

            # Full score recomputation
            new_scoring = self._compute_score(
                sem_calibrated, sem_available,
                new_overlap, new_penalty, weights, [],
                raw_semantic=sem_score,
            )

            projected = new_scoring.final_score
            new_fit = self._score_to_fit(projected)
            new_prob = self._estimate_shortlist_probability(
                projected, sim_gap_result,
                sem_calibrated, sem_available,
            )

            simulations.append(ScoreSimulation(
                skill_added=gap.skill,
                current_score=round(current_score, 2),
                projected_score=round(projected, 2),
                delta=round(projected - current_score, 2),
                new_fit_level=new_fit,
                new_shortlist_probability=round(new_prob, 3),
            ))

        simulations.sort(key=lambda s: s.delta, reverse=True)
        return simulations

    # =========================================================================
    # IMPROVEMENT PATH (ROI-RANKED)
    # =========================================================================

    def _build_improvement_path(
        self, gap_result: GapAnalysisResult,
        simulations: list[ScoreSimulation],
    ) -> list[ImprovementAction]:
        """Build ROI-ranked improvement actions from gaps + simulations."""
        sim_map = {s.skill_added: s for s in simulations}
        actions: list[ImprovementAction] = []

        for rank, gap in enumerate(gap_result.gaps, 1):
            sim = sim_map.get(gap.skill)
            delta = sim.delta if sim else 0.0

            # ROI reasoning
            if sim and delta > 5:
                roi_reason = (
                    f"Learning {gap.skill} has the highest ROI: "
                    f"score jumps from {sim.current_score:.0f} to {sim.projected_score:.0f} "
                    f"(+{delta:.1f}), moving you to {sim.new_fit_level.value.replace('_', ' ')}."
                )
            elif gap.related_present:
                present = ", ".join(gap.related_present[:2])
                roi_reason = (
                    f"Your existing {present} knowledge means {gap.skill} "
                    f"can be learned faster than starting from scratch."
                )
            else:
                roi_reason = gap.reasoning[:150]  # Truncated gap reasoning

            actions.append(ImprovementAction(
                skill=gap.skill,
                priority=gap.priority,
                impact_score_delta=round(delta, 2),
                learning_time=gap.learning_time_estimate or "2-4 weeks",
                reasoning=roi_reason,
                roi_rank=rank,
            ))

        # Re-sort by actual impact delta (simulation-based), not just priority
        actions.sort(key=lambda a: a.impact_score_delta, reverse=True)
        for i, action in enumerate(actions, 1):
            action.roi_rank = i

        return actions

    # =========================================================================
    # DECISION LOGIC
    # =========================================================================

    def _make_recommendation(
        self, score: float, gap_result: GapAnalysisResult,
        shortlist_prob: float,
    ) -> Recommendation:
        """Convert score + gaps into actionable recommendation."""
        if score >= self._config.fit_strong and gap_result.critical_count == 0:
            return Recommendation.STRONG_APPLY

        if score >= self._config.fit_good and gap_result.critical_count <= 1:
            return Recommendation.APPLY

        if score >= self._config.fit_potential:
            if gap_result.critical_count <= 2:
                return Recommendation.APPLY_WITH_PREPARATION
            else:
                return Recommendation.UPSKILL_THEN_APPLY

        if score >= self._config.fit_weak and shortlist_prob >= 0.15:
            return Recommendation.UPSKILL_THEN_APPLY

        return Recommendation.DO_NOT_APPLY

    def _score_to_fit(self, score: float) -> FitLevel:
        if score >= self._config.fit_strong:
            return FitLevel.STRONG_FIT
        elif score >= self._config.fit_good:
            return FitLevel.GOOD_FIT
        elif score >= self._config.fit_potential:
            return FitLevel.POTENTIAL_FIT
        elif score >= self._config.fit_weak:
            return FitLevel.WEAK_FIT
        else:
            return FitLevel.NO_FIT

    # =========================================================================
    # REASONING
    # =========================================================================

    def _generate_decision_reasoning(
        self, recommendation, scoring, gap_result,
        shortlist_prob, strengths, weaknesses,
        improvement_path, sem_score, sem_available,
    ) -> str:
        """Generate multi-factor reasoning for the decision."""
        parts: list[str] = []

        # Opening — the verdict
        rec_text = {
            Recommendation.STRONG_APPLY: "Strong match — apply with confidence.",
            Recommendation.APPLY: "Good match — apply. Minor gaps are compensable.",
            Recommendation.APPLY_WITH_PREPARATION: "Viable match, but preparation needed before applying.",
            Recommendation.UPSKILL_THEN_APPLY: "Significant gaps exist — upskill before applying.",
            Recommendation.DO_NOT_APPLY: "Poor fit for this specific role at this time.",
        }
        parts.append(rec_text.get(recommendation, ""))

        # Score context
        parts.append(
            f"Overall fit score: {scoring.final_score:.0f}/100 "
            f"(shortlist probability: {shortlist_prob:.0%})."
        )

        # Semantic alignment
        if sem_available:
            if sem_score >= 0.80:
                parts.append(
                    "Your resume language strongly aligns with this JD — "
                    "you speak the right technical vocabulary."
                )
            elif sem_score >= 0.60:
                parts.append("Moderate semantic alignment with the JD.")
            else:
                parts.append(
                    "Low semantic alignment — your resume may need rewording "
                    "to better match this role's language."
                )

        # Strengths
        if strengths:
            parts.append(f"Key strengths: {', '.join(strengths[:3])}.")

        # Gaps
        if gap_result.critical_count > 0:
            critical_skills = [
                g.skill for g in gap_result.gaps
                if g.priority == GapPriority.CRITICAL
            ][:3]
            parts.append(
                f"Critical gaps: {', '.join(critical_skills)}. "
                f"These are core requirements that significantly impact your candidacy."
            )

        # Top improvement
        if improvement_path:
            top = improvement_path[0]
            parts.append(
                f"Highest-ROI action: learn {top.skill} "
                f"(+{top.impact_score_delta:.1f} score points, {top.learning_time})."
            )

        return " ".join(parts)

    # =========================================================================
    # STRENGTHS & WEAKNESSES
    # =========================================================================

    def _analyze_strengths_weaknesses(
        self, resume_result, jd_result, gap_result,
        sem_score, sem_available,
    ) -> tuple[list[str], list[str]]:
        """Extract top strengths and weaknesses."""
        strengths: list[str] = []
        weaknesses: list[str] = []

        resume_skills = {s.canonical.lower(): s for s in resume_result.skills}
        jd_skills = {s.canonical.lower(): s for s in jd_result.skills}

        # Strengths: matched skills with high proficiency
        matched_strong = []
        for key in set(resume_skills.keys()) & set(jd_skills.keys()):
            skill = resume_skills[key]
            if skill.proficiency_score >= 0.7:
                matched_strong.append((skill.canonical, skill.proficiency_score))

        matched_strong.sort(key=lambda x: x[1], reverse=True)
        for name, prof in matched_strong[:5]:
            strengths.append(f"{name} (proficiency: {prof:.0%})")

        # Strength: semantic alignment
        if sem_available and sem_score >= 0.75:
            strengths.append(f"Strong resume-JD semantic alignment ({sem_score:.0%})")

        # Strength: high overlap
        if gap_result.overlap_score >= 0.70:
            strengths.append(f"High skill coverage ({gap_result.overlap_score:.0%})")

        # Weaknesses: critical gaps
        for gap in gap_result.gaps:
            if gap.priority == GapPriority.CRITICAL:
                weaknesses.append(f"Missing {gap.skill} (critical)")
            elif gap.priority == GapPriority.HIGH and len(weaknesses) < 5:
                weaknesses.append(f"Missing {gap.skill} (high priority)")

        # Weakness: low semantic
        if sem_available and sem_score < 0.50:
            weaknesses.append("Resume language doesn't match JD well")

        return strengths[:5], weaknesses[:5]

    # =========================================================================
    # CONFIDENCE
    # =========================================================================

    def _compute_decision_confidence(
        self, sem_available, resume_result, jd_result, gap_result,
    ) -> float:
        """
        How confident are we in this decision? (0-1)
        Higher when: more data points, less degradation, clear signals.
        """
        conf = 0.5  # base

        # Semantic available = major confidence boost
        if sem_available:
            conf += 0.15

        # Extraction quality
        if not resume_result.degraded:
            conf += 0.10
        if not jd_result.degraded:
            conf += 0.10

        # Skill count (more skills = more signal)
        total_skills = len(resume_result.skills) + len(jd_result.skills)
        if total_skills >= 20:
            conf += 0.10
        elif total_skills >= 10:
            conf += 0.05

        # Clear gap signal (either very good or very bad = more confident)
        if gap_result.overlap_score >= 0.80 or gap_result.overlap_score <= 0.20:
            conf += 0.05

        return min(0.95, conf)

    # =========================================================================
    # FEEDBACK LOOP
    # =========================================================================

    def record_feedback(
        self, decision: Decision, outcome: str,
        user_notes: str = "",
        analysis_id: Optional[str] = None,
    ) -> None:
        """
        Record whether the decision was correct.

        Args:
            decision: the Decision that was made
            outcome: 'hired', 'rejected', 'interview', 'ghosted', 'user_disagrees'
            user_notes: optional freeform notes
            analysis_id: the analysis being judged, or None if it is unknown
                (doc 08 §3.2 permits feedback with `decision_found: false`)

        The row is written through `StateBackend`, so it survives a restart and
        is still there when the learning loop is built in M5:
        - Calibrate shortlist_probability curve
        - Adjust scoring weights
        - Improve gap priority accuracy
        """
        import uuid

        self._state.store_feedback(FeedbackRecord(
            feedback_id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            outcome=outcome,
            user_notes=user_notes,
            score=decision.overall_score,
            shortlist_probability=decision.shortlist_probability,
            confidence=decision.confidence,
            recommendation=decision.recommendation.value,
            fit_level=decision.fit_level.value,
        ))

        logger.info(
            "Feedback recorded: outcome=%s, score=%.1f, prob=%.2f, recommendation=%s",
            outcome, decision.overall_score,
            decision.shortlist_probability, decision.recommendation.value,
        )

        # Trigger recalibration if enough data
        recorded = self._state.count_feedback()
        if recorded >= self._config.feedback_recalibrate_threshold:
            self._trigger_recalibration(recorded)

    def _trigger_recalibration(self, recorded: int) -> None:
        """
        Placeholder for the M5 learning loop.
        When enough feedback accumulates:
        1. Adjust shortlist_probability curve parameters
        2. Re-weight scoring components
        3. Update gap priority model
        """
        logger.info(
            "Recalibration triggered with %d feedback entries (not yet implemented)",
            recorded,
        )
        # Future: logistic regression on stored feedback to calibrate probability
        # Future: gradient-based weight adjustment for scoring components

    def get_feedback_stats(self) -> FeedbackStats:
        """Return feedback statistics for monitoring."""
        return self._state.get_feedback_stats()
