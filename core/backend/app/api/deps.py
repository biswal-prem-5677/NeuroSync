"""
NeuroSync — Dependency Injection.
All service instances created once, injected via FastAPI Depends.
Thread-safe lazy singletons for every core service.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# ─── Singletons (initialized on first call) ──────────────────────────────────
_taxonomy = None
_embedding_store = None
_semantic_model = None
_extractor = None
_gap_analyzer = None
_semantic_engine = None
_intelligence_engine = None

# ─── Analysis Result Cache ────────────────────────────────────────────────────
# Maps analysis_id → Decision object so the feedback endpoint can reference
# the actual decision that was made, not a dummy stub.
_analysis_cache: dict[str, object] = {}
_ANALYSIS_CACHE_MAX = 500


def cache_analysis(analysis_id: str, decision: object) -> None:
    """Store a Decision in the in-memory cache (bounded size)."""
    global _analysis_cache
    if len(_analysis_cache) >= _ANALYSIS_CACHE_MAX:
        # Evict oldest entry (first inserted)
        oldest_key = next(iter(_analysis_cache))
        del _analysis_cache[oldest_key]
    _analysis_cache[analysis_id] = decision


def get_cached_analysis(analysis_id: str) -> Optional[object]:
    """Retrieve a cached Decision by analysis_id, or None."""
    return _analysis_cache.get(analysis_id)


# ─── Service Factories ───────────────────────────────────────────────────────

def get_taxonomy():
    """Return the SkillTaxonomy singleton (thread-safe, loaded from JSON)."""
    from app.utils.skill_taxonomy import SkillTaxonomy
    global _taxonomy
    if _taxonomy is None:
        _taxonomy = SkillTaxonomy()
    return _taxonomy


def get_semantic_model():
    """
    Return the shared SentenceTransformer model.
    This is loaded ONCE and shared across SemanticEngine, SkillExtractor,
    and SkillEmbeddingStore — never loaded multiple times.
    """
    global _semantic_model
    if _semantic_model is None:
        config = get_settings()
        try:
            from sentence_transformers import SentenceTransformer
            _semantic_model = SentenceTransformer(config.embedding_model_name)
            logger.info("SentenceTransformer '%s' loaded", config.embedding_model_name)
        except Exception as e:
            logger.warning("SentenceTransformer unavailable: %s", e)
            _semantic_model = None
    return _semantic_model


def get_embedding_store():
    """
    Return the SkillEmbeddingStore singleton.
    FIXED: Previously passed `config` as first arg — constructor expects `model`.
    Now passes the shared SentenceTransformer model and calls initialize().
    """
    from app.utils.embedding_store import SkillEmbeddingStore
    global _embedding_store
    if _embedding_store is None:
        model = get_semantic_model()
        taxonomy = get_taxonomy()
        config = get_settings()
        _embedding_store = SkillEmbeddingStore(
            model=model,
            taxonomy=taxonomy,
            threshold=config.embedding_discovery_threshold,
        )
        # Build the embedding index for all taxonomy skills
        if model is not None:
            _embedding_store.initialize()
            logger.info("SkillEmbeddingStore initialized with %d skills", taxonomy.skill_count)
        else:
            logger.warning("SkillEmbeddingStore created without model — discovery disabled")
    return _embedding_store


def get_extractor():
    """Return the SkillExtractor singleton (4-layer hybrid extraction)."""
    from app.services.skill_extractor import SkillExtractor
    global _extractor
    if _extractor is None:
        _extractor = SkillExtractor(
            config=get_settings(),
            taxonomy=get_taxonomy(),
            embedding_store=get_embedding_store(),
            semantic_model=get_semantic_model(),
        )
    return _extractor


def get_gap_analyzer():
    """Return the SkillGapAnalyzer singleton."""
    from app.services.skill_gap_analyzer import SkillGapAnalyzer
    global _gap_analyzer
    if _gap_analyzer is None:
        _gap_analyzer = SkillGapAnalyzer(
            config=get_settings(),
            taxonomy=get_taxonomy(),
        )
    return _gap_analyzer


def get_semantic_engine():
    """Return the SemanticEngine singleton (requires SentenceTransformer)."""
    from app.services.semantic_engine import SemanticEngine
    global _semantic_engine
    model = get_semantic_model()
    if _semantic_engine is None and model is not None:
        _semantic_engine = SemanticEngine(
            model=model,
            config=get_settings(),
        )
    return _semantic_engine


def get_intelligence_engine():
    """Return the IntelligenceEngine singleton (central decision brain)."""
    from app.services.intelligence_engine import IntelligenceEngine
    global _intelligence_engine
    if _intelligence_engine is None:
        _intelligence_engine = IntelligenceEngine(
            config=get_settings(),
            taxonomy=get_taxonomy(),
        )
    return _intelligence_engine
