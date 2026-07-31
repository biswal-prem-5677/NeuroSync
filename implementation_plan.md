# NeuroSync Resume Analysis Engine — Enhanced Implementation Plan

## Project Analysis Summary

### What Exists Today

**1. Blueprints (Reference Only)** — 4-part SCA deconstruction: monolithic FastAPI, TF-IDF matching, substring skill extraction, triple-fallback classifier, 15 security vulnerabilities.

**2. Current `core/backend/` (~30% Scaffold)** — Correct directory layout but hollow: 17-line main.py, 7 skill aliases, hardcoded stubs, empty services. `fit_classifier.py` (317 lines) is most substantive but has no gap intelligence, reasoning, or explainability.

**3. Blueprint Context Goals** — Career Intelligence Engine with semantic understanding, skill-graph reasoning, gap intelligence, explainability, LLM-assisted reasoning, scalable to millions.

### 12 Critical Limitations Identified

Static skill list (7 aliases) • No NER • Substring false positives • No semantic skill matching • No taxonomy/ontology • No gap priority • No explainability • Naive `np.mean()` fusion • No structured insights • No LLM integration • No config management • No error handling

---

## Enhanced Architecture

```text
core/backend/
├── app/
│   ├── main.py                          # App factory + lifespan
│   ├── config.py                        # Pydantic Settings (zero hardcoding)
│   │
│   ├── api/                             # Thin controllers
│   │   ├── deps.py                      # DI (engine singletons)
│   │   └── v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── analyze.py           # POST /api/v1/analyze
│   │           ├── feedback.py          # POST /api/v1/feedback
│   │           └── health.py            # GET /api/v1/health
│   │
│   ├── models/                          # Pydantic schemas
│   │   ├── requests.py                  # AnalyzeRequest, FeedbackRequest
│   │   ├── responses.py                 # AnalysisResult (full structured output)
│   │   ├── domain.py                    # Skill, SkillMatch, SkillGapItem, etc.
│   │   └── enums.py                     # SkillCategory, GapPriority, FitLevel
│   │
│   ├── services/                        # Intelligence layer
│   │   ├── intelligence_engine.py       # ★ Central Decision Engine
│   │   ├── semantic_engine.py           # Sentence-transformer similarity
│   │   ├── skill_extractor.py           # Hybrid NER + dynamic + embedding discovery
│   │   ├── skill_gap_analyzer.py        # Context-aware gap reasoning
│   │   ├── reasoning_engine.py          # ★ Dynamic explanation generation
│   │   ├── insights_engine.py           # Structured SWOT insights
│   │   ├── adaptive_scorer.py           # ★ Learnable scoring mechanism
│   │   ├── llm_enhancer.py              # Optional LLM reasoning layer
│   │   └── feedback_processor.py        # ★ Learning from corrections
│   │
│   ├── utils/
│   │   ├── text_processor.py            # Text cleaning, section detection
│   │   ├── file_parser.py               # PDF/DOCX/TXT extraction
│   │   ├── skill_taxonomy.py            # Taxonomy loader + runtime extension
│   │   ├── embedding_store.py           # ★ Skill embedding cache + discovery
│   │   └── scoring.py                   # Score computation utilities
│   │
│   ├── state/                           # ★ Pluggable state layer
│   │   ├── base.py                      # Abstract state interface
│   │   ├── memory_state.py              # In-memory (dev/testing)
│   │   ├── redis_state.py               # Redis (production)
│   │   └── models.py                    # FeedbackRecord, ScoringHistory, etc.
│   │
│   └── data/
│       ├── skill_taxonomy.json          # 500+ skills with graph relationships
│       └── industry_weights.json        # Industry-specific importance modifiers
│
├── tests/
│   ├── conftest.py
│   ├── test_intelligence_engine.py
│   ├── test_skill_extractor.py
│   ├── test_reasoning_engine.py
│   ├── test_adaptive_scorer.py
│   ├── test_feedback_processor.py
│   └── test_analyze_endpoint.py
│
├── requirements.txt
└── README.md
```

---

## Proposed Changes — Full File Specification

### Configuration Layer

#### [NEW] config.py

Pydantic `BaseSettings` — all configurable via env vars:

- Embedding model name, semantic threshold, max text length
- Scoring weights (initial defaults, overridable)
- LLM provider config (optional)
- State backend selection (`memory` | `redis`)
- Feedback collection toggle
- Score thresholds for fit levels

---

### Models Layer

#### [NEW] enums.py

`SkillCategory` (9 types) • `GapPriority` (CRITICAL/HIGH/MEDIUM/LOW) • `FitLevel` (5 levels) • `InsightType` (STRENGTH/WEAKNESS/OPPORTUNITY/RECOMMENDATION) • `MatchMethod` (TAXONOMY/NER/SEMANTIC/EMBEDDING_DISCOVERY)

#### [NEW] domain.py

- `Skill`: name, canonical, category, aliases, related, confidence, discovered_by
- `SkillMatch`: skill, source, matched_by (MatchMethod), similarity_score
- `SkillGapItem`: skill, priority, reasoning (dynamic string), learning_estimate, related_present, confidence
- `ScoringBreakdown`: per-component scores, weights used, confidence, explanation
- `ReasoningTrace`: chain of evidence objects explaining each decision

#### [NEW] requests.py

- `AnalyzeRequest`: resume_text, jd_text, options (AnalysisOptions)
- `AnalysisOptions`: enable_llm, industry_context, detail_level, session_id
- `FeedbackRequest`: analysis_id, corrections (skill add/remove/re-prioritize), score_adjustment, free_text

#### [NEW] responses.py

- `AnalysisResult`: overall_score, fit_level, semantic_similarity, skill_analysis, gap_intelligence, insights, scoring_breakdown, reasoning_trace, llm_enhancement (optional), metadata (timing, models_used, confidence, analysis_id)

---

### Utils Layer

#### [NEW] text_processor.py

- `clean_text()`: Unicode normalize, HTML strip, smart tech-term preservation (C++, C#, .NET)
- `normalize_for_matching()`: Lowercase preserving tech symbols
- `extract_sections()`: Heuristic resume section detection
- `chunk_text()`: Semantic chunking with overlap for embeddings

#### [NEW] file_parser.py

PDF (PyPDF2 + pdfplumber fallback) • DOCX • TXT → `ParsedDocument`

#### [NEW] skill_taxonomy.py

- Loads `skill_taxonomy.json` (500+ skills, aliases, categories, relationships)
- `resolve_skill()` → canonical name
- `get_related()`, `get_category()`, `get_importance()`
- **`register_discovered_skill()`** — runtime extension for embedding-discovered skills
- Thread-safe, singleton pattern

#### [NEW] scoring.py

- `compute_weighted_score()`: Applies component weights
- `compute_gap_penalty()`: Critical-gap-aware penalty
- `determine_fit_level()`: Score → FitLevel with configurable thresholds
- `compute_confidence()`: Meta-confidence based on data quality

#### [NEW] embedding_store.py — ★ NEW (Dynamic Skill Intelligence)

Pre-computed embedding cache for all taxonomy skills + runtime expansion:

```python
class SkillEmbeddingStore:
    """Embeds all taxonomy skills at startup. Enables:
    1. Semantic skill matching (cosine similarity between skill embeddings)
    2. Unknown skill discovery (cluster unknown terms against known embeddings)
    3. Dynamic taxonomy expansion (register new skills found via embedding proximity)
    """
    def __init__(self, model, taxonomy):
        self.embeddings = {}  # canonical_name -> np.ndarray
        self._build_index(taxonomy)

    def find_nearest_skill(self, text, threshold=0.7) -> Optional[Skill]:
        """Map unknown text to nearest known skill via embedding similarity"""

    def discover_unknown_skills(self, text_chunks) -> list[Skill]:
        """Find technical terms not in taxonomy but clustered near known skills.
        Creates new Skill objects with discovered_by=EMBEDDING_DISCOVERY"""

    def register_skill(self, skill: Skill):
        """Add discovered skill to runtime index (does NOT modify JSON file)"""
```

This replaces static-only taxonomy with a **living skill graph** that grows as it encounters new terms.

---

### Services Layer — Intelligence

#### [NEW] semantic_engine.py

- Singleton `SentenceTransformer('all-MiniLM-L6-v2')`
- `compute_similarity(text_a, text_b)` → document-level cosine
- `compute_section_similarities(sections, jd)` → per-section analysis
- `compute_skill_similarity(skill_a, skill_b)` → skill-level semantic match
- Chunking + max-pooling for long texts
- Returns `SemanticResult` with scores + explanations

#### [NEW] skill_extractor.py — Enhanced with Embedding Discovery

**Layer 1 — Taxonomy** (fast, high precision): Alias + normalized matching
**Layer 2 — spaCy NER** (discovers unknown entities): PhraseMatcher + entity ruler
**Layer 3 — Semantic** (catches paraphrases): Cosine > 0.75 on resume chunks
**Layer 4 — Embedding Discovery** ★ NEW: Uses `SkillEmbeddingStore.discover_unknown_skills()` to find technical terms not in taxonomy but semantically close to known skill clusters. These are tagged `matched_by: EMBEDDING_DISCOVERY` with a confidence score.

Output: `ExtractionResult` with per-skill extraction method + confidence

#### [NEW] skill_gap_analyzer.py — Context-Aware Reasoning

For each missing skill, computes priority from multiple signals:

- JD frequency × position weight
- Industry context weight
- Related skill partial credit (via taxonomy graph + embedding similarity)
- Category importance

**Reasoning is generated dynamically** (not template strings):

- Uses a `ReasoningChain` that accumulates evidence:

  ```python
  chain = ReasoningChain()
  chain.add("frequency", f"Mentioned {count}x in JD", weight=0.3)
  chain.add("position", "Appears in first paragraph (high priority)", weight=0.2)
  chain.add("related", f"You have {related} (similarity: {sim:.0%})", weight=-0.15)
  chain.synthesize()  # → natural language reasoning string

  ```
- When LLM is available, the chain can optionally be passed to LLM for more fluent synthesis

#### [NEW] reasoning_engine.py — ★ NEW (Dynamic Reasoning Layer)

Central reasoning module that replaces fixed rule-based explanations:

```python
class ReasoningEngine:
    """Generates context-aware explanations for every decision.
    
    Two modes:
    1. Computational (default): Evidence-chain synthesis — fast, deterministic
    2. LLM-assisted (optional): Sends evidence chain to LLM for fluent prose
    
    The key insight: reasoning is NEVER hardcoded strings.
    It's always synthesized from an evidence chain.
    """
    
    def explain_score(self, breakdown: ScoringBreakdown) -> str:
        """Why is the overall score X?"""
    
    def explain_gap(self, gap: SkillGapItem, context: AnalysisContext) -> str:
        """Why is this gap priority CRITICAL vs LOW?"""
    
    def explain_fit(self, fit_level: FitLevel, evidence: list) -> str:
        """Why GOOD_FIT and not STRONG_FIT?"""
    
    def generate_trace(self, all_evidence: dict) -> ReasoningTrace:
        """Full decision trace — every score explained"""
```

**Evidence Chain Architecture:**
```text
EvidenceItem(source, claim, weight, confidence)
    ↓
ReasoningChain.accumulate([evidence_items])
    ↓
ReasoningChain.synthesize() → natural language
    ↓ (optional)
LLM.refine(synthesized_text) → fluent prose
```

This means the system can explain itself at any level of detail — from "Score: 72" all the way to "Score is 72 because: semantic similarity was 0.81 (weight 0.4), skill overlap was 0.65 (weight 0.35), gap penalty was -0.12 from 2 critical missing skills (Python, AWS)..."

#### [NEW] adaptive_scorer.py — ★ NEW (Learnable Scoring)

Replaces fixed `weights = {"semantic": 0.4, "skill": 0.35, "gap": 0.25}` with a system that can learn:

```python
class AdaptiveScorer:
    """Scoring mechanism that evolves over time.
    
    Phase 1 (Day 1): Uses configurable default weights from config.py
    Phase 2 (With feedback): Adjusts weights based on user/recruiter corrections
    Phase 3 (With training data): Can train a lightweight regression model
    
    The interface stays identical across all phases — only internals change.
    """
    
    def __init__(self, config, state_backend):
        self.weights = config.default_weights  # Phase 1
        self.feedback_history = state_backend   # Phase 2 storage
        self.trained_model = None               # Phase 3
    
    def score(self, components: dict[str, float]) -> ScoringResult:
        """Score using best available method"""
        if self.trained_model:
            return self._score_ml(components)       # Phase 3
        elif self._has_sufficient_feedback():
            return self._score_adjusted(components)  # Phase 2
        else:
            return self._score_default(components)   # Phase 1
    
    def record_feedback(self, analysis_id, actual_outcome):
        """Store outcome for future weight adjustment"""
    
    def recalibrate(self):
        """Recalculate weights from accumulated feedback.
        Uses simple gradient descent on MSE(predicted_score, feedback_score)"""
```

**Weight Evolution:**
```text
Day 1:    weights = {semantic: 0.40, skill: 0.35, gap: 0.25}  ← config defaults
Week 4:   weights = {semantic: 0.38, skill: 0.37, gap: 0.25}  ← 50 feedbacks
Month 3:  weights = trained_model.predict(components)          ← 500+ feedbacks
```

#### [NEW] insights_engine.py

Generates structured SWOT insights from analysis data. Each insight has: type, title, description, evidence list, confidence. Uses `ReasoningEngine` for description synthesis (not template strings).

#### [NEW] llm_enhancer.py

Optional LLM layer (only when `enable_llm=True`):

- Receives computed facts (not raw text) — anti-hallucination
- Enhances reasoning with deeper career context
- Complete graceful degradation
- Can refine `ReasoningEngine` outputs into fluent prose

#### [NEW] feedback_processor.py — ★ NEW (Learning System)

```python
class FeedbackProcessor:
    """Closes the learning loop.
    
    Accepts corrections:
    - Skill corrections: "React was missed" / "Java was wrong"
    - Priority corrections: "AWS should be CRITICAL not MEDIUM"
    - Score corrections: "This should be ~85 not 72"
    
    Actions:
    1. Stores feedback in state backend
    2. Updates skill taxonomy runtime (register missed skills)
    3. Feeds adaptive scorer for weight recalibration
    4. Generates taxonomy improvement suggestions (for curator review)
    """
    
    def process(self, feedback: FeedbackRequest) -> FeedbackResult:
        """Process a single feedback submission"""
    
    def get_taxonomy_suggestions(self) -> list[TaxonomySuggestion]:
        """Skills frequently corrected → suggest adding to taxonomy JSON"""
    
    def get_scoring_drift_report(self) -> DriftReport:
        """Are scores systematically too high/low? Detect calibration drift"""
```

**Feedback Loop Architecture:**

```text
User/Recruiter submits correction
    ↓
FeedbackProcessor.process()
    ├─► state_backend.store(feedback_record)
    ├─► skill_taxonomy.register_discovered_skill()  (if skill was missed)
    ├─► adaptive_scorer.record_feedback()
    └─► Returns acknowledgment + impact summary

Periodic (or on-demand):
    adaptive_scorer.recalibrate()  ← uses accumulated feedback
    feedback_processor.get_taxonomy_suggestions()  ← for human review
```

#### [NEW] intelligence_engine.py — ★ NEW (Central Decision Engine)

The brain. Replaces `analysis_orchestrator.py` as the unified intelligence core:

```python
class IntelligenceEngine:
    """Central Decision Engine — unifies all subsystems.
    
    This is NOT just an orchestrator that calls services sequentially.
    It's a decision-making system that:
    1. Orchestrates the pipeline (extraction → analysis → scoring → reasoning)
    2. Makes meta-decisions (which layers to use based on input quality)
    3. Produces unified, explainable output
    4. Feeds learning back into the system
    5. Manages confidence across all components
    """
    
    def __init__(self, config, semantic, extractor, gap_analyzer, 
                 reasoning, scorer, insights, llm, feedback, state):
        # All services injected — fully testable
        
    def analyze(self, request: AnalyzeRequest) -> AnalysisResult:
        """Master analysis pipeline."""
        
        # 1. Preprocess
        resume_clean = self.text_processor.clean(request.resume_text)
        jd_clean = self.text_processor.clean(request.jd_text)
        
        # 2. Extract (hybrid: taxonomy + NER + semantic + embedding discovery)
        resume_skills = self.extractor.extract(resume_clean)
        jd_skills = self.extractor.extract(jd_clean)
        
        # 3. Semantic similarity
        semantic = self.semantic.compute_similarity(resume_clean, jd_clean)
        
        # 4. Skill analysis (match, miss, extra)
        skill_analysis = self._compute_skill_analysis(resume_skills, jd_skills)
        
        # 5. Gap intelligence (priority + context-aware reasoning)
        gaps = self.gap_analyzer.analyze(
            skill_analysis.missing, resume_skills, request.options
        )
        
        # 6. Adaptive scoring (learnable weights)
        score_result = self.scorer.score({
            "semantic": semantic.overall_score,
            "skill_overlap": skill_analysis.overlap_score,
            "gap_penalty": gaps.penalty_score
        })
        
        # 7. Reasoning (dynamic, evidence-chain based)
        reasoning_trace = self.reasoning.generate_trace({
            "semantic": semantic, "skills": skill_analysis,
            "gaps": gaps, "score": score_result
        })
        
        # 8. Insights (SWOT from all data)
        insights = self.insights.generate(
            semantic, skill_analysis, gaps, score_result
        )
        
        # 9. Optional LLM enhancement
        llm_result = None
        if request.options.enable_llm:
            llm_result = self.llm.enhance(reasoning_trace, insights)
        
        # 10. Assemble result
        return AnalysisResult(
            analysis_id=generate_id(),
            overall_score=score_result.final_score,
            fit_level=score_result.fit_level,
            semantic_similarity=semantic,
            skill_analysis=skill_analysis,
            gap_intelligence=gaps,
            insights=insights,
            scoring_breakdown=score_result.breakdown,
            reasoning_trace=reasoning_trace,
            llm_enhancement=llm_result,
            metadata=self._build_metadata(start_time)
        )
    
    def submit_feedback(self, feedback: FeedbackRequest) -> FeedbackResult:
        """Process feedback → update scorer + taxonomy"""
        return self.feedback.process(feedback)
```

**Pipeline Flow:**

```text
                    ┌─────────────────────────────┐
                    │    INTELLIGENCE ENGINE       │
                    │    (Central Decision Core)   │
                    └─────────┬───────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
  ┌──────────┐        ┌──────────┐          ┌──────────┐
  │ Semantic  │        │  Skill   │          │   Skill  │
  │  Engine   │        │Extractor │          │   Gap    │
  │(embeddings│        │(4-layer  │          │ Analyzer │
  │ + cosine) │        │ hybrid)  │          │(context) │
  └─────┬────┘        └────┬─────┘          └────┬─────┘
        │                  │                      │
        └──────────┬───────┴──────────────────────┘
                   ▼
           ┌──────────────┐
           │  Adaptive    │◄──── Feedback Loop
           │   Scorer     │      (learns over time)
           └──────┬───────┘
                  ▼
           ┌──────────────┐
           │  Reasoning   │──── Evidence Chains
           │   Engine     │     (not templates)
           └──────┬───────┘
                  ▼
           ┌──────────────┐
           │   Insights   │──── SWOT Analysis
           │   Engine     │
           └──────┬───────┘
                  ▼
           ┌──────────────┐
           │  LLM Layer   │──── Optional Enhancement
           │ (if enabled) │
           └──────┬───────┘
                  ▼
           AnalysisResult
```

---

### State Layer — ★ NEW (Scalability)

#### [NEW] state/base.py

```python
class StateBackend(ABC):
    """Pluggable state interface — swap implementations without changing services."""
    
    @abstractmethod
    async def store_feedback(self, record: FeedbackRecord) -> str: ...
    
    @abstractmethod
    async def get_feedback_history(self, limit: int) -> list[FeedbackRecord]: ...
    
    @abstractmethod
    async def store_analysis(self, analysis_id: str, result: dict) -> None: ...
    
    @abstractmethod
    async def get_scoring_weights(self) -> dict[str, float]: ...
    
    @abstractmethod
    async def update_scoring_weights(self, weights: dict[str, float]) -> None: ...
```

#### [NEW] state/memory_state.py

In-memory implementation — for development and testing. No external dependencies.

#### [NEW] state/redis_state.py

Redis-backed implementation — for production. Supports horizontal scaling since all API instances share state through Redis.

**Scalability Design:**

```text
          ┌──────────┐  ┌──────────┐  ┌──────────┐
          │ API Pod 1│  │ API Pod 2│  │ API Pod N│   ← Stateless
          └────┬─────┘  └────┬─────┘  └────┬─────┘
               │             │             │
               └─────────────┼─────────────┘
                             │
                      ┌──────▼──────┐
                      │    Redis    │   ← Shared state
                      │  (weights,  │
                      │  feedback,  │
                      │  taxonomy+) │
                      └─────────────┘
```

- API layer is **fully stateless** — any pod can serve any request
- State backend is pluggable — swap `memory → redis → postgres` via config
- Models (sentence-transformer, spaCy) loaded per-pod at startup — no shared GPU needed

---

### API Layer

#### [MODIFY] main.py

App factory with lifespan handler (model loading/shutdown), CORS, exception handlers, request-ID middleware, mounts v1 router.

#### [NEW] api/v1/endpoints/analyze.py

`POST /api/v1/analyze` — validates input, calls `IntelligenceEngine.analyze()`, returns `AnalysisResult`.

#### [NEW] api/v1/endpoints/feedback.py — ★ NEW

`POST /api/v1/feedback` — accepts `FeedbackRequest`, calls `IntelligenceEngine.submit_feedback()`. Returns impact summary.

#### [NEW] api/v1/endpoints/health.py

`GET /api/v1/health` — models loaded, embedding store ready, state backend connected, feedback count.

---

## Evolution Roadmap

| Phase | Timeline | Scoring | Reasoning | Skills | State |
| --- | --- | --- | --- | --- | --- |
| **Phase 1** (Build) | Now | Config defaults | Evidence-chain synthesis | Taxonomy + NER + Semantic + Embedding | In-memory |
| **Phase 2** (Learn) | +2 weeks | Feedback-adjusted weights | Evidence + LLM refinement | + discovered skills from feedback | Redis |
| **Phase 3** (Train) | +2 months | Trained regression model | Full LLM reasoning | + auto-taxonomy expansion | Redis + persistence |

The **interface is identical across all phases** — only internal implementations evolve.

---

## Capability Comparison

| Capability | SCA/Current | Previous Plan | Enhanced Plan |
| --- | --- | --- | --- |
| Skill matching | Substring | Taxonomy+NER+Semantic | + Embedding discovery of unknown skills |
| Scoring | `np.mean()` | Fixed configurable weights | Learnable adaptive weights |
| Reasoning | None | Template strings | Evidence-chain synthesis + optional LLM |
| Learning | None | None | Feedback loop → scorer + taxonomy |
| Unknown skills | Ignored | Ignored | Dynamically discovered + registered |
| State | None | None | Pluggable (memory/redis) |
| Scalability | Single process | Single process | Stateless pods + shared state |
| Evolution | Static forever | Static after deploy | Self-improving over time |

---

## Cross-Cutting Layer 1: Resilience

Every service in the pipeline is designed to **degrade gracefully** — never crash the full analysis.

### Fallback Chain per Service

| Service | Primary | Fallback | Degraded Output |
| --- | --- | --- | --- |
| `semantic_engine` | SentenceTransformer cosine | TF-IDF cosine (sklearn) | `semantic_score=None`, flag `semantic_degraded=True` |
| `skill_extractor` Layer 2 (NER) | spaCy PhraseMatcher + EntityRuler | Skip NER, rely on Layers 1+3+4 | Fewer discovered skills, confidence reduced |
| `skill_extractor` Layer 4 (Embedding) | SkillEmbeddingStore discovery | Skip, rely on Layers 1+2+3 | No unknown skill discovery |
| `reasoning_engine` LLM mode | LLM-refined prose | Computational synthesis only | Slightly less fluent, fully functional |
| `llm_enhancer` | Gemini/OpenAI call | Return `None` | `llm_enhancement=null` in response |
| `adaptive_scorer` | Feedback-adjusted weights | Config default weights | Accurate but not personalized |
| `state` backend (Redis) | Redis read/write | In-memory fallback | Feedback not persisted across restarts |

### Partial Scoring Support

The `IntelligenceEngine` tracks which components succeeded and computes scores from **whatever is available**:

```python
# Inside IntelligenceEngine.analyze():
components = {}
available_weights = {}

if semantic_result:
    components["semantic"] = semantic_result.overall_score
    available_weights["semantic"] = self.config.weights.semantic
    
if skill_analysis:
    components["skill_overlap"] = skill_analysis.overlap_score
    available_weights["skill_overlap"] = self.config.weights.skill

if gaps:
    components["gap_penalty"] = gaps.penalty_score
    available_weights["gap_penalty"] = self.config.weights.gap

# Re-normalize weights to sum to 1.0 over available components
score = self.scorer.score(components, weights=normalize(available_weights))
```

If only taxonomy matching works (NER, embedding, semantic all fail), the system still returns a valid `AnalysisResult` with:

- `overall_score` computed from skill overlap alone
- `metadata.degraded = True`
- `metadata.components_used = ["taxonomy_matching"]`
- `metadata.components_failed = ["semantic", "ner", "embedding_discovery"]`

### Degraded Mode Metadata

Added to `AnalysisMetadata` in `responses.py`:

```python
class AnalysisMetadata(BaseModel):
    # ... existing fields ...
    degraded: bool = False
    components_used: list[str] = []       # What succeeded
    components_failed: list[str] = []     # What failed + why
    confidence_penalty: float = 0.0       # How much confidence dropped due to failures
```

---

## Cross-Cutting Layer 2: Performance

### Caching Strategy

#### Embedding Cache (in `embedding_store.py`)

- All taxonomy skill embeddings computed **once at startup** and held in memory
- `lru_cache` on `find_nearest_skill()` — same input text → same result
- Resume/JD document embeddings cached per `analysis_id` within a request lifecycle

#### Skill Extraction Cache (in `skill_extractor.py`)

- `lru_cache(maxsize=1024)` on `extract()` — keyed on `hash(normalized_text)`
- Identical resumes submitted multiple times → instant cache hit
- Cache invalidated when taxonomy is updated via feedback

#### Taxonomy Lookup Cache (in `skill_taxonomy.py`)

- `resolve_skill()` results cached in a dict — O(1) after first lookup
- `get_related()` graph traversals cached per canonical skill name

### Async / Parallel Execution

The `IntelligenceEngine.analyze()` pipeline runs independent steps concurrently:

```python
async def analyze(self, request: AnalyzeRequest) -> AnalysisResult:
    # Step 1: Preprocess (fast, sync)
    resume_clean = self.text_processor.clean(request.resume_text)
    jd_clean = self.text_processor.clean(request.jd_text)
    
    # Step 2: Run independent extractions in parallel
    resume_skills, jd_skills, semantic = await asyncio.gather(
        self.extractor.extract_async(resume_clean),
        self.extractor.extract_async(jd_clean),
        self.semantic.compute_similarity_async(resume_clean, jd_clean)
    )
    
    # Step 3: Sequential (depends on Step 2 outputs)
    skill_analysis = self._compute_skill_analysis(resume_skills, jd_skills)
    gaps = self.gap_analyzer.analyze(skill_analysis.missing, resume_skills)
    
    # Step 4: Scoring + reasoning in parallel
    score_result, reasoning_trace = await asyncio.gather(
        self.scorer.score_async(components),
        self.reasoning.generate_trace_async(evidence)
    )
    
    # Step 5: Insights + optional LLM
    insights = self.insights.generate(semantic, skill_analysis, gaps, score_result)
    llm_result = await self.llm.enhance_async(...) if request.options.enable_llm else None
    
    return AnalysisResult(...)
```

**Parallelism map:**

```text
Time ──────────────────────────────────────────────►
 
[preprocess]──┬──[extract resume]──┐
              ├──[extract JD]──────┤
              └──[semantic sim]────┘
                                   ├──[skill analysis]──[gap analysis]──┬──[scoring]──┐
                                   │                                    └──[reasoning]─┤
                                   │                                                   ├──[insights]──[LLM?]──► Result
```

### Response Time Budget

| Component | Target | Fallback Timeout |
| --- | --- | --- |
| Text preprocessing | <10ms | N/A (always succeeds) |
| Skill extraction (all layers) | <200ms | 500ms → skip embedding discovery |
| Semantic similarity | <150ms | 300ms → fallback to TF-IDF |
| Gap analysis | <50ms | N/A (pure computation) |
| Adaptive scoring | <10ms | N/A (pure computation) |
| Reasoning trace | <30ms | N/A (pure computation) |
| Insights generation | <30ms | N/A (pure computation) |
| LLM enhancement | <3000ms | 5000ms → skip, return null |
| **Total (without LLM)** | **<500ms** | |
| **Total (with LLM)** | **<3500ms** | |

Timeouts enforced via `asyncio.wait_for()` — on timeout, the component falls back to its degraded mode from the Resilience Layer.

---

## Cross-Cutting Layer 3: Versioning

### Version Tracking

Every component that can evolve independently gets a version identifier:

```python
# In config.py
class VersionConfig(BaseModel):
    taxonomy_version: str = "1.0.0"      # Bumped when skill_taxonomy.json changes
    scoring_version: str = "1.0.0"       # Bumped when weights/algorithm changes
    embedding_model_version: str = "all-MiniLM-L6-v2"  # The model name IS the version
    spacy_model_version: str = "en_core_web_sm"
    engine_version: str = "1.0.0"        # Overall system version
    api_version: str = "v1"
```

### Version in AnalysisResult

Extended `AnalysisMetadata` in `responses.py`:

```python
class AnalysisMetadata(BaseModel):
    analysis_id: str
    processing_time_ms: float
    models_used: list[str]
    confidence: float
    # Resilience fields
    degraded: bool = False
    components_used: list[str] = []
    components_failed: list[str] = []
    confidence_penalty: float = 0.0
    # Version fields
    versions: VersionInfo

class VersionInfo(BaseModel):
    engine: str           # "1.0.0"
    taxonomy: str         # "1.0.0"  
    scoring: str          # "1.0.0"
    embedding_model: str  # "all-MiniLM-L6-v2"
    spacy_model: str      # "en_core_web_sm"
    api: str              # "v1"
```

### Why This Matters

- **Reproducibility**: Same resume + JD + version = same result. If taxonomy changes, the version changes and explains score drift.
- **Debugging**: "Score dropped from 78 to 65" → check `taxonomy_version` changed from 1.0.0 to 1.1.0 → new skills added.
- **Feedback alignment**: Feedback collected under `scoring_version=1.0.0` is only used to recalibrate that version's weights.
- **A/B testing**: Run two scoring versions side-by-side, compare feedback quality.

### Health Endpoint Extension

`GET /api/v1/health` now includes:

```json
{
  "status": "healthy",
  "versions": {
    "engine": "1.0.0",
    "taxonomy": "1.0.0",
    "scoring": "1.0.0", 
    "embedding_model": "all-MiniLM-L6-v2",
    "spacy_model": "en_core_web_sm"
  },
  "taxonomy_skill_count": 523,
  "feedback_count": 47,
  "scorer_mode": "feedback_adjusted",
  "degraded_components": []
}
```

---

## Cross-Cutting Layer 4: Input Validation

### Validation Rules (in `requests.py`)

```python
class AnalyzeRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=50_000)
    jd_text: str = Field(..., min_length=20, max_length=20_000)
    options: AnalysisOptions = AnalysisOptions()

    @field_validator("resume_text", "jd_text")
    @classmethod
    def reject_junk(cls, v: str, info) -> str:
        stripped = v.strip()
        if len(stripped) < 20:
            raise ValueError(f"{info.field_name} too short after stripping whitespace")
        alpha_ratio = sum(c.isalpha() for c in stripped) / len(stripped)
        if alpha_ratio < 0.3:
            raise ValueError(f"{info.field_name} appears to be non-text content")
        return stripped
```

| Rule | Limit | Rationale |
| --- | --- | --- |
| Resume max length | 50,000 chars (~12 pages) | Prevents DoS, embedding model has token limits |
| Resume min length | 50 chars | Rejects empty/junk submissions |
| JD max length | 20,000 chars (~5 pages) | JDs are shorter than resumes |
| JD min length | 20 chars | Rejects empty/junk submissions |
| Alpha ratio check | >30% alphabetic | Rejects binary/encoded/garbage input |
| Content-Type | `application/json` only | Enforced by FastAPI |
| Request body size | 1MB max | Middleware-level limit |

### Sanitization Pipeline (in `text_processor.py`)

Applied **before** any processing:

1. Strip null bytes and control characters
2. Normalize Unicode (NFC form)
3. Strip HTML tags (prevent injection)
4. Collapse excessive whitespace/newlines (>3 consecutive → 2)
5. Truncate to max length if somehow bypassed

### Error Response Contract

All validation errors return structured JSON:

```json
{
  "error": "validation_error",
  "detail": [
    {
      "field": "resume_text",
      "message": "String should have at least 50 characters",
      "input_length": 12
    }
  ]
}
```

---

## Cross-Cutting Layer 5: Observability

### Structured Logging

All logs are JSON-formatted for machine parsing (ELK/CloudWatch/Datadog ready):

```python
# In utils/logging.py
import logging, json, uuid

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            **getattr(record, "extra", {})
        })
```

### Request ID Middleware

Every request gets a unique `request_id` propagated through all services:

```python
# In main.py middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id
    # Set in contextvars for access in any service
    REQUEST_ID.set(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### Per-Component Timing

The `IntelligenceEngine` records timing for every pipeline step:

```python
class ComponentTimer:
    """Records execution time per component."""
    def __init__(self):
        self.timings: dict[str, float] = {}
    
    @contextmanager
    def track(self, component: str):
        start = time.perf_counter()
        yield
        self.timings[component] = round((time.perf_counter() - start) * 1000, 2)

# Usage in IntelligenceEngine.analyze():
timer = ComponentTimer()

with timer.track("text_preprocessing"):
    resume_clean = self.text_processor.clean(request.resume_text)

with timer.track("skill_extraction"):
    resume_skills = self.extractor.extract(resume_clean)

with timer.track("semantic_similarity"):
    semantic = self.semantic.compute_similarity(resume_clean, jd_clean)

# Included in response:
# metadata.component_timings = {"text_preprocessing": 4.2, "skill_extraction": 187.3, ...}
```

### Error Logging per Service

Every service logs failures with context — never silent swallowing:

```python
# Pattern used in every service:
try:
    result = self._compute(data)
except Exception as e:
    logger.error("Component failed", extra={
        "extra": {
            "component": "semantic_engine",
            "error_type": type(e).__name__,
            "error_message": str(e),
            "request_id": REQUEST_ID.get(),
            "input_length": len(data)
        }
    })
    return self._fallback(data)  # Resilience layer kicks in
```

### Metadata in AnalysisResult (Final Shape)

```python
class AnalysisMetadata(BaseModel):
    analysis_id: str
    processing_time_ms: float
    component_timings: dict[str, float]   # Per-component ms
    models_used: list[str]
    confidence: float
    request_id: str                        # Trace across logs
    # Resilience
    degraded: bool = False
    components_used: list[str] = []
    components_failed: list[str] = []
    confidence_penalty: float = 0.0
    # Versions
    versions: VersionInfo
```

### System Status Summary

| Area | Status |
| --- | --- |
| Architecture | ✅ Elite |
| Intelligence | ✅ Advanced |
| Scalability | ✅ Production-ready |
| Learning | ✅ Strong |
| Resilience | ✅ Strong |
| Performance | ✅ Good |
| Versioning | ✅ Complete |
| Validation | ✅ Complete |
| Observability | ✅ Complete |

---

## Power Engines — From Tool to Decision System

> Architecture shift: `Resume → Score` becomes `Resume + JD + Market + History → Decision + Expected Outcome`

### [NEW] services/market_intelligence_engine.py

Injects **real-world context** into every analysis:

- `get_skill_demand(skill)` → demand trend (↑37% / stable / ↓12%), time window
- `get_salary_signal(skills, role)` → market salary range for skill combination
- `get_hiring_velocity(role, region)` → how fast companies are hiring for this role
- Data sources: pluggable adapter pattern (`MarketDataProvider` ABC)
  - Phase 1: Static curated snapshots (JSON)
  - Phase 2: API integrations (LinkedIn Talent Insights, Indeed, Glassdoor)
- Gap analyzer uses this: "Kubernetes demand ↑37% in 6 months → CRITICAL gap" instead of static priority
- Integrated into `IntelligenceEngine` pipeline between gap analysis and scoring

### [NEW] services/career_trajectory_engine.py

Adds the **time dimension** — tracks growth, predicts trajectory:

- `record_snapshot(user_id, skills, score, timestamp)` → stores point-in-time state
- `compute_growth_velocity(user_id)` → skills/month learning rate
- `predict_trajectory(user_id, target_role)` → estimated time to readiness
- `simulate_skill_addition(user_id, skill)` → "If you learn AWS, score jumps from 72 → 86"
- Storage: pluggable via `StateBackend` (same as feedback/scoring state)
- Enables insights like: "You've gained 4 skills in 3 months → above-average velocity"

### [NEW] services/decision_engine.py ⭐

Converts analysis into **actionable decisions with expected outcomes**:

```python
class DecisionEngine:
    def decide(self, analysis: AnalysisResult, market: MarketContext,
               trajectory: TrajectoryData) -> DecisionResult:
        """
        Returns:
        - apply_recommendation: YES / NO / CONDITIONAL
        - confidence: 0-100
        - shortlist_probability: estimated % chance of shortlist
        - optimal_next_skill: highest ROI skill to learn
        - expected_score_after_skill: projected score improvement
        - time_to_ready: estimated time to reach STRONG_FIT
        """
```

Output example:

```json
{
  "decision": "APPLY_WITH_PREPARATION",
  "confidence": 78,
  "shortlist_probability": 68,
  "reasoning": "Strong semantic alignment (82%) but missing 2 critical skills",
  "optimal_next_action": {
    "skill": "AWS",
    "expected_score_delta": "+14",
    "estimated_learning_time": "3-4 weeks",
    "market_demand_trend": "↑42% in 6 months"
  },
  "if_you_add_aws": {
    "new_score": 86,
    "new_shortlist_probability": 84,
    "new_fit_level": "STRONG_FIT"
  }
}
```

### Updated Pipeline Flow

```text
Resume + JD + Market Data + User History
        ↓
┌─────────────────────────────┐
│    INTELLIGENCE ENGINE      │
│ (Extraction → Analysis →    │
│  Scoring → Reasoning)       │
└─────────────┬───────────────┘
              ↓
┌─────────────────────────────┐
│    DECISION ENGINE ⭐        │
│ (Apply? → Probability →     │
│  Next Action → ROI →        │
│  Simulate Future)           │
└─────────────┬───────────────┘
              ↓
    Actionable Outcome
```

---

## Open Questions

> [!IMPORTANT]
> **Q1**: Should existing `core/backend/app/` stubs (auth.py, report.py, roadmap.py) be preserved as-is or cleaned up? This plan focuses on the Analysis Engine only.

<!-- -->

> [!IMPORTANT]
> **Q2**: Skill taxonomy — start with 500+ now or ~200 curated and expand? Recommendation: 500+ since the embedding store can handle discovery of missing ones.

<!-- -->

> [!IMPORTANT]
> **Q3**: Replace existing `fit_classifier.py` entirely with `IntelligenceEngine`? Recommendation: **Yes** — the new system completely subsumes it.

<!-- -->

> [!IMPORTANT]
> **Q4** ★ NEW: For the state backend — should Phase 1 include the Redis implementation, or just the in-memory version with Redis added in Phase 2?

---

## Verification Plan

### Automated Tests

- `test_intelligence_engine.py` — full pipeline integration
- `test_skill_extractor.py` — all 4 layers including embedding discovery
- `test_reasoning_engine.py` — evidence chain synthesis produces valid explanations
- `test_adaptive_scorer.py` — default scoring → feedback adjustment → recalibration
- `test_feedback_processor.py` — corrections stored, taxonomy updated, scorer notified
- `test_analyze_endpoint.py` — API contract, edge cases, error handling

### Manual Verification

- POST resume + JD → inspect full `AnalysisResult` JSON
- Submit feedback → verify scorer weights shift
- Verify reasoning traces explain every score component
- Health endpoint confirms all subsystems loaded
