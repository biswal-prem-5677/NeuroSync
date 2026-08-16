"""
NeuroSync — Adaptive Scorer (Phase 4.3)

Provides per-role scoring weight profiles and dynamic weight adjustments.
Backend roles weight skill overlap higher; product/lead roles weight semantic alignment.
"""
from __future__ import annotations

import logging
from typing import Any
from pydantic import BaseModel, Field

from app.config import ScoringWeights

logger = logging.getLogger(__name__)


# Role-specific weight profiles
_ROLE_WEIGHT_PROFILES: dict[str, dict[str, float]] = {
    "backend": {"semantic": 0.25, "skill_overlap": 0.45, "gap_penalty": 0.30},
    "frontend": {"semantic": 0.30, "skill_overlap": 0.40, "gap_penalty": 0.30},
    "data_ai": {"semantic": 0.20, "skill_overlap": 0.50, "gap_penalty": 0.30},
    "leadership": {"semantic": 0.45, "skill_overlap": 0.30, "gap_penalty": 0.25},
    "default": {"semantic": 0.30, "skill_overlap": 0.40, "gap_penalty": 0.30},
}


class AdaptiveScorer:
    """Adapts scoring weight profiles dynamically based on job domain/role."""

    def get_role_weights(self, role_type: str = "default") -> ScoringWeights:
        key = role_type.strip().lower()
        profile = _ROLE_WEIGHT_PROFILES.get(key, _ROLE_WEIGHT_PROFILES["default"])

        return ScoringWeights(
            semantic=profile["semantic"],
            skill=profile["skill_overlap"],
            gap=profile["gap_penalty"],
        )

    def calculate_adaptive_score(
        self,
        semantic_score: float,
        skill_overlap_score: float,
        gap_penalty: float,
        role_type: str = "default",
    ) -> float:
        w = self.get_role_weights(role_type)
        raw = (
            semantic_score * w.semantic * 100.0 +
            skill_overlap_score * w.skill -
            gap_penalty * w.gap * 10.0
        )
        return max(0.0, min(100.0, raw))

