"""
NeuroSync — Feedback Processor (Phase 3.3)

Turns accumulated outcome feedback into actionable scoring calibration.

Responsibilities:
  1. Aggregate feedback entries from the StateBackend
  2. Detect scoring drift (predicted shortlist prob vs actual outcome)
  3. Compute weight adjustments for the scoring formula
  4. Register newly-discovered skills into the taxonomy (vocabulary growth)
  5. Trigger recalibration when N >= config.feedback_recalibrate_at

Recalibration writes adjusted weights back to the StateBackend so they
survive process restarts (doc 12 Rule 5: StateBackend is the ONLY persistence).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

from app.config import Settings
from app.state.base import FeedbackRecord, StateBackend
from app.utils.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)


@dataclass
class DriftReport:
    """Scoring calibration drift between predicted and actual outcomes."""
    total_feedback: int
    positive_outcomes: int             # user actually got interview/offer
    negative_outcomes: int
    mean_predicted_prob: float         # average shortlist_probability we gave
    actual_positive_rate: float        # ground truth positive rate
    drift: float                       # actual - predicted (positive = over-pessimistic)
    calibration_quality: str           # "well_calibrated" | "over_optimistic" | "over_pessimistic"
    recalibrate_recommended: bool


@dataclass
class WeightAdjustment:
    """Proposed adjustment to a scoring weight."""
    weight_name: str
    current_value: float
    proposed_value: float
    delta: float
    rationale: str


@dataclass
class RecalibrationResult:
    """Full output of a feedback processing run."""
    feedback_count: int
    drift: DriftReport
    weight_adjustments: list[WeightAdjustment] = field(default_factory=list)
    new_skills_registered: list[str] = field(default_factory=list)
    recalibration_applied: bool = False
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "feedback_count": self.feedback_count,
            "drift": {
                "total": self.drift.total_feedback,
                "positive_outcomes": self.drift.positive_outcomes,
                "actual_positive_rate": round(self.drift.actual_positive_rate, 3),
                "mean_predicted_prob": round(self.drift.mean_predicted_prob, 3),
                "drift": round(self.drift.drift, 3),
                "calibration_quality": self.drift.calibration_quality,
                "recalibrate_recommended": self.drift.recalibrate_recommended,
            },
            "weight_adjustments": [
                {
                    "weight": w.weight_name,
                    "current": round(w.current_value, 4),
                    "proposed": round(w.proposed_value, 4),
                    "delta": round(w.delta, 4),
                    "rationale": w.rationale,
                }
                for w in self.weight_adjustments
            ],
            "new_skills_registered": self.new_skills_registered,
            "recalibration_applied": self.recalibration_applied,
            "message": self.message,
        }


class FeedbackProcessor:
    """
    Full learning loop for scoring calibration.

    Usage:
        processor = FeedbackProcessor(config, taxonomy)
        result = await processor.process(state_backend)
    """

    # Drift thresholds that trigger weight adjustments
    _DRIFT_THRESHOLD_OPTIMISTIC = 0.10    # We are 10%+ over-optimistic
    _DRIFT_THRESHOLD_PESSIMISTIC = -0.10  # We are 10%+ over-pessimistic

    # Weight adjustment damping (don't over-correct in one pass)
    _DAMPING = 0.3

    def __init__(self, config: Settings, taxonomy: SkillTaxonomy):
        self._config = config
        self._taxonomy = taxonomy

    async def process(self, state: StateBackend) -> RecalibrationResult:
        """
        Run the full feedback processing pipeline.

        1. Load all feedback records
        2. Compute drift
        3. Optionally apply weight adjustments
        4. Register new skills
        5. Return structured result
        """
        records = state.list_feedback()

        if not records:
            return RecalibrationResult(
                feedback_count=0,
                drift=DriftReport(
                    total_feedback=0,
                    positive_outcomes=0,
                    negative_outcomes=0,
                    mean_predicted_prob=0.0,
                    actual_positive_rate=0.0,
                    drift=0.0,
                    calibration_quality="well_calibrated",
                    recalibrate_recommended=False,
                ),
                message="No feedback records available. Continue collecting data.",
            )

        drift = self._compute_drift(records)
        adjustments: list[WeightAdjustment] = []
        recalibrated = False

        recalibrate_at = getattr(self._config, "feedback_recalibrate_at", 50)
        if len(records) >= recalibrate_at and drift.recalibrate_recommended:
            adjustments = self._compute_weight_adjustments(drift)
            # Note: weight persistence is a future enhancement requiring StateBackend.set_weights()
            # Currently returns proposed adjustments for operator review.
            recalibrated = False  # Will be True when StateBackend.set_weights() is implemented
            logger.info(
                "Recalibration recommended: drift=%.3f, adjustments=%d",
                drift.drift,
                len(adjustments),
            )

        new_skills = self._discover_new_skills(records)

        msg_parts = [
            f"Processed {len(records)} feedback records.",
            f"Drift: {drift.drift:+.1%} ({drift.calibration_quality}).",
        ]
        if adjustments:
            msg_parts.append(f"{len(adjustments)} weight adjustment(s) proposed.")
        if new_skills:
            msg_parts.append(f"{len(new_skills)} new skill(s) discovered.")
        if len(records) < recalibrate_at:
            remaining = recalibrate_at - len(records)
            msg_parts.append(f"Need {remaining} more feedback entries to trigger recalibration.")

        return RecalibrationResult(
            feedback_count=len(records),
            drift=drift,
            weight_adjustments=adjustments,
            new_skills_registered=new_skills,
            recalibration_applied=recalibrated,
            message=" ".join(msg_parts),
        )

    # ─────────────────────────────────────────────────────────
    # DRIFT ANALYSIS
    # ─────────────────────────────────────────────────────────

    def _compute_drift(self, records: list[FeedbackRecord]) -> DriftReport:
        """Measure gap between our shortlist probabilities and actual outcomes."""
        positive_outcomes = sum(
            1 for r in records
            if r.outcome in ("interview", "offer", "positive", "hired", True, "true", "1")
        )
        negative_outcomes = len(records) - positive_outcomes

        actual_rate = positive_outcomes / len(records) if records else 0.0

        # Pull predicted probabilities from the stored analysis
        predicted_probs = []
        for r in records:
            # FeedbackRecord stores the cached analysis; extract shortlist_probability
            if hasattr(r, "shortlist_probability") and r.shortlist_probability is not None:
                predicted_probs.append(float(r.shortlist_probability))

        mean_predicted = sum(predicted_probs) / len(predicted_probs) if predicted_probs else 0.5

        drift = actual_rate - mean_predicted

        if drift > self._DRIFT_THRESHOLD_PESSIMISTIC:
            quality = "over_pessimistic"
        elif drift < -self._DRIFT_THRESHOLD_OPTIMISTIC:
            quality = "over_optimistic"
        else:
            quality = "well_calibrated"

        recalibrate = abs(drift) > max(
            self._DRIFT_THRESHOLD_OPTIMISTIC,
            abs(self._DRIFT_THRESHOLD_PESSIMISTIC),
        )

        return DriftReport(
            total_feedback=len(records),
            positive_outcomes=positive_outcomes,
            negative_outcomes=negative_outcomes,
            mean_predicted_prob=mean_predicted,
            actual_positive_rate=actual_rate,
            drift=drift,
            calibration_quality=quality,
            recalibrate_recommended=recalibrate,
        )

    # ─────────────────────────────────────────────────────────
    # WEIGHT ADJUSTMENTS
    # ─────────────────────────────────────────────────────────

    def _compute_weight_adjustments(self, drift: DriftReport) -> list[WeightAdjustment]:
        """Propose scoring weight changes to correct drift."""
        adjustments: list[WeightAdjustment] = []
        w = self._config.scoring

        if drift.calibration_quality == "over_optimistic":
            # We're too generous — increase gap penalty weight
            current = w.gap_penalty_weight
            delta = drift.drift * self._DAMPING  # negative drift → increase penalty
            proposed = max(0.05, current + abs(delta))
            adjustments.append(WeightAdjustment(
                weight_name="gap_penalty_weight",
                current_value=current,
                proposed_value=proposed,
                delta=proposed - current,
                rationale=(
                    f"Actual positive rate ({drift.actual_positive_rate:.1%}) is "
                    f"{abs(drift.drift):.1%} below predicted ({drift.mean_predicted_prob:.1%}). "
                    f"Increasing gap_penalty_weight to reduce over-optimism."
                ),
            ))

        elif drift.calibration_quality == "over_pessimistic":
            # We're too harsh — reduce gap penalty weight
            current = w.gap_penalty_weight
            delta = abs(drift.drift) * self._DAMPING
            proposed = max(0.01, current - delta)
            adjustments.append(WeightAdjustment(
                weight_name="gap_penalty_weight",
                current_value=current,
                proposed_value=proposed,
                delta=proposed - current,
                rationale=(
                    f"Actual positive rate ({drift.actual_positive_rate:.1%}) is "
                    f"{abs(drift.drift):.1%} above predicted ({drift.mean_predicted_prob:.1%}). "
                    f"Reducing gap_penalty_weight to reduce over-pessimism."
                ),
            ))

        return adjustments

    # ─────────────────────────────────────────────────────────
    # TAXONOMY GROWTH
    # ─────────────────────────────────────────────────────────

    def _discover_new_skills(self, records: list[FeedbackRecord]) -> list[str]:
        """
        Identify skills mentioned in feedback that are not in the taxonomy.
        Returns skills added. Currently a stub — full implementation requires
        a taxonomy write method (tracked as Phase 3.3 enhancement).
        """
        # Future: parse feedback.notes / feedback.additional_skills fields
        # and call self._taxonomy.register_runtime_skill(name, category, ...)
        return []
