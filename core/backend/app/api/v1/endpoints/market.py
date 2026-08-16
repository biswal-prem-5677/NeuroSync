"""
NeuroSync — Market & Trajectory API Endpoints (Phase 4).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import (
    get_market_intelligence_engine,
    get_career_trajectory_engine,
)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/demand", summary="Get market demand signal for a skill")
async def get_demand(skill: str = Query(..., description="Skill name")):
    market_engine = get_market_intelligence_engine()
    return market_engine.get_skill_demand(skill)


@router.get("/salary", summary="Estimate salary range and skill boosts")
async def get_salary(
    skills: str = Query("", description="Comma-separated skill list"),
    role: str = Query("Software Engineer", description="Target role"),
):
    market_engine = get_market_intelligence_engine()
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    return market_engine.get_salary_signal(skill_list, role)


@router.get("/velocity", summary="Get regional hiring velocity for a role")
async def get_velocity(
    role: str = Query("Software Engineer", description="Target role"),
    region: str = Query("Global/Remote", description="Region"),
):
    market_engine = get_market_intelligence_engine()
    return market_engine.get_hiring_velocity(role, region)


@router.get("/trajectory", summary="Get career growth trajectory & time to readiness")
async def get_trajectory(
    user_id: str = Query(..., description="User ID"),
    current_score: float = Query(70.0, description="Current overall score"),
    target_role: str = Query("Software Engineer", description="Target role"),
):
    traj_engine = get_career_trajectory_engine()
    velocity = traj_engine.compute_growth_velocity(user_id)
    projection = traj_engine.predict_readiness(user_id, current_score, target_role)
    return {
        "velocity": velocity,
        "projection": projection,
    }
