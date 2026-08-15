"""
NeuroSync — Hybrid Skill Extractor (v2).
4-layer extraction pipeline: Taxonomy → NER → Semantic → Embedding Discovery.
Now with: section-aware weighting, frequency scoring, proficiency detection,
filtered embedding discovery, and contextual evidence strength.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.config import Settings
from app.models.domain import ExtractionResult, Skill
from app.models.enums import MatchMethod, SkillCategory
from app.services.skill_noise_filter import SkillNoiseFilter
from app.utils.embedding_store import SkillEmbeddingStore
from app.utils.skill_taxonomy import SkillTaxonomy
from app.utils.text_processor import (
    normalize_for_matching, preserve_tech_term, extract_sections,
    chunk_text,
)

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="skill-extract")

# ---------------------------------------------------------------------------
# Section Weights — "Experience" mention is stronger than "Skills" list
# ---------------------------------------------------------------------------
_SECTION_WEIGHTS: dict[str, float] = {
    "experience":     1.0,    # Strongest signal — used the skill professionally
    "projects":       0.95,   # Built something with it
    "work experience": 1.0,
    "professional experience": 1.0,
    "key projects":   0.95,
    "summary":        0.7,    # Claims expertise
    "profile":        0.7,
    "objective":      0.6,
    "skills":         0.5,    # Just listed — weakest active signal
    "technical skills": 0.5,
    "core competencies": 0.5,
    "education":      0.4,    # Coursework mention
    "certifications": 0.6,    # Certified
    "publications":   0.8,    # Published research using it
    "research":       0.8,
    "awards":         0.5,
    "header":         0.3,    # Appears in name/title area
}

# Proficiency signal words
_HIGH_PROFICIENCY_SIGNALS = re.compile(
    r"\b(expert|advanced|proficient|extensive|deep|senior|lead|architect|built|designed|"
    r"implemented|developed|engineered|created|optimized|scaled|production)\b", re.I
)
_LOW_PROFICIENCY_SIGNALS = re.compile(
    r"\b(basic|beginner|familiar|exposure|learning|coursework|introductory|"
    r"fundamental|novice|elementary|some experience)\b", re.I
)

# Noise policy for the discovery layers lives in SkillNoiseFilter — see
# services/skill_noise_filter.py. Keeping it there rather than as a module
# constant here is what closes tracker D2: the same rules have to apply to NER
# and to embedding discovery, and both used to filter (or not) independently.


class SkillExtractor:
    """
    Hybrid 4-layer skill extraction pipeline with intensity detection.

    Layer 1 — Taxonomy Matching (fast, high precision)
    Layer 2 — spaCy NER (discovers unknown entities)
    Layer 3 — Semantic Matching (cross-document paraphrases)
    Layer 4 — Embedding Discovery (finds unknown skills with filtering)

    New in v2:
    - Section-aware weighting (Experience > Skills listing)
    - Frequency scoring (occurrence_count)
    - Proficiency detection (context signals)
    - Evidence strength computation
    - Filtered embedding discovery (blacklist + min confidence)
    """

    def __init__(
        self,
        config: Settings,
        taxonomy: SkillTaxonomy,
        embedding_store: Optional[SkillEmbeddingStore] = None,
        semantic_model=None,
        noise_filter: Optional[SkillNoiseFilter] = None,
    ):
        self._config = config
        self._taxonomy = taxonomy
        self._embedding_store = embedding_store
        self._semantic_model = semantic_model
        self._noise_filter = noise_filter or SkillNoiseFilter(config, taxonomy)
        self._nlp = None
        self._nlp_failed = False
        self._cache: dict[str, ExtractionResult] = {}
        self._cache_max = config.extraction_cache_size

    def warm_up(self) -> None:
        """Pre-warm spaCy NER pipeline during startup to avoid cold start latency."""
        nlp = self._get_nlp()
        if nlp is not None:
            logger.info("SkillExtractor spaCy NER warmed up successfully")
        else:
            logger.warning("SkillExtractor warm_up skipped: spaCy NER unavailable")

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def extract(self, text: str) -> ExtractionResult:
        """
        Extract skills from text using all available layers.
        Now includes: frequency, section awareness, proficiency, evidence strength.
        """
        start = time.perf_counter()

        # Check cache
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            logger.debug("Cache hit for skill extraction (key=%s)", cache_key[:12])
            return self._cache[cache_key]

        # Parse document sections for context-aware extraction
        sections = extract_sections(text)
        normalized = normalize_for_matching(text)

        all_skills: dict[str, Skill] = {}
        methods_used: list[str] = []
        failed_layers: list[str] = []

        # ----- Layer 1: Taxonomy Matching (section-aware) -----
        try:
            taxonomy_skills = self._extract_taxonomy_sectioned(text, normalized, sections)
            for skill in taxonomy_skills:
                key = skill.canonical.lower()
                if key not in all_skills or skill.confidence > all_skills[key].confidence:
                    all_skills[key] = skill
            methods_used.append("taxonomy")
            logger.debug("Layer 1 (Taxonomy): found %d skills", len(taxonomy_skills))
        except Exception as e:
            logger.error("Layer 1 (Taxonomy) failed: %s", e)
            failed_layers.append("taxonomy")

        # ----- Layer 2: spaCy NER -----
        try:
            ner_skills = self._extract_ner(text, sections)
            for skill in ner_skills:
                key = skill.canonical.lower()
                if key not in all_skills:
                    all_skills[key] = skill
                else:
                    # Merge: add sections from NER if taxonomy already found it
                    existing = all_skills[key]
                    merged_sections = list(set(existing.found_in_sections + skill.found_in_sections))
                    all_skills[key] = existing.model_copy(update={
                        "found_in_sections": merged_sections,
                        "occurrence_count": existing.occurrence_count + skill.occurrence_count,
                    })
            methods_used.append("ner")
            logger.debug("Layer 2 (NER): found %d skills", len(ner_skills))
        except Exception as e:
            logger.warning("Layer 2 (NER) failed (degraded mode): %s", e)
            failed_layers.append("ner")

        # ----- Layer 4: Embedding Discovery (filtered) -----
        try:
            if self._embedding_store and self._embedding_store.has_embeddings:
                chunks = chunk_text(text, chunk_size=256, overlap=32)
                known = {s.canonical.lower() for s in all_skills.values()}
                discovered = self._extract_embedding_filtered(chunks, known, text)
                for skill in discovered:
                    key = skill.canonical.lower()
                    if key not in all_skills:
                        all_skills[key] = skill
                        # Quarantined until corroborated by another document —
                        # a one-off sighting no longer becomes a taxonomy entry
                        # visible to every later request (tracker D2).
                        self._taxonomy.register_discovered_skill(
                            canonical=skill.canonical,
                            category=skill.category,
                            importance_weight=0.4,
                            related=skill.related_skills,
                            document_id=cache_key,
                            promote_after=self._config.discovery_promotion_sightings,
                        )
                methods_used.append("embedding_discovery")
                logger.debug("Layer 4 (Embedding): discovered %d skills", len(discovered))
            else:
                logger.debug("Layer 4 (Embedding): skipped — store not available")
        except Exception as e:
            logger.warning("Layer 4 (Embedding Discovery) failed: %s", e)
            failed_layers.append("embedding_discovery")

        # ----- Post-processing: compute evidence strength & proficiency -----
        for key, skill in all_skills.items():
            all_skills[key] = self._compute_intensity(skill, text, sections)

        elapsed = (time.perf_counter() - start) * 1000

        result = ExtractionResult(
            skills=list(all_skills.values()),
            extraction_methods_used=methods_used,
            degraded=len(failed_layers) > 0,
            failed_layers=failed_layers,
            processing_time_ms=round(elapsed, 2),
        )

        self._cache_put(cache_key, result)

        logger.info(
            "Extracted %d skills in %.1fms (methods: %s, failed: %s)",
            len(result.skills), elapsed,
            ", ".join(methods_used) or "none",
            ", ".join(failed_layers) or "none",
        )

        return result

    async def extract_async(self, text: str) -> ExtractionResult:
        """Async wrapper — runs extraction in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_executor, self.extract, text)

    def extract_cross_document(
        self,
        resume_text: str,
        jd_text: str,
        resume_skills: ExtractionResult,
        jd_skills: ExtractionResult,
    ) -> list[Skill]:
        """
        Layer 3 — Semantic Matching (cross-document only).
        For JD skills NOT found in resume, check if the resume text
        semantically expresses the same concept.
        """
        if not self._semantic_model:
            logger.debug("Layer 3 (Semantic): skipped — no semantic model")
            return []

        resume_canonical = {s.canonical.lower() for s in resume_skills.skills}
        jd_only_skills = [
            s for s in jd_skills.skills
            if s.canonical.lower() not in resume_canonical
        ]

        if not jd_only_skills:
            return []

        try:
            resume_chunks = chunk_text(resume_text, chunk_size=256, overlap=32)
            if not resume_chunks:
                return []

            import numpy as np
            chunk_embeddings = self._semantic_model.encode(
                resume_chunks, normalize_embeddings=True, show_progress_bar=False,
            )

            semantic_matches: list[Skill] = []
            threshold = self._config.semantic_similarity_threshold

            for jd_skill in jd_only_skills:
                skill_embedding = self._semantic_model.encode(
                    [jd_skill.canonical], normalize_embeddings=True, show_progress_bar=False,
                )[0]

                similarities = np.dot(chunk_embeddings, skill_embedding)
                max_sim = float(np.max(similarities))

                if max_sim >= threshold:
                    matched_skill = Skill(
                        name=jd_skill.canonical,
                        canonical=jd_skill.canonical,
                        category=jd_skill.category,
                        confidence=round(max_sim, 3),
                        matched_by=MatchMethod.SEMANTIC,
                        aliases=jd_skill.aliases,
                        related_skills=jd_skill.related_skills,
                        proficiency_score=0.5,  # Unknown depth via semantic match
                        evidence_strength=round(max_sim * 0.7, 3),
                        occurrence_count=1,
                    )
                    semantic_matches.append(matched_skill)

            return semantic_matches

        except Exception as e:
            logger.warning("Layer 3 (Semantic) failed: %s", e)
            return []

    # =========================================================================
    # LAYER 1: TAXONOMY MATCHING (SECTION-AWARE)
    # =========================================================================

    def _extract_taxonomy_sectioned(
        self, raw_text: str, normalized_text: str, sections: dict[str, str]
    ) -> list[Skill]:
        """
        Taxonomy matching with section awareness.
        Tracks: which sections each skill appears in, frequency per section.
        """
        # First: extract from full text for completeness
        found: dict[str, _SkillAccumulator] = {}
        searchable = self._taxonomy.get_all_searchable_terms()
        sorted_terms = sorted(searchable.keys(), key=len, reverse=True)
        matched_positions: list[tuple[int, int]] = []

        # Pass 1: Full text matching (gets occurrence_count)
        for term in sorted_terms:
            canonical = searchable[term]
            can_lower = canonical.lower()

            escaped = re.escape(term)
            pattern = self._build_skill_pattern(term, escaped)

            matches = list(re.finditer(pattern, normalized_text))
            if not matches:
                continue

            # Count non-overlapping occurrences
            valid_matches = []
            for match in matches:
                start, end = match.start(), match.end()
                overlap = any(start < me and end > ms for ms, me in matched_positions)
                if not overlap:
                    matched_positions.append((start, end))
                    valid_matches.append(match)

            if valid_matches and can_lower not in found:
                entry = self._taxonomy.get_entry(canonical)
                preserved = preserve_tech_term(term)
                found[can_lower] = _SkillAccumulator(
                    name=valid_matches[0].group(0).strip(),
                    canonical=preserved or canonical,
                    category=entry.category if entry else SkillCategory.OTHER,
                    entry=entry,
                    total_count=len(matches),  # Total including overlaps
                )

        # Pass 2: Per-section matching (gets found_in_sections)
        for section_name, section_text in sections.items():
            if not section_text:
                continue
            section_normalized = normalize_for_matching(section_text)
            for term in sorted_terms:
                canonical = searchable[term]
                can_lower = canonical.lower()
                if can_lower not in found:
                    continue

                escaped = re.escape(term)
                pattern = self._build_skill_pattern(term, escaped)
                if re.search(pattern, section_normalized):
                    found[can_lower].sections.add(section_name)

        # Build Skill objects
        result: list[Skill] = []
        for acc in found.values():
            skill = Skill(
                name=acc.name,
                canonical=acc.canonical,
                category=acc.category,
                confidence=1.0,
                matched_by=MatchMethod.TAXONOMY,
                aliases=list(acc.entry.aliases) if acc.entry else [],
                related_skills=list(acc.entry.related) if acc.entry else [],
                occurrence_count=max(1, acc.total_count),
                found_in_sections=sorted(acc.sections),
            )
            result.append(skill)

        return result

    @staticmethod
    def _build_skill_pattern(term: str, escaped: str) -> str:
        """Build regex pattern with smart boundary handling for tech terms."""
        if len(term) <= 2 and term.isalpha():
            return rf"(?<![a-zA-Z]){escaped}(?![a-zA-Z])"
        if any(c in term for c in ["+", "#", "."]):
            return rf"(?<![a-zA-Z]){escaped}(?![a-zA-Z0-9])"
        return rf"\b{escaped}\b"

    # =========================================================================
    # LAYER 2: spaCy NER (SECTION-AWARE)
    # =========================================================================

    def _extract_ner(self, text: str, sections: dict[str, str]) -> list[Skill]:
        """NER extraction with section tracking."""
        nlp = self._get_nlp()
        if nlp is None:
            return []

        try:
            max_len = min(len(text), self._config.max_text_length)
            doc = nlp(text[:max_len])

            found: dict[str, Skill] = {}

            for ent in doc.ents:
                if ent.label_ not in ("SKILL", "ORG", "PRODUCT"):
                    continue

                ent_text = ent.text.strip()
                if len(ent_text) < 2:
                    continue

                canonical = self._taxonomy.resolve_skill(ent_text)
                ent_sections = self._find_sections_for_text(ent_text, sections)

                if canonical:
                    can_lower = canonical.lower()
                    entry = self._taxonomy.get_entry(canonical)
                    if can_lower not in found:
                        found[can_lower] = Skill(
                            name=ent_text,
                            canonical=canonical,
                            category=entry.category if entry else SkillCategory.OTHER,
                            confidence=0.85,
                            matched_by=MatchMethod.NER,
                            aliases=list(entry.aliases) if entry else [],
                            related_skills=list(entry.related) if entry else [],
                            occurrence_count=1,
                            found_in_sections=ent_sections,
                        )
                    else:
                        existing = found[can_lower]
                        found[can_lower] = existing.model_copy(update={
                            "occurrence_count": existing.occurrence_count + 1,
                            "found_in_sections": sorted(set(
                                existing.found_in_sections + ent_sections
                            )),
                        })
                else:
                    # An entity spaCy could not resolve to a known skill. This
                    # branch used to accept everything, which is where
                    # `Techcorp`, `Xyz University` and `B.Tech Computer Science`
                    # entered the skill set (tracker D2).
                    verdict = self._noise_filter.judge(
                        ent_text, source_label=ent.label_, full_text=text,
                    )
                    if verdict.rejected:
                        continue

                    if verdict.alias_of:
                        self._taxonomy.register_alias(verdict.alias_of, ent_text)
                        continue

                    norm = ent_text.lower()
                    if norm not in found:
                        found[norm] = Skill(
                            name=ent_text,
                            canonical=ent_text.title(),
                            category=SkillCategory.OTHER,
                            confidence=0.6,
                            matched_by=MatchMethod.NER,
                            occurrence_count=1,
                            found_in_sections=ent_sections,
                        )

            return list(found.values())

        except Exception as e:
            logger.warning("spaCy NER processing failed: %s", e)
            return []

    def _get_nlp(self):
        """Lazy-load spaCy model. Fail once, skip forever."""
        if self._nlp is not None:
            return self._nlp
        if self._nlp_failed:
            return None

        try:
            import spacy

            nlp = spacy.load(self._config.spacy_model_name, disable=["parser", "lemmatizer"])

            if "entity_ruler" not in nlp.pipe_names:
                ruler = nlp.add_pipe("entity_ruler", before="ner")
                patterns = []
                for canonical in self._taxonomy.get_all_canonical_names():
                    patterns.append({"label": "SKILL", "pattern": canonical})
                    entry = self._taxonomy.get_entry(canonical)
                    if entry:
                        for alias in entry.aliases:
                            if alias:
                                patterns.append({"label": "SKILL", "pattern": alias})
                ruler.add_patterns(patterns)
                logger.info("spaCy EntityRuler loaded with %d patterns", len(patterns))

            self._nlp = nlp
            logger.info("spaCy model '%s' loaded", self._config.spacy_model_name)
            return self._nlp

        except (ImportError, OSError) as e:
            logger.warning("spaCy unavailable (%s) — NER layer disabled", e)
            self._nlp_failed = True
            return None
        except Exception as e:
            logger.error("Failed to load spaCy: %s", e)
            self._nlp_failed = True
            return None

    # =========================================================================
    # LAYER 4: EMBEDDING DISCOVERY (FILTERED)
    # =========================================================================

    def _extract_embedding_filtered(
        self,
        chunks: list[str],
        known_skills: set[str],
        full_text: str,
    ) -> list[Skill]:
        """
        Embedding discovery, gated by SkillNoiseFilter.

        The filter owns every judgement about whether a term is a skill (tracker
        D2). What stays here is the mechanical part: the term must actually
        occur in the document as a distinct phrase, and a term the filter
        recognises as a variant of a known skill is folded into that skill
        rather than reported as a discovery.
        """
        if not self._embedding_store or not self._embedding_store.has_embeddings:
            return []
        if not self._config.discovery_enabled:
            logger.debug("Layer 4 (Embedding Discovery): disabled by config")
            return []

        raw_discovered = self._embedding_store.discover_unknown_skills(
            chunks, known_skills,
            threshold=self._config.embedding_discovery_threshold,
        )

        filtered: list[Skill] = []
        full_lower = full_text.lower()

        for skill in raw_discovered:
            name_lower = skill.name.lower().strip()
            nearest = skill.related_skills[0] if skill.related_skills else None

            verdict = self._noise_filter.judge(
                skill.name, similarity=skill.confidence, nearest=nearest,
                full_text=full_text,
            )
            if verdict.rejected:
                continue

            # A variant spelling of a known skill: teach the taxonomy the alias
            # instead of minting a second entry for the same capability.
            if verdict.alias_of:
                if self._taxonomy.register_alias(verdict.alias_of, skill.name):
                    logger.debug(
                        "Discovery '%s' absorbed as alias of %s",
                        skill.name, verdict.alias_of,
                    )
                continue

            # Must occur as a distinct phrase — chunking can produce fragments
            # that never appear in the source text.
            pattern = rf"\b{re.escape(name_lower)}\b"
            occurrences = len(re.findall(pattern, full_lower))
            if occurrences == 0:
                logger.debug("Embedding discovery filtered (not in text): '%s'", skill.name)
                continue

            filtered.append(skill.model_copy(update={
                "occurrence_count": occurrences,
                "category": self._noise_filter.category_for(nearest, skill.confidence),
                "confidence": round(skill.confidence * 0.95, 3),  # Slight penalty vs taxonomy
            }))

        logger.debug("Embedding discovery: %d raw → %d after filtering",
                     len(raw_discovered), len(filtered))
        return filtered

    # =========================================================================
    # INTENSITY COMPUTATION
    # =========================================================================

    def _compute_intensity(
        self, skill: Skill, full_text: str, sections: dict[str, str]
    ) -> Skill:
        """
        Post-processing: compute evidence_strength and proficiency_score
        from context signals.
        """
        # --- Evidence Strength ---
        # Combines: section_weight × frequency factor
        max_section_weight = 0.3  # default if no section info
        for section_name in skill.found_in_sections:
            w = _SECTION_WEIGHTS.get(section_name, 0.3)
            max_section_weight = max(max_section_weight, w)

        # Frequency factor: diminishing returns (log-ish)
        freq_factor = min(1.0, 0.5 + (skill.occurrence_count - 1) * 0.15)

        # Method confidence factor
        method_factor = {
            MatchMethod.TAXONOMY: 1.0,
            MatchMethod.NER: 0.85,
            MatchMethod.SEMANTIC: 0.7,
            MatchMethod.EMBEDDING_DISCOVERY: 0.6,
        }.get(skill.matched_by, 0.5)

        evidence_strength = round(
            max_section_weight * 0.5 + freq_factor * 0.3 + method_factor * 0.2,
            3,
        )

        # --- Proficiency Score ---
        proficiency = self._detect_proficiency(skill, full_text, sections)

        return skill.model_copy(update={
            "evidence_strength": min(1.0, evidence_strength),
            "proficiency_score": proficiency,
        })

    def _detect_proficiency(
        self, skill: Skill, full_text: str, sections: dict[str, str]
    ) -> float:
        """
        Detect proficiency level from contextual clues around the skill mention.

        Signals:
        - "expert in Python" → high
        - "Python (basic)" → low
        - "Built production ML pipelines in Python" → high
        - "Familiar with Python" → low
        - Appears in Experience with action verbs → high
        - Appears only in Skills list → neutral (0.5)
        """
        skill_name_lower = skill.canonical.lower()
        proficiency = 0.5  # neutral default

        # Check surrounding context (±100 chars around each mention)
        for match in re.finditer(
            rf"\b{re.escape(skill_name_lower)}\b",
            full_text.lower(),
        ):
            start = max(0, match.start() - 100)
            end = min(len(full_text), match.end() + 100)
            context = full_text[start:end].lower()

            # High proficiency signals
            high_matches = len(_HIGH_PROFICIENCY_SIGNALS.findall(context))
            # Low proficiency signals
            low_matches = len(_LOW_PROFICIENCY_SIGNALS.findall(context))

            if high_matches > low_matches:
                proficiency = max(proficiency, 0.7 + min(0.25, high_matches * 0.05))
            elif low_matches > high_matches:
                proficiency = min(proficiency, 0.35 - min(0.15, low_matches * 0.05))

        # Section-based adjustment
        if "experience" in skill.found_in_sections or "projects" in skill.found_in_sections:
            proficiency = max(proficiency, 0.65)  # At least 0.65 if used professionally
        if "education" in skill.found_in_sections and len(skill.found_in_sections) == 1:
            proficiency = min(proficiency, 0.45)  # Only in education = likely academic

        # Frequency boost (used often = probably proficient)
        if skill.occurrence_count >= 5:
            proficiency = max(proficiency, 0.75)
        elif skill.occurrence_count >= 3:
            proficiency = max(proficiency, 0.60)

        return round(min(1.0, max(0.05, proficiency)), 3)

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _find_sections_for_text(text: str, sections: dict[str, str]) -> list[str]:
        """Find which sections contain the given text."""
        text_lower = text.lower()
        found: list[str] = []
        for section_name, section_text in sections.items():
            if text_lower in section_text.lower():
                found.append(section_name)
        return sorted(found)

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _cache_put(self, key: str, result: ExtractionResult) -> None:
        if len(self._cache) >= self._cache_max:
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = result

    def invalidate_cache(self) -> None:
        """Clear extraction cache — call after taxonomy updates."""
        self._cache.clear()
        logger.debug("Skill extraction cache invalidated")

    def get_stats(self) -> dict:
        """Return extraction stats for health endpoint."""
        return {
            "taxonomy_skills": self._taxonomy.skill_count,
            "embedding_store_ready": (
                self._embedding_store.is_ready if self._embedding_store else False
            ),
            "embedding_store_has_data": (
                self._embedding_store.has_embeddings if self._embedding_store else False
            ),
            "ner_available": self._nlp is not None and not self._nlp_failed,
            "ner_failed": self._nlp_failed,
            "cache_size": len(self._cache),
            "cache_max": self._cache_max,
            "discovery_enabled": self._config.discovery_enabled,
            "noise_rejections": self._noise_filter.rejection_counts,
            **self._taxonomy.get_discovery_stats(),
        }


# ---------------------------------------------------------------------------
# Internal accumulator (not exported)
# ---------------------------------------------------------------------------

class _SkillAccumulator:
    """Temporary structure for building Skill objects during taxonomy pass."""
    __slots__ = ("name", "canonical", "category", "entry", "total_count", "sections")

    def __init__(self, name, canonical, category, entry, total_count):
        self.name = name
        self.canonical = canonical
        self.category = category
        self.entry = entry
        self.total_count = total_count
        self.sections: set[str] = set()
