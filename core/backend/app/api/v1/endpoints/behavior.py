"""
NeuroSync — Behavior & Human State API Endpoints (Phase 3.5).
"""
from __future__ import annotations

import uuid
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.observation import AgentObservation, ObservationSource
from app.models.career_state import CareerState, LearningSession
from app.api.deps import get_human_state_engine, get_agent_decision_engine

router = APIRouter(prefix="/behavior", tags=["behavior"])

# In-memory active sessions store
_active_sessions: dict[str, LearningSession] = {}


class SessionStartRequest(BaseModel):
    user_id: str


class SessionStopRequest(BaseModel):
    session_id: str


class EventRequest(BaseModel):
    user_id: str
    source: ObservationSource
    metric_name: str
    raw_value: float
    normalized_score: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.post("/session/start", summary="Start a learning/practice session")
async def start_session(body: SessionStartRequest):
    session_id = str(uuid.uuid4())
    session = LearningSession(session_id=session_id, user_id=body.user_id)
    _active_sessions[session_id] = session
    return {"status": "started", "session": session}


@router.post("/session/stop", summary="Stop an active learning session")
async def stop_session(body: SessionStopRequest):
    session = _active_sessions.get(body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")
    session.active = False
    return {"status": "stopped", "session": session}


@router.post("/event", summary="Record a behavioral observation event")
async def record_event(body: EventRequest):
    engine = get_human_state_engine()
    obs = AgentObservation(
        user_id=body.user_id,
        source=body.source,
        metric_name=body.metric_name,
        raw_value=body.raw_value,
        normalized_score=body.normalized_score,
        metadata=body.metadata,
    )
    engine.record_observation(obs)
    return {"status": "recorded", "metric": body.metric_name, "user_id": body.user_id}


@router.get("/state", summary="Get CareerState & AI Agent Decisions")
async def get_user_state(user_id: str = Query(..., description="User ID")):
    state_engine = get_human_state_engine()
    decision_engine = get_agent_decision_engine()

    career_state = state_engine.compute_career_state(user_id)
    agent_decisions = decision_engine.evaluate(career_state)

    return {
        "user_id": user_id,
        "career_state": career_state,
        "agent_decisions": agent_decisions,
    }
