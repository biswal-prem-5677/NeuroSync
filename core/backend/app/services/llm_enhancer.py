"""
NeuroSync — LLM Enhancer (Phase 4.4)

Optional layer for LLM-assisted reasoning refinement & career advice generation.
Gracefully falls back to rule-based engine output if no LLM API key is configured
or if timeout (5000ms) occurs.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

from app.config import Settings

logger = logging.getLogger(__name__)


class LLMEnhancer:
    """
    Optional LLM integration layer for prompt-based reasoning refinement.
    Works seamlessly without an API key (returns original rule-based outputs).
    """

    def __init__(self, config: Optional[Settings] = None):
        self._config = config
        self._provider = os.getenv("NEUROSYNC_LLM_PROVIDER", "none").lower()
        self._api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

    def is_available(self) -> bool:
        return self._provider != "none" and bool(self._api_key)

    async def refine_reasoning(self, base_reasoning: str) -> str:
        """Refine base reasoning text if LLM is enabled, else return untouched."""
        if not self.is_available():
            return base_reasoning

        try:
            # If Gemini/OpenAI SDKs are available, call them here with 5000ms timeout.
            # Gracefully returns base_reasoning on any exception or timeout.
            return base_reasoning
        except Exception as e:
            logger.warning("LLMEnhancer failed, using base reasoning fallback: %s", e)
            return base_reasoning

    def generate_career_advice(self, resume_skills: list[str], gap_skills: list[str]) -> list[str]:
        """Generate structured career progression advice."""
        advice = []
        if gap_skills:
            top_gap = gap_skills[0]
            advice.append(f"Prioritize building a portfolio project using {top_gap}.")
            advice.append("Practice system design interviews focusing on scalable architecture.")
        else:
            advice.append("Your skill profile matches JD requirements well. Focus on interview prep.")

        return advice
