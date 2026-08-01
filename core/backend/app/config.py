"""
NeuroSync — Centralized Configuration.
All settings via environment variables. Zero hardcoding.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class ScoringWeights(BaseSettings):
    """Default scoring component weights (learnable via AdaptiveScorer later)."""
    semantic: float = 0.40
    skill: float = 0.35
    gap: float = 0.25


class VersionConfig(BaseSettings):
    """Component version identifiers for reproducibility."""
    engine: str = "1.0.0"
    taxonomy: str = "1.0.0"
    scoring: str = "1.0.0"
    api: str = "v1"


class Settings(BaseSettings):
    """Master configuration — all values overridable via env vars."""

    model_config = {"env_prefix": "NEUROSYNC_", "case_sensitive": False}

    # --- Embedding / NLP Models ---
    embedding_model_name: str = "all-MiniLM-L6-v2"
    spacy_model_name: str = "en_core_web_sm"

    # --- Thresholds ---
    semantic_similarity_threshold: float = 0.75
    skill_semantic_threshold: float = 0.70
    embedding_discovery_threshold: float = 0.65
    max_text_length: int = 50_000
    max_jd_length: int = 20_000

    # --- Extraction Quality (D2 — noise control) ---
    discovery_min_confidence: float = 0.70      # Minimum cosine for a discovery to survive
    alias_absorption_threshold: float = 0.88    # Above this, a "new" term is an alias, not a new skill
    discovery_enabled: bool = True              # Master switch for Layer 4
    #
    # Category inheritance: a discovery used to adopt its nearest neighbour's
    # category unconditionally, which filed "Computer Science" under `ml_ai`
    # from a 0.68 cosine — close enough to notice, nowhere near close enough to
    # classify. Below this bound a discovery is filed as OTHER.
    discovery_category_confidence: float = 0.80
    #
    # Corroboration: a term seen once in one document is not evidence of a new
    # skill. Discoveries are quarantined until they recur in this many distinct
    # documents, so per-document noise expires while real skills accumulate.
    # 1 restores the pre-D2 behaviour of registering on first sighting.
    discovery_promotion_sightings: int = 2

    # --- Requirement Semantics (D1 — what the JD actually asks for) ---
    substitute_credit: float = 0.85             # Credit when a requirement is met by an implied skill
    alternative_credit: float = 1.0             # Credit when one member of an "A or B" group is held
    optional_requirement_weight: float = 0.4    # Weight of "nice to have" JD skills vs required ones

    # --- Signal Calibration (D1 — mapping raw signals onto the 0-100 scale) ---
    # Rationale required by blueprint 02 §11 ("no magic numbers without explanation").
    #
    # Presence floor: blueprint 02 §11 says "Proficiency > Presence" — expert Python
    # beats basic Python. It does NOT say presence is worthless. Multiplying credit
    # by proficiency outright meant a resume covering EVERY requirement at the
    # default inferred proficiency (0.5) scored 0.50, indistinguishable from one
    # covering half the role perfectly. Presence earns this floor of the credit;
    # proficiency modulates the remaining 30%.
    coverage_presence_floor: float = 0.70
    #
    # Semantic band: the semantic composite (02 §4: section_weighted*0.45 +
    # chunk_best*0.25 + skill_alignment*0.30) is compressed by construction —
    # skill_alignment compares against a synthetic phrase and rarely clears 0.35 —
    # so a resume and a JD never approach 1.0 however well they match. Consuming
    # the raw value as a percentage therefore caps every score the system can emit.
    #
    # Bounds measured against pairs of known relatedness (probe, 2026-07-31):
    #   resume vs itself (unreachable ceiling)  0.666
    #   resume vs well-matched backend JD       0.418
    #   resume vs adjacent frontend JD          0.294
    #   resume vs unrelated pastry-chef JD      0.138
    # Floor sits at the unrelated reading, ceiling at the strong-match reading.
    # Values outside the band are clamped.
    semantic_floor: float = 0.15                # At or below -> no semantic credit
    semantic_ceiling: float = 0.45              # At or above -> full semantic credit

    # --- Scoring ---
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    fit_strong: float = 80.0
    fit_good: float = 65.0
    fit_potential: float = 50.0
    fit_weak: float = 35.0

    # --- LLM (optional) ---
    llm_provider: Optional[str] = None          # "gemini" | "openai" | None
    llm_api_key: Optional[str] = None
    llm_model: str = "gemini-pro"
    llm_temperature: float = 0.3

    # --- State Backend (doc 12 §2 Cross-Cutting: State) ---
    # "memory" — in-process, lost on restart. Fine for a probe, wrong for a user.
    # "sql"    — durable. PostgreSQL in production, SQLite for local development.
    #
    # The default is deliberately the volatile one: nothing in this repository
    # should assume a database it was not told about. Production sets both vars.
    state_backend: str = "memory"
    database_url: Optional[str] = None          # e.g. postgresql+psycopg://user:pass@host/neurosync
    database_echo: bool = False                 # log every SQL statement (debug only)

    # --- Feedback ---
    feedback_enabled: bool = True
    feedback_recalibrate_threshold: int = 50    # Recalibrate after N feedbacks

    # --- Performance ---
    extraction_cache_size: int = 1024
    embedding_cache_size: int = 2048
    skill_extraction_timeout_ms: int = 500
    semantic_timeout_ms: int = 300
    llm_timeout_ms: int = 5000

    # --- Versions ---
    versions: VersionConfig = Field(default_factory=VersionConfig)


# Singleton
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Returns cached settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
