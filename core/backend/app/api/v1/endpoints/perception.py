"""NeuroSync — Perception API Endpoint Router."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any

from app.services.perception_engine import (
    perception_engine,
    FacialLandmarksPayload,
    PerceptionFrameResult,
    PerceptionSessionReport
)

router = APIRouter(prefix="/perception", tags=["Perception & Emotion Intelligence"])


class StartSessionRequest(BaseModel):
    session_id: str


@router.post("/session/start", response_model=Dict[str, Any], summary="Start camera monitoring session")
async def start_session(payload: StartSessionRequest):
    """Initialize a timestamped camera monitoring session."""
    return perception_engine.start_session(payload.session_id)


@router.post("/frame", response_model=PerceptionFrameResult, summary="Analyze single video telemetry frame")
async def process_frame(
    session_id: str = Query(..., description="Active session ID"),
    payload: FacialLandmarksPayload = ...
):
    """Process incoming facial telemetry / landmarks frame and return 10-state emotion + attention analytics."""
    return perception_engine.process_frame(session_id, payload)


@router.post("/session/end", response_model=PerceptionSessionReport, summary="End session & generate report card")
async def end_session(session_id: str = Query(..., description="Session ID to end")):
    """End active session and compute overall session analytics, focus timeline & revision queue."""
    return perception_engine.generate_session_report(session_id)


@router.get("/session/{session_id}", response_model=PerceptionSessionReport, summary="Get session report")
async def get_session_report(session_id: str):
    """Retrieve session report card and analytics."""
    return perception_engine.generate_session_report(session_id)
