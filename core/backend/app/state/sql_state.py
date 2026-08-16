"""
NeuroSync — SQL StateBackend (PostgreSQL in production, SQLite for local work).

Doc 12 §2 lists `redis_state.py` here. Doc 15 §4 chose PostgreSQL instead and
doc 14 §2.3 pulled it into M1: Redis is a cache, and the data being lost on every
restart is the scarcest asset the product accumulates (doc 15 R3). Decision
logged as doc 10 D-007; doc 12's file map is amended to match.

This module is the only place in the app that may import `app.db`.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.db.models import Analysis, Base, Feedback
from app.db.session import build_engine, build_session_factory, redact
from app.state.base import (
    AnalysisRecord,
    FeedbackRecord,
    FeedbackStats,
    StateBackend,
)

logger = logging.getLogger(__name__)


class SqlState(StateBackend):
    """Durable persistence through SQLAlchemy 2.0."""

    name = "sql"

    def __init__(
        self,
        database_url: str,
        recalibrate_at: int = 50,
        echo: bool = False,
        create_all: bool = False,
    ):
        """
        Args:
            database_url: SQLAlchemy URL, e.g. `postgresql+psycopg://…` or `sqlite:///./x.db`
            recalibrate_at: threshold reported in feedback stats
            echo: log every statement
            create_all: create tables directly instead of via Alembic. Off by
                default — schema changes belong in a migration (doc 09 §4). The
                probe and the test suite turn it on to build a throwaway database.
        """
        self._url = database_url
        self._recalibrate_at = recalibrate_at
        self._echo = echo
        self._create_all = create_all
        self._engine = None
        self._session_factory = None

    # --- lifecycle --------------------------------------------------------

    def initialize(self) -> None:
        self._engine = build_engine(self._url, echo=self._echo)
        self._session_factory = build_session_factory(self._engine)

        if self._create_all:
            Base.metadata.create_all(self._engine)

        # Fail loudly at startup rather than on the first user request.
        with self._engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")

        logger.info("State backend 'sql' ready (%s)", redact(self._url))

    def close(self) -> None:
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def health(self) -> dict[str, Any]:
        base: dict[str, Any] = {"backend": self.name, "durable": True}
        if self._engine is None:
            return {**base, "status": "uninitialized"}
        base["dialect"] = self._engine.dialect.name
        try:
            with self._session_factory() as session:      # type: ignore[misc]
                analyses = session.scalar(select(func.count()).select_from(Analysis))
                feedback = session.scalar(select(func.count()).select_from(Feedback))
            return {**base, "status": "healthy", "analyses": analyses, "feedback": feedback}
        except SQLAlchemyError as e:
            logger.error("State backend health check failed: %s", e)
            return {**base, "status": "unhealthy", "error": type(e).__name__}

    # --- analyses ---------------------------------------------------------

    def store_analysis(self, record: AnalysisRecord) -> None:
        with self._session_factory() as session:          # type: ignore[misc]
            row = session.get(Analysis, record.analysis_id)
            if row is None:
                row = Analysis(id=record.analysis_id)
                session.add(row)
            row.user_id = record.user_id
            row.resume_text = record.resume_text
            row.jd_text = record.jd_text
            row.recommendation = record.recommendation
            row.fit_level = record.fit_level
            row.overall_score = record.overall_score
            row.shortlist_probability = record.shortlist_probability
            row.confidence = record.confidence
            row.reasoning = record.reasoning
            row.semantic_score = record.semantic_score
            row.skill_overlap_score = record.skill_overlap_score
            row.gap_penalty = record.gap_penalty
            row.scoring_explanation = record.scoring_explanation
            row.payload = record.payload
            row.processing_time_ms = int(record.processing_time_ms)
            row.created_at = record.created_at
            session.commit()

    def get_analysis(self, analysis_id: str) -> Optional[AnalysisRecord]:
        with self._session_factory() as session:          # type: ignore[misc]
            row = session.get(Analysis, analysis_id)
            if row is None:
                return None
            return AnalysisRecord(
                analysis_id=row.id,
                user_id=row.user_id,
                resume_text=row.resume_text,
                jd_text=row.jd_text,
                recommendation=row.recommendation,
                fit_level=row.fit_level,
                overall_score=row.overall_score,
                shortlist_probability=row.shortlist_probability,
                confidence=row.confidence,
                reasoning=row.reasoning,
                semantic_score=row.semantic_score,
                skill_overlap_score=row.skill_overlap_score,
                gap_penalty=row.gap_penalty,
                scoring_explanation=row.scoring_explanation,
                payload=row.payload or {},
                processing_time_ms=row.processing_time_ms,
                created_at=row.created_at,
            )

    # --- feedback ---------------------------------------------------------

    def store_feedback(self, record: FeedbackRecord) -> None:
        with self._session_factory() as session:          # type: ignore[misc]
            analysis_id = record.analysis_id
            # A UNIQUE analysis_id means one outcome per analysis: a second
            # report is a correction, not a new row.
            existing = None
            if analysis_id is not None:
                existing = session.scalar(
                    select(Feedback).where(Feedback.analysis_id == analysis_id)
                )
            row = existing or Feedback(id=record.feedback_id or str(uuid.uuid4()))
            if existing is None:
                session.add(row)
            row.analysis_id = analysis_id
            row.outcome = record.outcome
            row.user_notes = record.user_notes
            row.score = record.score
            row.shortlist_probability = record.shortlist_probability
            row.confidence = record.confidence
            row.recommendation = record.recommendation
            row.fit_level = record.fit_level
            row.is_processed = record.is_processed
            row.created_at = record.created_at
            session.commit()

    def get_feedback_stats(self) -> FeedbackStats:
        with self._session_factory() as session:          # type: ignore[misc]
            total = session.scalar(select(func.count()).select_from(Feedback)) or 0
            if total == 0:
                return FeedbackStats(recalibrate_at=self._recalibrate_at)

            outcomes = dict(
                session.execute(
                    select(Feedback.outcome, func.count()).group_by(Feedback.outcome)
                ).all()
            )
            avg_score = session.scalar(select(func.avg(Feedback.score)))

        return FeedbackStats(
            count=total,
            outcomes={k: int(v) for k, v in outcomes.items()},
            avg_score=float(avg_score) if avg_score is not None else None,
            recalibrate_at=self._recalibrate_at,
        )

    def count_feedback(self) -> int:
        with self._session_factory() as session:          # type: ignore[misc]
            return session.scalar(select(func.count()).select_from(Feedback)) or 0

    def list_feedback(self, limit: int = 500) -> list[FeedbackRecord]:
        with self._session_factory() as session:          # type: ignore[misc]
            rows = session.scalars(
                select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
            ).all()
            return [
                FeedbackRecord(
                    feedback_id=r.id,
                    analysis_id=r.analysis_id,
                    outcome=r.outcome,
                    user_notes=r.user_notes or "",
                    score=r.score,
                    shortlist_probability=r.shortlist_probability,
                    confidence=r.confidence,
                    recommendation=r.recommendation,
                    fit_level=r.fit_level,
                    is_processed=r.is_processed,
                    created_at=r.created_at,
                )
                for r in rows
            ]

