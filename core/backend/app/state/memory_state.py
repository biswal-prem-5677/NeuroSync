"""
NeuroSync — In-memory StateBackend.

Doc 12 §2: the dev/test implementation. No external dependencies, and no
persistence — everything here dies with the process. That is the whole point of
naming it: before this layer existed the same volatility was hidden inside
module-level dicts in `deps.py` and `intelligence_engine.py`, where nothing
advertised that feedback was being destroyed on every restart (doc 15 R3).

Use `NEUROSYNC_STATE_BACKEND=sql` for anything whose data matters.
"""
from __future__ import annotations

import logging
import threading
from collections import Counter, OrderedDict
from typing import Any, Optional

from app.state.base import (
    AnalysisRecord,
    FeedbackRecord,
    FeedbackStats,
    StateBackend,
)

logger = logging.getLogger(__name__)


class MemoryState(StateBackend):
    """Bounded in-process store. Analyses evict oldest-first; feedback never evicts."""

    name = "memory"

    def __init__(self, max_analyses: int = 500, recalibrate_at: int = 50):
        self._max_analyses = max_analyses
        self._recalibrate_at = recalibrate_at
        self._lock = threading.Lock()
        self._analyses: "OrderedDict[str, AnalysisRecord]" = OrderedDict()
        self._feedback: list[FeedbackRecord] = []

    # --- lifecycle --------------------------------------------------------

    def initialize(self) -> None:
        logger.warning(
            "State backend is 'memory' — analyses and feedback are lost on restart. "
            "Set NEUROSYNC_STATE_BACKEND=sql with NEUROSYNC_DATABASE_URL to persist."
        )

    def health(self) -> dict[str, Any]:
        with self._lock:
            return {
                "backend": self.name,
                "status": "healthy",
                "durable": False,
                "analyses": len(self._analyses),
                "feedback": len(self._feedback),
            }

    # --- analyses ---------------------------------------------------------

    def store_analysis(self, record: AnalysisRecord) -> None:
        with self._lock:
            if record.analysis_id in self._analyses:
                del self._analyses[record.analysis_id]
            elif len(self._analyses) >= self._max_analyses:
                self._analyses.popitem(last=False)   # evict oldest
            self._analyses[record.analysis_id] = record

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisRecord]:
        with self._lock:
            return self._analyses.get(analysis_id)

    # --- feedback ---------------------------------------------------------

    def store_feedback(self, record: FeedbackRecord) -> None:
        with self._lock:
            self._feedback.append(record)

    def get_feedback_stats(self) -> FeedbackStats:
        with self._lock:
            entries = list(self._feedback)

        if not entries:
            return FeedbackStats(recalibrate_at=self._recalibrate_at)

        return FeedbackStats(
            count=len(entries),
            outcomes=dict(Counter(e.outcome for e in entries)),
            avg_score=sum(e.score for e in entries) / len(entries),
            recalibrate_at=self._recalibrate_at,
        )

    def count_feedback(self) -> int:
        with self._lock:
            return len(self._feedback)

    def list_feedback(self, limit: int = 500) -> list[FeedbackRecord]:
        with self._lock:
            return list(reversed(self._feedback))[:limit]

