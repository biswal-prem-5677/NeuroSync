"""
NeuroSync — Dependency Injection.
All service instances created once, injected via FastAPI Depends.
Thread-safe lazy singletons for every core service.
"""
from __future__ import annotations

import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

# ─── Singletons (initialized on first call) ──────────────────────────────────
_taxonomy = None
_embedding_store = None
_semantic_model = None
_extractor = None
_gap_analyzer = None
_semantic_engine = None
_intelligence_engine = None
_state_backend = None
_feedback_processor = None
_human_state_engine = None
_agent_decision_engine = None
_market_intelligence_engine = None
_career_trajectory_engine = None
_adaptive_scorer = None
_llm_enhancer = None





# ─── State Backend ───────────────────────────────────────────────────────────
# Doc 12 §4 Rule 5. This replaced two module-level dicts — an analysis cache
# here and a feedback list inside IntelligenceEngine — that silently discarded
# every recorded outcome on restart (doc 15 R3).

def get_state_backend():
    """Return the StateBackend singleton chosen by `NEUROSYNC_STATE_BACKEND`."""
    global _state_backend
    if _state_backend is not None:
        return _state_backend

    config = get_settings()
    choice = (config.state_backend or "memory").strip().lower()

    if choice == "sql":
        if not config.database_url:
            raise RuntimeError(
                "NEUROSYNC_STATE_BACKEND=sql requires NEUROSYNC_DATABASE_URL. "
                "Refusing to fall back to in-memory state: a silent downgrade "
                "here loses user data without anyone noticing."
            )
        from app.state.sql_state import SqlState
        _state_backend = SqlState(
            database_url=config.database_url,
            recalibrate_at=config.feedback_recalibrate_threshold,
            echo=config.database_echo,
        )
    elif choice == "memory":
        from app.state.memory_state import MemoryState
        _state_backend = MemoryState(
            recalibrate_at=config.feedback_recalibrate_threshold,
        )
    else:
        raise ValueError(
            f"Unknown NEUROSYNC_STATE_BACKEND '{config.state_backend}' "
            f"(expected 'memory' or 'sql')"
        )

    _state_backend.initialize()
    return _state_backend


def set_state_backend(backend) -> None:
    """
    Install a StateBackend directly, bypassing config.

    For probes and tests that need a throwaway database. Must be called before
    the first `get_state_backend()`; the caller owns `initialize()`/`close()`.
    """
    global _state_backend, _intelligence_engine
    _state_backend = backend
    _intelligence_engine = None      # rebuilt against the new backend


def close_state_backend() -> None:
    """Release the state backend at shutdown."""
    global _state_backend, _intelligence_engine
    if _state_backend is not None:
        _state_backend.close()
        _state_backend = None
        _intelligence_engine = None


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
    """Return the IntelligenceEngine singleton (central decision brain).

    Now receives all pipeline services so it can orchestrate the full
    analysis pipeline (doc 12 Rule 1), not just the decision step.
    """
    from app.services.intelligence_engine import IntelligenceEngine
    global _intelligence_engine
    if _intelligence_engine is None:
        _intelligence_engine = IntelligenceEngine(
            config=get_settings(),
            taxonomy=get_taxonomy(),
            state=get_state_backend(),
            extractor=get_extractor(),
            gap_analyzer=get_gap_analyzer(),
            semantic_engine=get_semantic_engine(),
        )
    return _intelligence_engine


def get_feedback_processor():
    """Return the FeedbackProcessor singleton (Phase 3.3 learning loop)."""
    from app.services.feedback_processor import FeedbackProcessor
    global _feedback_processor
    if _feedback_processor is None:
        _feedback_processor = FeedbackProcessor(
            config=get_settings(),
            taxonomy=get_taxonomy(),
        )
    return _feedback_processor


def get_human_state_engine():
    """Return the HumanStateEngine singleton (Phase 3.5 human intelligence)."""
    from app.services.human_state_engine import HumanStateEngine
    global _human_state_engine
    if _human_state_engine is None:
        _human_state_engine = HumanStateEngine()
    return _human_state_engine


def get_agent_decision_engine():
    """Return the AgentDecisionEngine singleton (Phase 3.5 career decisions)."""
    from app.services.agent_decision_engine import AgentDecisionEngine
    global _agent_decision_engine
    if _agent_decision_engine is None:
        _agent_decision_engine = AgentDecisionEngine()
    return _agent_decision_engine


def get_market_intelligence_engine():
    """Return the MarketIntelligenceEngine singleton (Phase 4.1 market data)."""
    from app.services.market_intelligence_engine import MarketIntelligenceEngine
    global _market_intelligence_engine
    if _market_intelligence_engine is None:
        _market_intelligence_engine = MarketIntelligenceEngine()
    return _market_intelligence_engine


def get_career_trajectory_engine():
    """Return the CareerTrajectoryEngine singleton (Phase 4.2 trajectory forecasting)."""
    from app.services.career_trajectory_engine import CareerTrajectoryEngine
    global _career_trajectory_engine
    if _career_trajectory_engine is None:
        _career_trajectory_engine = CareerTrajectoryEngine()
    return _career_trajectory_engine


def get_adaptive_scorer():
    """Return the AdaptiveScorer singleton (Phase 4.3 per-role weights)."""
    from app.services.adaptive_scorer import AdaptiveScorer
    global _adaptive_scorer
    if _adaptive_scorer is None:
        _adaptive_scorer = AdaptiveScorer()
    return _adaptive_scorer


def get_llm_enhancer():
    """Return the LLMEnhancer singleton (Phase 4.4 optional LLM refinement)."""
    from app.services.llm_enhancer import LLMEnhancer
    global _llm_enhancer
    if _llm_enhancer is None:
        _llm_enhancer = LLMEnhancer(get_settings())
    return _llm_enhancer



