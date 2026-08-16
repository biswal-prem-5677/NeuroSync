"""NeuroSync — Recruiter Cold Email & Resume Customizer API Router."""

from fastapi import APIRouter
from app.services.outreach_engine import (
    outreach_engine,
    ColdEmailRequest,
    ColdEmailResponse,
    ResumeCustomizationRequest,
    ResumeCustomizationResponse
)

router = APIRouter(prefix="/outreach", tags=["Cold Email & Resume Customizer"])


@router.post("/cold-email", response_model=ColdEmailResponse, summary="Generate recruiter cold email")
async def generate_cold_email(payload: ColdEmailRequest):
    """Generate high-conversion recruiter cold email & follow-up sequence."""
    return outreach_engine.generate_cold_email(payload)


@router.post("/customize-resume", response_model=ResumeCustomizationResponse, summary="Tailor resume to JD")
async def customize_resume(payload: ResumeCustomizationRequest):
    """Tailor resume bullet points to JD and compute ATS match score."""
    return outreach_engine.customize_resume(payload)
