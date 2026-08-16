"""
NeuroSync — Agent Decision Engine (Phase 3.5)

Consumes CareerState (NEVER raw signals directly) and generates
personalized learning & career recommendations.
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from app.models.career_state import CareerState

logger = logging.getLogger(__name__)


class AgentActionType(str, Enum):
    TAKE_BREAK = "take_break"
    REINFORCE_BASICS = "reinforce_basics"
    INCREASE_DIFFICULTY = "increase_difficulty"
    SCHEDULE_MOCK_INTERVIEW = "schedule_mock_interview"
    BOOST_MOTIVATION = "boost_motivation"
    MAINTAIN_PACE = "maintain_pace"


class AgentDecision(BaseModel):
    """An autonomous agent recommendation for the user's career path."""
    action_type: AgentActionType
    title: str
    rationale: str
    priority: str                       # critical | high | medium | low
    suggested_resource: Optional[str] = None


class AgentDecisionEngine:
    """Evaluates CareerState predictions and decides proactive interventions."""

    def evaluate(self, state: CareerState) -> list[AgentDecision]:
        decisions: list[AgentDecision] = []

        preds = state.predictions

        # 1. Burnout risk intervention
        if preds and preds.burnout_probability >= 0.6:
            decisions.append(AgentDecision(
                action_type=AgentActionType.TAKE_BREAK,
                title="Rest & Recovery Recommended",
                rationale=f"High burnout probability ({preds.burnout_probability:.0%}) detected. Rest for 24-48 hours.",
                priority="critical",
                suggested_resource="Mindfulness & Recovery Guide",
            ))

        # 2. Dropout risk intervention
        if preds and preds.dropout_probability >= 0.5:
            decisions.append(AgentDecision(
                action_type=AgentActionType.BOOST_MOTIVATION,
                title="Re-engage with Quick Wins",
                rationale=f"Engagement momentum is dropping. Complete 1 small 15-minute module to regain momentum.",
                priority="high",
                suggested_resource="15-minute Python Quick Win",
            ))

        # 3. High interview readiness -> Schedule Mock
        if state.interview_readiness >= 0.7:
            decisions.append(AgentDecision(
                action_type=AgentActionType.SCHEDULE_MOCK_INTERVIEW,
                title="Ready for Mock Interview",
                rationale=f"Interview readiness is high ({state.interview_readiness:.0%}). Practice in simulated interview mode.",
                priority="high",
                suggested_resource="AI Mock Interviewer",
            ))

        # 4. High growth & low burnout -> Increase Difficulty
        if state.growth_velocity >= 0.75 and state.burnout_risk < 0.4:
            decisions.append(AgentDecision(
                action_type=AgentActionType.INCREASE_DIFFICULTY,
                title="Challenge Mode Unlocked",
                rationale="You are excelling rapidly. Step up to senior-level architectural challenges.",
                priority="medium",
                suggested_resource="Advanced Distributed Systems Lab",
            ))

        # Default fallback
        if not decisions:
            decisions.append(AgentDecision(
                action_type=AgentActionType.MAINTAIN_PACE,
                title="Maintain Steady Learning Pace",
                rationale="Your career metrics are balanced. Continue your current roadmap.",
                priority="low",
            ))

        return decisions
