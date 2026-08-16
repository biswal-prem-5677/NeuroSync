"""NeuroSync — Achievement Timeline & AI Career Assistant Router."""

from fastapi import APIRouter
from typing import List
from app.services.achievement_growth_engine import (
    achievement_growth_engine,
    CareerMilestone,
    InterviewPracticeRequest,
    InterviewPracticeResponse,
    CareerAssistantAdvice
)

router = APIRouter(prefix="/growth", tags=["Achievement Timeline & AI Career Assistant"])


@router.get("/timeline", response_model=List[CareerMilestone], summary="Get career growth timeline")
async def get_growth_timeline(user_id: str = "usr_biswal"):
    """Retrieve chronological growth timeline of skills, projects & certifications."""
    return achievement_growth_engine.get_growth_timeline(user_id)


@router.post("/interview/evaluate", response_model=InterviewPracticeResponse, summary="Evaluate interview answer")
async def evaluate_interview(payload: InterviewPracticeRequest):
    """Evaluate practice interview response and provide score & feedback."""
    return achievement_growth_engine.evaluate_interview_answer(payload)


@router.get("/assistant/advice", response_model=CareerAssistantAdvice, summary="Get AI career assistant next steps")
async def get_assistant_advice(user_id: str = "usr_biswal"):
    """Get personalized AI Career Assistant advice & next step checklist."""
    return achievement_growth_engine.get_assistant_advice(user_id)
