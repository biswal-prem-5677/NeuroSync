"""Tests for Session Timeline, Growth Milestone, and Billing Dashboard Services."""

import pytest
from app.services.session_timeline_logger import session_timeline_logger
from app.services.achievement_growth_engine import achievement_growth_engine, InterviewPracticeRequest
from app.services.cloud_auth_billing_engine import cloud_auth_billing_engine


def test_session_timeline_logger():
    """Verify session report card and timeline generation."""
    report = session_timeline_logger.generate_full_report("sess_full_1")
    assert report.session_id == "sess_full_1"
    assert len(report.attention_timeline) > 0
    assert len(report.personalized_revision_queue) > 0


def test_achievement_growth_engine():
    """Verify growth timeline, interview practice evaluator, and AI assistant advice."""
    timeline = achievement_growth_engine.get_growth_timeline("usr_biswal")
    assert len(timeline) >= 3

    eval_res = achievement_growth_engine.evaluate_interview_answer(
        InterviewPracticeRequest(
            question="How do you handle microservices concurrency?",
            user_answer="I use FastAPI async loops with PostgreSQL connection pooling and Redis caching."
        )
    )
    assert eval_res.score > 60.0
    assert len(eval_res.key_strengths) > 0

    advice = achievement_growth_engine.get_assistant_advice("usr_biswal")
    assert advice.action_priority == "HIGH"


def test_cloud_auth_billing_engine():
    """Verify OAuth URLs, pricing plans, and master dashboard aggregation."""
    auth_data = cloud_auth_billing_engine.get_google_auth_url()
    assert "auth_url" in auth_data

    plans = cloud_auth_billing_engine.get_subscription_plans()
    assert len(plans) == 3

    checkout = cloud_auth_billing_engine.create_stripe_checkout("usr_biswal", "plan_pro")
    assert "checkout_url" in checkout

    dashboard = cloud_auth_billing_engine.get_master_dashboard("usr_biswal")
    assert dashboard.overall_ecosystem_completion_pct == 100.0
