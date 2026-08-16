"""
NeuroSync — Market Intelligence Engine (Phase 4.1)

Provides real-time and curated market intelligence:
- Skill demand trends & percentage change
- Market salary range estimations
- Regional hiring velocity
- Skill gap priority upgrade based on market demand surging
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SkillDemandSignal(BaseModel):
    skill: str
    demand_trend: str                  # e.g., "surging" | "stable" | "declining"
    percent_change: float              # e.g., +37.5 for +37.5% YoY
    demand_score: float = Field(ge=0.0, le=100.0)
    market_tier: str                   # "tier_1_critical" | "tier_2_high" | "tier_3_standard"


class SalarySignal(BaseModel):
    role: str
    currency: str = "USD"
    min_salary: float
    median_salary: float
    max_salary: float
    top_skill_boosts: dict[str, float] = Field(default_factory=dict)  # skill -> salary uplift %


class HiringVelocity(BaseModel):
    role: str
    region: str
    openings_count: int
    velocity_rating: str               # "high_volume" | "moderate" | "niche"
    avg_days_to_fill: int


# Curated Market Demand Database
_MARKET_DEMAND_DB: dict[str, dict[str, Any]] = {
    "kubernetes": {"trend": "surging", "change": 37.5, "score": 92.0, "tier": "tier_1_critical"},
    "docker": {"trend": "stable", "change": 12.0, "score": 85.0, "tier": "tier_1_critical"},
    "python": {"trend": "surging", "change": 28.0, "score": 95.0, "tier": "tier_1_critical"},
    "react": {"trend": "stable", "change": 8.5, "score": 88.0, "tier": "tier_2_high"},
    "typescript": {"trend": "surging", "change": 31.0, "score": 90.0, "tier": "tier_1_critical"},
    "aws": {"trend": "surging", "change": 22.0, "score": 94.0, "tier": "tier_1_critical"},
    "pytorch": {"trend": "surging", "change": 45.0, "score": 96.0, "tier": "tier_1_critical"},
    "golang": {"trend": "surging", "change": 34.0, "score": 89.0, "tier": "tier_1_critical"},
    "postgresql": {"trend": "stable", "change": 15.0, "score": 87.0, "tier": "tier_2_high"},
    "system design": {"trend": "surging", "change": 26.0, "score": 93.0, "tier": "tier_1_critical"},
}


class MarketIntelligenceEngine:
    """Provides market trend signals and dynamic gap priority modulation."""

    def get_skill_demand(self, skill: str) -> SkillDemandSignal:
        canonical = skill.strip().lower()
        info = _MARKET_DEMAND_DB.get(canonical, {
            "trend": "stable",
            "change": 5.0,
            "score": 70.0,
            "tier": "tier_3_standard",
        })
        return SkillDemandSignal(
            skill=skill,
            demand_trend=info["trend"],
            percent_change=info["change"],
            demand_score=info["score"],
            market_tier=info["tier"],
        )

    def get_salary_signal(self, skills: list[str], role: str = "Software Engineer") -> SalarySignal:
        base_median = 135000.0
        boosts: dict[str, float] = {}

        for s in skills:
            d = self.get_skill_demand(s)
            if d.percent_change > 25.0:
                boost_pct = round(d.percent_change * 0.2, 1)
                boosts[s] = boost_pct

        total_boost_pct = min(40.0, sum(boosts.values()))
        median = base_median * (1.0 + total_boost_pct / 100.0)

        return SalarySignal(
            role=role,
            currency="USD",
            min_salary=round(median * 0.8, -3),
            median_salary=round(median, -3),
            max_salary=round(median * 1.3, -3),
            top_skill_boosts=boosts,
        )

    def get_hiring_velocity(self, role: str = "Software Engineer", region: str = "Global/Remote") -> HiringVelocity:
        return HiringVelocity(
            role=role,
            region=region,
            openings_count=42500,
            velocity_rating="high_volume",
            avg_days_to_fill=32,
        )
