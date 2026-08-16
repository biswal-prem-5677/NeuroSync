"""
NeuroSync — Tests for Phase 3.5 Human State Intelligence.
Tests HumanStateEngine, AgentDecisionEngine, and /behavior endpoints.
"""
from __future__ import annotations

import pytest
from app.models.observation import AgentObservation, ObservationSource
from app.services.human_state_engine import HumanStateEngine
from app.services.agent_decision_engine import AgentDecisionEngine


def test_human_state_engine_computation():
    engine = HumanStateEngine()
    user_id = "user_test_123"

    # Baseline state
    init_state = engine.compute_career_state(user_id)
    assert init_state.confidence == 0.5

    # Record practice test high accuracy
    engine.record_observation(AgentObservation(
        user_id=user_id,
        source=ObservationSource.PRACTICE_TEST,
        metric_name="confidence",
        raw_value=0.9,
        normalized_score=0.9,
    ))

    state = engine.compute_career_state(user_id)
    assert state.confidence == 0.9
    assert state.predictions is not None
    assert state.predictions.interview_success_probability > 0.5


def test_agent_decision_engine():
    state_engine = HumanStateEngine()
    decision_engine = AgentDecisionEngine()
    user_id = "user_burnout_test"

    # High burnout risk setup
    state_engine.record_observation(AgentObservation(
        user_id=user_id,
        source=ObservationSource.PRACTICE_TEST,
        metric_name="confidence",
        raw_value=0.1,
        normalized_score=0.1,
    ))
    state_engine.record_observation(AgentObservation(
        user_id=user_id,
        source=ObservationSource.GOAL_PROGRESS,
        metric_name="momentum",
        raw_value=0.1,
        normalized_score=0.1,
    ))

    state = state_engine.compute_career_state(user_id)
    decisions = decision_engine.evaluate(state)

    assert len(decisions) > 0
    action_types = [d.action_type for d in decisions]
    assert "take_break" in action_types or "boost_motivation" in action_types


@pytest.mark.anyio
async def test_behavior_endpoints(client):
    user_id = "api_user_99"

    # 1. Start session
    res_start = client.post("/api/v1/behavior/session/start", json={"user_id": user_id})
    assert res_start.status_code == 200
    session_id = res_start.json()["session"]["session_id"]

    # 2. Record event
    res_event = client.post("/api/v1/behavior/event", json={
        "user_id": user_id,
        "source": "practice_test",
        "metric_name": "confidence",
        "raw_value": 0.85,
        "normalized_score": 0.85,
    })
    assert res_event.status_code == 200

    # 3. Get state & decisions
    res_state = client.get(f"/api/v1/behavior/state?user_id={user_id}")
    assert res_state.status_code == 200
    data = res_state.json()
    assert data["career_state"]["confidence"] == 0.85
    assert len(data["agent_decisions"]) > 0

    # 4. Stop session
    res_stop = client.post("/api/v1/behavior/session/stop", json={"session_id": session_id})
    assert res_stop.status_code == 200
    assert res_stop.json()["session"]["active"] is False
