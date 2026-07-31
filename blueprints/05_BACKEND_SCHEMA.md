# NeuroSync — Backend Schema

**Version**: 1.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE

---

## 1. Data Models

### Model Hierarchy

```text
User
 ├── CareerProfile
 │    ├── ResumeSnapshot[]
 │    └── TargetRole[]
 ├── Analysis[]
 │    ├── ExtractionResult (resume)
 │    ├── ExtractionResult (jd)
 │    ├── SemanticResult
 │    ├── GapResult
 │    └── Decision
 ├── Feedback[]
 └── CareerTrajectory
      └── TrajectorySnapshot[]
```

---

### Core Models

#### Skill

The fundamental unit of the system. Every skill carries metadata about HOW it was found and HOW well the candidate knows it.

```python
class Skill(BaseModel):
    name: str                              # Raw text as found ("ReactJS")
    canonical: str                         # Normalized ("React")
    category: SkillCategory                # frontend | backend | data | etc.
    confidence: float                      # 0.0 - 1.0 (extraction confidence)
    matched_by: MatchMethod                # taxonomy | ner | semantic | embedding
    proficiency_score: float               # 0.0 - 1.0 (HOW WELL they know it)
    evidence_strength: float               # 0.0 - 1.0 (HOW STRONG the evidence)
    occurrence_count: int                   # How many times mentioned
    found_in_sections: list[str]           # ["experience", "projects"]
    aliases: list[str]                     # ["ReactJS", "React.js"]
    related_skills: list[str]             # ["Redux", "Next.js"]
```

#### ExtractionResult

Output of the 4-layer extraction pipeline.

```python
class ExtractionResult(BaseModel):
    skills: list[Skill]                    # All extracted skills
    extraction_methods_used: list[str]     # ["taxonomy", "ner", "semantic"]
    degraded: bool                         # True if any layer failed
    failed_layers: list[str]              # ["ner"] if spaCy crashed
    processing_time_ms: float
```

#### SkillGapItem

A single missing skill with full reasoning.

```python
class SkillGapItem(BaseModel):
    skill: str                             # Canonical skill name
    category: SkillCategory
    priority: GapPriority                  # critical | high | medium | low
    reasoning: str                         # Dynamic explanation (not template)
    learning_time_estimate: str | None     # "3-4 weeks"
    related_present: list[str]            # Related skills user HAS
    confidence: float                      # 0.0 - 1.0
```

#### GapResult

Complete gap analysis output.

```python
class GapResult(BaseModel):
    gaps: list[SkillGapItem]              # All missing skills with reasoning
    matched_skills: list[SkillMatch]      # Skills found in both documents
    overlap_score: float                   # 0.0 - 1.0
    matched_count: int
    missing_count: int
    gap_clusters: dict[str, list[str]]    # {"Cloud": ["K8s", "Terraform"]}
    critical_gap_count: int
    high_gap_count: int
```

#### ScoringBreakdown

Transparent scoring with full explainability.

```python
class ScoringBreakdown(BaseModel):
    semantic_score: float | None           # 0.0 - 1.0 (None if unavailable)
    skill_overlap_score: float | None
    gap_penalty: float | None
    weights_used: dict[str, float]        # {"semantic": 0.40, "skill": 0.35}
    final_score: float                     # 0.0 - 100.0
    confidence: float                      # 0.0 - 1.0
    explanation: str                       # Human-readable scoring explanation
```

#### Decision

The central output — recommendation + reasoning + simulations.

```python
class Decision(BaseModel):
    recommendation: Recommendation         # STRONG_APPLY | APPLY | etc.
    confidence: float
    shortlist_probability: float
    fit_level: FitLevel                    # STRONG | GOOD | POTENTIAL | WEAK | NO_FIT
    overall_score: float                   # 0.0 - 100.0
    reasoning: str                         # Multi-factor reasoning text
    scoring: ScoringBreakdown
    strengths: list[str]
    weaknesses: list[str]
    improvement_path: list[ImprovementAction]
    top_simulations: list[WhatIfSimulation]
    evidence: list[EvidenceItem]
```

#### ImprovementAction

ROI-ranked skill to learn.

```python
class ImprovementAction(BaseModel):
    roi_rank: int                          # 1 = highest ROI
    skill: str                             # Skill to learn
    impact_score_delta: float             # Expected score improvement
    learning_time: str                     # "3-4 weeks"
    reasoning: str                         # Why this skill has highest ROI
```

#### WhatIfSimulation

Full pipeline re-simulation with one skill added.

```python
class WhatIfSimulation(BaseModel):
    skill_added: str                       # The skill hypothetically added
    current_score: float
    projected_score: float
    delta: float                           # Score improvement
    new_fit_level: FitLevel
    new_shortlist_probability: float
```

---

### User & Session Models (Phase 2)

#### User

```python
class User(BaseModel):
    id: str                                # UUID
    email: str
    name: str
    created_at: datetime
    career_profile: CareerProfile | None
```

#### CareerProfile

```python
class CareerProfile(BaseModel):
    user_id: str
    current_role: str | None
    target_roles: list[str]
    years_experience: int | None
    education_level: str | None
    location: str | None
    resume_snapshots: list[ResumeSnapshot]
```

#### ResumeSnapshot

```python
class ResumeSnapshot(BaseModel):
    id: str
    user_id: str
    text: str                              # Raw resume text
    extracted_skills: list[Skill]
    created_at: datetime
```

#### Analysis

```python
class Analysis(BaseModel):
    id: str                                # analysis_id
    user_id: str | None                    # None for anonymous
    resume_text: str
    jd_text: str
    resume_skills: ExtractionResult
    jd_skills: ExtractionResult
    semantic_result: SemanticResult | None
    gap_result: GapResult
    decision: Decision
    created_at: datetime
    processing_time_ms: float
```

#### Feedback

```python
class Feedback(BaseModel):
    id: str
    analysis_id: str
    user_id: str | None
    outcome: str                           # "interview" | "hired" | "rejected" | "ghosted"
    notes: str
    decision_snapshot: Decision            # The decision that was made
    created_at: datetime
```

---

### Market & Trajectory Models (Phase 3)

#### MarketSignal

```python
class MarketSignal(BaseModel):
    skill: str
    demand_trend: float                    # +0.37 = 37% increase
    demand_period: str                     # "6 months"
    salary_range: tuple[int, int] | None   # (min, max) in local currency
    hiring_velocity: int | None            # Openings per month
    source: str                            # "curated" | "api"
    last_updated: datetime
```

#### TrajectorySnapshot

```python
class TrajectorySnapshot(BaseModel):
    user_id: str
    skills: list[Skill]
    target_role: str
    score: float
    timestamp: datetime
```

---

### Human State Intelligence Models (Phase 2+) ★ NEW

> These models transform NeuroSync from Resume Intelligence to Human + Career Intelligence.
> Hierarchy: AgentObservation → StateObservation → CareerState → StateTransition

#### ObservationSource

Every signal carries its source. Agent decisions operate on CareerState, not raw signals.

```python
class ObservationSource(str, Enum):
    RESUME = "resume"
    JD = "jd"
    FEEDBACK = "feedback"
    LEARNING = "learning"
    PROJECT = "project"
    INTERVIEW = "interview"
    MARKET = "market"
    CAMERA = "camera"               # OPTIONAL — system is 95% functional without it
```

#### AgentObservation

Raw signal from any observation source. The agent memory layer.

```python
class AgentObservation(BaseModel):
    id: str                                 # UUID
    user_id: str
    source: ObservationSource              # WHERE the signal came from
    signal: str                            # "engagement_low", "completion_drop", "focus_high"
    confidence: float                      # 0.0 - 1.0
    raw_data: dict | None                  # Optional raw payload (never stored for camera)
    timestamp: datetime
```

#### StateObservation

Derived observation — NOT raw events. Aggregated from multiple AgentObservations.

```python
class StateObservation(BaseModel):
    id: str
    user_id: str
    signal: str                             # "struggling", "accelerating", "disengaged"
    derived_from: list[ObservationSource]   # [CAMERA, LEARNING, PROJECT]
    contributing_observations: list[str]    # AgentObservation IDs
    confidence: float                       # 0.0 - 1.0
    timestamp: datetime
```

#### CareerState

The unified state representation. All agent decisions consume this — never raw signals.

```python
class CareerState(BaseModel):
    user_id: str
    confidence_score: float                 # 0.0 - 1.0 — self-efficacy
    momentum_score: float                   # 0.0 - 1.0 — rate of improvement
    engagement_score: float                 # 0.0 - 1.0 — active participation
    consistency_score: float                # 0.0 - 1.0 — regularity of effort
    growth_velocity: float                  # score points/month
    burnout_risk: float                     # 0.0 - 1.0 — predicted burnout
    interview_readiness: float              # 0.0 - 1.0 — can they pass?
    career_readiness: float                 # 0.0 - 1.0 — should they apply now?
    updated_at: datetime
```

#### StateTransition

Agent memory of growth — tracks before/after states with reasoning.

```python
class StateTransition(BaseModel):
    id: str
    user_id: str
    previous_state: CareerState
    new_state: CareerState
    reason: str                             # "Engagement dropped 60% over 3 days"
    triggered_actions: list[str]            # ["pause_roadmap", "reduce_workload"]
    timestamp: datetime
```

#### LearningSession

Tracks learning activity for Human State Intelligence.

```python
class LearningSession(BaseModel):
    id: str
    user_id: str
    roadmap_id: str | None
    skill_focus: str                        # Canonical skill being learned
    duration_minutes: int
    completion_rate: float                  # 0.0 - 1.0
    engagement_score: float                 # 0.0 - 1.0 (derived)
    abandoned: bool
    started_at: datetime
    ended_at: datetime | None
```

## 2. Enums

```python
class SkillCategory(str, Enum):
    LANGUAGE = "language"
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    DATA = "data"
    AI_ML = "ai_ml"
    CLOUD = "cloud"
    TESTING = "testing"
    MOBILE = "mobile"
    TOOL = "tool"
    SOFT_SKILL = "soft_skill"
    INFRASTRUCTURE = "infrastructure"
    SECURITY = "security"
    OTHER = "other"

class MatchMethod(str, Enum):
    TAXONOMY = "taxonomy"
    NER = "ner"
    SEMANTIC = "semantic"
    EMBEDDING = "embedding"
    CONTEXT = "context"

class GapPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class FitLevel(str, Enum):
    STRONG_FIT = "strong_fit"
    GOOD_FIT = "good_fit"
    POTENTIAL_FIT = "potential_fit"
    WEAK_FIT = "weak_fit"
    NO_FIT = "no_fit"

class Recommendation(str, Enum):
    STRONG_APPLY = "strong_apply"
    APPLY = "apply"
    APPLY_WITH_PREPARATION = "apply_with_preparation"
    UPSKILL_THEN_APPLY = "upskill_then_apply"
    DO_NOT_APPLY = "do_not_apply"

class InsightType(str, Enum):
    STRENGTH = "strength"
    WEAKNESS = "weakness"
    OPPORTUNITY = "opportunity"
    THREAT = "threat"
```

---

## 3. Model Relationships

```text
┌──────┐  1    N  ┌──────────┐
│ User │──────────│ Analysis │
└──┬───┘          └────┬─────┘
   │                   │
   │ 1    1            │ 1    1
   │                   │
┌──▼──────────┐  ┌─────▼──────────┐
│ CareerProfile│  │   Decision     │
└──┬──────────┘  │ ├─ Scoring     │
   │             │ ├─ Simulations │
   │ 1    N      │ ├─ Improvements│
   │             │ └─ Evidence    │
┌──▼──────────┐  └────────────────┘
│ResumeSnapshot│
└─────────────┘         │
                        │
                   1    │    N
              ┌─────────▼──────┐
              │   Feedback     │
              │ (outcome →     │
              │  calibration)  │
              └────────────────┘
```

---

## 4. API Contracts

### POST /api/v1/analyze

**Request:**

```json
{
  "resume_text": "string (50-50000 chars)",
  "jd_text": "string (20-20000 chars)",
  "include_simulations": true,
  "include_evidence": true
}
```

**Response (200):**

```json
{
  "analysis_id": "a1b2c3d4e5f6",
  "decision": {
    "recommendation": "apply_with_preparation",
    "confidence": 0.78,
    "shortlist_probability": 0.55,
    "fit_level": "potential_fit",
    "overall_score": 62.4,
    "reasoning": "string"
  },
  "scoring": {
    "semantic_score": 0.74,
    "skill_overlap_score": 0.65,
    "gap_penalty": 0.28,
    "final_score": 62.4,
    "explanation": "string"
  },
  "skills": {
    "resume_count": 12,
    "jd_count": 8,
    "matched": 6,
    "missing": 2,
    "overlap_score": 0.75,
    "resume_skills": [{ ... }]
  },
  "gaps": [{ ... }],
  "improvement_path": [{ ... }],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "simulations": [{ ... }],
  "evidence": [{ ... }],
  "semantic": { ... },
  "meta": {
    "processing_time_ms": 423.7,
    "extraction_degraded": false,
    "semantic_available": true
  }
}
```

### POST /api/v1/feedback

**Request:**

```json
{
  "analysis_id": "a1b2c3d4e5f6",
  "outcome": "interview",
  "notes": "Got past screening round"
}
```

**Response (200):**

```json
{
  "status": "recorded",
  "analysis_id": "a1b2c3d4e5f6",
  "outcome": "interview",
  "decision_found": true,
  "feedback_stats": {
    "total_feedbacks": 15,
    "by_outcome": { "interview": 4, "rejected": 8, "hired": 2, "ghosted": 1 }
  }
}
```

### GET /api/v1/health

**Response (200):**

```json
{
  "status": "healthy",
  "taxonomy_loaded": true,
  "taxonomy_skill_count": 294,
  "embedding_model_loaded": true,
  "spacy_model_loaded": true,
  "embedding_store_ready": true,
  "feedback_count": 0,
  "versions": { "engine": "1.0.0", "taxonomy": "1.0.0", "api": "v1" }
}
```

### POST /api/v1/quick-score (Planned)

**Request:**

```json
{
  "resume_text": "string",
  "jd_text": "string"
}
```

**Response (200):**

```json
{
  "score": 72.5,
  "fit_level": "good_fit",
  "top_gaps": ["Kubernetes", "Terraform"],
  "processing_time_ms": 180.2
}
```

### GET /api/v1/career-roadmap (Planned)

**Response (200):**

```json
{
  "user_id": "string",
  "target_role": "Senior Backend Engineer",
  "current_score": 62,
  "trajectory": {
    "growth_velocity": 5.7,
    "estimated_ready_date": "2026-10-01",
    "snapshots": [{ ... }]
  },
  "recommended_skills": [{ ... }]
}
```

### GET /api/v1/market-intelligence (Planned)

**Response (200):**

```json
{
  "skills": [
    {
      "skill": "Kubernetes",
      "demand_trend": 0.37,
      "salary_impact": "+18%",
      "hiring_velocity": 2400
    }
  ]
}
```

---

## 5. State Layer

### Interface

```python
class StateBackend(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any: ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def list_keys(self, prefix: str) -> list[str]: ...
```

### Implementations

| Backend | Use Case | Configuration |
| --- | --- | --- |
| **MemoryState** | Development, testing, single-pod | `NEUROSYNC_STATE_BACKEND=memory` |
| **RedisState** | Production, multi-pod, persistence | `NEUROSYNC_STATE_BACKEND=redis` |
| **PostgresState** | Long-term storage, analytics (future) | `NEUROSYNC_STATE_BACKEND=postgres` |

### State Keys

| Key Pattern | Data | TTL |
| --- | --- | --- |
| `analysis:{id}` | Cached Decision | 24h |
| `feedback:log` | List of feedback entries | Permanent |
| `feedback:stats` | Aggregated statistics | Recomputed on write |
| `scoring:weights` | Current calibrated weights | Permanent |
| `taxonomy:runtime:{skill}` | Runtime-discovered skills | Permanent |
| `trajectory:{user_id}` | User trajectory snapshots | 365 days |

### Vector Storage (Future)

| Store | Purpose | Data |
| --- | --- | --- |
| **Taxonomy embeddings** | Skill discovery | 294 × 384-dim vectors (in-memory) |
| **Resume embeddings** | Similar resume retrieval | Per-user, 384-dim (Qdrant/Pinecone) |
| **JD embeddings** | Similar JD clustering | Per-analysis, 384-dim |

---

*This document is the contract between frontend and backend, between services, and between system and storage. All implementations conform to these schemas.*
