"""Tests for Perception & Emotion Intelligence Engine (Pillar 1)."""

import pytest
from app.services.perception_engine import (
    perception_engine,
    FacialLandmarksPayload
)


def test_start_session():
    """Verify camera session initialization."""
    res = perception_engine.start_session("sess_test_123")
    assert res["session_id"] == "sess_test_123"
    assert res["status"] == "active"


def test_process_frame_focused():
    """Test focused learning state frame processing."""
    payload = FacialLandmarksPayload(
        head_pose={"pitch": 2.0, "yaw": 1.0, "roll": 0.0},
        eye_gaze={"x": 0.05, "y": 0.02},
        ear_left=0.32,
        ear_right=0.31,
        mar=0.12,
        expression_scores={"focused": 0.85, "neutral": 0.10}
    )
    result = perception_engine.process_frame("sess_test_123", payload)

    assert result.attention_score > 70.0
    assert result.is_distracted is False
    assert result.is_sleepy is False
    assert result.learning_state in ["focused", "engaged"]


def test_process_frame_sleepy_and_distracted():
    """Test fatigue & distraction detection when eye aspect ratio drops."""
    payload = FacialLandmarksPayload(
        head_pose={"pitch": 25.0, "yaw": 30.0, "roll": 0.0},
        eye_gaze={"x": 0.80, "y": 0.60},
        ear_left=0.12,  # Closed eyes
        ear_right=0.14,
        mar=0.15
    )
    result = perception_engine.process_frame("sess_test_123", payload)

    assert result.is_sleepy is True
    assert result.is_distracted is True
    assert result.learning_state in ["sleepy", "distracted"]


def test_generate_session_report():
    """Test generating post-session analytics & report card."""
    report = perception_engine.generate_session_report("sess_test_123")

    assert report.session_id == "sess_test_123"
    assert report.avg_attention_score >= 0.0
    assert isinstance(report.recommendations, list)
    assert len(report.recommendations) > 0
