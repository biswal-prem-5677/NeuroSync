"""
NeuroSync — Tests for /feedback endpoint and state persistence.
"""
import pytest


def test_feedback_flow(client, sample_resume, sample_jd):
    # 1. POST /analyze to create an analysis
    res = client.post(
        "/api/v1/analyze",
        json={"resume_text": sample_resume, "jd_text": sample_jd},
    )
    assert res.status_code == 200
    analysis_id = res.json()["analysis_id"]

    # 2. POST /feedback with valid analysis_id
    fb_res = client.post(
        "/api/v1/feedback",
        json={"analysis_id": analysis_id, "outcome": "hired", "notes": "Got the job!"},
    )
    assert fb_res.status_code == 200
    fb_data = fb_res.json()
    assert fb_data["status"] == "recorded"
    assert fb_data["decision_found"] is True


def test_feedback_unknown_id(client):
    fb_res = client.post(
        "/api/v1/feedback",
        json={"analysis_id": "nonexistent-id", "outcome": "rejected"},
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["decision_found"] is False
