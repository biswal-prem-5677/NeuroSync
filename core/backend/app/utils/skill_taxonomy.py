"""
NeuroSync — Skill Taxonomy Loader.
Thread-safe singleton that loads the skill graph and supports runtime extension.
"""
from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

from app.models.domain import TaxonomyEntry
from app.models.enums import SkillCategory

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_TAXONOMY_FILE = _DATA_DIR / "skill_taxonomy.json"
_IMPLICATIONS_FILE = _DATA_DIR / "skill_implications.json"

# Separators that carry no meaning for lookup: "Infrastructure-As-Code" and
# "infrastructure as code" are the same term.
_SEPARATOR_RE = re.compile(r"[-_/]+")
_WS_RE = re.compile(r"\s+")


def normalize_term(text: str) -> str:
    """Collapse hyphens/underscores/slashes and whitespace for lookup."""
    return _WS_RE.sub(" ", _SEPARATOR_RE.sub(" ", text.lower().strip())).strip()


@dataclass
class ProvisionalSkill:
    """
    A discovered term held in quarantine, awaiting corroboration.

    Tracker D2: a term seen once in one resume used to become a permanent
    taxonomy entry. `documents` records the distinct documents it has been seen
    in; only a term that recurs earns promotion. This is what makes discovery
    self-correcting instead of merely optimistic — noise is per-document, real
    skills recur.
    """
    entry: TaxonomyEntry
    documents: set[str] = field(default_factory=set)

    @property
    def sightings(self) -> int:
        return len(self.documents)


class SkillTaxonomy:
    """
    In-memory skill graph loaded from skill_taxonomy.json.
    Supports:
    - Canonical name resolution (alias → canonical)
    - Related skill lookup
    - Category + importance retrieval
    - Runtime registration of discovered skills (thread-safe)
    """

    _instance: Optional["SkillTaxonomy"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SkillTaxonomy":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._initialized = False
                    cls._instance = inst
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._entries: dict[str, TaxonomyEntry] = {}       # key → TaxonomyEntry
        self._alias_index: dict[str, str] = {}              # normalized alias → key
        self._canonical_index: dict[str, str] = {}          # normalized canonical → key
        self._loose_index: dict[str, str] = {}              # separator-normalized term → key
        self._resolve_cache: dict[str, Optional[str]] = {}  # text → canonical (or None)
        self._runtime_skills: dict[str, TaxonomyEntry] = {} # dynamically added (promoted)
        self._provisional: dict[str, ProvisionalSkill] = {} # quarantined, unpromoted
        self._rw_lock = threading.Lock()
        self._load()
        self._load_implications()
        self._initialized = True

    def _load(self) -> None:
        """Load taxonomy from JSON file."""
        if not _TAXONOMY_FILE.exists():
            logger.warning("Taxonomy file not found at %s — starting with empty taxonomy", _TAXONOMY_FILE)
            return

        try:
            with open(_TAXONOMY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw_skills = data.get("skills", {})
            for key, entry_data in raw_skills.items():
                entry = TaxonomyEntry(
                    canonical=entry_data["canonical"],
                    category=SkillCategory(entry_data.get("category", "other")),
                    aliases=entry_data.get("aliases", []),
                    related=entry_data.get("related", []),
                    importance_weight=entry_data.get("importance_weight", 0.5),
                )
                self._entries[key] = entry

                # Build alias index
                norm_canonical = entry.canonical.lower().strip()
                self._canonical_index[norm_canonical] = key
                self._alias_index[norm_canonical] = key

                self._loose_index.setdefault(normalize_term(entry.canonical), key)

                for alias in entry.aliases:
                    norm_alias = alias.lower().strip()
                    if norm_alias:
                        self._alias_index[norm_alias] = key
                        self._loose_index.setdefault(normalize_term(alias), key)

            logger.info("Loaded %d skills from taxonomy (version: %s)",
                        len(self._entries), data.get("version", "unknown"))

        except Exception as e:
            logger.error("Failed to load taxonomy: %s", e)

    def _load_implications(self) -> None:
        """
        Load the directed subsumption graph and attach the transitive closure
        to each entry's `implies` list.

        Kept in a separate file from the taxonomy because it is a different
        relation: `related` is symmetric association, `implies` is directed
        subsumption. Conflating the two is what let "PostgreSQL present, SQL
        missing" pass as a real gap (tracker D1).
        """
        if not _IMPLICATIONS_FILE.exists():
            logger.warning(
                "Implications file not found at %s — parent/child resolution disabled",
                _IMPLICATIONS_FILE,
            )
            return

        try:
            with open(_IMPLICATIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            raw: dict[str, list[str]] = data.get("implies", {})

            # Resolve every edge to a taxonomy key so the closure walk is total.
            direct: dict[str, set[str]] = {}
            unknown_terms: set[str] = set()

            for child, parents in raw.items():
                child_key = self._key_for(child)
                if child_key is None:
                    unknown_terms.add(child)
                    continue
                for parent in parents:
                    parent_key = self._key_for(parent)
                    if parent_key is None:
                        unknown_terms.add(parent)
                        continue
                    if parent_key != child_key:
                        direct.setdefault(child_key, set()).add(parent_key)

            # Transitive closure, cycle-safe.
            resolved: dict[str, set[str]] = {}

            def close(key: str, seen: frozenset[str]) -> set[str]:
                if key in resolved:
                    return resolved[key]
                if key in seen:
                    return set()          # cycle — stop, do not recurse
                out: set[str] = set()
                for parent in direct.get(key, ()):
                    out.add(parent)
                    out |= close(parent, seen | {key})
                if key not in seen:
                    resolved[key] = out
                return out

            edge_count = 0
            for child_key in direct:
                parents = close(child_key, frozenset())
                entry = self._entries[child_key]
                entry.implies = sorted(
                    self._entries[p].canonical for p in parents if p in self._entries
                )
                edge_count += len(entry.implies)

            if unknown_terms:
                logger.warning(
                    "Implications reference %d unknown skills (ignored): %s",
                    len(unknown_terms), ", ".join(sorted(unknown_terms)[:10]),
                )

            logger.info(
                "Loaded skill implications (version %s): %d skills → %d closed edges",
                data.get("version", "unknown"), len(direct), edge_count,
            )

        except Exception as e:
            logger.error("Failed to load skill implications: %s", e)

    def _key_for(self, term: str) -> Optional[str]:
        """Resolve any term to an internal taxonomy key (static entries only)."""
        norm = term.lower().strip()
        key = (
            self._alias_index.get(norm)
            or self._canonical_index.get(norm)
            or self._loose_index.get(normalize_term(term))
        )
        if key is None and norm in self._entries:
            key = norm
        return key if key in self._entries else None

    # ----- Public API -----

    def resolve_skill(self, text: str) -> Optional[str]:
        """
        Resolve any text fragment to a canonical skill name.
        Returns None if not found in taxonomy.
        Uses cached results for O(1) repeated lookups.
        """
        norm = text.lower().strip()

        # Check cache first
        if norm in self._resolve_cache:
            return self._resolve_cache[norm]

        # Direct alias/canonical lookup
        key = self._alias_index.get(norm) or self._canonical_index.get(norm)

        if key and key in self._entries:
            canonical = self._entries[key].canonical
            self._resolve_cache[norm] = canonical
            return canonical

        # Check runtime skills
        with self._rw_lock:
            if norm in self._runtime_skills:
                canonical = self._runtime_skills[norm].canonical
                self._resolve_cache[norm] = canonical
                return canonical

        # Separator-insensitive fallback: "Infrastructure-As-Code" is the same
        # term as "infrastructure as code" and must not be discovered as new.
        loose = normalize_term(text)
        if loose != norm:
            key = self._loose_index.get(loose)
            if key and key in self._entries:
                canonical = self._entries[key].canonical
                self._resolve_cache[norm] = canonical
                return canonical
            with self._rw_lock:
                for rt_key, rt_entry in self._runtime_skills.items():
                    if normalize_term(rt_key) == loose:
                        self._resolve_cache[norm] = rt_entry.canonical
                        return rt_entry.canonical

        self._resolve_cache[norm] = None
        return None

    def get_entry(self, canonical_or_key: str) -> Optional[TaxonomyEntry]:
        """Get full taxonomy entry by canonical name or key."""
        norm = canonical_or_key.lower().strip()
        key = self._alias_index.get(norm) or self._canonical_index.get(norm)
        if key:
            return self._entries.get(key)
        with self._rw_lock:
            return self._runtime_skills.get(norm)

    def get_related(self, skill_name: str) -> list[str]:
        """Get related skills for a given skill."""
        entry = self.get_entry(skill_name)
        return list(entry.related) if entry else []

    def get_category(self, skill_name: str) -> SkillCategory:
        """Get category for a skill."""
        entry = self.get_entry(skill_name)
        return entry.category if entry else SkillCategory.OTHER

    def get_importance(self, skill_name: str) -> float:
        """Get importance weight for a skill (0.0 - 1.0)."""
        entry = self.get_entry(skill_name)
        return entry.importance_weight if entry else 0.5

    def get_all_canonical_names(self) -> list[str]:
        """Return all canonical skill names (static + runtime)."""
        names = [e.canonical for e in self._entries.values()]
        with self._rw_lock:
            names.extend(e.canonical for e in self._runtime_skills.values())
        return names

    def get_all_searchable_terms(self) -> dict[str, str]:
        """Return dict of all searchable terms → canonical name for fast matching."""
        terms: dict[str, str] = {}
        for key, entry in self._entries.items():
            norm = entry.canonical.lower().strip()
            terms[norm] = entry.canonical
            for alias in entry.aliases:
                terms[alias.lower().strip()] = entry.canonical
        with self._rw_lock:
            for key, entry in self._runtime_skills.items():
                terms[key] = entry.canonical
        return terms

    @property
    def skill_count(self) -> int:
        """Total skills (static + runtime)."""
        with self._rw_lock:
            return len(self._entries) + len(self._runtime_skills)

    # ----- Runtime Extension -----

    def register_discovered_skill(
        self,
        canonical: str,
        category: SkillCategory = SkillCategory.OTHER,
        importance_weight: float = 0.4,
        related: Optional[list[str]] = None,
        *,
        document_id: Optional[str] = None,
        promote_after: int = 1,
    ) -> str:
        """
        Offer a runtime-discovered skill to the taxonomy. Thread-safe. Never
        touches the JSON file.

        Discovery used to be unconditional, which is how `Mentored` and
        `Designed Postgresql` became permanent entries visible to every later
        request (tracker D2). A term now has to be corroborated: it is held in
        quarantine until it has been seen in `promote_after` distinct documents.

        Args:
            document_id: fingerprint of the document this sighting came from.
                Sightings from the same document do not accumulate.
            promote_after: distinct documents required before promotion. 1
                restores the old immediate-registration behaviour.

        Returns:
            "known" — already in the taxonomy, nothing to do.
            "provisional" — quarantined, not yet part of the taxonomy.
            "promoted" — corroborated and now a real entry.
        """
        norm = canonical.lower().strip()

        with self._rw_lock:
            if norm in self._alias_index or norm in self._runtime_skills:
                return "known"

            prov = self._provisional.get(norm)
            if prov is None:
                prov = ProvisionalSkill(
                    entry=TaxonomyEntry(
                        canonical=canonical,
                        category=category,
                        aliases=[],
                        related=related or [],
                        importance_weight=importance_weight,
                    )
                )
                self._provisional[norm] = prov

            prov.documents.add(document_id or canonical)

            if prov.sightings < max(1, promote_after):
                logger.debug(
                    "Provisional skill '%s' (%d/%d sightings) — not registered",
                    canonical, prov.sightings, promote_after,
                )
                return "provisional"

            # Corroborated — promote into the live taxonomy.
            del self._provisional[norm]
            self._runtime_skills[norm] = prov.entry
            self._resolve_cache.pop(norm, None)
            logger.info(
                "Promoted runtime skill: %s (category: %s, %d sightings)",
                canonical, prov.entry.category.value, prov.sightings,
            )
            return "promoted"

    def register_alias(self, canonical: str, alias: str) -> bool:
        """
        Attach a spelling variant to an existing skill.

        Used when discovery finds a term so close to a known skill that it is
        the same skill written differently ("Postgres DB" → PostgreSQL).
        Registering it as a separate entry would split one skill in two and
        understate coverage.
        """
        norm_alias = alias.lower().strip()
        if not norm_alias:
            return False

        key = self._key_for(canonical)
        if key is None:
            return False

        with self._rw_lock:
            if norm_alias in self._alias_index:
                return False
            entry = self._entries[key]
            if norm_alias not in (a.lower() for a in entry.aliases):
                entry.aliases.append(alias)
            self._alias_index[norm_alias] = key
            self._loose_index.setdefault(normalize_term(alias), key)
            self._provisional.pop(norm_alias, None)
            self._resolve_cache.pop(norm_alias, None)

        logger.debug("Registered alias '%s' → %s", alias, entry.canonical)
        return True

    def get_discovery_stats(self) -> dict:
        """Discovery/quarantine counts — surfaced on /health."""
        with self._rw_lock:
            return {
                "static_skills": len(self._entries),
                "promoted_skills": len(self._runtime_skills),
                "provisional_skills": len(self._provisional),
                "provisional_terms": sorted(
                    p.entry.canonical for p in self._provisional.values()
                )[:20],
            }

    def invalidate_cache(self) -> None:
        """Clear resolve cache — call after taxonomy updates via feedback."""
        self._resolve_cache.clear()
        logger.debug("Taxonomy resolve cache invalidated")
