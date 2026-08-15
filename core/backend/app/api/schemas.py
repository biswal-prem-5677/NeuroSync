"""
NeuroSync — API Request/Response Models.
Clean data contracts for the API layer. Separate from internal domain objects.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from app.utils.text_processor import clean_text, compute_alpha_ratio


# =========================================================================
# REQUESTS
# =========================================================================

class AnalyzeRequest(BaseModel):
    """POST /api/v1/analyze — full resume-to-JD analysis."""
    resume_text: str = Field(
        ..., min_length=50, max_length=50_000,
        description="Raw resume text (plaintext)",
    )
    jd_text: str = Field(
        ..., min_length=20, max_length=20_000,
        description="Raw job description text",
    )
    include_simulations: bool = Field(
        default=True,
        description="Include what-if improvement simulations",
    )
    include_evidence: bool = Field(
        default=True,
        description="Include full evidence chain in response",
    )

    @field_validator("resume_text", "jd_text")
    @classmethod
    def validate_and_sanitize_text(cls, v: str, info) -> str:
        cleaned = clean_text(v)
        if len(cleaned) < (50 if info.field_name == "resume_text" else 20):
            raise ValueError(f"{info.field_name} is too short after stripping control characters and HTML tags")
        alpha_ratio = compute_alpha_ratio(cleaned)
        if alpha_ratio < 0.3:
            raise ValueError(f"{info.field_name} appears to be binary, encoded, or non-text junk content")
        return cleaned



class FeedbackRequest(BaseModel):
    """POST /api/v1/feedback — record outcome feedback."""
    analysis_id: str = Field(..., description="ID from the analysis response")
    outcome: str = Field(
        ..., pattern="^(hired|rejected|interview|ghosted|user_disagrees)$",
        description="What happened after applying",
    )
    notes: Optional[str] = Field(default=None, max_length=1000)


class QuickScoreRequest(BaseModel):
    """POST /api/v1/quick-score — lightweight score only."""
    resume_text: str = Field(..., min_length=50, max_length=50_000)
    jd_text: str = Field(..., min_length=20, max_length=20_000)
