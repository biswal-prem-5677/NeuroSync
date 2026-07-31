"""
NeuroSync — Skill Embedding Store.
Pre-computed embedding cache for dynamic skill intelligence.
Enables: semantic skill matching, unknown skill discovery, runtime taxonomy expansion.
"""
from __future__ import annotations

import logging
import threading
import time
from functools import lru_cache
from typing import Optional

import numpy as np

from app.models.domain import Skill
from app.models.enums import SkillCategory, MatchMethod
from app.utils.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)


class SkillEmbeddingStore:
    """
    Embeds all taxonomy skills at startup using the shared SentenceTransformer.
    Provides:
    1. Semantic skill matching (cosine similarity between skill embeddings)
    2. Unknown skill discovery (find terms near known skill clusters)
    3. Dynamic taxonomy expansion (register new skills found via proximity)
    """

    def __init__(self, model, taxonomy: SkillTaxonomy, threshold: float = 0.70):
        """
        Args:
            model: SentenceTransformer instance (shared with SemanticEngine)
            taxonomy: SkillTaxonomy singleton
            threshold: minimum cosine similarity to consider a match
        """
        self._model = model
        self._taxonomy = taxonomy
        self._threshold = threshold
        self._embeddings: dict[str, np.ndarray] = {}   # canonical → embedding vector
        self._canonical_list: list[str] = []            # ordered list for batch ops
        self._embedding_matrix: Optional[np.ndarray] = None  # (N, dim) matrix
        self._lock = threading.Lock()
        self._ready = False

    def initialize(self) -> None:
        """
        Build embedding index for all taxonomy skills.
        Call this during app startup (lifespan handler).
        """
        start = time.perf_counter()

        try:
            all_names = self._taxonomy.get_all_canonical_names()
            if not all_names:
                logger.warning("No skills in taxonomy — embedding store will be empty")
                self._ready = True
                return

            # Batch encode all skill names
            embeddings = self._model.encode(
                all_names,
                batch_size=128,
                show_progress_bar=False,
                normalize_embeddings=True,
            )

            with self._lock:
                self._canonical_list = list(all_names)
                self._embedding_matrix = np.array(embeddings, dtype=np.float32)
                for i, name in enumerate(all_names):
                    self._embeddings[name.lower()] = self._embedding_matrix[i]

            elapsed = (time.perf_counter() - start) * 1000
            logger.info("Embedding store initialized: %d skills indexed in %.1fms", len(all_names), elapsed)
            self._ready = True

        except Exception as e:
            logger.error("Failed to initialize embedding store: %s", e)
            self._ready = True  # Mark ready even on failure — degraded mode

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def has_embeddings(self) -> bool:
        return self._embedding_matrix is not None and len(self._embedding_matrix) > 0

    def find_nearest_skill(self, text: str, threshold: Optional[float] = None) -> Optional[tuple[str, float]]:
        """
        Map unknown text to nearest known skill via embedding cosine similarity.

        Returns:
            (canonical_name, similarity_score) if above threshold, else None
        """
        if not self.has_embeddings:
            return None

        threshold = threshold or self._threshold

        try:
            # Encode the query text
            query_embedding = self._model.encode(
                [text],
                normalize_embeddings=True,
                show_progress_bar=False,
            )[0]

            # Compute cosine similarity against all skills
            with self._lock:
                similarities = np.dot(self._embedding_matrix, query_embedding)
                best_idx = int(np.argmax(similarities))
                best_score = float(similarities[best_idx])

            if best_score >= threshold:
                return (self._canonical_list[best_idx], best_score)

            return None

        except Exception as e:
            logger.error("find_nearest_skill failed for '%s': %s", text, e)
            return None

    def compute_skill_similarity(self, skill_a: str, skill_b: str) -> float:
        """
        Compute cosine similarity between two skill names.
        Returns 0.0 if either skill is not embedded.
        """
        if not self.has_embeddings:
            return 0.0

        key_a = skill_a.lower()
        key_b = skill_b.lower()

        with self._lock:
            emb_a = self._embeddings.get(key_a)
            emb_b = self._embeddings.get(key_b)

        if emb_a is None or emb_b is None:
            # Encode on-the-fly for unknown skills
            try:
                texts = []
                if emb_a is None:
                    texts.append(skill_a)
                if emb_b is None:
                    texts.append(skill_b)

                new_embs = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
                idx = 0
                if emb_a is None:
                    emb_a = new_embs[idx]
                    idx += 1
                if emb_b is None:
                    emb_b = new_embs[idx]
            except Exception:
                return 0.0

        return float(np.dot(emb_a, emb_b))

    def discover_unknown_skills(
        self,
        text_chunks: list[str],
        known_skills: set[str],
        threshold: Optional[float] = None,
    ) -> list[Skill]:
        """
        Find technical terms in text that are NOT in taxonomy but are
        semantically close to known skill clusters.

        Args:
            text_chunks: text fragments to scan
            known_skills: skills already extracted (skip these)
            threshold: similarity threshold for discovery

        Returns:
            List of discovered Skill objects with matched_by=EMBEDDING_DISCOVERY
        """
        if not self.has_embeddings:
            return []

        threshold = threshold or self._threshold * 0.9  # Slightly lower for discovery
        discovered: list[Skill] = []
        seen: set[str] = set()

        for chunk in text_chunks:
            # Extract candidate terms (2-3 word technical-looking phrases)
            candidates = self._extract_candidate_terms(chunk)

            for candidate in candidates:
                norm = candidate.lower().strip()

                # Skip if already known or already discovered
                if norm in known_skills or norm in seen:
                    continue

                # Skip if it's already in taxonomy
                if self._taxonomy.resolve_skill(norm):
                    continue

                # Check embedding proximity
                result = self.find_nearest_skill(candidate, threshold=threshold)
                if result:
                    nearest_canonical, similarity = result
                    category = self._taxonomy.get_category(nearest_canonical)

                    skill = Skill(
                        name=candidate,
                        canonical=candidate.title(),
                        category=category,
                        confidence=round(similarity, 3),
                        matched_by=MatchMethod.EMBEDDING_DISCOVERY,
                        related_skills=[nearest_canonical],
                    )
                    discovered.append(skill)
                    seen.add(norm)

                    logger.debug(
                        "Discovered skill via embedding: '%s' (near '%s', sim=%.3f)",
                        candidate, nearest_canonical, similarity,
                    )

        return discovered

    def register_skill_embedding(self, canonical: str) -> None:
        """Add a new skill's embedding to the runtime index."""
        if not self._model:
            return

        try:
            key = canonical.lower()
            with self._lock:
                if key in self._embeddings:
                    return

            emb = self._model.encode([canonical], normalize_embeddings=True, show_progress_bar=False)[0]

            with self._lock:
                self._embeddings[key] = emb
                self._canonical_list.append(canonical)
                # Rebuild matrix
                self._embedding_matrix = np.array(
                    [self._embeddings[k.lower()] for k in self._canonical_list],
                    dtype=np.float32,
                )

            logger.debug("Registered embedding for runtime skill: %s", canonical)

        except Exception as e:
            logger.error("Failed to register embedding for '%s': %s", canonical, e)

    @staticmethod
    def _extract_candidate_terms(text: str) -> list[str]:
        """
        Extract potential skill-like terms from text.
        Looks for capitalized phrases, tech patterns, acronyms.
        """
        import re

        candidates: list[str] = []

        # Pattern 1: Capitalized multi-word terms (e.g., "Apache Kafka")
        for match in re.finditer(r"\b([A-Z][a-zA-Z+#.]*(?:\s+[A-Z][a-zA-Z+#.]*){0,2})\b", text):
            term = match.group(1).strip()
            if 2 <= len(term) <= 40:
                candidates.append(term)

        # Pattern 2: All-caps acronyms (e.g., "AWS", "GCP", "NLP")
        for match in re.finditer(r"\b([A-Z]{2,6})\b", text):
            candidates.append(match.group(1))

        # Pattern 3: Tech patterns with dots/hyphens (e.g., "Vue.js", "scikit-learn")
        for match in re.finditer(r"\b([a-zA-Z]+[.\-][a-zA-Z]+(?:[.\-][a-zA-Z]+)?)\b", text):
            candidates.append(match.group(1))

        # Deduplicate preserving order
        seen: set[str] = set()
        unique: list[str] = []
        for c in candidates:
            norm = c.lower()
            if norm not in seen and len(norm) >= 2:
                seen.add(norm)
                unique.append(c)

        return unique
