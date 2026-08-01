"""
NeuroSync — StateBackend interface.

Doc 12 §2 (Cross-Cutting: State) and §4 Rule 5. Everything that must outlive a
single request goes through this interface: nothing else writes to disk, a
database, or an external store.

The records below are the *persistence contract* — deliberately narrower than the
domain objects they are built from. A `Decision` carries improvement paths,
simulations and an evidence chain; what the learning loop needs back is the
decision's shape (score, probability, recommendation) plus the full response as an
opaque document. Storing the document as JSON rather than as columns is doc 15 §4's
"correct call": the report is a document, not a relational entity.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


# =========================================================================
# PERSISTENCE RECORDS
# =========================================================================

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisRecord(BaseModel):
    """One completed `/analyze` run, as persisted."""

    analysis_id: str
    user_id: Optional[str] = None          # None = guest scan (no auth until M2)

    resume_text: str
    jd_text: str

    # Decision shape — columns because they are queried and aggregated.
    recommendation: str
    fit_level: str
    overall_score: float
    shortlist_probability: float
    confidence: float
    reasoning: str = ""

    # Scoring components — nullable because semantic can be unavailable.
    semantic_score: Optional[float] = None
    skill_overlap_score: float = 0.0
    gap_penalty: float = 0.0
    scoring_explanation: str = ""

    # The full API response, kept verbatim for auditability and replay.
    payload: dict[str, Any] = Field(default_factory=dict)

    processing_time_ms: float = 0.0
    created_at: datetime = Field(default_factory=_utc_now)


class FeedbackRecord(BaseModel):
    """One outcome report against an analysis."""

    feedback_id: str
    analysis_id: Optional[str] = None      # None when the analysis is unknown
    outcome: str                           # hired|rejected|interview|ghosted|user_disagrees
    user_notes: str = ""

    # Snapshot of the decision being judged. Denormalised on purpose: the
    # learning loop must still be able to compute calibration statistics if the
    # analysis row is later deleted under a data-deletion request (M2).
    score: float = 0.0
    shortlist_probability: float = 0.0
    confidence: float = 0.0
    recommendation: str = ""
    fit_level: str = ""

    is_processed: bool = False
    created_at: datetime = Field(default_factory=_utc_now)


class FeedbackStats(BaseModel):
    """Aggregate feedback view — the shape doc 08 §3.2 promises."""

    count: int = 0
    outcomes: dict[str, int] = Field(default_factory=dict)
    avg_score: Optional[float] = None
    recalibrate_at: int = 0

    def as_response(self) -> dict[str, Any]:
        """Doc 08 §3.2 omits `avg_score` entirely when there is no feedback."""
        if self.count == 0:
            return {"count": 0, "outcomes": {}}
        return {
            "count": self.count,
            "outcomes": self.outcomes,
            "avg_score": self.avg_score,
            "recalibrate_at": self.recalibrate_at,
        }


# =========================================================================
# INTERFACE
# =========================================================================

class StateBackend(ABC):
    """
    Abstract persistence boundary.

    Implementations must be safe to call from multiple threads: FastAPI runs
    sync work in a threadpool, so two requests can be inside the backend at once.

    Scope note — the interface is what M1 needs and no more. Doc 12 §2 also lists
    `get_scoring_weights()`; that arrives with `AdaptiveScorer` in M5, because an
    abstract method with no caller is a shape guess, not a contract.
    """

    #: Short identifier reported by /health, e.g. "memory" or "sql".
    name: str = "abstract"

    # --- lifecycle --------------------------------------------------------

    def initialize(self) -> None:
        """Open connections / create structures. Called once from `lifespan`."""

    def close(self) -> None:
        """Release resources. Called once at shutdown."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Report backend liveness for `/health`. Must never raise."""

    # --- analyses ---------------------------------------------------------

    @abstractmethod
    def store_analysis(self, record: AnalysisRecord) -> None:
        """Persist a completed analysis. Overwrites on duplicate id."""

    @abstractmethod
    def get_analysis(self, analysis_id: str) -> Optional[AnalysisRecord]:
        """Return a stored analysis, or None if unknown."""

    # --- feedback ---------------------------------------------------------

    @abstractmethod
    def store_feedback(self, record: FeedbackRecord) -> None:
        """Persist an outcome report."""

    @abstractmethod
    def get_feedback_stats(self) -> FeedbackStats:
        """Aggregate recorded feedback."""

    @abstractmethod
    def count_feedback(self) -> int:
        """Total feedback rows — drives the recalibration threshold."""
