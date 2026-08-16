"""NeuroSync — Session Timeline & Topic Difficulty API Router."""

from fastapi import APIRouter
from typing import Dict, Any
from app.services.session_timeline_logger import (
    session_timeline_logger,
    TimelineEvent,
    SessionAnalyticsReport
)

router = APIRouter(prefix="/timeline", tags=["Session Timeline & Analytics"])


@router.post("/event", response_model=TimelineEvent, summary="Log timestamped study event")
async def log_event(session_id: str, event: TimelineEvent):
    """Log a timestamped focus/distraction/confusion event."""
    return session_timeline_logger.log_event(session_id, event)


@router.get("/report/{session_id}", response_model=SessionAnalyticsReport, summary="Get session analytics report card")
async def get_report(session_id: str):
    """Get full session analytics report with timeline charts data & revision queue."""
    return session_timeline_logger.generate_full_report(session_id)
