"""
NeuroSync — Skill Gap Analyzer.
Context-aware gap intelligence with cluster reasoning and dynamic explanations.
Not template-based — every reasoning string is computed from evidence.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from app.config import Settings
from app.models.domain import (
    CoverageResult, ExtractionResult, RequirementGroup, RequirementSet,
    Skill, SkillGapItem,
)
from app.models.enums import GapPriority, SkillCategory
from app.services.requirement_resolver import CoverageResolver, RequirementParser
from app.utils.skill_taxonomy import SkillTaxonomy

logger = logging.getLogger(__name__)

# Learning time heuristics by category (weeks)
_LEARNING_ESTIMATES: dict[SkillCategory, tuple[str, str]] = {
    SkillCategory.PROGRAMMING: ("4-8 weeks", "8-16 weeks"),      # (familiar, proficient)
    SkillCategory.FRAMEWORK:   ("2-4 weeks", "4-8 weeks"),
    SkillCategory.DATABASE:    ("2-3 weeks", "4-6 weeks"),
    SkillCategory.CLOUD:       ("2-4 weeks", "4-8 weeks"),
    SkillCategory.DEVOPS:      ("2-4 weeks", "4-8 weeks"),
    SkillCategory.ML_AI:       ("4-8 weeks", "8-16 weeks"),
    SkillCategory.SOFT_SKILL:  ("2-4 weeks", "ongoing"),
    SkillCategory.DOMAIN:      ("4-8 weeks", "8-16 weeks"),
    SkillCategory.OTHER:       ("2-4 weeks", "4-8 weeks"),
}


class SkillGapAnalyzer:
    """
    Analyzes the gap between resume skills and JD requirements.

    Goes beyond "missing X" to explain WHY each gap matters:
    - Cluster analysis: what skill groups the user is strong/weak in
    - Importance weighting: taxonomy-driven priority
    - Frequency impact: how many times the JD mentions the skill
    - Related skill proximity: "you have A and B, missing C completes the stack"
    - Confidence scoring per gap
    """

    def __init__(
        self,
        config: Settings,
        taxonomy: SkillTaxonomy,
        parser: Optional[RequirementParser] = None,
        resolver: Optional[CoverageResolver] = None,
    ):
        self._config = config
        self._taxonomy = taxonomy
        self._parser = parser or RequirementParser(config, taxonomy)
        self._resolver = resolver or CoverageResolver(config, taxonomy)

    def analyze(
        self,
        resume_result: ExtractionResult,
        jd_result: ExtractionResult,
        jd_text: str = "",
    ) -> GapAnalysisResult:
        """
        Full gap analysis between resume skills and JD requirements.

        The unit of analysis is a *requirement group*, not a JD skill: an
        "A or B" line is one requirement, and a skill the resume subsumes
        (PostgreSQL → SQL) counts as held. Diffing raw skill sets instead is
        what produced seven phantom gaps in tracker defect D1.

        Args:
            resume_result: skills extracted from resume (with intensity)
            jd_result: skills extracted from JD
            jd_text: raw JD text (for requirement parsing + frequency counting)

        Returns:
            GapAnalysisResult with prioritized gaps and summary stats
        """
        start = time.perf_counter()

        resume_skills = {s.canonical.lower(): s for s in resume_result.skills}

        requirements = self._parser.parse(jd_text, jd_result.skills)
        coverage = self._resolver.resolve(resume_result.skills, requirements)

        # Build skill clusters for the user
        user_clusters = self._build_skill_clusters(resume_result.skills)

        # Compute JD frequency map (how often each skill appears)
        jd_freq = self._compute_jd_frequency(jd_result.skills, jd_text)

        # Analyze each unmet requirement
        gaps: list[SkillGapItem] = [
            self._analyze_single_gap(c.group, resume_skills, user_clusters, jd_freq)
            for c in coverage.coverages if not c.satisfied
        ]

        # Sort by priority: CRITICAL > HIGH > MEDIUM > LOW, then by confidence desc
        priority_order = {
            GapPriority.CRITICAL: 0, GapPriority.HIGH: 1,
            GapPriority.MEDIUM: 2, GapPriority.LOW: 3,
        }
        gaps.sort(key=lambda g: (priority_order.get(g.priority, 4), -g.confidence))

        elapsed = (time.perf_counter() - start) * 1000

        result = GapAnalysisResult(
            gaps=gaps,
            matched_count=coverage.satisfied_count,
            missing_count=coverage.unmet_count,
            total_jd_skills=len(requirements.groups),
            overlap_score=round(coverage.coverage_score, 3),
            critical_count=sum(1 for g in gaps if g.priority == GapPriority.CRITICAL),
            high_count=sum(1 for g in gaps if g.priority == GapPriority.HIGH),
            processing_time_ms=round(elapsed, 2),
            requirements=requirements,
            coverage=coverage,
            total_importance=requirements.total_weighted_importance,
        )

        logger.info(
            "Gap analysis: %d/%d requirements met (%d implied), %d gaps "
            "(%d critical, %d high) in %.1fms",
            result.matched_count, result.total_jd_skills,
            len(coverage.implied_matches), result.missing_count,
            result.critical_count, result.high_count, elapsed,
        )

        return result

    # =========================================================================
    # SINGLE GAP ANALYSIS
    # =========================================================================

    def _analyze_single_gap(
        self,
        group: RequirementGroup,
        resume_skills: dict[str, Skill],
        user_clusters: dict[str, list[str]],
        jd_freq: dict[str, int],
    ) -> SkillGapItem:
        """Analyze one unmet requirement with full context reasoning."""

        canonical = group.primary
        can_lower = canonical.lower()
        category = group.category
        alternatives = [o for o in group.options[1:]]

        # ── Gather evidence ──────────────────────────────────
        importance = group.importance
        related = self._taxonomy.get_related(canonical)
        # An "A or B" requirement is as loud as its loudest member.
        freq_in_jd = max((jd_freq.get(o.lower(), 1) for o in group.options), default=1)

        # Which related skills does the user already have?
        related_present = [
            r for r in related
            if r.lower() in resume_skills
        ]
        related_missing = [
            r for r in related
            if r.lower() not in resume_skills and r.lower() != can_lower
        ]

        # Cluster analysis: is this skill part of a cluster the user is strong in?
        cluster_name = self._get_cluster_name(canonical, category)
        cluster_strength = self._compute_cluster_strength(
            cluster_name, user_clusters, resume_skills
        )

        # ── Compute priority score ───────────────────────────
        priority_score = self._compute_priority_score(
            importance=importance,
            freq_in_jd=freq_in_jd,
            related_present_count=len(related_present),
            related_total=len(related),
            cluster_strength=cluster_strength,
            category=category,
        )

        priority = self._score_to_priority(priority_score)

        # A "nice to have" is never a blocker, however important the skill is
        # in the abstract — the JD itself said it was optional.
        if not group.required and priority in (GapPriority.CRITICAL, GapPriority.HIGH):
            priority = GapPriority.MEDIUM

        # ── Generate reasoning ───────────────────────────────
        reasoning = self._generate_reasoning(
            canonical=canonical,
            priority_score=priority_score,
            importance=importance,
            freq_in_jd=freq_in_jd,
            related_present=related_present,
            related_missing=related_missing,
            cluster_name=cluster_name,
            cluster_strength=cluster_strength,
            alternatives=alternatives,
            optional=not group.required,
        )

        # ── Confidence ───────────────────────────────────────
        confidence = self._compute_confidence(
            importance, freq_in_jd, len(related_present), 1.0
        )

        # ── Learning time ────────────────────────────────────
        learning_time = self._estimate_learning_time(
            category, related_present, cluster_strength
        )

        return SkillGapItem(
            skill=canonical,
            category=category,
            priority=priority,
            reasoning=reasoning,
            learning_time_estimate=learning_time,
            related_present=related_present,
            confidence=round(confidence, 3),
            alternatives=alternatives,
            optional=not group.required,
            importance=importance,
            weight=group.weight,
        )

    # =========================================================================
    # PRIORITY SCORING
    # =========================================================================

    def _compute_priority_score(
        self,
        importance: float,
        freq_in_jd: int,
        related_present_count: int,
        related_total: int,
        cluster_strength: float,
        category: SkillCategory,
    ) -> float:
        """
        Compute raw priority score (0-1). Higher = more critical.

        Formula:
            priority = importance_weight * 0.30
                     + jd_frequency_signal * 0.25
                     + cluster_gap_signal * 0.25
                     + category_weight * 0.20
        """
        # JD frequency signal: mentioned 3+ times = strong signal
        freq_signal = min(1.0, freq_in_jd / 3.0)

        # Cluster gap: if user has MANY related skills but not this one → CRITICAL
        # It's the missing piece that completes the stack
        if related_total > 0:
            related_ratio = related_present_count / related_total
            # Inverted: having MORE related skills makes this gap MORE critical
            # (you're so close, this one skill completes the set)
            cluster_gap = related_ratio * 0.8 + 0.2 if related_present_count > 0 else 0.3
        else:
            cluster_gap = 0.4  # No related info → neutral

        # Category weight: technical skills weigh more than soft skills
        cat_weight = {
            SkillCategory.PROGRAMMING: 0.8,
            SkillCategory.FRAMEWORK: 0.75,
            SkillCategory.CLOUD: 0.85,
            SkillCategory.DATABASE: 0.7,
            SkillCategory.DEVOPS: 0.8,
            SkillCategory.ML_AI: 0.85,
            SkillCategory.DOMAIN: 0.6,
            SkillCategory.SOFT_SKILL: 0.4,
            SkillCategory.OTHER: 0.5,
        }.get(category, 0.5)

        score = (
            importance * 0.30
            + freq_signal * 0.25
            + cluster_gap * 0.25
            + cat_weight * 0.20
        )

        return min(1.0, score)

    @staticmethod
    def _score_to_priority(score: float) -> GapPriority:
        """Convert raw score to discrete priority level."""
        if score >= 0.75:
            return GapPriority.CRITICAL
        elif score >= 0.55:
            return GapPriority.HIGH
        elif score >= 0.35:
            return GapPriority.MEDIUM
        else:
            return GapPriority.LOW

    # =========================================================================
    # REASONING GENERATION (NOT TEMPLATES)
    # =========================================================================

    def _generate_reasoning(
        self,
        canonical: str,
        priority_score: float,
        importance: float,
        freq_in_jd: int,
        related_present: list[str],
        related_missing: list[str],
        cluster_name: str,
        cluster_strength: float,
        alternatives: list[str],
        optional: bool,
    ) -> str:
        """
        Generate dynamic, evidence-based reasoning for why this gap matters.
        Every sentence is derived from computed data — no static templates.
        """
        parts: list[str] = []

        # Only skills that actually belong to this cluster may be cited as
        # coverage *of* it. Citing every related skill regardless of cluster is
        # what produced "coverage in Programming Languages (Docker, Kubernetes)"
        # in tracker defect D3.
        in_cluster = [
            r for r in related_present
            if self._get_cluster_name(r, self._taxonomy.get_category(r)) == cluster_name
        ]
        adjacent = [r for r in related_present if r not in in_cluster]

        # ── Opening: cluster context ─────────────────────────
        if len(in_cluster) >= 3:
            parts.append(
                f"You already have strong coverage in {cluster_name} "
                f"({', '.join(in_cluster[:4])}), but {canonical} is the missing "
                f"link that would complete this skill stack."
            )
        elif in_cluster:
            parts.append(
                f"Your existing {', '.join(in_cluster)} knowledge creates a "
                f"foundation, but without {canonical}, your {cluster_name} "
                f"capability has a significant gap."
            )
        elif adjacent:
            parts.append(
                f"You have adjacent experience in {', '.join(adjacent[:4])}, "
                f"which shortens the path to {canonical}, but nothing in your "
                f"resume covers {cluster_name} itself."
            )
        else:
            parts.append(
                f"{canonical} is required by this role and you currently "
                f"have no directly related skills in {cluster_name}."
            )

        # ── Alternatives: the JD offered a choice and you hold none ──
        if alternatives:
            alt_str = " or ".join(alternatives) if len(alternatives) <= 2 \
                else ", ".join(alternatives[:-1]) + f", or {alternatives[-1]}"
            parts.append(
                f"This requirement accepts alternatives — {alt_str} would "
                f"satisfy it equally — but you hold none of them, so learning "
                f"whichever is closest to your background is enough."
            )

        # ── Optionality: a 'nice to have' is not a blocker ──
        if optional:
            parts.append(
                f"The JD lists {canonical} as a nice-to-have, so this gap "
                f"weakens rather than blocks your candidacy."
            )

        # ── JD emphasis ──────────────────────────────────────
        if freq_in_jd >= 3 and not optional:
            parts.append(
                f"The job description mentions {canonical} {freq_in_jd} times, "
                f"indicating it is a core requirement — not optional."
            )
        elif freq_in_jd == 2:
            parts.append(
                f"{canonical} appears multiple times in the JD, "
                f"suggesting meaningful importance to the role."
            )

        # ── Importance context ───────────────────────────────
        if importance >= 0.8:
            parts.append(
                f"In the broader market, {canonical} carries high importance "
                f"(weight: {importance:.1f}) — it's a key differentiator "
                f"for candidates in this space."
            )
        elif importance >= 0.6:
            parts.append(
                f"{canonical} has moderate-to-high market relevance "
                f"(weight: {importance:.1f})."
            )

        # ── Cluster gap insight ──────────────────────────────
        if cluster_strength >= 0.6 and in_cluster:
            delta_estimate = round(priority_score * 20, 0)
            parts.append(
                f"Adding {canonical} to your existing {cluster_name} skills "
                f"could boost your fit score by an estimated +{delta_estimate:.0f}% "
                f"due to stack completion."
            )

        # ── Missing related cascade ──────────────────────────
        if related_missing and len(related_missing) <= 3:
            missing_str = ", ".join(related_missing[:3])
            parts.append(
                f"Note: {missing_str} {'is' if len(related_missing) == 1 else 'are'} "
                f"also related and missing — addressing {canonical} first would "
                f"create a stronger learning foundation."
            )

        return " ".join(parts)

    # =========================================================================
    # CLUSTER ANALYSIS
    # =========================================================================

    def _build_skill_clusters(
        self, skills: list[Skill]
    ) -> dict[str, list[str]]:
        """
        Group user skills into logical clusters based on taxonomy relationships.
        Returns: cluster_name → list of canonical skill names
        """
        clusters: dict[str, list[str]] = {}

        for skill in skills:
            cluster = self._get_cluster_name(skill.canonical, skill.category)
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(skill.canonical)

            # Also add to related clusters
            for related in skill.related_skills:
                rel_cluster = self._get_cluster_name(
                    related, self._taxonomy.get_category(related)
                )
                if rel_cluster not in clusters:
                    clusters[rel_cluster] = []
                # Don't duplicate
                if skill.canonical not in clusters[rel_cluster]:
                    clusters[rel_cluster].append(skill.canonical)

        return clusters

    def _get_cluster_name(self, skill: str, category: SkillCategory) -> str:
        """
        Derive a human-readable cluster name from skill + category.
        Uses taxonomy relationships to form meaningful groups.
        """
        related = self._taxonomy.get_related(skill)

        # Infer cluster from relationships
        related_lower = {r.lower() for r in related}

        if category == SkillCategory.CLOUD:
            if any(k in skill.lower() for k in ["aws", "ec2", "s3", "lambda", "ecs", "eks"]):
                return "AWS Cloud"
            if any(k in skill.lower() for k in ["azure", "aks"]):
                return "Azure Cloud"
            if any(k in skill.lower() for k in ["gcp", "bigquery", "cloud run"]):
                return "Google Cloud"
            return "Cloud Infrastructure"

        if category == SkillCategory.DEVOPS:
            if "kubernetes" in related_lower or "docker" in related_lower:
                return "Container & Orchestration"
            if "ci/cd" in related_lower or "jenkins" in related_lower:
                return "CI/CD Pipeline"
            return "DevOps & Infrastructure"

        if category == SkillCategory.ML_AI:
            if "deep learning" in related_lower or "neural networks" in related_lower:
                return "Deep Learning"
            if "nlp" in related_lower or "llm" in related_lower:
                return "NLP & Language AI"
            if "data science" in related_lower or "pandas" in related_lower:
                return "Data Science & Analytics"
            return "Machine Learning"

        if category == SkillCategory.FRAMEWORK:
            if "react" in related_lower or "angular" in related_lower or "vue" in related_lower:
                return "Frontend Frameworks"
            if "python" in related_lower or "java" in related_lower:
                return "Backend Frameworks"
            return "Frameworks & Libraries"

        if category == SkillCategory.PROGRAMMING:
            return "Programming Languages"

        if category == SkillCategory.DATABASE:
            if "nosql" in related_lower:
                return "NoSQL Databases"
            return "Databases & Storage"

        if category == SkillCategory.SOFT_SKILL:
            return "Professional Skills"

        return category.value.replace("_", " ").title()

    def _compute_cluster_strength(
        self,
        cluster_name: str,
        user_clusters: dict[str, list[str]],
        resume_skills: dict[str, Skill],
    ) -> float:
        """
        How strong is the user in this cluster? (0-1)
        Considers both count and proficiency of skills in the cluster.
        """
        cluster_skills = user_clusters.get(cluster_name, [])
        if not cluster_skills:
            return 0.0

        # Average proficiency of skills in this cluster
        proficiencies = []
        for skill_name in cluster_skills:
            skill = resume_skills.get(skill_name.lower())
            if skill:
                proficiencies.append(skill.proficiency_score)

        if not proficiencies:
            return 0.0

        avg_prof = sum(proficiencies) / len(proficiencies)
        count_factor = min(1.0, len(proficiencies) / 3.0)  # 3+ skills = full factor

        return round(avg_prof * 0.6 + count_factor * 0.4, 3)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _compute_jd_frequency(
        self, jd_skills: list[Skill], jd_text: str
    ) -> dict[str, int]:
        """Count how many times each skill appears in JD text."""
        freq: dict[str, int] = {}
        jd_lower = jd_text.lower()
        for skill in jd_skills:
            key = skill.canonical.lower()
            # Use occurrence_count if available, otherwise count in text
            if skill.occurrence_count > 1:
                freq[key] = skill.occurrence_count
            else:
                count = jd_lower.count(key)
                freq[key] = max(1, count)
        return freq

    def _compute_confidence(
        self,
        importance: float,
        freq_in_jd: int,
        related_present_count: int,
        extraction_confidence: float,
    ) -> float:
        """
        Confidence that this gap assessment is correct.
        Higher when: JD clearly requires it, taxonomy knows it, user context is clear.
        """
        # Base: extraction confidence (was the JD skill correctly identified?)
        conf = extraction_confidence * 0.4

        # Taxonomy knowledge (we know this skill well)
        if importance > 0.0:
            conf += 0.3  # Known skill
        else:
            conf += 0.1  # Unknown/discovered skill

        # JD clarity (mentioned multiple times = clearly required)
        conf += min(0.2, freq_in_jd * 0.07)

        # Context clarity (we know related skills = better assessment)
        if related_present_count > 0:
            conf += 0.1

        return min(1.0, conf)

    def _estimate_learning_time(
        self,
        category: SkillCategory,
        related_present: list[str],
        cluster_strength: float,
    ) -> str:
        """
        Estimate learning time based on category and existing knowledge.
        If user already has related skills, learning is faster.
        """
        base_familiar, base_proficient = _LEARNING_ESTIMATES.get(
            category, ("2-4 weeks", "4-8 weeks")
        )

        # If user has related skills, they'll learn faster
        if related_present and cluster_strength >= 0.5:
            return f"{base_familiar} (accelerated — you already know {related_present[0]})"
        elif related_present:
            return f"{base_familiar} (your {related_present[0]} background helps)"
        else:
            return base_proficient


# =========================================================================
# OUTPUT MODEL
# =========================================================================

from pydantic import BaseModel, Field


class GapAnalysisResult(BaseModel):
    """Complete gap analysis output."""
    gaps: list[SkillGapItem] = Field(default_factory=list)
    matched_count: int = 0
    missing_count: int = 0
    total_jd_skills: int = 0            # Requirement groups, not raw JD skills
    overlap_score: float = 0.0          # 0-1 weighted credit / total importance
    critical_count: int = 0
    high_count: int = 0
    processing_time_ms: float = 0.0

    # --- Requirement semantics (D1) ---
    # Carried through so the scorer works off what the JD actually asks for
    # rather than re-diffing raw skill sets.
    requirements: RequirementSet = Field(default_factory=RequirementSet)
    coverage: CoverageResult = Field(default_factory=CoverageResult)
    total_importance: float = 0.0       # Σ weight × importance over all groups
