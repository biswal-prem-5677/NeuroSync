"""NeuroSync — Job Search & Application Tracker API Router."""

from fastapi import APIRouter, Query, HTTPException
from typing import Dict, List, Optional

from app.services.job_discovery_engine import (
    job_discovery_engine,
    JobOpportunity,
    ApplicationRecord
)

router = APIRouter(prefix="/jobs", tags=["Job Search & Application Tracker"])


@router.get("/search", response_model=List[JobOpportunity], summary="Search matching job opportunities")
async def search_jobs(query: Optional[str] = Query(None), min_match: float = Query(70.0)):
    """Search for jobs matching user profile & filter score floor."""
    return job_discovery_engine.search_jobs(query, min_match)


@router.get("/applications", response_model=List[ApplicationRecord], summary="Get application Kanban tracking board")
async def get_applications(user_id: str = Query("usr_biswal", description="Authenticated user ID")):
    """Retrieve user's active job application Kanban tracking board."""
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user ID")
    return job_discovery_engine.get_applications(user_id)


@router.post("/applications/status", response_model=ApplicationRecord, summary="Update application status")
async def update_status(user_id: str = Query(...), app_id: str = Query(...), new_status: str = Query(...)):
    """Update job application Kanban status (Applied, Interview, Offer)."""
    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user ID")
    try:
        return job_discovery_engine.update_application_status(user_id, app_id, new_status)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


