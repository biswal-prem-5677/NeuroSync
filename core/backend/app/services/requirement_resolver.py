"""
NeuroSync — Requirement Semantics.

Two collaborating pieces, both deterministic (no LLM, no network):

1. `RequirementParser` — reads the JD as a list of *requirements*, not a bag of
   skills. "Python, Go, or Java" is ONE requirement with three options;
   "Nice to have: GraphQL" is a requirement worth a fraction of a hard one.

2. `CoverageResolver` — decides whether the resume meets each requirement,
   accepting a subsuming skill as evidence: PostgreSQL meets SQL, AWS meets
   Cloud Computing, CI/CD meets DevOps.

Together these close tracker defect D1, where a candidate holding Python, AWS,
PostgreSQL and CI/CD was reported as missing Go, Java, GCP, Azure, SQL,
Cloud Computing and DevOps — seven phantom gaps that dominated the score.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable, Optional

from app.config import Settings
from app.models.domain import (
    CoverageResult, RequirementCoverage, RequirementGroup, RequirementSet, Skill,
)
from app.models.enums import SkillCategory
from app.utils.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)

# --- Line classification -----------------------------------------------------

_BULLET_RE = re.compile(r"^[\s\-•‣●▪\*–—>]+")

_OPTIONAL_HEADING_RE = re.compile(
    r"^\s*(nice[\s-]to[\s-]have|good[\s-]to[\s-]have|preferred(\s+qualifications?)?|"
    r"bonus(\s+points?)?|desirable|optional|pluses?|a\s+plus)\b[\s:.\-]*$",
    re.I,
)
_REQUIRED_HEADING_RE = re.compile(
    r"^\s*(requirements?|required(\s+qualifications?)?|must[\s-]have|qualifications|"
    r"responsibilities|what\s+you.{0,3}ll\s+(do|need)|who\s+you\s+are|"
    r"skills?\s+(and|&)\s+experience|minimum\s+qualifications?)\b[\s:.\-]*$",
    re.I,
)
# Everything after one of these is company boilerplate, not a requirement.
_CLOSING_HEADING_RE = re.compile(
    r"^\s*(we\s+offer|what\s+we\s+offer|benefits|perks|about\s+(us|the\s+company)|"
    r"why\s+join|compensation|equal\s+opportunity|how\s+to\s+apply)\b",
    re.I,
)
# Optionality stated inline rather than as a heading.
_INLINE_OPTIONAL_RE = re.compile(
    r"\b(nice\s+to\s+have|preferred|is\s+a\s+plus|are\s+a\s+plus|bonus|desirable|"
    r"good\s+to\s+have|would\s+be\s+a\s+plus)\b",
    re.I,
)

# --- List detection ----------------------------------------------------------
# An item is 1-3 words of skill-ish characters. Slash stays INSIDE items so
# "CI/CD" survives; it is therefore not usable as a separator.
_ITEM_TAIL = r"[A-Za-z0-9+#./\-]"
_ITEM = rf"[A-Za-z]{_ITEM_TAIL}*(?:[ ]{_ITEM_TAIL}+){{0,2}}"
_SEP = r"(?:\s*,\s*(?:or\s+|and\s+)?|\s+or\s+|\s+and\s+)"
_LIST_RE = re.compile(rf"{_ITEM}(?:{_SEP}{_ITEM})+")
_SEP_SPLIT_RE = re.compile(_SEP)
_HAS_OR_RE = re.compile(r"(?:,\s*or\s|\bor\s)", re.I)

_PAREN_RE = re.compile(r"\(([^()]{2,120})\)")
_EXAMPLE_RE = re.compile(
    r"\b(?:like|such\s+as|e\.g\.,?|including|incl\.)\s+(.{2,120}?)(?=[.;:]|$)", re.I
)

# Words that never start a real requirement item even if the taxonomy knows them.
_ITEM_STOPWORDS = frozenset({
    "experience", "experiences", "knowledge", "understanding", "skills", "skill",
    "strong", "solid", "proven", "hands", "years", "year", "work", "working",
    "ability", "familiarity", "exposure", "background", "expertise",
})

_MAX_LINE_LEN = 400


class RequirementParser:
    """
    JD text → RequirementSet.

    Line-oriented and conservative: a group is only formed when at least two
    of its members resolve against the taxonomy. Anything the parser misses
    still reaches the requirement set as a single-option group via the
    extraction fallback, so recall never drops below the old behaviour.
    """

    def __init__(self, config: Settings, taxonomy: SkillTaxonomy):
        self._config = config
        self._taxonomy = taxonomy

    # ---------------------------------------------------------------- public

    def parse(self, jd_text: str, jd_skills: Iterable[Skill]) -> RequirementSet:
        lines = self._classify_lines(jd_text)

        groups: list[RequirementGroup] = []
        seen: dict[frozenset[str], RequirementGroup] = {}
        claimed: set[str] = set()          # canonical.lower() already in a group

        # ── Pass A: structural groups from JD lines ──────────────────────
        for line_text, optional in lines:
            for options, kind in self._groups_in_line(line_text):
                key = frozenset(o.lower() for o in options)
                if key in seen:
                    # Same requirement stated twice — keep the stricter one.
                    if not optional:
                        seen[key].required = True
                        seen[key].weight = 1.0
                    continue
                group = self._build_group(options, kind, optional, line_text)
                seen[key] = group
                groups.append(group)
                claimed.update(key)

        # ── Pass B: extracted skills not claimed by any structural group ──
        for skill in jd_skills:
            key_l = skill.canonical.lower()
            if key_l in claimed:
                continue
            optional = self._skill_is_optional_only(skill, lines)
            group = self._build_group(
                [skill.canonical], "single", optional,
                source="", category=skill.category,
            )
            key = frozenset({key_l})
            if key in seen:
                continue
            seen[key] = group
            groups.append(group)
            claimed.add(key_l)

        total = sum(g.weight * g.importance for g in groups)
        result = RequirementSet(
            groups=groups,
            total_weighted_importance=round(total, 4),
            optional_count=sum(1 for g in groups if not g.required),
            alternative_count=sum(1 for g in groups if g.kind == "alternative"),
        )

        logger.debug(
            "Parsed %d requirement groups (%d alternative, %d optional)",
            len(groups), result.alternative_count, result.optional_count,
        )
        return result

    # ---------------------------------------------------------------- lines

    def _classify_lines(self, jd_text: str) -> list[tuple[str, bool]]:
        """Split the JD into (line, is_optional) pairs, dropping boilerplate."""
        out: list[tuple[str, bool]] = []
        optional_mode = False

        for raw in (jd_text or "").split("\n"):
            line = _BULLET_RE.sub("", raw).strip()
            if not line:
                continue

            if _CLOSING_HEADING_RE.match(line):
                break                                  # nothing after this is a requirement
            if _OPTIONAL_HEADING_RE.match(line):
                optional_mode = True
                continue
            if _REQUIRED_HEADING_RE.match(line):
                optional_mode = False
                continue

            is_optional = optional_mode or bool(_INLINE_OPTIONAL_RE.search(line))
            out.append((line[:_MAX_LINE_LEN], is_optional))

        return out

    def _skill_is_optional_only(
        self, skill: Skill, lines: list[tuple[str, bool]]
    ) -> bool:
        """True when every JD line mentioning this skill sits under 'nice to have'."""
        needles = [skill.canonical.lower()] + [a.lower() for a in skill.aliases if a]
        seen_any = False
        for line_text, optional in lines:
            low = line_text.lower()
            if any(n in low for n in needles):
                if not optional:
                    return False
                seen_any = True
        return seen_any

    # --------------------------------------------------------------- groups

    def _groups_in_line(self, line: str) -> list[tuple[list[str], str]]:
        """
        Extract requirement groups from one JD line.

        Returns (options, kind) pairs. Consumed character spans are masked out
        so a parenthetical list is not re-parsed by the generic list scanner.
        """
        found: list[tuple[list[str], str]] = []
        masked = line

        def consume(start: int, end: int) -> None:
            nonlocal masked
            masked = masked[:start] + (" " * (end - start)) + masked[end:]

        # 1. Parenthetical lists: "cloud platforms (AWS, GCP, or Azure)".
        #    A parenthesis holding two or more skills is always a menu.
        for m in _PAREN_RE.finditer(line):
            options = self._resolve_list(m.group(1))
            if len(options) >= 2:
                found.append((options, "alternative"))
                consume(m.start(), m.end())

        # 2. Example lists: "monitoring tools like Prometheus and Grafana".
        for m in _EXAMPLE_RE.finditer(masked):
            options = self._resolve_list(m.group(1))
            if len(options) >= 2:
                found.append((options, "alternative"))
                consume(m.start(), m.end())

        # 3. Generic runs. "or" means a menu; "and"/comma means separate asks.
        for m in _LIST_RE.finditer(masked):
            run = m.group(0)
            options = self._resolve_list(run)
            if not options:
                continue
            if _HAS_OR_RE.search(run) and len(options) >= 2:
                found.append((options, "alternative"))
            else:
                found.extend(([opt], "single") for opt in options)
            consume(m.start(), m.end())

        return self._dedupe(found)

    @staticmethod
    def _dedupe(
        groups: list[tuple[list[str], str]]
    ) -> list[tuple[list[str], str]]:
        """Drop singles already covered by an alternative group on the same line."""
        in_alternative = {
            o.lower() for opts, kind in groups if kind == "alternative" for o in opts
        }
        out: list[tuple[list[str], str]] = []
        seen: set[frozenset[str]] = set()
        for options, kind in groups:
            key = frozenset(o.lower() for o in options)
            if key in seen:
                continue
            if kind == "single" and options[0].lower() in in_alternative:
                continue
            seen.add(key)
            out.append((options, kind))
        return out

    def _build_group(
        self,
        options: list[str],
        kind: str,
        optional: bool,
        source: str = "",
        category: Optional[SkillCategory] = None,
    ) -> RequirementGroup:
        """Order options by importance so `primary` is the one worth reporting."""
        ranked = sorted(
            options, key=lambda o: self._taxonomy.get_importance(o), reverse=True
        )
        importance = self._taxonomy.get_importance(ranked[0]) if ranked else 0.5
        cat = category or self._taxonomy.get_category(ranked[0])
        return RequirementGroup(
            options=ranked,
            kind=kind if len(ranked) > 1 else "single",
            required=not optional,
            importance=importance,
            weight=1.0 if not optional else self._config.optional_requirement_weight,
            category=cat,
            source=source[:160],
        )

    # ------------------------------------------------------------ resolution

    def _resolve_list(self, text: str) -> list[str]:
        """Split a run on its separators and resolve each part to a canonical."""
        out: list[str] = []
        seen: set[str] = set()
        for part in _SEP_SPLIT_RE.split(text):
            canonical = self._resolve_item(part)
            if canonical and canonical.lower() not in seen:
                seen.add(canonical.lower())
                out.append(canonical)
        return out

    def _resolve_item(self, text: str) -> Optional[str]:
        """
        Resolve one list item to a canonical skill.

        The item often carries filler the regex could not avoid swallowing
        ("experience with Python"), so try progressively shorter windows,
        longest-leftmost first.
        """
        words = [w for w in re.split(r"\s+", text.strip()) if w]
        if not words or len(words) > 4:
            return None

        for start in range(len(words)):
            if words[start].lower().strip(".,") in _ITEM_STOPWORDS:
                continue
            for end in range(len(words), start, -1):
                candidate = " ".join(words[start:end]).strip(" .,;:")
                if len(candidate) < 2:
                    continue
                canonical = self._taxonomy.resolve_skill(candidate)
                if canonical:
                    return canonical
        return None


class CoverageResolver:
    """
    Requirements × resume skills → coverage.

    A requirement is met when the resume holds any option directly, or holds a
    skill that subsumes an option (`implies` closure from skill_implications.json).
    Subsumed matches earn `substitute_credit` rather than full credit: knowing
    PostgreSQL is strong evidence of SQL, not proof of it.
    """

    def __init__(self, config: Settings, taxonomy: SkillTaxonomy):
        self._config = config
        self._taxonomy = taxonomy

    def resolve(
        self, resume_skills: Iterable[Skill], requirements: RequirementSet
    ) -> CoverageResult:
        held: dict[str, Skill] = {}
        for skill in resume_skills:
            key = skill.canonical.lower()
            existing = held.get(key)
            if existing is None or skill.proficiency_score > existing.proficiency_score:
                held[key] = skill

        implied = self._build_implied_index(held)

        coverages: list[RequirementCoverage] = []
        implied_matches: dict[str, str] = {}
        earned = 0.0
        earned_prof = 0.0
        total = 0.0

        alt_credit = self._config.alternative_credit
        sub_credit = self._config.substitute_credit
        floor = self._config.coverage_presence_floor

        for group in requirements.groups:
            denom = group.weight * group.importance
            total += denom

            best: Optional[tuple[float, float, str, str, str]] = None  # credit, prof, by, option, via
            for option in group.options:
                key = option.lower()
                if key in held:
                    src = held[key]
                    candidate = (1.0, src.proficiency_score, src.canonical, option, "direct")
                elif key in implied:
                    src = implied[key]
                    candidate = (sub_credit, src.proficiency_score, src.canonical, option, "implied")
                else:
                    continue
                if best is None or candidate[0] * max(candidate[1], 0.01) > best[0] * max(best[1], 0.01):
                    best = candidate

            if best is None:
                coverages.append(RequirementCoverage(group=group))
                continue

            credit, prof, by, option, via = best
            if len(group.options) > 1:
                credit *= alt_credit
            credit = min(1.0, credit)

            if via == "implied":
                implied_matches[option] = by

            earned += denom * credit
            # Presence earns `floor` of the credit; proficiency modulates the rest.
            earned_prof += denom * credit * (floor + (1.0 - floor) * prof)
            coverages.append(RequirementCoverage(
                group=group,
                satisfied=True,
                satisfied_by=by,
                matched_option=option,
                via=via,
                credit=round(credit, 3),
                proficiency=round(prof, 3),
            ))

        satisfied = sum(1 for c in coverages if c.satisfied)
        return CoverageResult(
            coverages=coverages,
            coverage_score=round(earned / total, 4) if total > 0 else 0.0,
            proficiency_weighted_score=round(earned_prof / total, 4) if total > 0 else 0.0,
            satisfied_count=satisfied,
            unmet_count=len(coverages) - satisfied,
            implied_matches=implied_matches,
        )

    def _build_implied_index(self, held: dict[str, Skill]) -> dict[str, Skill]:
        """
        canonical.lower() → the strongest resume skill that subsumes it.
        Directly-held skills are excluded: they need no substitute.
        """
        implied: dict[str, Skill] = {}
        for skill in held.values():
            entry = self._taxonomy.get_entry(skill.canonical)
            if not entry or not entry.implies:
                continue
            for parent in entry.implies:
                key = parent.lower()
                if key in held:
                    continue
                current = implied.get(key)
                if current is None or skill.proficiency_score > current.proficiency_score:
                    implied[key] = skill
        return implied
