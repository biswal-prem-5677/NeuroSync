"""Tests for Pillar 3 Social, Identity, Job Tracker & Cold Outreach Services."""

import pytest
from app.services.social_profile_engine import social_profile_engine
from app.services.job_discovery_engine import job_discovery_engine
from app.services.outreach_engine import outreach_engine, ColdEmailRequest


def test_social_profile_engine():
    """Verify unified profile and achievement feed."""
    profile = social_profile_engine.get_profile("usr_biswal")
    assert profile.full_name == "Priyabrata Biswal"
    assert len(profile.projects) > 0
    assert "Python" in profile.top_skills

    feed = social_profile_engine.get_community_feed()
    assert len(feed) >= 2


def test_job_discovery_engine():
    """Verify job search and application Kanban tracking."""
    jobs = job_discovery_engine.search_jobs("Vercel")
    assert len(jobs) > 0
    assert jobs[0].company_name == "Vercel"

    apps = job_discovery_engine.get_applications("usr_biswal")
    assert len(apps) >= 2

    updated = job_discovery_engine.update_application_status("usr_biswal", "app_1", "Offer")
    assert updated.status == "Offer"


def test_outreach_engine():
    """Verify recruiter cold email generator."""
    req = ColdEmailRequest(
        recipient_name="Sarah",
        recipient_role="Recruiter",
        company_name="Vercel",
        target_role="AI Engineer"
    )
    res = outreach_engine.generate_cold_email(req)

    assert "Vercel" in res.subject_line
    assert "Sarah" in res.email_body
    assert len(res.followup_sequence) == 2
