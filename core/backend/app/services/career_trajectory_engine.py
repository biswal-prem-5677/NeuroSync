"""
NeuroSync — Career Trajectory Engine (Phase 4.2)

Tracks candidate skill & score progression over time, computes growth velocity,
and projects estimated weeks to readiness for a target role.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TrajectorySnapshot(BaseModel):
    user_id: str
    skills_count: int
    overall_score: float
    target_role: str
    created_at: datetime = Field(default_factory=_utc_now)


class GrowthVelocity(BaseModel):
    user_id: str
    skills_per_month: float
    score_improvement_per_month: float
    readiness_velocity_tier: str       # "accelerated" | "steady" | "plateau"


class TrajectoryProjection(BaseModel):
    user_id: str
    target_role: str
    current_score: float
    target_score: float = 80.0
    estimated_weeks_to_readiness: int
    recommended_milestones: list[str] = Field(default_factory=list)


class CareerTrajectoryEngine:
    """Tracks progression over time and forecasts career growth velocity."""

    def __init__(self):
        self._user_history: dict[str, list[TrajectorySnapshot]] = {}

    def record_snapshot(
        self,
        user_id: str,
        skills_count: int,
        overall_score: float,
        target_role: str = "Software Engineer",
    ) -> TrajectorySnapshot:
        snap = TrajectorySnapshot(
            user_id=user_id,
            skills_count=skills_count,
            overall_score=overall_score,
            target_role=target_role,
        )
        if user_id not in self._user_history:
            self._user_history[user_id] = []
        self._user_history[user_id].append(snap)
        return snap

    def compute_growth_velocity(self, user_id: str) -> GrowthVelocity:
        history = self._user_history.get(user_id, [])
        if len(history) < 2:
            return GrowthVelocity(
                user_id=user_id,
                skills_per_month=3.5,
                score_improvement_per_month=6.0,
                readiness_velocity_tier="steady",
            )

        first = history[0]
        last = history[-1]
        days = max(1.0, (last.created_at - first.created_at).total_seconds() / 86400.0)
        months = max(0.1, days / 30.0)

        skills_vel = (last.skills_count - first.skills_count) / months
        score_vel = (last.overall_score - first.overall_score) / months

        tier = "steady"
        if score_vel >= 10.0:
            tier = "accelerated"
        elif score_vel <= 1.0:
            tier = "plateau"

        return GrowthVelocity(
            user_id=user_id,
            skills_per_month=round(max(0.5, skills_vel), 1),
            score_improvement_per_month=round(max(0.5, score_vel), 1),
            readiness_velocity_tier=tier,
        )

    def predict_readiness(
        self,
        user_id: str,
        current_score: float,
        target_role: str = "Software Engineer",
        target_score: float = 80.0,
    ) -> TrajectoryProjection:
        vel = self.compute_growth_velocity(user_id)
        gap = max(0.0, target_score - current_score)

        months_needed = gap / vel.score_improvement_per_month if vel.score_improvement_per_month > 0 else 3.0
        weeks_needed = max(1, int(round(months_needed * 4.3)))

        milestones = [
            "Complete top-ranked gap skill in improvement path",
            "Achieve ≥75 overall score on practice job descriptions",
            "Build 1 production project featuring key missing skills",
        ]

        return TrajectoryProjection(
            user_id=user_id,
            target_role=target_role,
            current_score=current_score,
            target_score=target_score,
            estimated_weeks_to_readiness=weeks_needed,
            recommended_milestones=milestones,
        )
