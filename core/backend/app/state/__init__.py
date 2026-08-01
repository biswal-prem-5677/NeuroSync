"""
NeuroSync — State (cross-cutting persistence layer).

Doc 12 §4 Rule 5: `StateBackend` is the ONLY persistence. No service, endpoint or
module-level dict stores anything that must outlive a single request.
"""
from app.state.base import (
    AnalysisRecord,
    FeedbackRecord,
    FeedbackStats,
    StateBackend,
)

__all__ = [
    "AnalysisRecord",
    "FeedbackRecord",
    "FeedbackStats",
    "StateBackend",
]
