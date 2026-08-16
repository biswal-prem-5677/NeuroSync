"""
NeuroSync — Human State Engine (Phase 3.5)

Aggregates observations across 8 sources, computes CareerState,
and calculates predictive probabilities (burnout, dropout, interview success).
"""
from __future__ import annotations

import logging
import math
from typing import Optional

from app.models.observation import AgentObservation, ObservationSource
from app.models.career_state import CareerState, StatePrediction

logger = logging.getLogger(__name__)


class HumanStateEngine:
    """
    Engine that synthesizes human state from raw behavioral observations.
    """

    def __init__(self):
        # In-memory storage for observations per user
        self._user_observations: dict[str, list[AgentObservation]] = {}

    def record_observation(self, obs: AgentObservation) -> None:
        """Record a single observation for a user."""
        if obs.user_id not in self._user_observations:
            self._user_observations[obs.user_id] = []
        self._user_observations[obs.user_id].append(obs)
        logger.debug("Recorded observation %s for user %s", obs.metric_name, obs.user_id)

    def compute_career_state(self, user_id: str) -> CareerState:
        """Synthesize current CareerState for a user from their observations."""
        obss = self._user_observations.get(user_id, [])

        if not obss:
            state = CareerState(user_id=user_id)
            state.predictions = self._compute_predictions(state)
            return state

        # Group observations by source or metric
        scores_by_metric: dict[str, list[float]] = {}
        for o in obss:
            if o.metric_name not in scores_by_metric:
                scores_by_metric[o.metric_name] = []
            scores_by_metric[o.metric_name].append(o.normalized_score)

        def avg_metric(name: str, default: float = 0.5) -> float:
            vals = scores_by_metric.get(name, [])
            return sum(vals) / len(vals) if vals else default

        confidence = avg_metric("confidence", avg_metric("practice_accuracy", 0.5))
        momentum = avg_metric("momentum", avg_metric("streak_length", 0.5))
        engagement = avg_metric("engagement", avg_metric("session_frequency", 0.5))
        consistency = avg_metric("consistency", avg_metric("typing_regularity", 0.5))
        growth_velocity = avg_metric("growth_velocity", avg_metric("score_delta", 0.5))

        # Burnout risk rises when engagement is high but momentum/confidence drop
        burnout_risk = max(0.0, min(1.0, (1.0 - confidence) * 0.4 + (1.0 - momentum) * 0.4 + (engagement) * 0.2))
        interview_readiness = max(0.0, min(1.0, confidence * 0.5 + consistency * 0.3 + growth_velocity * 0.2))
        career_readiness = max(0.0, min(1.0, interview_readiness * 0.6 + momentum * 0.4))

        state = CareerState(
            user_id=user_id,
            confidence=round(confidence, 3),
            momentum=round(momentum, 3),
            engagement=round(engagement, 3),
            consistency=round(consistency, 3),
            growth_velocity=round(growth_velocity, 3),
            burnout_risk=round(burnout_risk, 3),
            interview_readiness=round(interview_readiness, 3),
            career_readiness=round(career_readiness, 3),
        )

        state.predictions = self._compute_predictions(state)
        return state

    def _compute_predictions(self, state: CareerState) -> StatePrediction:
        """Compute predictive probabilities from state metrics."""
        burnout_prob = min(1.0, max(0.0, state.burnout_risk * 0.8 + (1.0 - state.consistency) * 0.2))
        dropout_prob = min(1.0, max(0.0, (1.0 - state.engagement) * 0.5 + (1.0 - state.momentum) * 0.5))
        interview_prob = min(1.0, max(0.0, state.interview_readiness * 0.7 + state.confidence * 0.3))
        skill_completion_prob = min(1.0, max(0.0, state.growth_velocity * 0.6 + state.consistency * 0.4))

        return StatePrediction(
            burnout_probability=round(burnout_prob, 3),
            dropout_probability=round(dropout_prob, 3),
            interview_success_probability=round(interview_prob, 3),
            skill_completion_probability=round(skill_completion_prob, 3),
        )
