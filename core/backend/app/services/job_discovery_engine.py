"""NeuroSync — Job Search, Matching & Application Kanban Engine (Pillar 3).

Searches curated career opportunities, evaluates profile-to-job suitability,
tracks active application Kanban states (Applied, Interview, Offer, Rejected),
and displays company discovery signals.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class JobOpportunity(BaseModel):
    id: str
    company_name: str
    role_title: str
    location: str
    remote_type: str  # Remote, Hybrid, Onsite
    salary_range: str
    match_score: float
    required_skills: List[str]
    posted_days_ago: int
    apply_url: str


class ApplicationRecord(BaseModel):
    id: str
    job_id: str
    company_name: str
    role_title: str
    status: str  # Saved, Applied, Interview, Offer, Rejected
    applied_date: str
    notes: str
    match_score: float


class JobDiscoveryEngine:
    """Manages personalized job matching, company discovery, and application Kanban tracking."""

    def __init__(self):
        self._jobs: List[JobOpportunity] = [
            JobOpportunity(
                id="job_101",
                company_name="Stripe",
                role_title="Senior Infrastructure Engineer",
                location="San Francisco, CA / Remote",
                remote_type="Remote",
                salary_range="$185,000 - $240,000",
                match_score=88.5,
                required_skills=["Python", "Go", "Kubernetes", "AWS", "Terraform", "Distributed Systems"],
                posted_days_ago=2,
                apply_url="https://stripe.com/jobs/infra-sr"
            ),
            JobOpportunity(
                id="job_102",
                company_name="Vercel",
                role_title="Senior Full Stack AI Developer",
                location="New York, NY / Remote",
                remote_type="Remote",
                salary_range="$170,000 - $220,000",
                match_score=92.0,
                required_skills=["React", "TypeScript", "Python", "FastAPI", "Next.js", "Docker"],
                posted_days_ago=1,
                apply_url="https://vercel.com/careers/ai-dev"
            ),
            JobOpportunity(
                id="job_103",
                company_name="Datadog",
                role_title="Backend Systems Engineer — Data Pipelines",
                location="Boston, MA / Remote",
                remote_type="Hybrid",
                salary_range="$165,000 - $210,000",
                match_score=84.0,
                required_skills=["Python", "Kafka", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
                posted_days_ago=4,
                apply_url="https://datadoghq.com/careers/backend"
            )
        ]

        self._applications: Dict[str, List[ApplicationRecord]] = {}

    def search_jobs(self, query: Optional[str] = None, min_match: float = 70.0) -> List[JobOpportunity]:
        """Filter jobs matching student query and match score floor."""
        if not query:
            return [j for j in self._jobs if j.match_score >= min_match]

        q = query.lower()
        return [
            j for j in self._jobs
            if (q in j.role_title.lower() or q in j.company_name.lower() or any(q in s.lower() for s in j.required_skills))
        ]

    def get_applications(self, user_id: str) -> List[ApplicationRecord]:
        """Retrieve user's active job application Kanban tracking board."""
        if user_id not in self._applications:
            self._applications[user_id] = [
                ApplicationRecord(
                    id="app_1",
                    job_id="job_102",
                    company_name="Vercel",
                    role_title="Senior Full Stack AI Developer",
                    status="Interview",
                    applied_date="2026-08-10",
                    notes="Technical interview scheduled for Thursday with Tech Lead.",
                    match_score=92.0
                ),
                ApplicationRecord(
                    id="app_2",
                    job_id="job_101",
                    company_name="Stripe",
                    role_title="Senior Infrastructure Engineer",
                    status="Applied",
                    applied_date="2026-08-12",
                    notes="Custom tailored resume uploaded; cold email sent to recruiter.",
                    match_score=88.5
                )
            ]

        return self._applications[user_id]

    def update_application_status(self, user_id: str, app_id: str, new_status: str) -> ApplicationRecord:
        """Update Kanban column status (Applied -> Interview -> Offer)."""
        apps = self.get_applications(user_id)
        for app in apps:
            if app.id == app_id:
                app.status = new_status
                return app
        raise ValueError(f"Application {app_id} not found")


job_discovery_engine = JobDiscoveryEngine()
