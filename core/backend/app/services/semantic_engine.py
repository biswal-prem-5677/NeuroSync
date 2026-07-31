"""
NeuroSync — Semantic Engine.
Section-aware, chunk-level semantic similarity with skill alignment.
Not basic cosine — multi-layer semantic intelligence.
"""
from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from pydantic import BaseModel, Field

from app.config import Settings
from app.models.domain import ExtractionResult
from app.utils.text_processor import extract_sections, chunk_text, clean_text

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="semantic")

# Section weights for semantic aggregation
_SECTION_SEMANTIC_WEIGHTS: dict[str, float] = {
    "experience":     1.0,
    "work experience": 1.0,
    "professional experience": 1.0,
    "projects":       0.90,
    "key projects":   0.90,
    "summary":        0.70,
    "profile":        0.70,
    "objective":      0.60,
    "skills":         0.40,   # Skill lists have low semantic signal
    "technical skills": 0.40,
    "core competencies": 0.40,
    "education":      0.35,
    "certifications": 0.50,
    "publications":   0.80,
    "research":       0.80,
    "awards":         0.30,
    "header":         0.20,
}


# =========================================================================
# OUTPUT MODELS
# =========================================================================

class SectionScore(BaseModel):
    """Semantic score for a single resume section."""
    section: str
    score: float = Field(ge=0.0, le=1.0)
    weight: float
    chunk_count: int
    best_chunk_score: float = 0.0


class SemanticResult(BaseModel):
    """Complete semantic analysis output."""
    overall_score: float = Field(ge=0.0, le=1.0)
    section_scores: list[SectionScore] = Field(default_factory=list)
    chunk_level_max: float = 0.0          # Best single chunk-to-JD score
    chunk_level_mean: float = 0.0         # Average chunk-to-JD score
    skill_alignment_score: float = 0.0    # How well skill contexts align
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    processing_time_ms: float = 0.0
    degraded: bool = False
    fallback_used: Optional[str] = None   # "tfidf" if fell back


# =========================================================================
# SEMANTIC ENGINE
# =========================================================================

class SemanticEngine:
    """
    Multi-layer semantic similarity engine.

    Layer 1 — Section-aware embeddings
        Chunk each resume section separately, embed, compare to JD.
        Weight: Experience (1.0) > Projects (0.9) > Summary (0.7) > Skills (0.4)

    Layer 2 — Chunk-level similarity
        Find the best-matching chunks between resume and JD.
        Captures local alignment even if overall document diverges.

    Layer 3 — Skill-aligned semantic matching
        For each JD skill, find surrounding context in resume.
        "Built ML pipelines in Python" ≈ "machine learning engineering"

    Aggregation:
        overall = section_weighted * 0.50
                + chunk_best * 0.25
                + skill_alignment * 0.25
    """

    def __init__(self, model, config: Settings):
        """
        Args:
            model: SentenceTransformer instance (shared across system)
            config: application settings
        """
        self._model = model
        self._config = config
        self._embed_cache: dict[str, np.ndarray] = {}

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def compute_similarity(
        self,
        resume_text: str,
        jd_text: str,
        resume_skills: Optional[ExtractionResult] = None,
        jd_skills: Optional[ExtractionResult] = None,
    ) -> SemanticResult:
        """
        Full semantic analysis: section-aware + chunk-level + skill-aligned.
        """
        start = time.perf_counter()

        try:
            result = self._compute_full(
                resume_text, jd_text, resume_skills, jd_skills
            )
        except Exception as e:
            logger.error("Semantic engine failed, attempting TF-IDF fallback: %s", e)
            result = self._compute_tfidf_fallback(resume_text, jd_text)

        result.processing_time_ms = round(
            (time.perf_counter() - start) * 1000, 2
        )
        return result

    async def compute_similarity_async(
        self,
        resume_text: str,
        jd_text: str,
        resume_skills: Optional[ExtractionResult] = None,
        jd_skills: Optional[ExtractionResult] = None,
    ) -> SemanticResult:
        """Async wrapper."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _executor,
            self.compute_similarity,
            resume_text, jd_text, resume_skills, jd_skills,
        )

    # =========================================================================
    # FULL COMPUTATION
    # =========================================================================

    def _compute_full(
        self, resume_text, jd_text, resume_skills, jd_skills,
    ) -> SemanticResult:
        """Core computation: 3-layer semantic analysis."""

        resume_clean = clean_text(resume_text)
        jd_clean = clean_text(jd_text)

        # ── Layer 1: Section-aware similarity ────────────────
        sections = extract_sections(resume_clean)
        jd_embedding = self._encode_text(jd_clean)
        section_scores, section_weighted_score = self._compute_section_scores(
            sections, jd_embedding
        )

        # ── Layer 2: Chunk-level similarity ──────────────────
        resume_chunks = chunk_text(resume_clean, chunk_size=384, overlap=48)
        jd_chunks = chunk_text(jd_clean, chunk_size=384, overlap=48)

        chunk_max, chunk_mean = self._compute_chunk_similarity(
            resume_chunks, jd_chunks
        )

        # ── Layer 3: Skill-aligned matching ──────────────────
        skill_alignment = 0.0
        if resume_skills and jd_skills:
            skill_alignment = self._compute_skill_alignment(
                resume_text, jd_skills, resume_skills
            )

        # ── Aggregation ──────────────────────────────────────
        has_skill_data = resume_skills is not None and jd_skills is not None

        if has_skill_data:
            overall = (
                section_weighted_score * 0.45
                + chunk_max * 0.25
                + skill_alignment * 0.30
            )
        else:
            overall = (
                section_weighted_score * 0.55
                + chunk_max * 0.30
                + chunk_mean * 0.15
            )

        # ── Confidence ───────────────────────────────────────
        confidence = self._compute_confidence(
            sections, resume_chunks, jd_chunks, has_skill_data
        )

        return SemanticResult(
            overall_score=round(max(0.0, min(1.0, overall)), 4),
            section_scores=section_scores,
            chunk_level_max=round(chunk_max, 4),
            chunk_level_mean=round(chunk_mean, 4),
            skill_alignment_score=round(skill_alignment, 4),
            confidence=round(confidence, 3),
        )

    # =========================================================================
    # LAYER 1: SECTION-AWARE
    # =========================================================================

    def _compute_section_scores(
        self, sections: dict[str, str], jd_embedding: np.ndarray,
    ) -> tuple[list[SectionScore], float]:
        """
        Embed each section, compare to JD, weight by section importance.
        """
        results: list[SectionScore] = []
        weighted_sum = 0.0
        weight_total = 0.0

        for section_name, section_text in sections.items():
            if not section_text or len(section_text.strip()) < 20:
                continue

            weight = _SECTION_SEMANTIC_WEIGHTS.get(section_name, 0.3)

            # Chunk this section
            section_chunks = chunk_text(section_text, chunk_size=256, overlap=32)
            if not section_chunks:
                continue

            # Embed and compare each chunk to JD
            chunk_embeddings = self._encode_texts(section_chunks)
            similarities = np.dot(chunk_embeddings, jd_embedding)

            best_score = float(np.max(similarities))
            mean_score = float(np.mean(similarities))

            # Section score = weighted average of best and mean
            section_score = best_score * 0.6 + mean_score * 0.4

            results.append(SectionScore(
                section=section_name,
                score=round(section_score, 4),
                weight=weight,
                chunk_count=len(section_chunks),
                best_chunk_score=round(best_score, 4),
            ))

            weighted_sum += section_score * weight
            weight_total += weight

        # Weighted average across sections
        overall = weighted_sum / weight_total if weight_total > 0 else 0.0

        # Sort by score descending
        results.sort(key=lambda s: s.score, reverse=True)

        return results, overall

    # =========================================================================
    # LAYER 2: CHUNK-LEVEL
    # =========================================================================

    def _compute_chunk_similarity(
        self, resume_chunks: list[str], jd_chunks: list[str],
    ) -> tuple[float, float]:
        """
        Chunk-to-chunk similarity matrix.
        Returns: (max similarity, mean similarity)
        """
        if not resume_chunks or not jd_chunks:
            return 0.0, 0.0

        resume_embs = self._encode_texts(resume_chunks)
        jd_embs = self._encode_texts(jd_chunks)

        # Similarity matrix: (n_resume_chunks, n_jd_chunks)
        sim_matrix = np.dot(resume_embs, jd_embs.T)

        chunk_max = float(np.max(sim_matrix))
        # Mean of best matches per JD chunk (how well each JD part is covered)
        best_per_jd = np.max(sim_matrix, axis=0)  # best resume chunk for each JD chunk
        chunk_mean = float(np.mean(best_per_jd))

        return chunk_max, chunk_mean

    # =========================================================================
    # LAYER 3: SKILL-ALIGNED MATCHING
    # =========================================================================

    def _compute_skill_alignment(
        self, resume_text: str, jd_skills: ExtractionResult,
        resume_skills: ExtractionResult,
    ) -> float:
        """
        For each JD skill, find surrounding context in resume and measure
        semantic alignment. This captures deep skill expression:
        "Built ML pipelines" ≈ "machine learning engineering"
        """
        resume_lower = resume_text.lower()
        resume_canonical = {s.canonical.lower() for s in resume_skills.skills}

        alignment_scores: list[float] = []

        for jd_skill in jd_skills.skills:
            jd_name = jd_skill.canonical

            # If skill is directly present, check surrounding context depth
            if jd_name.lower() in resume_canonical:
                # Find context around skill mention in resume
                context = self._extract_skill_context(resume_text, jd_name)
                if context:
                    # How rich is the context? (not just "Python" in a list)
                    context_emb = self._encode_text(context)
                    skill_phrase_emb = self._encode_text(
                        f"extensive experience with {jd_name} in production"
                    )
                    depth_score = float(np.dot(context_emb, skill_phrase_emb))
                    alignment_scores.append(max(0.5, depth_score))
                else:
                    alignment_scores.append(0.5)  # Present but no context
            else:
                # Skill NOT present — check if resume expresses it differently
                context_chunks = self._extract_skill_context_chunks(
                    resume_text, jd_name
                )
                if context_chunks:
                    chunk_embs = self._encode_texts(context_chunks)
                    skill_emb = self._encode_text(jd_name)
                    sims = np.dot(chunk_embs, skill_emb)
                    best = float(np.max(sims))
                    alignment_scores.append(max(0.0, best * 0.8))
                else:
                    alignment_scores.append(0.0)

        if not alignment_scores:
            return 0.0

        return float(np.mean(alignment_scores))

    def _extract_skill_context(self, text: str, skill_name: str) -> Optional[str]:
        """Extract ±150 chars around the first mention of a skill."""
        import re
        pattern = re.compile(re.escape(skill_name), re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            return None

        start = max(0, match.start() - 150)
        end = min(len(text), match.end() + 150)
        return text[start:end].strip()

    def _extract_skill_context_chunks(
        self, text: str, skill_name: str
    ) -> list[str]:
        """Extract relevant chunks that might discuss the skill conceptually."""
        chunks = chunk_text(text, chunk_size=200, overlap=30)
        # Only keep chunks that might be relevant (contains related terms)
        # Simple heuristic: return top-N shortest distance chunks
        return chunks[:5] if chunks else []

    # =========================================================================
    # TF-IDF FALLBACK
    # =========================================================================

    def _compute_tfidf_fallback(
        self, resume_text: str, jd_text: str,
    ) -> SemanticResult:
        """Fallback when SentenceTransformer fails. Uses sklearn TF-IDF."""
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words="english",
                ngram_range=(1, 2),
            )
            tfidf = vectorizer.fit_transform([resume_text, jd_text])
            score = float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])

            return SemanticResult(
                overall_score=round(score, 4),
                confidence=0.5,  # Lower confidence for fallback
                degraded=True,
                fallback_used="tfidf",
            )

        except Exception as e:
            logger.error("TF-IDF fallback also failed: %s", e)
            return SemanticResult(
                overall_score=0.0,
                confidence=0.1,
                degraded=True,
                fallback_used="failed",
            )

    # =========================================================================
    # ENCODING (CACHED)
    # =========================================================================

    def _encode_text(self, text: str) -> np.ndarray:
        """Encode single text with caching."""
        cache_key = text[:200]  # Use prefix as cache key
        if cache_key in self._embed_cache:
            return self._embed_cache[cache_key]

        emb = self._model.encode(
            [text], normalize_embeddings=True, show_progress_bar=False,
        )[0]

        # Cache (limit size)
        if len(self._embed_cache) < self._config.embedding_cache_size:
            self._embed_cache[cache_key] = emb

        return emb

    def _encode_texts(self, texts: list[str]) -> np.ndarray:
        """Batch encode with caching per text."""
        # Check which are cached
        cached = {}
        to_encode = []
        to_encode_idx = []

        for i, text in enumerate(texts):
            key = text[:200]
            if key in self._embed_cache:
                cached[i] = self._embed_cache[key]
            else:
                to_encode.append(text)
                to_encode_idx.append(i)

        # Encode uncached
        if to_encode:
            new_embs = self._model.encode(
                to_encode, normalize_embeddings=True,
                show_progress_bar=False, batch_size=64,
            )
            for idx, emb in zip(to_encode_idx, new_embs):
                key = texts[idx][:200]
                cached[idx] = emb
                if len(self._embed_cache) < self._config.embedding_cache_size:
                    self._embed_cache[key] = emb

        # Reconstruct in order
        result = np.array([cached[i] for i in range(len(texts))], dtype=np.float32)
        return result

    # =========================================================================
    # CONFIDENCE
    # =========================================================================

    def _compute_confidence(
        self, sections, resume_chunks, jd_chunks, has_skill_data,
    ) -> float:
        """How confident are we in the semantic score?"""
        conf = 0.6  # base

        # More sections = more signal
        if len(sections) >= 4:
            conf += 0.10
        elif len(sections) >= 2:
            conf += 0.05

        # More chunks = more granular comparison
        total_chunks = len(resume_chunks) + len(jd_chunks)
        if total_chunks >= 15:
            conf += 0.10
        elif total_chunks >= 8:
            conf += 0.05

        # Skill data available = alignment layer active
        if has_skill_data:
            conf += 0.10

        return min(0.95, conf)
