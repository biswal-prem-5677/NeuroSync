"""
NeuroSync — Extraction Noise Filter.

Closes tracker defect D2: the NER and embedding-discovery layers had no noise
filter, so a single resume produced `Mentored`, `Designed Postgresql`,
`Computer Science` (filed under `ml_ai`), `Techcorp` and `Xyz University` as
"skills" — and every one of them was written permanently into the in-memory
taxonomy, where it stayed for the life of the process and leaked into every
later analysis.

Blueprint 02 §3 asks for a blacklist of "common English words that survive NER".
A word list alone cannot hold: the failures above are not common words, they are
*structural* mistakes — an inflected verb, a phrase wrapping a known skill, an
academic field, an employer name. So this module classifies by structure and
keeps the word lists for the residue.

Deterministic: no LLM, no network, no model inference. Every rejection carries a
reason so `/health` and the probes can report *why* a term was dropped.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from app.config import Settings
from app.models.enums import SkillCategory
from app.utils.skill_taxonomy import SkillTaxonomy, normalize_term

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

# Resume action verbs. A closed, well-known set — these open bullet points, get
# capitalized by that position, and land near a real skill in embedding space
# ("Mentored" sits at cosine 0.82 from "Mentoring").
_ACTION_VERBS = frozenset({
    "achieved", "administered", "analyzed", "architected", "authored",
    "automated", "built", "collaborated", "conducted", "configured",
    "constructed", "consulted", "contributed", "coordinated", "created",
    "debugged", "decreased", "defined", "delivered", "deployed", "designed",
    "developed", "devised", "diagnosed", "directed", "documented", "drove",
    "enabled", "engineered", "enhanced", "ensured", "established", "evaluated",
    "executed", "expanded", "facilitated", "forecasted", "formulated",
    "generated", "guided", "handled", "headed", "identified", "implemented",
    "improved", "increased", "influenced", "initiated", "innovated",
    "installed", "instituted", "integrated", "introduced", "launched", "led",
    "leveraged", "maintained", "managed", "mentored", "migrated", "modeled",
    "modernized", "monitored", "negotiated", "operated", "optimized",
    "orchestrated", "organized", "overhauled", "owned", "partnered",
    "performed", "pioneered", "planned", "prototyped", "provided",
    "published", "recommended", "redesigned", "reduced", "refactored",
    "researched", "resolved", "restructured", "revamped", "scaled",
    "shipped", "simplified", "solved", "spearheaded", "standardized",
    "streamlined", "strengthened", "supervised", "supported", "tested",
    "trained", "transformed", "translated", "troubleshot", "utilized",
    "validated", "wrote",
})

# Academic fields, degrees and credential markers. Real things, but they are
# qualifications, not skills — and "Computer Science" landing in `ml_ai` is the
# exact miscategorisation the tracker recorded.
_ACADEMIC_TERMS = frozenset({
    "computer science", "computer engineering", "information technology",
    "information systems", "software engineering", "electrical engineering",
    "electronics", "mechanical engineering", "civil engineering",
    "mathematics", "applied mathematics", "statistics", "physics",
    "chemistry", "biology", "economics", "business administration",
    "b.tech", "btech", "b.e.", "b.sc", "bsc", "b.s.", "bs", "ba", "b.a.",
    "m.tech", "mtech", "m.sc", "msc", "m.s.", "ms", "ma", "m.a.", "mba",
    "phd", "ph.d", "doctorate", "bachelor", "bachelors", "master", "masters",
    "diploma", "cgpa", "gpa", "percentage", "honours", "honors",
    "coursework", "curriculum", "semester", "thesis", "dissertation",
    "university", "college", "institute", "school", "academy",
})

# Organisation suffixes — employers, vendors, schools. An entity ending in one
# of these is a company or an institution, never a skill.
_ORG_SUFFIXES = (
    "inc", "inc.", "llc", "ltd", "ltd.", "limited", "corp", "corp.",
    "corporation", "company", "co", "co.", "gmbh", "plc", "pvt", "pvt.",
    "private", "group", "holdings", "labs", "laboratories", "partners",
    "ventures", "capital", "consulting", "consultancy", "solutions",
    "university", "college", "institute", "academy", "school", "foundation",
)

# Filler that can wrap a real skill without creating a new one. Used by the
# "phrase containing a known skill" rule: if everything around the known skill
# is filler, the candidate is a sentence fragment, not a skill.
_FILLER_WORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "for", "with", "within", "using",
    "used", "use", "in", "on", "at", "to", "from", "by", "via", "across",
    "our", "your", "their", "its", "his", "her", "my", "we", "you", "they",
    "new", "old", "other", "various", "multiple", "several", "both", "all",
    "some", "any", "each", "every", "more", "most", "many", "few",
    "based", "related", "driven", "oriented", "focused", "centric",
    "level", "type", "kind", "sort", "general", "overall", "core", "key",
    "main", "primary", "secondary", "additional", "extra", "further",
    "strong", "solid", "deep", "extensive", "advanced", "basic", "modern",
    "real", "full", "high", "low", "large", "small", "big", "great", "good",
    "best", "better", "excellent", "proven", "hands", "on", "years", "year",
    "experience", "experienced", "knowledge", "understanding", "expertise",
    "skills", "skill", "ability", "familiarity", "exposure", "background",
    "production", "enterprise", "scalable", "robust", "efficient",
    "end", "to", "cross", "functional", "team", "teams", "work", "working",
    "project", "projects", "system", "systems", "platform", "platforms",
    "tool", "tools", "technology", "technologies", "stack", "solution",
    "solutions", "service", "services", "application", "applications",
    "app", "apps", "software", "hardware", "product", "products",
    "senior", "junior", "lead", "principal", "staff", "chief", "head",
    "engineer", "engineers", "developer", "developers", "architect",
    "manager", "analyst", "consultant", "specialist", "intern",
})

# Generic single words that read as skills but carry no signal on their own.
# Blueprint 02 §3 calls for exactly this list ("Team", "System", "Data").
_GENERIC_TERMS = frozenset({
    "team", "teams", "system", "systems", "data", "code", "coding", "tool",
    "tools", "test", "tests", "testing", "plan", "planning", "user", "users",
    "part", "area", "need", "needs", "must", "good", "best", "high", "make",
    "help", "like", "know", "want", "find", "give", "time", "times", "year",
    "years", "work", "role", "roles", "job", "jobs", "task", "tasks",
    "process", "processes", "practice", "practices", "method", "methods",
    "approach", "solution", "solutions", "service", "services", "product",
    "platform", "framework", "library", "technology", "technologies",
    "software", "hardware", "application", "project", "projects", "company",
    "client", "clients", "customer", "customers", "business", "industry",
    "market", "value", "quality", "performance", "growth", "success",
    "requirements", "qualifications", "responsibilities", "benefits",
    "salary", "remote", "onsite", "hybrid", "fulltime", "parttime",
    "opportunity", "opportunities", "candidate", "candidates", "applicant",
    "resume", "cv", "profile", "summary", "objective", "education",
    "certification", "certifications", "award", "awards", "publication",
    "reference", "references", "detail", "details", "example", "examples",
})

# Common words and JD boilerplate that survive NER or embedding proximity.
# Inherited verbatim from the blacklist that used to live in skill_extractor.py,
# so this module is the single owner of noise policy — blueprint 02 §3's
# "Blacklist" requirement.
_BOILERPLATE_TERMS = frozenset({
    "the", "and", "for", "with", "from", "this", "that", "which", "have", "will",
    "your", "our", "their", "been", "were", "being", "also", "into", "over",
    "such", "than", "other", "more", "both", "each", "most", "only", "very",
    "well", "just", "even", "back", "much", "many", "some", "time", "year",
    "team", "work", "role", "data", "code", "tool", "test", "plan", "user",
    "part", "area", "need", "must", "good", "best", "high", "make", "take",
    "help", "like", "know", "want", "find", "give", "tell", "come",
    "new york", "san francisco", "los angeles", "united states",
    "strong", "ability", "responsible", "required", "preferred",
    "experience", "knowledge", "understanding", "skills",
    "nice", "senior", "junior", "looking", "offer", "join", "competitive",
    "salary", "remote", "continuous", "learning", "opportunities",
    "requirements", "qualifications", "about", "company", "apply",
    "similar", "years", "plus", "using", "including", "working",
    "building", "developing", "designing", "implementing", "leading",
    "managing", "creating", "maintaining", "supporting", "driving",
    "open", "source", "contributions", "based", "level", "type",
    "infrastructure", "platform", "service", "services", "system",
    "systems", "solutions", "technologies", "tools", "practices",
    "engineer", "developer", "architect", "manager", "lead", "specialist",
    "bachelor", "master", "degree", "education", "university", "college",
    "cgpa", "gpa", "grade",
})

_ONLY_PUNCT_RE = re.compile(r"^[\W_]+$")
_HAS_LETTER_RE = re.compile(r"[A-Za-z]")
_TOKEN_SPLIT_RE = re.compile(r"[\s/]+")
_MOSTLY_DIGITS_RE = re.compile(r"^[\d\W_]*\d[\d\W_]*$")

_MAX_CANDIDATE_LEN = 40
_MAX_CANDIDATE_WORDS = 4


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NoiseVerdict:
    """
    Outcome of judging one candidate term.

    `accepted`  — plausible skill; may still be quarantined by the taxonomy.
    `alias_of`  — not a new skill but a spelling of an existing one; the caller
                  should report the existing canonical instead of registering.
    `reason`    — why it was rejected, for logs and the noise probe.
    """
    accepted: bool
    reason: str = ""
    alias_of: Optional[str] = None
    category: SkillCategory = SkillCategory.OTHER

    @property
    def rejected(self) -> bool:
        return not self.accepted


_ACCEPT = NoiseVerdict(accepted=True)


class SkillNoiseFilter:
    """
    Gatekeeper for every skill the discovery layers propose.

    Applied to Layer 2 (NER entities that do not resolve to the taxonomy) and
    Layer 4 (embedding-proximity discoveries). Layer 1 needs no filtering — a
    taxonomy match is true by construction — and Layer 3 only ever re-states a
    skill the JD already named.
    """

    def __init__(self, config: Settings, taxonomy: SkillTaxonomy):
        self._config = config
        self._taxonomy = taxonomy
        self._rejections: dict[str, int] = {}

    # ---------------------------------------------------------------- public

    def judge(
        self,
        candidate: str,
        *,
        similarity: float = 1.0,
        nearest: Optional[str] = None,
        source_label: Optional[str] = None,
        full_text: Optional[str] = None,
    ) -> NoiseVerdict:
        """
        Decide whether `candidate` may enter the skill set.

        Args:
            candidate: the raw term as found in the document.
            similarity: cosine to `nearest`, for discovery layers (1.0 for NER).
            nearest: the closest known skill, when the caller knows it.
            source_label: spaCy entity label ("ORG", "PRODUCT", …) for NER.
            full_text: the source document, enabling the fragment check.
        """
        raw = (candidate or "").strip()

        verdict = (
            self._check_shape(raw)
            or self._check_entity_label(raw, source_label)
            or self._check_lexicon(raw)
            or self._check_verb_form(raw)
            or self._check_wraps_known_skill(raw)
            or self._check_fragment(raw, full_text)
            or self._check_similarity(similarity, nearest)
        )

        if verdict is not None:
            if verdict.rejected:
                self._rejections[verdict.reason] = (
                    self._rejections.get(verdict.reason, 0) + 1
                )
                logger.debug("Noise filter rejected '%s' (%s)", raw, verdict.reason)
            return verdict

        return _ACCEPT

    def category_for(
        self, nearest: Optional[str], similarity: float
    ) -> SkillCategory:
        """
        Category to file a discovery under.

        Inheriting the nearest neighbour's category unconditionally is what put
        `Computer Science` in `ml_ai` — the neighbour was an ML skill at cosine
        0.68, close enough to notice and nowhere near close enough to classify.
        Below the alias threshold the honest answer is OTHER.
        """
        if not nearest:
            return SkillCategory.OTHER
        if similarity < self._config.discovery_category_confidence:
            return SkillCategory.OTHER
        return self._taxonomy.get_category(nearest)

    @property
    def rejection_counts(self) -> dict[str, int]:
        """Rejections by reason since process start — surfaced on /health."""
        return dict(self._rejections)

    def reset_stats(self) -> None:
        self._rejections.clear()

    # ----------------------------------------------------------------- rules

    def _check_shape(self, raw: str) -> Optional[NoiseVerdict]:
        """Structural sanity: length, characters, word count."""
        if len(raw) < 2:
            return NoiseVerdict(False, "too_short")
        if len(raw) > _MAX_CANDIDATE_LEN:
            return NoiseVerdict(False, "too_long")
        if any(c in raw for c in ("\n", "\r", "\t")):
            return NoiseVerdict(False, "control_chars")
        if not _HAS_LETTER_RE.search(raw):
            return NoiseVerdict(False, "no_letters")
        if _ONLY_PUNCT_RE.match(raw) or _MOSTLY_DIGITS_RE.match(raw):
            return NoiseVerdict(False, "not_alphabetic")

        words = [w for w in _TOKEN_SPLIT_RE.split(raw) if w]
        if len(words) > _MAX_CANDIDATE_WORDS:
            return NoiseVerdict(False, "too_many_words")
        return None

    def _check_entity_label(
        self, raw: str, source_label: Optional[str]
    ) -> Optional[NoiseVerdict]:
        """
        An ORG that does not resolve to the taxonomy is an employer or a school.

        spaCy tags `Docker` and `TechCorp` both as ORG. The useful ones already
        resolve through Layer 1 or the EntityRuler, so an *unresolved* ORG is
        the residue: `Techcorp`, `Xyz University`, `StartupXYZ`.
        """
        low = raw.lower().strip(" .,")
        tokens = [t.strip(" .,") for t in _TOKEN_SPLIT_RE.split(low) if t]

        if tokens and tokens[-1] in _ORG_SUFFIXES:
            return NoiseVerdict(False, "organisation_name")
        if any(t in _ORG_SUFFIXES for t in tokens) and len(tokens) > 1:
            return NoiseVerdict(False, "organisation_name")

        if source_label == "ORG":
            return NoiseVerdict(False, "unresolved_org")
        return None

    def _check_lexicon(self, raw: str) -> Optional[NoiseVerdict]:
        """Word-list residue: generic nouns and academic credentials."""
        low = raw.lower().strip(" .,")
        loose = normalize_term(raw)

        if low in _ACADEMIC_TERMS or loose in _ACADEMIC_TERMS:
            return NoiseVerdict(False, "academic_term")
        if low in _GENERIC_TERMS or loose in _GENERIC_TERMS:
            return NoiseVerdict(False, "generic_term")
        if low in _BOILERPLATE_TERMS or loose in _BOILERPLATE_TERMS:
            return NoiseVerdict(False, "boilerplate_term")

        # A multi-word candidate built purely from filler carries no skill.
        tokens = [t.strip(" .,") for t in _TOKEN_SPLIT_RE.split(low) if t]
        if tokens and all(
            t in _FILLER_WORDS or t in _GENERIC_TERMS or t in _BOILERPLATE_TERMS
            for t in tokens
        ):
            return NoiseVerdict(False, "all_filler")

        # "B.Tech Computer Science" — a credential marker anywhere is decisive.
        if any(t in _ACADEMIC_TERMS for t in tokens):
            return NoiseVerdict(False, "academic_term")
        return None

    def _check_verb_form(self, raw: str) -> Optional[NoiseVerdict]:
        """
        Reject inflected verbs: `Mentored`, `Designed`, `Implemented`.

        Only the head token is tested, and only when the candidate does not
        resolve to a real skill — so `Machine Learning` and `Deep Learning`
        survive despite the -ing, and `Continuous Integration` is untouched.
        """
        low = raw.lower().strip(" .,")
        tokens = [t.strip(" .,") for t in _TOKEN_SPLIT_RE.split(low) if t]
        if not tokens:
            return None

        head = tokens[0]

        if head in _ACTION_VERBS:
            return NoiseVerdict(False, "action_verb")

        # Suffix fallback for verbs outside the lexicon. Requires a real stem so
        # "Red" / "Ted" style short words are not swept up, and defers to the
        # taxonomy so a genuine -ed/-ing skill name is never dropped.
        if (
            len(tokens) == 1
            and len(head) > 5
            and head.endswith("ed")
            and self._taxonomy.resolve_skill(raw) is None
        ):
            return NoiseVerdict(False, "inflected_verb")
        return None

    def _check_wraps_known_skill(self, raw: str) -> Optional[NoiseVerdict]:
        """
        Reject a phrase that merely wraps a skill already in the taxonomy.

        `Designed Postgresql` is not a new skill — it is `PostgreSQL` with a
        verb glued on. Only fires when every token outside the known skill is
        filler or a verb, so `React Native` (real, unknown, `Native` is not
        filler) still gets through.
        """
        tokens = [t for t in _TOKEN_SPLIT_RE.split(raw.strip()) if t]
        if len(tokens) < 2:
            return None

        for length in range(len(tokens) - 1, 0, -1):
            for start in range(len(tokens) - length + 1):
                span = " ".join(tokens[start:start + length])
                canonical = self._taxonomy.resolve_skill(span)
                if not canonical:
                    continue

                remainder = [
                    t.lower().strip(" .,")
                    for i, t in enumerate(tokens)
                    if not (start <= i < start + length)
                ]
                if all(
                    t in _FILLER_WORDS or t in _ACTION_VERBS or t in _GENERIC_TERMS
                    for t in remainder
                ):
                    return NoiseVerdict(
                        False, "wraps_known_skill", alias_of=canonical
                    )
        return None

    def _check_fragment(
        self, raw: str, full_text: Optional[str]
    ) -> Optional[NoiseVerdict]:
        """
        Reject a term that only ever occurs glued inside a larger one.

        `CI/CD` is one skill, but a bare-acronym scan splits it and offers `CI`
        as a discovery — and because `CI` recurs in every document that mentions
        CI/CD, corroboration would happily promote it. A candidate is a fragment
        when every occurrence in the document is joined to more text by a
        skill-internal separator (`/`, `-`, `.`, `+`), i.e. it never stands
        alone. Terms that carry their own separator (`scikit-learn`, `Vue.js`)
        are unaffected: their boundaries fall outside the glue.

        A separator only counts as glue when word characters continue on the far
        side of it. `.` is the reason this matters: it joins in `Vue.js` but ends
        a sentence in `…deployed with Terraform.`, and treating those alike
        condemned every skill unlucky enough to land before a full stop.
        """
        if not full_text or not raw:
            return None

        joiners = "/-.+"
        low = full_text.lower()
        pattern = re.compile(rf"\b{re.escape(raw.lower())}\b")

        saw_occurrence = False
        for match in pattern.finditer(low):
            saw_occurrence = True
            start, end = match.start(), match.end()

            # Glue on the right: separator, then the compound continues.
            glued_after = (
                end + 1 < len(low)
                and low[end] in joiners
                and low[end + 1].isalnum()
            )
            # Glue on the left: the compound ran up to a separator. `start >= 2`
            # also makes a term opening the document a clean stand-alone.
            glued_before = (
                start >= 2
                and low[start - 1] in joiners
                and low[start - 2].isalnum()
            )
            if not glued_before and not glued_after:
                return None            # stands alone at least once — genuine
        if saw_occurrence:
            return NoiseVerdict(False, "fragment_of_compound")
        return None

    def _check_similarity(
        self, similarity: float, nearest: Optional[str]
    ) -> Optional[NoiseVerdict]:
        """
        Confidence gate, plus alias absorption.

        Above `alias_absorption_threshold` a "new" term is the same skill spelled
        differently ("Postgres DB" vs "PostgreSQL"); recording it as a separate
        entry would split one skill into two and understate coverage.
        """
        if similarity < self._config.discovery_min_confidence:
            return NoiseVerdict(False, "low_confidence")

        if nearest and similarity >= self._config.alias_absorption_threshold:
            return NoiseVerdict(True, "absorbed_as_alias", alias_of=nearest)
        return None
