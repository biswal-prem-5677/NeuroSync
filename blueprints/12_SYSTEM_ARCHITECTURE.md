# NeuroSync — System Architecture (Source of Truth)

**Version**: 2.0.0
**Author**: Priyabrata Biswal
**Date**: June 2026
**Status**: ACTIVE

> **This is the definitive architecture document.**
> Every file, every service, every data structure, every call chain traces back here.
> If this document and any other document disagree — this document wins.

---

## 1. Layer Map — Who Lives Where

```text
┌───────────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — INPUT                                                         │
│  Receives raw input, validates, normalizes                               │
│  Owner: API Layer + Utils                                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ API Request  │ │  Resume PDF  │ │  Resume DOCX │ │  Raw Text    │    │
│  │ (JSON body)  │ │              │ │              │ │              │    │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘    │
│         └────────────────┴────────────────┴────────────────┘            │
│                                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │
│  │ Camera Signal│ │Learning Event│ │Project Signal│ │Interview Data│    │
│  │  (OPTIONAL)  │ │              │ │              │ │              │    │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘    │
│         └────────────────┴────────────────┴────────────────┘            │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────┐
│  LAYER 2 — PROCESSING                                                    │
│  Cleans text, extracts from files, prepares for intelligence             │
│  Owner: text_processor.py, file_parser.py                                │
│  ┌──────────────┐ ┌──────────────┐                                      │
│  │Text Processor│ │ File Parser  │                                      │
│  │(clean, chunk,│ │(PDF → text,  │                                      │
│  │ section det.)│ │ DOCX → text) │                                      │
│  └──────┬───────┘ └──────┬───────┘                                      │
│         └────────────────┘                                              │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────┐
│  LAYER 3 — INTELLIGENCE                                                  │
│  Extracts skills, computes semantic similarity, analyzes gaps            │
│  Owner: skill_extractor.py, semantic_engine.py, skill_gap_analyzer.py    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │   Skill      │ │   Semantic   │ │   Skill Gap  │                    │
│  │  Extractor   │ │    Engine    │ │   Analyzer   │                    │
│  │ (4-layer     │ │ (3-layer     │ │ (reasoning,  │                    │
│  │  hybrid)     │ │  similarity) │ │  clustering) │                    │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘                    │
│         └────────────────┴────────────────┘                            │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────┐
│  LAYER 3.5 — HUMAN STATE INTELLIGENCE  ★ NEW                             │
│  Observes behavioral signals → derives CareerState → predicts outcomes   │
│  Owner: human_state_engine.py, agent_decision_engine.py                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ Human State  │ │ Agent        │ │ Prediction   │ │ Gamification │   │
│  │ Intelligence │ │ Decision     │ │ Layer        │ │ Engine       │   │
│  │ Engine       │ │ Engine       │ │ (burnout,    │ │ (XP, levels, │   │
│  │ (8 sources → │ │ (CareerState │ │  dropout,    │ │  streaks)    │   │
│  │  CareerState)│ │  → actions)  │ │  readiness)  │ │              │   │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘   │
│         └────────────────┴────────────────┴────────────────┘           │
│  Camera signals are OPTIONAL — system is 95% functional without them   │
└───────────────────────────────────────┬───────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────┐
│  LAYER 4 — DECISION (Fusion Layer)                                       │
│  Orchestrates full pipeline, scores, decides, simulates                  │
│  Owner: intelligence_engine.py, decision_engine.py [FUTURE]              │
│  ┌──────────────────────┐ ┌──────────────────────┐                      │
│  │ Intelligence Engine  │ │  Decision Engine     │                      │
│  │ (Central Brain —     │ │  (Apply? Probability │                      │
│  │  orchestrates L2-L7, │ │   What-If, ROI)      │                      │
│  │  computes score,     │ │  [FUTURE: Phase 2]   │                      │
│  │  produces Decision)  │ │                      │                      │
│  └──────────┬───────────┘ └──────────────────────┘                      │
└─────────────┼─────────────────────────────────────────────────────────────┘
              │
┌─────────────▼─────────────────────────────────────────────────────────────┐
│  LAYER 5 — REASONING                                                     │
│  Explains every decision with evidence chains, generates insights        │
│  Owner: reasoning_engine.py, insights_engine.py                          │
│  ┌──────────────┐ ┌──────────────┐                                      │
│  │  Reasoning   │ │   Insights   │                                      │
│  │   Engine     │ │    Engine    │                                      │
│  │ (evidence    │ │ (SWOT from   │                                      │
│  │  chains →    │ │  analysis    │                                      │
│  │  explanation)│ │  data)       │                                      │
│  └──────────────┘ └──────────────┘                                      │
└───────────────────────────────────────────────────────────────────────────┘
              │
┌─────────────▼─────────────────────────────────────────────────────────────┐
│  LAYER 6 — LEARNING                                                      │
│  System gets smarter over time through feedback                          │
│  Owner: feedback_processor.py, adaptive_scorer.py,                       │
│         career_trajectory_engine.py [FUTURE]                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │  Feedback    │ │  Adaptive    │ │  Trajectory  │                    │
│  │  Processor   │ │   Scorer     │ │   Engine     │                    │
│  │ (stores,     │ │ (learnable   │ │ (growth      │                    │
│  │  triggers    │ │  weights,    │ │  velocity,   │                    │
│  │  recalibrate)│ │  phases 1-3) │ │  prediction) │                    │
│  └──────────────┘ └──────────────┘ └──────────────┘                    │
│                                     [FUTURE: Phase 2+]                  │
└───────────────────────────────────────────────────────────────────────────┘
              │
┌─────────────▼─────────────────────────────────────────────────────────────┐
│  LAYER 7 — EXTERNAL INTELLIGENCE                                         │
│  Optional enrichment from external sources                               │
│  Owner: market_intelligence_engine.py, llm_enhancer.py                   │
│  ┌──────────────┐ ┌──────────────┐                                      │
│  │   Market     │ │     LLM      │                                      │
│  │ Intelligence │ │   Enhancer   │                                      │
│  │ (demand      │ │ (Gemini/     │                                      │
│  │  trends,     │ │  OpenAI —    │                                      │
│  │  salary,     │ │  optional    │                                      │
│  │  velocity)   │ │  refinement) │                                      │
│  └──────────────┘ └──────────────┘                                      │
│  [FUTURE: Phase 2+]                                                     │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Registry — Who Owns What

### Layer 1: Input

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **API Endpoints** | `api/v1/endpoints/analyze.py` | HTTP request validation | Validates JSON body, generates `analysis_id`, delegates to IntelligenceEngine |
| **API Endpoints** | `api/v1/endpoints/feedback.py` | HTTP feedback intake | Validates feedback, delegates to IntelligenceEngine |
| **API Endpoints** | `api/v1/endpoints/health.py` | System status | Queries all components, returns health report |
| **DI Container** | `api/deps.py` | Service lifecycle | Lazy singleton creation, startup warming |
| **Config** | `config.py` | All tunable parameters | Env-var driven, zero hardcoding, Pydantic Settings |

### Layer 2: Processing

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Text Processor** | `utils/text_processor.py` | Text normalization | `clean_text()`, `normalize_for_matching()`, `extract_sections()`, `chunk_text()` |
| **File Parser** | `utils/file_parser.py` | File → text extraction | PDF (PyPDF2 + pdfplumber), DOCX, TXT → `ParsedDocument` |

### Layer 3: Intelligence

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Skill Extractor** | `services/skill_extractor.py` | Skill discovery from text | 4-layer extraction (taxonomy → NER → semantic → embedding discovery) → `ExtractionResult` |
| **Semantic Engine** | `services/semantic_engine.py` | Document similarity | 3-layer similarity (section → chunk → skill-aligned) → `SemanticResult` |
| **Skill Gap Analyzer** | `services/skill_gap_analyzer.py` | Gap reasoning | Priority computation, clustering, reasoning chains → `GapResult` |
| **Skill Taxonomy** | `utils/skill_taxonomy.py` | Canonical skill knowledge | Loads JSON, resolves aliases, relationships, runtime extension |
| **Embedding Store** | `utils/embedding_store.py` | Skill embedding index | Pre-computed embeddings, nearest-skill lookup, unknown skill discovery |

### Layer 3.5: Human State Intelligence ★ NEW

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Human State Engine** | `services/human_state_engine.py` | Behavioral state computation | Aggregates 8 observation sources → derives CareerState → detects StateTransitions → runs Prediction Layer |
| **Agent Decision Engine** | `services/agent_decision_engine.py` | Agentic decision-making | Consumes CareerState (NEVER raw signals) → checks prediction thresholds → generates recommendations |
| **Gamification Engine** | `services/gamification_engine.py` | Career XP & motivation | Levels, streaks, XP calculation, motivation reinforcement |
| **Behavior Endpoints** | `api/v1/endpoints/behavior.py` | HTTP behavior intake | Session start/stop, event recording, state/profile retrieval |
| **CareerState Model** | `models/career_state.py` | State domain models | `CareerState`, `StateObservation`, `StateTransition`, `LearningSession` |
| **Observation Model** | `models/observation.py` | Signal domain models | `ObservationSource` enum, `AgentObservation` |

> **Camera signals are permanently optional.** The system operates at 95% capability without camera. No raw video is ever stored.

### Layer 4: Decision

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Intelligence Engine** | `services/intelligence_engine.py` | **Full pipeline orchestration** | THE BRAIN. Calls L2→L3→L3.5→L5→L6→L7. Produces `Decision`. Owns composite scoring, caching, meta-decisions |
| **Decision Engine** | `services/decision_engine.py` | Apply/don't-apply decisions | [FUTURE] Recommendations, shortlist probability, what-if simulations. Currently embedded in IntelligenceEngine |

### Layer 5: Reasoning

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Reasoning Engine** | `services/reasoning_engine.py` | Explanation synthesis | Evidence-chain assembly → natural language reasoning text |
| **Insights Engine** | `services/insights_engine.py` | SWOT generation | Strengths, weaknesses, opportunities from analysis data |

### Layer 6: Learning

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Feedback Processor** | `services/feedback_processor.py` | Feedback ingestion | Stores outcomes, triggers recalibration, taxonomy suggestions |
| **Adaptive Scorer** | `services/adaptive_scorer.py` | Score weights | Phase 1: config defaults. Phase 2: feedback-adjusted. Phase 3: trained model |
| **Trajectory Engine** | `services/career_trajectory_engine.py` | Growth tracking | [FUTURE] Snapshots, velocity, prediction |

### Layer 7: External Intelligence

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **Market Intelligence** | `services/market_intelligence_engine.py` | Market context | [FUTURE] Skill demand trends, salary signals, hiring velocity |
| **LLM Enhancer** | `services/llm_enhancer.py` | Optional AI refinement | Receives computed facts (not raw text), refines reasoning into prose. Graceful degradation to `null` |

### Cross-Cutting: State

| Component | File | Owns | Responsibility |
| --- | --- | --- | --- |
| **State Backend** | `state/base.py` | Abstract persistence interface | `store_feedback()`, `get_scoring_weights()`, `store_analysis()` |
| **Memory State** | `state/memory_state.py` | Dev/test implementation | In-memory, no external deps |
| **Redis State** | `state/redis_state.py` | Production implementation | Shared across pods, horizontal scaling |

---

## 3. Call Chain — Who Calls Whom

### Primary Analysis Flow

```text
Client
  │
  ▼
analyze.py (Layer 1)
  │  validates request, generates analysis_id
  │
  ▼
IntelligenceEngine.analyze() (Layer 4) ← THE SINGLE ENTRY POINT
  │
  ├──► TextProcessor.clean_text(resume)     (Layer 2)  → resume_clean: str
  ├──► TextProcessor.clean_text(jd)         (Layer 2)  → jd_clean: str
  │
  │    ┌─── PARALLEL ──────────────────────────────────────────────┐
  ├──► │ SkillExtractor.extract(resume_clean)  (Layer 3) → ExtractionResult  │
  ├──► │ SkillExtractor.extract(jd_clean)      (Layer 3) → ExtractionResult  │
  ├──► │ SemanticEngine.compute_similarity()   (Layer 3) → SemanticResult    │
  │    └───────────────────────────────────────────────────────────┘
  │
  ├──► SkillGapAnalyzer.analyze()            (Layer 3)  → GapResult
  │       (receives: matched_skills, missing_skills, resume_skills, jd_skills)
  │
  ├──► AdaptiveScorer.score()                (Layer 6)  → ScoringResult
  │       (receives: {semantic, skill_overlap, gap_penalty})
  │
  ├──► ReasoningEngine.generate_trace()      (Layer 5)  → ReasoningTrace
  │       (receives: semantic, skills, gaps, score)
  │
  ├──► InsightsEngine.generate()             (Layer 5)  → list[Insight]
  │       (receives: semantic, skills, gaps, score)
  │
  ├──► LLMEnhancer.enhance() [optional]     (Layer 7)  → LLMResult | None
  │       (receives: reasoning_trace, insights — NEVER raw text)
  │
  └──► Assembles → Decision (returned to API layer)
```

### Feedback Flow

```text
Client
  │
  ▼
feedback.py (Layer 1)
  │  validates analysis_id + outcome
  │
  ▼
IntelligenceEngine.submit_feedback() (Layer 4)
  │
  ├──► StateBackend.get_analysis(analysis_id)    → cached Decision | None
  │
  ├──► FeedbackProcessor.process()               (Layer 6)
  │       ├──► StateBackend.store_feedback()
  │       ├──► SkillTaxonomy.register_discovered_skill()  (if new skill)
  │       └──► AdaptiveScorer.record_feedback()
  │
  └──► Returns FeedbackResult
```

### Health Check Flow

```text
Client
  │
  ▼
health.py (Layer 1)
  │
  ├──► SkillTaxonomy.count()
  ├──► EmbeddingStore.is_ready()
  ├──► SemanticEngine.is_available()
  ├──► IntelligenceEngine.is_available()
  ├──► StateBackend.get_feedback_stats()
  │
  └──► Returns HealthResponse
```

### Behavior Event Flow ★ NEW

```text
Client
  │  POST /api/v1/behavior/event
  ▼
behavior.py (Layer 1)
  │  validates source, signal, confidence
  │
  ▼
HumanStateEngine.record_observation() (Layer 3.5)
  │
  ├──► StateBackend.store_observation()    → AgentObservation persisted
  │
  ├──► HumanStateEngine.derive_state()     → StateObservation(s)
  │       (aggregates across sources, derives stable signal)
  │
  ├──► HumanStateEngine.compute_career_state() → CareerState
  │       (confidence, momentum, engagement, consistency,
  │        growth_velocity, burnout_risk, interview_readiness,
  │        career_readiness)
  │
  ├──► HumanStateEngine.detect_transition() → StateTransition | None
  │       (if state changed significantly, records before → after)
  │
  ├──► HumanStateEngine.predict()          → Predictions
  │       ├── burnout_probability
  │       ├── dropout_probability
  │       ├── interview_success_probability
  │       └── skill_completion_probability
  │
  └──► AgentDecisionEngine.evaluate()      → Actions | None
          (if predictions cross thresholds → generates recommendations)
          ├── pause_roadmap
          ├── reduce_workload
          ├── add_encouragement
          └── defer_apply_recommendation
```

### CareerState Retrieval Flow

```text
Client
  │  GET /api/v1/behavior/state
  ▼
behavior.py (Layer 1)
  │
  ▼
HumanStateEngine.get_career_state(user_id) (Layer 3.5)
  │
  ├──► StateBackend.get_career_state()     → CareerState
  ├──► HumanStateEngine.predict()          → Predictions
  │
  └──► Returns CareerStateResponse (state + predictions)
```

---

## 4. Ownership Rules — The Law

### Rule 1: IntelligenceEngine is the ONLY orchestrator

No service in Layer 3, 5, 6, or 7 calls another service directly. Only `IntelligenceEngine` (Layer 4) calls them.

```text
✅ IntelligenceEngine → SkillExtractor
✅ IntelligenceEngine → SemanticEngine
✅ IntelligenceEngine → SkillGapAnalyzer
✅ IntelligenceEngine → ReasoningEngine

❌ SkillGapAnalyzer → SemanticEngine        (FORBIDDEN — goes through IE)
❌ ReasoningEngine → SkillExtractor          (FORBIDDEN — receives data, not services)
❌ InsightsEngine → SkillGapAnalyzer         (FORBIDDEN — receives data, not services)
```

### Rule 2: Layer 3 services receive DATA, not other services

Layer 3 services (Extractor, Semantic, Gap) receive **data objects** and return **data objects**. They never hold references to other services.

```python
# ✅ CORRECT — Gap Analyzer receives data
gap_analyzer.analyze(missing_skills, resume_skills, options)

# ❌ WRONG — Gap Analyzer holds SemanticEngine reference
gap_analyzer = SkillGapAnalyzer(semantic_engine=semantic_engine)
```

### Rule 3: API endpoints are THIN

Endpoints validate input, call `IntelligenceEngine`, return output. Zero business logic in endpoints.

```python
# ✅ CORRECT
@router.post("/analyze")
async def analyze(request: AnalyzeRequest, engine = Depends(get_engine)):
    return await engine.analyze(request)

# ❌ WRONG — business logic in endpoint
@router.post("/analyze")
async def analyze(request: AnalyzeRequest):
    skills = extractor.extract(request.resume_text)  # NO
    semantic = semantic_engine.compute(...)            # NO
```

### Rule 4: Utilities are STATELESS singletons

`text_processor`, `skill_taxonomy`, `embedding_store` — loaded once, never mutated during a request (except runtime taxonomy extension via feedback path).

### Rule 5: State Backend is the ONLY persistence

Nothing writes to disk, database, or external store directly. Everything goes through `StateBackend`.

---

## 5. Data Contracts — What Passes Between Layers

### Layer 1 → Layer 4 (API → Intelligence Engine)

```python
class AnalyzeRequest(BaseModel):
    resume_text: str          # 50-50,000 chars, validated
    jd_text: str              # 20-20,000 chars, validated
    include_simulations: bool = True
    include_evidence: bool = True
```

### Layer 2 → Layer 3 (Processing → Intelligence)

```python
# TextProcessor outputs
resume_clean: str             # Cleaned, normalized text
jd_clean: str                 # Cleaned, normalized text
sections: dict[str, str]      # {"experience": "...", "skills": "...", "education": "..."}
chunks: list[str]             # Semantic chunks with overlap
```

### Layer 3 Outputs (Intelligence → Layer 4)

```python
class ExtractionResult(BaseModel):
    skills: list[Skill]                     # All extracted skills
    extraction_methods_used: list[str]      # ["taxonomy", "ner", "semantic", "embedding"]
    degraded: bool                          # True if any layer failed
    failed_layers: list[str]               # ["ner"] if spaCy crashed
    processing_time_ms: float

class Skill(BaseModel):
    name: str                               # Raw text ("ReactJS")
    canonical: str                          # Normalized ("React")
    category: SkillCategory                 # frontend | backend | data | etc.
    confidence: float                       # 0.0 - 1.0 (extraction confidence)
    matched_by: MatchMethod                 # taxonomy | ner | semantic | embedding
    proficiency_score: float                # 0.0 - 1.0 (HOW WELL they know it)
    evidence_strength: float                # 0.0 - 1.0 (HOW STRONG the evidence)
    occurrence_count: int
    found_in_sections: list[str]            # ["experience", "projects"]
```

```python
class SemanticResult(BaseModel):
    overall_score: float                    # 0.0 - 1.0 (weighted aggregate)
    section_scores: dict[str, float]        # {"experience": 0.82, "projects": 0.65}
    chunk_best: float                       # Best chunk-level match
    chunk_mean: float                       # Mean chunk-level match
    skill_alignment: float                  # Skill context depth score
    confidence: float
    degraded: bool                          # True if fell back to TF-IDF
```

```python
class GapResult(BaseModel):
    gaps: list[SkillGapItem]               # All missing skills with reasoning
    matched_skills: list[SkillMatch]       # Skills found in BOTH documents
    overlap_score: float                    # 0.0 - 1.0
    matched_count: int
    missing_count: int
    gap_clusters: dict[str, list[str]]     # {"Cloud": ["K8s", "Terraform"]}
    critical_gap_count: int
    high_gap_count: int

class SkillGapItem(BaseModel):
    skill: str                              # Canonical skill name
    category: SkillCategory
    priority: GapPriority                   # critical | high | medium | low
    reasoning: str                          # Dynamic explanation (NOT template)
    learning_time_estimate: str | None      # "3-4 weeks"
    related_present: list[str]             # Related skills user HAS
    confidence: float
```

### Layer 4 Output (Intelligence Engine → API)

```python
class Decision(BaseModel):
    recommendation: Recommendation          # STRONG_APPLY | APPLY | etc.
    confidence: float                       # 0.0 - 1.0
    shortlist_probability: float            # 0.0 - 1.0
    fit_level: FitLevel                     # STRONG | GOOD | POTENTIAL | WEAK | NO_FIT
    overall_score: float                    # 0.0 - 100.0
    reasoning: str                          # Multi-factor reasoning text
    scoring: ScoringBreakdown
    strengths: list[str]
    weaknesses: list[str]
    improvement_path: list[ImprovementAction]
    top_simulations: list[WhatIfSimulation]
    evidence: list[EvidenceItem]

class ScoringBreakdown(BaseModel):
    semantic_score: float | None
    skill_overlap_score: float | None
    gap_penalty: float | None
    weights_used: dict[str, float]          # {"semantic": 0.40, "skill": 0.35, "gap": 0.25}
    final_score: float                      # 0.0 - 100.0
    confidence: float
    explanation: str                         # "semantic=0.78 (w=0.40) | overlap=0.82 (w=0.35) | ..."
```

### Layer 6 Input (Feedback → Learning)

```python
class FeedbackRequest(BaseModel):
    analysis_id: str
    outcome: str                            # "hired" | "rejected" | "interview" | "ghosted"
    notes: str = ""
```

### Layer 3.5 Contracts (Human State Intelligence) ★ NEW

```python
class ObservationSource(str, Enum):
    RESUME = "resume"
    JD = "jd"
    FEEDBACK = "feedback"
    LEARNING = "learning"
    PROJECT = "project"
    INTERVIEW = "interview"
    MARKET = "market"
    CAMERA = "camera"               # OPTIONAL — 95% functional without it

class AgentObservation(BaseModel):
    id: str                                 # UUID
    user_id: str
    source: ObservationSource
    signal: str                            # "engagement_low", "completion_drop"
    confidence: float                      # 0.0 - 1.0
    raw_data: dict | None                  # Optional (NEVER raw video)
    timestamp: datetime

class StateObservation(BaseModel):
    id: str
    user_id: str
    signal: str                             # "struggling", "accelerating"
    derived_from: list[ObservationSource]   # [CAMERA, LEARNING]
    contributing_observations: list[str]
    confidence: float
    timestamp: datetime

class CareerState(BaseModel):
    user_id: str
    confidence_score: float                 # 0.0 - 1.0
    momentum_score: float                   # 0.0 - 1.0
    engagement_score: float                 # 0.0 - 1.0
    consistency_score: float                # 0.0 - 1.0
    growth_velocity: float                  # score points/month
    burnout_risk: float                     # 0.0 - 1.0
    interview_readiness: float              # 0.0 - 1.0
    career_readiness: float                 # 0.0 - 1.0
    updated_at: datetime

class StateTransition(BaseModel):
    id: str
    user_id: str
    previous_state: CareerState
    new_state: CareerState
    reason: str                             # "Engagement dropped 60% over 3 days"
    triggered_actions: list[str]
    timestamp: datetime

class LearningSession(BaseModel):
    id: str
    user_id: str
    roadmap_id: str | None
    skill_focus: str
    duration_minutes: int
    completion_rate: float
    engagement_score: float
    abandoned: bool
    started_at: datetime
    ended_at: datetime | None
```

---

## 6. Dependency Injection Map

Every service receives its dependencies via constructor. Nothing is globally imported.

```python
# In api/deps.py — the DI container

def get_intelligence_engine() -> IntelligenceEngine:
    return IntelligenceEngine(
        config=get_config(),
        text_processor=get_text_processor(),
        extractor=get_skill_extractor(),
        semantic_engine=get_semantic_engine(),
        gap_analyzer=get_gap_analyzer(),
        reasoning_engine=get_reasoning_engine(),
        insights_engine=get_insights_engine(),
        scorer=get_adaptive_scorer(),
        feedback_processor=get_feedback_processor(),
        llm_enhancer=get_llm_enhancer(),
        state_backend=get_state_backend(),
    )
```

### Dependency Graph

```text
IntelligenceEngine
  ├── Config
  ├── TextProcessor
  ├── SkillExtractor
  │     ├── SkillTaxonomy (singleton)
  │     ├── EmbeddingStore (singleton)
  │     └── spaCy NLP model (singleton)
  ├── SemanticEngine
  │     └── SentenceTransformer model (singleton)
  ├── SkillGapAnalyzer
  │     └── SkillTaxonomy (singleton, shared)
  ├── ReasoningEngine
  ├── InsightsEngine
  ├── AdaptiveScorer
  │     └── StateBackend
  ├── FeedbackProcessor
  │     ├── StateBackend
  │     ├── SkillTaxonomy (for runtime extension)
  │     └── AdaptiveScorer (for recording feedback)
  ├── LLMEnhancer (optional)
  │     └── LLM API key (from Config)
  ├── HumanStateEngine ★ NEW
  │     └── StateBackend
  ├── AgentDecisionEngine ★ NEW
  │     └── HumanStateEngine (for CareerState + predictions)
  ├── GamificationEngine ★ NEW
  │     └── StateBackend
  └── StateBackend
        └── MemoryState | RedisState (from Config)
```

---

## 7. Startup Sequence

```text
uvicorn app.main:app
  │
  ▼
create_app()
  │
  ▼
lifespan(app) — STARTUP
  │
  ├── 1. Load Config                           (~0s)
  ├── 2. Load SkillTaxonomy (JSON → dict)      (~0.1s)   294 skills
  ├── 3. Load SentenceTransformer              (~5s)     all-MiniLM-L6-v2
  ├── 4. Build EmbeddingStore                  (~2s)     embed 294 skills
  ├── 5. Load spaCy + build PhraseMatcher      (~2s)     en_core_web_sm
  ├── 6. Create SkillExtractor                 (~0s)     receives 2-5
  ├── 7. Create SemanticEngine                 (~0s)     receives 3
  ├── 8. Create remaining services             (~0s)     all other L3-L7
  ├── 9. Create IntelligenceEngine             (~0s)     receives all above
  └── 10. Initialize StateBackend              (~0s)     memory or redis
  │
  ▼
Server ready on :8000 (~10-15s cold start)
```

---

## 8. Fallback Chain — What Happens When Things Break

Every component in Layer 3+ has a fallback. The system NEVER crashes — it degrades.

| Component | Primary | Fallback | Degraded Output |
| --- | --- | --- | --- |
| **Semantic Engine** | SentenceTransformer cosine | TF-IDF cosine (sklearn) | `semantic_score=None`, `degraded=True` |
| **Skill Extractor L2** (NER) | spaCy PhraseMatcher + EntityRuler | Skip NER, rely on L1+L3+L4 | Fewer discovered skills |
| **Skill Extractor L4** (Embedding) | EmbeddingStore discovery | Skip, rely on L1+L2+L3 | No unknown skill discovery |
| **Reasoning Engine** (LLM mode) | LLM-refined prose | Computational synthesis only | Slightly less fluent |
| **LLM Enhancer** | Gemini/OpenAI call | Return `None` | `llm_enhancement=null` |
| **Adaptive Scorer** | Feedback-adjusted weights | Config default weights | Accurate but not personalized |
| **State Backend** (Redis) | Redis read/write | In-memory fallback | Feedback not persisted across restarts |

### Partial Scoring Rule

If any Layer 3 component fails, `IntelligenceEngine` re-normalizes scoring weights over the AVAILABLE components:

```text
All available:  semantic * 0.40 + skill * 0.35 + gap * 0.25 = 1.0
Semantic fails: ────────────────  skill * 0.58 + gap * 0.42 = 1.0  (re-normalized)
```

Result always includes `meta.degraded = true` and `meta.components_failed = [...]`.

---

## 9. Enums — Shared Vocabulary

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
    STRONG_FIT = "strong_fit"       # >= 80
    GOOD_FIT = "good_fit"           # >= 65
    POTENTIAL_FIT = "potential_fit"  # >= 50
    WEAK_FIT = "weak_fit"           # >= 35
    NO_FIT = "no_fit"               # < 35

class Recommendation(str, Enum):
    STRONG_APPLY = "strong_apply"
    APPLY = "apply"
    APPLY_WITH_PREPARATION = "apply_with_preparation"
    UPSKILL_THEN_APPLY = "upskill_then_apply"
    DO_NOT_APPLY = "do_not_apply"
```

---

## 10. File Map — Every File, Its Layer, Its Phase

> **Column semantics (settled 2026-07-27).** The `Phase` column here denotes **MVP scope tier**, not
> execution order: `1` = required for the v1.0 architecture to be complete, `2` = deliberately deferred
> beyond v1.0. It does **not** assert that the file exists today. Execution sequencing lives in
> [07_IMPLEMENTATION_PLAN.md](07_IMPLEMENTATION_PLAN.md); actual build status lives in
> [13_STATUS_TRACKER.md](13_STATUS_TRACKER.md). When those two disagree with each other, the tracker
> wins on *what is built* and this document wins on *what must exist*.

| Layer | File | Phase | Status |
| --- | --- | --- | --- |
| **Config** | `app/config.py` | 1 | Build |
| **Config** | `app/main.py` | 1 | Build |
| **L1 Input** | `app/api/deps.py` | 1 | Build |
| **L1 Input** | `app/api/v1/router.py` | 1 | Build |
| **L1 Input** | `app/api/v1/endpoints/analyze.py` | 1 | Build |
| **L1 Input** | `app/api/v1/endpoints/feedback.py` | 1 | Build |
| **L1 Input** | `app/api/v1/endpoints/health.py` | 1 | Build |
| **L2 Processing** | `app/utils/text_processor.py` | 1 | Build |
| **L2 Processing** | `app/utils/file_parser.py` | 2 | Planned |
| **L3 Intelligence** | `app/services/skill_extractor.py` | 1 | Build |
| **L3 Intelligence** | `app/services/semantic_engine.py` | 1 | Build |
| **L3 Intelligence** | `app/services/skill_gap_analyzer.py` | 1 | Build |
| **L3 Intelligence** | `app/utils/skill_taxonomy.py` | 1 | Build |
| **L3 Intelligence** | `app/utils/embedding_store.py` | 1 | Build |
| **L4 Decision** | `app/services/intelligence_engine.py` | 1 | Build |
| **L4 Decision** | `app/services/decision_engine.py` | 2 | Planned |
| **L5 Reasoning** | `app/services/reasoning_engine.py` | 1 | Build |
| **L5 Reasoning** | `app/services/insights_engine.py` | 1 | Build |
| **L6 Learning** | `app/services/feedback_processor.py` | 1 | Build |
| **L6 Learning** | `app/services/adaptive_scorer.py` | 1 | Build |
| **L6 Learning** | `app/services/career_trajectory_engine.py` | 2 | Planned |
| **L7 External** | `app/services/market_intelligence_engine.py` | 2 | Planned |
| **L7 External** | `app/services/llm_enhancer.py` | 1 | Build (graceful null) |
| **State** | `app/state/base.py` | 1 | Build |
| **State** | `app/state/memory_state.py` | 1 | Build |
| **State** | `app/state/redis_state.py` | 2 | Planned |
| **Models** | `app/models/domain.py` | 1 | Build |
| **Models** | `app/models/enums.py` | 1 | Build |
| **Data** | `app/data/skill_taxonomy.json` | 1 | Build |
| **L3.5 Human State** | `app/services/human_state_engine.py` | 2 | Planned |
| **L3.5 Human State** | `app/services/agent_decision_engine.py` | 2 | Planned |
| **L3.5 Human State** | `app/services/gamification_engine.py` | 2 | Planned |
| **L3.5 Human State** | `app/models/career_state.py` | 2 | Planned |
| **L3.5 Human State** | `app/models/observation.py` | 2 | Planned |
| **L1 Input** | `app/api/v1/endpoints/behavior.py` | 2 | Planned |

---

## 11. What This Document Settles

| Question | Answer |
| --- | --- |
| **Who orchestrates the pipeline?** | `IntelligenceEngine` — the only service that calls other services |
| **Can services call each other?** | NO. Only IntelligenceEngine calls services. Services receive DATA. |
| **Where does scoring happen?** | `AdaptiveScorer` computes weights; `IntelligenceEngine` assembles components |
| **Where does reasoning happen?** | `ReasoningEngine` synthesizes evidence chains into text |
| **Who owns feedback?** | `FeedbackProcessor` stores + triggers; `AdaptiveScorer` adjusts weights |
| **What data passes between layers?** | Typed Pydantic models. See Section 5. |
| **What happens when a component fails?** | Graceful degradation (Section 8). Never crashes. |
| **Where is state stored?** | `StateBackend` (memory or Redis). Nothing else touches persistence. |
| **What is in MVP (tier 1) scope?** | Everything except: decision_engine, trajectory, market, redis, file_parser, human_state (Section 10). Tier-1 scope ≠ already built — see [13_STATUS_TRACKER.md](13_STATUS_TRACKER.md) |
| **What is CareerState?** | The unified state representation. Agent decisions consume this — never raw signals. |
| **Is camera mandatory?** | NO. Camera is permanently optional. System is 95% functional without it. |
| **Where does behavioral state live?** | `HumanStateEngine` (Layer 3.5) derives CareerState from 8 observation sources |
| **What is a StateTransition?** | Agent memory of growth. Records before → after CareerState with reasoning. |
| **What predictions does the system make?** | burnout_probability, dropout_probability, interview_success_probability, skill_completion_probability |

---

*This document is the architectural constitution of NeuroSync. When in doubt, this wins.*
