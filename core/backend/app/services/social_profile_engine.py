"""NeuroSync — Unified Social, Identity & Portfolio Engine (Pillar 3).

Manages user professional identity, achievement feed, portfolio case studies,
GitHub repo integration, and public showcase URLs.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class SocialLink(BaseModel):
    platform: str
    url: str
    username: str


class AchievementPost(BaseModel):
    id: str
    user_id: str
    user_name: str
    title: str
    category: str  # project, certification, hackathon, milestone
    description: str
    skills_used: List[str]
    likes_count: int = 0
    created_at: float


class PortfolioProject(BaseModel):
    id: str
    title: str
    tagline: str
    description: str
    tech_stack: List[str]
    github_url: str
    demo_url: Optional[str] = None
    featured: bool = True


class UnifiedProfile(BaseModel):
    user_id: str
    full_name: str
    headline: str
    bio: str
    location: str
    social_links: List[SocialLink]
    top_skills: List[str]
    projects: List[PortfolioProject]
    achievements_count: int
    public_profile_url: str
    badge_title: str


class SocialProfileEngine:
    """Manages public achievement feed, social profiles, and AI portfolio generation."""

    def __init__(self):
        self._profiles: Dict[str, UnifiedProfile] = {}
        self._feed: List[AchievementPost] = [
            AchievementPost(
                id="post_1",
                user_id="usr_biswal",
                user_name="Priyabrata Biswal",
                title="Built NeuroSync — AI Emotion & Career Decision Platform",
                category="project",
                description="Deployed full-stack local AI intelligence engine with 4-layer hybrid skill extraction, What-If simulation playground, and camera attention monitor.",
                skills_used=["Python", "FastAPI", "React", "PyTorch", "spaCy", "Docker"],
                likes_count=42,
                created_at=1771147200.0
            ),
            AchievementPost(
                id="post_2",
                user_id="usr_alex",
                user_name="Alex Chen",
                title="AWS Certified Solutions Architect — Associate",
                category="certification",
                description="Passed AWS SAA-C03 certification with 890/1000 score after 3 weeks of intensive study using NeuroSync revision queue.",
                skills_used=["AWS", "Cloud Architecture", "System Design"],
                likes_count=28,
                created_at=1771060800.0
            )
        ]

    def get_profile(self, user_id: str) -> UnifiedProfile:
        """Retrieve or construct user's unified public identity profile."""
        if user_id in self._profiles:
            return self._profiles[user_id]

        profile = UnifiedProfile(
            user_id=user_id,
            full_name="Priyabrata Biswal",
            headline="Senior Software Engineer | AI & Cloud Systems",
            bio="Building high-throughput distributed engines, local-first ML pipelines, and emotion-adaptive software systems.",
            location="Bengaluru, India",
            social_links=[
                SocialLink(platform="GitHub", url="https://github.com/biswal-prem-5677", username="biswal-prem-5677"),
                SocialLink(platform="LinkedIn", url="https://linkedin.com/in/priyabrata-biswal", username="priyabrata-biswal")
            ],
            top_skills=["Python", "FastAPI", "React", "Docker", "Kubernetes", "AWS", "PyTorch", "PostgreSQL"],
            projects=[
                PortfolioProject(
                    id="proj_1",
                    title="NeuroSync Intelligence Engine",
                    tagline="Multi-factor Career & Emotion Decision Platform",
                    description="Self-contained local AI platform running PyTorch embeddings & spaCy NER for skill gap analysis and what-if score simulations.",
                    tech_stack=["Python", "FastAPI", "React", "PyTorch", "Docker"],
                    github_url="https://github.com/biswal-prem-5677/NeuroSync",
                    demo_url="https://neurosync.onrender.com"
                )
            ],
            achievements_count=12,
            public_profile_url=f"https://neurosync.ai/p/{user_id}",
            badge_title="Top 1% AI Systems Contributor"
        )
        self._profiles[user_id] = profile
        return profile

    def get_community_feed(self) -> List[AchievementPost]:
        """Return public achievement community feed."""
        return self._feed


    def create_post(self, post: AchievementPost) -> AchievementPost:
        """Publish a new achievement to the public feed."""
        self._feed.insert(0, post)
        return post


social_profile_engine = SocialProfileEngine()
