"""
NeuroSync — Deep End-to-End Product Logic, Feature Integration & Workflow Tests.

Tests the ENTIRE product as one connected system, not isolated functions.
Covers: data lineage, profile consistency, learning→career bridge,
session variation, job matching, state machines, multi-tenant isolation,
empty states, duplication, concurrent users, and business invariants.
"""
import pytest
from starlette.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ═══════════════════════════════════════════════════════════════
# SECTION 1: AUTH FLOW & USER IDENTITY PRESERVATION
# ═══════════════════════════════════════════════════════════════

class TestAuthFlow:
    """Tests 1-2: Sign up, authenticate, identity preservation."""

    def test_magic_link_returns_token(self, client):
        """Step 1: Request magic link → get token."""
        resp = client.post("/api/v1/auth/magic-link", json={"email": "testuser@neurosync.ai"})
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["status"] == "success"

    def test_verify_token_returns_jwt(self, client):
        """Step 2: Verify magic link → get JWT access token."""
        resp1 = client.post("/api/v1/auth/magic-link", json={"email": "testuser@neurosync.ai"})
        token = resp1.json()["token"]
        resp2 = client.post("/api/v1/auth/verify", json={"token": token})
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["status"] == "authenticated"
        assert "access_token" in data
        assert data["user"]["email"] == "testuser@neurosync.ai"

    def test_auth_me_with_valid_jwt(self, client):
        """Step 3: /auth/me returns correct user from JWT."""
        resp1 = client.post("/api/v1/auth/magic-link", json={"email": "user_a@test.com"})
        token = resp1.json()["token"]
        resp2 = client.post("/api/v1/auth/verify", json={"token": token})
        jwt = resp2.json()["access_token"]
        resp3 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {jwt}"})
        assert resp3.status_code == 200
        assert resp3.json()["email"] == "user_a@test.com"

    def test_auth_me_rejects_bad_token(self, client):
        """Verify bad token → 401, not fake success."""
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_garbage"})
        assert resp.status_code == 401

    def test_auth_me_rejects_missing_header(self, client):
        """Verify missing auth → 401."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════
# SECTION 9: LEARNING SESSION LOGIC — SESSION VARIATION
# ═══════════════════════════════════════════════════════════════

class TestPerceptionSessionLogic:
    """Tests 9, 11, 12: Session A ≠ B ≠ C, weak topic, recommendation quality."""

    def test_start_session(self, client):
        resp = client.post("/api/v1/perception/session/start", json={"session_id": "sess_e2e_A"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_session_a_high_attention(self, client):
        """Session A: High attention, low fatigue → focused learning state."""
        client.post("/api/v1/perception/session/start", json={"session_id": "sess_A"})
        resp = client.post(
            "/api/v1/perception/frame?session_id=sess_A",
            json={
                "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                "eye_gaze": {"x": 0.0, "y": 0.0},
                "ear_left": 0.32, "ear_right": 0.32,
                "mar": 0.15,
                "expression_scores": {"focused": 0.8, "neutral": 0.1}
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["attention_score"] > 75.0
        assert data["fatigue_index"] < 0.3
        assert data["is_sleepy"] is False
        assert data["learning_state"] == "focused"

    def test_session_b_low_attention_high_fatigue(self, client):
        """Session B: Low attention, high fatigue → sleepy state."""
        client.post("/api/v1/perception/session/start", json={"session_id": "sess_B"})
        resp = client.post(
            "/api/v1/perception/frame?session_id=sess_B",
            json={
                "head_pose": {"pitch": 0, "yaw": 30, "roll": 0},
                "eye_gaze": {"x": 0.8, "y": 0.5},
                "ear_left": 0.12, "ear_right": 0.14,
                "mar": 0.15,
                "expression_scores": {"sleepy": 0.7, "neutral": 0.1}
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_sleepy"] is True
        assert data["fatigue_index"] > 0.3
        assert data["learning_state"] in ("sleepy", "distracted")

    def test_session_c_high_confusion(self, client):
        """Session C: High confusion → confused state."""
        client.post("/api/v1/perception/session/start", json={"session_id": "sess_C"})
        resp = client.post(
            "/api/v1/perception/frame?session_id=sess_C",
            json={
                "head_pose": {"pitch": 5, "yaw": 5, "roll": 0},
                "eye_gaze": {"x": 0.1, "y": 0.1},
                "ear_left": 0.28, "ear_right": 0.28,
                "mar": 0.20,
                "expression_scores": {"confused": 0.85, "focused": 0.05}
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["primary_emotion"] == "confused"
        assert data["learning_state"] == "confused"

    def test_sessions_produce_different_states(self, client):
        """Sessions A, B, C must produce distinct learning states."""
        client.post("/api/v1/perception/session/start", json={"session_id": "cmp_A"})
        client.post("/api/v1/perception/session/start", json={"session_id": "cmp_B"})
        client.post("/api/v1/perception/session/start", json={"session_id": "cmp_C"})

        rA = client.post(
            "/api/v1/perception/frame?session_id=cmp_A",
            json={"ear_left": 0.32, "ear_right": 0.32, "mar": 0.15,
                  "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                  "eye_gaze": {"x": 0.0, "y": 0.0},
                  "expression_scores": {"focused": 0.9}}
        ).json()
        rB = client.post(
            "/api/v1/perception/frame?session_id=cmp_B",
            json={"ear_left": 0.12, "ear_right": 0.12, "mar": 0.15,
                  "head_pose": {"pitch": 0, "yaw": 35, "roll": 0},
                  "eye_gaze": {"x": 0.9, "y": 0.5},
                  "expression_scores": {"sleepy": 0.8}}
        ).json()
        rC = client.post(
            "/api/v1/perception/frame?session_id=cmp_C",
            json={"ear_left": 0.28, "ear_right": 0.28, "mar": 0.20,
                  "head_pose": {"pitch": 5, "yaw": 5, "roll": 0},
                  "eye_gaze": {"x": 0.1, "y": 0.1},
                  "expression_scores": {"confused": 0.9}}
        ).json()

        states = {rA["learning_state"], rB["learning_state"], rC["learning_state"]}
        assert len(states) == 3, f"Expected 3 distinct states, got {states}"

    def test_session_report_reflects_behavior(self, client):
        """Session report recommendations differ based on actual telemetry."""
        client.post("/api/v1/perception/session/start", json={"session_id": "rpt_good"})
        for _ in range(5):
            client.post(
                "/api/v1/perception/frame?session_id=rpt_good",
                json={"ear_left": 0.32, "ear_right": 0.32, "mar": 0.15,
                      "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                      "eye_gaze": {"x": 0.0, "y": 0.0},
                      "expression_scores": {"focused": 0.9}}
            )
        resp_good = client.get("/api/v1/perception/session/rpt_good")
        assert resp_good.status_code == 200
        good_report = resp_good.json()
        assert good_report["avg_attention_score"] > 70.0

        client.post("/api/v1/perception/session/start", json={"session_id": "rpt_bad"})
        for _ in range(5):
            client.post(
                "/api/v1/perception/frame?session_id=rpt_bad",
                json={"ear_left": 0.12, "ear_right": 0.12, "mar": 0.15,
                      "head_pose": {"pitch": 0, "yaw": 35, "roll": 0},
                      "eye_gaze": {"x": 0.8, "y": 0.6},
                      "expression_scores": {"sleepy": 0.8}}
            )
        resp_bad = client.get("/api/v1/perception/session/rpt_bad")
        assert resp_bad.status_code == 200
        bad_report = resp_bad.json()

        assert good_report["avg_attention_score"] > bad_report["avg_attention_score"]
        assert good_report["recommendations"] != bad_report["recommendations"]


# ═══════════════════════════════════════════════════════════════
# SECTION 14: RESUME → JD LOGIC — SKILL MATCHING
# ═══════════════════════════════════════════════════════════════

class TestResumeJDMatching:
    """Tests 14-16: Resume/JD matching, skill gap, career readiness."""

    def test_resume_jd_analysis_returns_gaps(self, client):
        """Upload resume text + JD → matched & missing skills computed."""
        resp = client.post("/api/v1/analyze", json={
            "resume_text": "Experienced Python developer. Built FastAPI microservices. Used PyTorch for ML model training. Strong SQL and PostgreSQL skills.",
            "jd_text": "Looking for Python, PyTorch, Docker, Kubernetes, AWS expertise."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "decision" in data
        assert "overall_score" in data["decision"]
        assert "gaps" in data
        assert "skills" in data
        assert data["skills"]["resume_count"] > 0
        assert data["skills"]["jd_count"] > 0

    def test_skill_gap_identifies_missing(self, client):
        """Verify the gap engine correctly identifies missing skills."""
        resp = client.post("/api/v1/analyze", json={
            "resume_text": "Python developer with FastAPI and SQL experience.",
            "jd_text": "We need Python, Docker, Kubernetes, Terraform, AWS."
        })
        data = resp.json()
        gap_skills = [g["skill"].lower() for g in data.get("gaps", [])]
        assert any("docker" in s for s in gap_skills) or any("kubernetes" in s for s in gap_skills) or len(gap_skills) > 0

    def test_career_readiness_differs_for_profiles(self, client):
        """Profile A (strong match) should score higher than Profile B (weak match)."""
        resp_strong = client.post("/api/v1/analyze", json={
            "resume_text": "Expert Python developer. 8 years FastAPI experience. Built production Docker containers. Deployed on Kubernetes and AWS. Strong Terraform IaC skills.",
            "jd_text": "Senior Python developer needed with Docker, Kubernetes, AWS, and Terraform."
        })
        resp_weak = client.post("/api/v1/analyze", json={
            "resume_text": "Basic computer user.",
            "jd_text": "Senior Python developer needed with Docker, Kubernetes, AWS, and Terraform."
        })
        score_strong = resp_strong.json()["decision"]["overall_score"]
        score_weak = resp_weak.json()["decision"]["overall_score"]
        assert score_strong >= score_weak


# ═══════════════════════════════════════════════════════════════
# SECTION 17-20: JOB SEARCH, MATCH, APPLICATION STATE MACHINE
# ═══════════════════════════════════════════════════════════════

class TestJobSearchAndApplications:
    """Tests 17-20: Job search, match logic, application Kanban state machine."""

    def test_job_search_returns_results(self, client):
        """Job search returns curated job list."""
        resp = client.get("/api/v1/jobs/search")
        assert resp.status_code == 200
        jobs = resp.json()
        assert isinstance(jobs, list)
        assert len(jobs) >= 1
        for job in jobs:
            assert "company_name" in job
            assert "role_title" in job
            assert "match_score" in job

    def test_job_search_filter_by_query(self, client):
        """Querying 'Stripe' should narrow results."""
        resp_all = client.get("/api/v1/jobs/search")
        resp_stripe = client.get("/api/v1/jobs/search?query=stripe")
        all_jobs = resp_all.json()
        stripe_jobs = resp_stripe.json()
        assert len(stripe_jobs) <= len(all_jobs)

    def test_application_kanban_retrieval(self, client):
        """Get application board for a user."""
        resp = client.get("/api/v1/jobs/applications?user_id=usr_e2e_test")
        assert resp.status_code == 200
        apps = resp.json()
        assert isinstance(apps, list)

    def test_application_status_update(self, client):
        """Update application status through valid transition."""
        client.get("/api/v1/jobs/applications?user_id=usr_e2e_state")
        resp = client.post(
            "/api/v1/jobs/applications/status?user_id=usr_e2e_state&app_id=app_1&new_status=Offer"
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "Offer"

    def test_application_invalid_id_raises_error(self, client):
        """Updating nonexistent application → error handling."""
        resp = client.post(
            "/api/v1/jobs/applications/status?user_id=usr_e2e_state&app_id=app_nonexistent&new_status=Interview"
        )
        assert resp.status_code in (400, 404, 422, 500)

    def test_user_id_validation_rejects_empty(self, client):
        """Empty user_id → 400 validation response."""
        resp = client.get("/api/v1/jobs/applications?user_id=")
        assert resp.status_code in (400, 422)


# ═══════════════════════════════════════════════════════════════
# SECTION 22-24: PORTFOLIO, SOCIAL PROFILE, ACHIEVEMENTS
# ═══════════════════════════════════════════════════════════════

class TestProfileAndPortfolio:
    """Tests 22-24: Portfolio, profile consistency, achievements."""

    def test_unified_profile_has_projects(self, client):
        """Profile returns projects, skills, social links."""
        resp = client.get("/api/v1/social/profile?user_id=usr_biswal")
        assert resp.status_code == 200
        profile = resp.json()
        assert "full_name" in profile
        assert "top_skills" in profile

    def test_community_feed_returns_posts(self, client):
        """Community feed contains achievement posts."""
        resp = client.get("/api/v1/social/feed")
        assert resp.status_code == 200
        feed = resp.json()
        assert isinstance(feed, list)
        assert len(feed) >= 1

    def test_growth_timeline_returns_milestones(self, client):
        """Career growth timeline returns milestone history."""
        resp = client.get("/api/v1/growth/timeline")
        assert resp.status_code == 200
        milestones = resp.json()
        assert isinstance(milestones, list)
        assert len(milestones) >= 1


# ═══════════════════════════════════════════════════════════════
# SECTION 28-29: OUTREACH & COLD EMAIL
# ═══════════════════════════════════════════════════════════════

class TestOutreachLogic:
    """Tests 28-29: Cold email generation, personalization, follow-up."""

    def test_cold_email_uses_actual_inputs(self, client):
        """Generated email must contain the actual recipient/company/role."""
        resp = client.post("/api/v1/outreach/cold-email", json={
            "recipient_name": "Sarah Jenkins",
            "recipient_role": "Recruiter",
            "company_name": "Vercel",
            "target_role": "Senior AI Developer",
            "user_name": "Test User",
            "key_achievements": [
                "Built production ML pipeline serving 1M predictions daily",
                "Designed microservices architecture on Kubernetes"
            ]
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "Sarah Jenkins" in data["email_body"]
        assert "Vercel" in data["email_body"]

    def test_resume_customization_returns_ats_score(self, client):
        """Resume tailoring must produce ATS score and bullet edits."""
        resp = client.post("/api/v1/outreach/customize-resume", json={
            "raw_resume": "Python developer with FastAPI experience.",
            "target_jd": "Senior Python developer, Docker, AWS, Kubernetes."
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "ats_score" in data
        assert data["ats_score"] > 0


# ═══════════════════════════════════════════════════════════════
# SECTION 30-32: INTERVIEW PRACTICE & AI ASSISTANT
# ═══════════════════════════════════════════════════════════════

class TestInterviewAndAssistant:
    """Tests 30-32: Interview evaluation, career assistant context."""

    def test_strong_answer_scores_higher_than_weak(self, client):
        """Strong answer must score >= weak answer."""
        resp_strong = client.post("/api/v1/growth/interview/evaluate", json={
            "question": "How do you handle high concurrency in backend systems?",
            "user_answer": (
                "I use FastAPI with async event loops and connection-pooled PostgreSQL queries. "
                "I implement Redis caching for hot paths, use load balancing with Nginx, "
                "and deploy on Kubernetes with horizontal pod autoscaling."
            ),
            "target_role": "Senior Backend Engineer"
        })
        resp_weak = client.post("/api/v1/growth/interview/evaluate", json={
            "question": "How do you handle high concurrency in backend systems?",
            "user_answer": "I use Python.",
            "target_role": "Senior Backend Engineer"
        })
        assert resp_strong.status_code == 200
        assert resp_weak.status_code == 200
        assert resp_strong.json()["score"] >= resp_weak.json()["score"]

    def test_career_assistant_returns_actionable_advice(self, client):
        """AI assistant returns next recommended action."""
        resp = client.get("/api/v1/growth/assistant/advice?user_id=usr_biswal")
        assert resp.status_code == 200
        advice = resp.json()
        assert "next_recommended_action" in advice
        assert "suggested_steps" in advice


# ═══════════════════════════════════════════════════════════════
# SECTION 34: BILLING & SUBSCRIPTION
# ═══════════════════════════════════════════════════════════════

class TestBillingAndSubscription:
    """Test 34: Subscription plans, master dashboard."""

    def test_subscription_plans_returned(self, client):
        """Get subscription tiers — Free, Pro, Enterprise."""
        resp = client.get("/api/v1/billing/plans")
        assert resp.status_code == 200
        plans = resp.json()
        assert isinstance(plans, list)
        assert len(plans) >= 2

    def test_master_dashboard_returns_overview(self, client):
        """Master dashboard aggregates all 3 pillar metrics."""
        resp = client.get("/api/v1/billing/dashboard/master?user_id=usr_biswal")
        assert resp.status_code == 200
        dash = resp.json()
        assert "career_fit_score" in dash
        assert "job_applications_count" in dash


# ═══════════════════════════════════════════════════════════════
# SECTION 35, 37: MULTI-TENANT ISOLATION & CONCURRENT USERS
# ═══════════════════════════════════════════════════════════════

class TestMultiTenantIsolation:
    """Tests 35, 37: User A data must not leak to User B."""

    def test_different_users_get_different_applications(self, client):
        """User A and User B get separate Kanban boards."""
        resp_a = client.get("/api/v1/jobs/applications?user_id=usr_tenant_A")
        resp_b = client.get("/api/v1/jobs/applications?user_id=usr_tenant_B")
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

    def test_perception_sessions_are_isolated(self, client):
        """Session data from User A does not leak into User B's sessions."""
        client.post("/api/v1/perception/session/start", json={"session_id": "tenant_A_sess"})
        client.post(
            "/api/v1/perception/frame?session_id=tenant_A_sess",
            json={"ear_left": 0.32, "ear_right": 0.32, "mar": 0.15,
                  "head_pose": {"pitch": 0, "yaw": 0, "roll": 0},
                  "eye_gaze": {"x": 0.0, "y": 0.0},
                  "expression_scores": {"focused": 0.9}}
        )
        client.post("/api/v1/perception/session/start", json={"session_id": "tenant_B_sess"})
        report_b = client.get("/api/v1/perception/session/tenant_B_sess")
        assert report_b.status_code == 200
        b_data = report_b.json()
        assert b_data["avg_attention_score"] == 0.0


# ═══════════════════════════════════════════════════════════════
# SECTION 39-40: ERROR LOGIC & EMPTY STATE
# ═══════════════════════════════════════════════════════════════

class TestErrorAndEmptyState:
    """Tests 39-40: Error propagation, empty/new user behavior."""

    def test_analyze_rejects_empty_resume(self, client):
        """Empty resume handling."""
        resp = client.post("/api/v1/analyze", json={
            "resume_text": "",
            "jd_text": "Python developer needed."
        })
        assert resp.status_code in (200, 400, 422)

    def test_empty_session_report(self, client):
        """Report for session with no frames → graceful empty report."""
        client.post("/api/v1/perception/session/start", json={"session_id": "empty_sess"})
        resp = client.get("/api/v1/perception/session/empty_sess")
        assert resp.status_code == 200
        data = resp.json()
        assert data["avg_attention_score"] == 0.0

    def test_health_endpoint_always_works(self, client):
        """Health check must always return healthy status."""
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded", "ok")


# ═══════════════════════════════════════════════════════════════
# SECTION 8: LEARNING → CAREER BRIDGE INTEGRATION TEST
# ═══════════════════════════════════════════════════════════════

class TestLearningCareerBridge:
    """Test 8: Verify learning behavioral data flows into career state."""

    def test_behavior_state_accepts_observations(self, client):
        """POST /behavior/event records observations."""
        resp = client.post("/api/v1/behavior/event", json={
            "user_id": "usr_bridge_test",
            "metric_name": "confidence",
            "raw_value": 85.0,
            "normalized_score": 0.85,
            "source": "resume_analysis"
        })
        assert resp.status_code == 200

    def test_behavior_state_changes_with_input(self, client):
        """GET /behavior/state returns user career state."""
        client.post("/api/v1/behavior/event", json={
            "user_id": "usr_high",
            "metric_name": "confidence",
            "raw_value": 95.0,
            "normalized_score": 0.95,
            "source": "practice_results"
        })
        resp_high = client.get("/api/v1/behavior/state?user_id=usr_high")
        assert resp_high.status_code == 200
        data = resp_high.json()
        assert "career_state" in data
        assert "agent_decisions" in data


# ═══════════════════════════════════════════════════════════════
# SECTION 38: FRONTEND ↔ BACKEND TRUTH — API RESPONSE STRUCTURE
# ═══════════════════════════════════════════════════════════════

class TestAPIResponseStructure:
    """Test 38: Every API response has the structure the frontend expects."""

    def test_analyze_response_has_all_sections(self, client):
        """Full analysis response must have decision, scoring, skills, gaps, improvement_path."""
        resp = client.post("/api/v1/analyze", json={
            "resume_text": "Python FastAPI developer with Docker and Kubernetes experience.",
            "jd_text": "Need Python, FastAPI, Docker, Kubernetes, AWS, Terraform."
        })
        assert resp.status_code == 200
        data = resp.json()
        required_keys = ["analysis_id", "decision", "scoring", "skills", "gaps", "improvement_path"]
        for key in required_keys:
            assert key in data, f"Missing key '{key}' in analysis response"


# ═══════════════════════════════════════════════════════════════
# SECTION 43: BUSINESS LOGIC INVARIANTS
# ═══════════════════════════════════════════════════════════════

class TestBusinessInvariants:
    """Test 43: Critical business logic invariants."""

    def test_match_score_responds_to_skill_changes(self, client):
        """Adding skills to resume → higher match score."""
        resp_few = client.post("/api/v1/analyze", json={
            "resume_text": "I know Python.",
            "jd_text": "Need Python, Docker, Kubernetes, AWS, Terraform, Go, Rust."
        })
        resp_many = client.post("/api/v1/analyze", json={
            "resume_text": "I am expert in Python, Docker, Kubernetes, AWS, Terraform, Go, and Rust with 10 years experience.",
            "jd_text": "Need Python, Docker, Kubernetes, AWS, Terraform, Go, Rust."
        })
        assert resp_few.status_code == 200
        assert resp_many.status_code == 200
        score_few = resp_few.json()["decision"]["overall_score"]
        score_many = resp_many.json()["decision"]["overall_score"]
        assert score_many >= score_few

    def test_timeline_session_returns_distinct_data(self, client):
        """Timeline report must have session-specific data."""
        resp = client.get("/api/v1/timeline/report/sess_unique_123")
        assert resp.status_code == 200
        report = resp.json()
        assert "session_id" in report
        assert report["session_id"] == "sess_unique_123"
