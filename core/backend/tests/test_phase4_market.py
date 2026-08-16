"""
NeuroSync — Tests for Phase 4 Market & Trajectory Services.
Tests MarketIntelligenceEngine, CareerTrajectoryEngine, AdaptiveScorer, and /market endpoints.
"""
from __future__ import annotations

import pytest
from app.services.market_intelligence_engine import MarketIntelligenceEngine
from app.services.career_trajectory_engine import CareerTrajectoryEngine
from app.services.adaptive_scorer import AdaptiveScorer


def test_market_intelligence_engine():
    engine = MarketIntelligenceEngine()

    demand = engine.get_skill_demand("kubernetes")
    assert demand.demand_trend == "surging"
    assert demand.percent_change > 30.0

    salary = engine.get_salary_signal(["kubernetes", "pytorch"], role="Senior Engineer")
    assert salary.median_salary > 135000.0
    assert "kubernetes" in salary.top_skill_boosts

    velocity = engine.get_hiring_velocity("Backend Developer", "North America")
    assert velocity.openings_count > 0


def test_career_trajectory_engine():
    engine = CareerTrajectoryEngine()
    user_id = "traj_user_1"

    engine.record_snapshot(user_id, skills_count=10, overall_score=60.0)
    engine.record_snapshot(user_id, skills_count=15, overall_score=75.0)

    velocity = engine.compute_growth_velocity(user_id)
    assert velocity.score_improvement_per_month > 0

    projection = engine.predict_readiness(user_id, current_score=75.0, target_role="Tech Lead")
    assert projection.estimated_weeks_to_readiness >= 1


def test_adaptive_scorer():
    scorer = AdaptiveScorer()
    backend_w = scorer.get_role_weights("backend")
    assert backend_w.skill > backend_w.semantic

    score = scorer.calculate_adaptive_score(semantic_score=0.8, skill_overlap_score=80.0, gap_penalty=5.0, role_type="backend")
    assert 0.0 <= score <= 100.0



@pytest.mark.anyio
async def test_market_endpoints(client):
    res_demand = client.get("/api/v1/market/demand?skill=python")
    assert res_demand.status_code == 200
    assert res_demand.json()["skill"] == "python"

    res_salary = client.get("/api/v1/market/salary?skills=python,aws&role=Data%20Engineer")
    assert res_salary.status_code == 200
    assert res_salary.json()["median_salary"] > 0

    res_velocity = client.get("/api/v1/market/velocity?role=DevOps")
    assert res_velocity.status_code == 200

    res_traj = client.get("/api/v1/market/trajectory?user_id=usr_42&current_score=68.5")
    assert res_traj.status_code == 200
    assert "velocity" in res_traj.json()
    assert "projection" in res_traj.json()
