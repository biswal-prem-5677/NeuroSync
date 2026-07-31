# NeuroSync — Implementation Plan (Phased)

**Version**: 2.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE  
**Detailed Architecture Reference**: [implementation_plan.md](file:///c:/%E0%B9%80%E0%B8%AD%E0%B8%81%E0%B8%AA%E0%B8%B2%E0%B8%A3/neurosync/implementation_plan.md) (1103-line original spec — preserved as technical reference)
**Verified Build Status**: [13_STATUS_TRACKER.md](13_STATUS_TRACKER.md) — this plan states *intent*; the tracker states *measured reality*.

---

## Architecture Summary

```text
core/backend/app/
├── api/                    ← Thin controllers (no business logic)
│   ├── deps.py             ← DI container (lazy singletons + analysis cache)
│   ├── schemas.py          ← Request/response schemas
│   └── v1/endpoints/       ← analyze.py, feedback.py, health.py
├── models/                 ← Domain models + enums
│   ├── domain.py           ← Skill, ExtractionResult, ScoringBreakdown, etc.
│   └── enums.py            ← SkillCategory, GapPriority, FitLevel, etc.
├── services/               ← Intelligence layer (ALL business logic lives here)
│   ├── skill_extractor.py  ← 4-layer hybrid extraction (712 lines)
│   ├── semantic_engine.py  ← 3-layer semantic similarity (489 lines)
│   ├── skill_gap_analyzer.py ← Cluster-based gap reasoning (568 lines)
│   └── intelligence_engine.py ← Central decision brain (776 lines)
├── utils/                  ← Shared utilities
│   ├── text_processor.py   ← Text cleaning, section detection, chunking
│   ├── skill_taxonomy.py   ← Taxonomy loader (294 skills, singleton)
│   └── embedding_store.py  ← Skill embedding index + discovery
├── config.py               ← Pydantic Settings (env-driven, zero hardcoding)
└── main.py                 ← FastAPI app factory + lifespan + middleware
```

---

## Phase Overview

| Phase | Name | Status | Files | Focus |
| --- | --- | --- | --- | --- |
| **0** | Foundation & Scaffolding | ✅ COMPLETE | 21 files | Architecture, models, config, taxonomy |
| **1** | Bug Fixes & Cleanup | 🟡 PARTIAL | 3 fixed, 12 deleted | DI wiring, dead code removal |
| **2** | Validate & Harden | 🟡 IN PROGRESS | ~5 files | Startup test, end-to-end validation, file parser |
| **3** | Intelligence Expansion | ⬜ PLANNED | ~6 new files | Reasoning, insights, feedback loop, state layer |
| **3.5** | Human State Intelligence | ⬜ PLANNED | ~5 new files | CareerState, observations, predictions, agent decisions |
| **4** | Market & Trajectory | ⬜ PLANNED | ~3 new files | Market intelligence, career tracking, adaptive scoring |
| **5** | Frontend | ⬜ PLANNED | ~15 files | React/Next.js dashboard, results UI, simulation playground |
| **6** | Scale & Production | ⬜ PLANNED | ~8 files | Redis state, Docker, auth, rate limiting, tests |

---

## Phase 0 — Foundation & Scaffolding ✅ COMPLETE

> Built the entire core pipeline from scratch. ~4,059 lines of production-grade code.

### Completed Modules

| # | File | Lines | What It Does |
| --- | --- | --- | --- |
| 1 | `config.py` | 85 | Centralized Pydantic Settings — every threshold env-overridable |
| 2 | `models/enums.py` | 51 | SkillCategory (9), MatchMethod (4), GapPriority (4), FitLevel (5), InsightType (4) |
| 3 | `models/domain.py` | 138 | Skill (with proficiency), ExtractionResult, SkillGapItem, ScoringBreakdown, ReasoningTrace |
| 4 | `models/__init__.py` | 13 | Clean re-exports |
| 5 | `utils/text_processor.py` | 157 | 8-step text cleaning, 9-section detection, semantic chunking |
| 6 | `utils/skill_taxonomy.py` | 220 | Taxonomy loader — 294 skills, alias resolution, category/related lookup, thread-safe singleton |
| 7 | `data/skill_taxonomy.json` | ~1800 | 294 skills across 15 categories with aliases, relationships, importance weights |
| 8 | `utils/embedding_store.py` | 288 | Skill embedding index — encode all taxonomy skills, cosine discovery, blacklist filtering |
| 9 | `services/skill_extractor.py` | 712 | 4-layer extraction: Taxonomy → NER (spaCy) → Semantic cross-doc → Embedding discovery |
| 10 | `services/semantic_engine.py` | 489 | 3-layer similarity: Section-aware → Chunk-level matrix → Skill-aligned context depth |
| 11 | `services/skill_gap_analyzer.py` | 568 | Cluster-based gap analysis with priority reasoning, improvement ROI ranking, learning time estimation |
| 12 | `services/intelligence_engine.py` | 776 | Central brain: composite scoring, fit classification, shortlist probability, what-if simulation, recommendation, feedback storage |
| 13 | `api/deps.py` | 134 | Dependency injection — lazy singletons for all services + analysis cache |
| 14 | `api/schemas.py` | 50 | AnalyzeRequest, FeedbackRequest validation |
| 15 | `api/v1/router.py` | 15 | Mounts analyze + health + feedback endpoints |
| 16 | `api/v1/endpoints/analyze.py` | 206 | Full pipeline: extract → semantic → gap → decision → response |
| 17 | `api/v1/endpoints/health.py` | 35 | Component-level health check |
| 18 | `api/v1/endpoints/feedback.py` | 67 | Outcome recording with cached decision lookup |
| 19 | `main.py` | 100 | App factory, CORS, request-ID middleware, global error handler, lifespan warmup |

**Total: ~4,059 lines across 19 production files.**

---

## Phase 1 — Bug Fixes & Cleanup 🟡 PARTIAL

> Fixed 3 critical bugs that would have crashed the system. Deleted 12 dead files.
>
> **Why not COMPLETE**: [12_SYSTEM_ARCHITECTURE.md](12_SYSTEM_ARCHITECTURE.md) §10 scopes 7 further
> services to MVP tier 1 — `reasoning_engine`, `insights_engine`, `feedback_processor`,
> `adaptive_scorer`, `llm_enhancer`, `state/base.py`, `state/memory_state.py`. None exist yet.
> They are **executed** in Phase 3 of this plan (settled 2026-07-27, see
> [10_DECISION_LOG.md](10_DECISION_LOG.md)), so Phase 1 stays open until Phase 3 lands.

### Bugs Fixed

| # | Bug | File | Fix |
| --- | --- | --- | --- |
| 1 | `SkillEmbeddingStore` received `config` instead of `model` | `deps.py` | Pass `get_semantic_model()` + `config.embedding_discovery_threshold` |
| 2 | `embedding_store.initialize()` never called | `deps.py` + `main.py` | Call during singleton creation + lifespan warmup |
| 3 | Feedback endpoint used dummy `Decision` stub | `feedback.py` + `analyze.py` + `deps.py` | Added `cache_analysis()` / `get_cached_analysis()` — feedback now references real decisions |

### Dead Code Removed

| File | Lines | Reason |
| --- | --- | --- |
| `services/fit_classifier.py` | 317 | Superseded by `intelligence_engine.py` |
| `services/resume_service.py` | 32 | Old pipeline — replaced by 4-service architecture |
| `services/report_service.py` | 0 | Empty stub |
| `services/roadmap_service.py` | 0 | Empty stub |
| `services/auth_service.py` | 0 | Empty stub |
| `utils/skill_engine.py` | 53 | 7-alias substring matcher — replaced by 294-skill taxonomy |
| `api/auth.py` | 8 | Empty stub causing duplicate operation ID warning |
| `api/resume.py` | 22 | Old endpoint |
| `api/report.py` | 4 | Empty stub |
| `api/roadmap.py` | 5 | Empty stub |
| `models/user.py` | 3 | Empty stub |
| `db/` directory | 2 files | Empty database stubs |

---

## Phase 2 — Validate & Harden 🟡 IN PROGRESS

> Goal: Prove the pipeline works end-to-end with real data. Add file upload support.
>
> **2.2 validation FAILED on quality** (2026-07-27): the pipeline returns a well-formed response but
> the wrong answer — a near-ideal candidate scored 20.85 → `do_not_apply`. Defects D1–D5 are recorded
> in [13_STATUS_TRACKER.md](13_STATUS_TRACKER.md) §4 and are fixed in **2.6** below before Phase 3 starts.

### 2.1 — Dependency Installation & Startup Test ✅

- [x] Install all Python dependencies (`requirements.txt`)
- [x] Download spaCy model (`en_core_web_sm` 3.8.0)
- [x] Run app — clean startup, all services initialized (embedding store: 294 skills in 996ms)
- [x] Hit `GET /api/v1/health` — 200 in 28ms *(caveat: reports `ner_available: false` until first request — see 2.7)*

### 2.2 — End-to-End Validation 🟡

- [x] Send real resume + JD to `POST /api/v1/analyze` — 200 in 9,413ms
- [x] Verify response shape matches schema (decision, scoring, skills, gaps, improvement_path)
- [x] Verify skill extraction returns meaningful results — 42 resume / 25 JD skills
- [x] Verify gap analysis produces reasoned explanations (not template strings) — confirmed contextual
- [x] Verify what-if simulations produce score deltas — 3 simulations, deltas +2.21 / +1.60 / +1.48
- [ ] **FAILED** — verify the decision is *correct*, not merely well-formed (see 2.6)
- [ ] Test with degraded mode (no SentenceTransformer) — verify fallback works

### 2.6 — Correctness Fixes ★ NEW (blocks Phase 3)

- [ ] **D1** JD alternative-group parsing — "Python, Go, **or** Java" is ONE requirement, not three
- [ ] **D1** Parent/child skill resolution — PostgreSQL satisfies SQL; AWS satisfies Cloud Computing
- [ ] **D1** Recalibrate gap penalty against corrected gap counts ([02](02_INTELLIGENCE_BLUEPRINT.md) §5, §8)
- [ ] **D2** Noise filter for NER + embedding discovery — stop registering `Mentored`, `Computer Science`
- [ ] **D3** Fix gap cluster labels — Docker/Kubernetes must not be labelled "Programming Languages"

### 2.7 — Latency & Warm-Up ★ NEW

- [ ] **D4** Warm spaCy in `lifespan` (doc 12 §7) — removes the ~6s cold-start spike
- [ ] **D4** Re-measure `/analyze` against [11_NFR](11_NON_FUNCTIONAL_REQUIREMENTS.md) §1 (P95 < 2.0s)
- [ ] **D5** Fix `/health` to report `ner_available` + `avg_score` + `recalibrate_at` per [08](08_API_CONTRACT.md) §4

### 2.3 — File Parser

- [ ] **[NEW] `utils/file_parser.py`** — Extract text from PDF (PyPDF2) and DOCX (python-docx)
- [ ] Add `POST /api/v1/analyze-file` endpoint accepting `multipart/form-data`
- [ ] Support: `.pdf`, `.docx`, `.txt`
- [ ] Max file size: 5MB
- [ ] Fallback: raw text extraction with encoding detection

### 2.4 — Response Models

- [ ] **[NEW] `api/responses.py`** — Formal Pydantic response models for type safety
- [ ] `AnalysisResponse`, `FeedbackResponse`, `HealthResponse`
- [ ] Auto-generate OpenAPI schema from models

### 2.5 — Edge Case Hardening

- [ ] Test with empty/minimal resume (50 chars)
- [ ] Test with non-English text
- [ ] Test with binary/garbage input
- [ ] Test with very long resume (50K chars)
- [ ] Verify all error responses are structured JSON

---

## Phase 3 — Intelligence Expansion ⬜ PLANNED

> Goal: Build the missing intelligence layers that separate NeuroSync from every other tool.

### 3.1 — Reasoning Engine

- [ ] **[NEW] `services/reasoning_engine.py`** — Standalone evidence-chain reasoning
- [ ] Input: scoring breakdown + gaps + semantic result → Output: multi-paragraph explanation
- [ ] Every claim backed by a specific data point (not template text)
- [ ] Reasoning synthesis: strengths + weaknesses + primary recommendation rationale
- [ ] Refactor `intelligence_engine.py` to delegate reasoning to this engine

### 3.2 — Insights Engine

- [ ] **[NEW] `services/insights_engine.py`** — SWOT-style structured analysis
- [ ] **Strengths**: What the candidate does well relative to this JD
- [ ] **Weaknesses**: Where the candidate falls short
- [ ] **Opportunities**: Skills close to qualifying (partial credit + short learning curve)
- [ ] **Threats**: Market trends making current skills less relevant (Phase 4 integration)
- [ ] Each insight carries: `type`, `claim`, `evidence`, `confidence`, `action_item`

### 3.3 — Feedback Processor

- [ ] **[NEW] `services/feedback_processor.py`** — Full learning loop
- [ ] Process feedback entries → compute scoring weight adjustments
- [ ] Probability curve recalibration (predicted vs actual outcomes)
- [ ] Taxonomy growth: register skills discovered during extraction
- [ ] Drift detection: alert when scores are consistently too optimistic/pessimistic
- [ ] Trigger threshold: recalibrate after N ≥ 50 feedbacks

### 3.4 — State Layer

- [ ] **[NEW] `state/base.py`** — Abstract `StateBackend` interface
- [ ] **[NEW] `state/memory_state.py`** — In-memory implementation (dict-based)
- [ ] **[NEW] `state/redis_state.py`** — Redis implementation (production)
- [ ] Wire into `config.py`: `NEUROSYNC_STATE_BACKEND=memory|redis`
- [ ] Migrate analysis cache, feedback storage, scoring weights to state layer

### 3.5 — Wiring

- [ ] Update `deps.py` with new service factories
- [ ] Update `analyze.py` to use reasoning + insights engines
- [ ] Update `main.py` lifespan for new services
- [ ] Update `health.py` to report new component status

---

## Phase 3.5 — Human State Intelligence ⬜ PLANNED ★ NEW

> Goal: Transform NeuroSync from Resume Intelligence to Human + Career Intelligence.
> This is the layer that adds behavioral signals, career state modeling, and predictive capabilities.

### 3.5.1 — Domain Models

- [ ] **[NEW] `models/observation.py`** — `ObservationSource` enum, `AgentObservation` model
- [ ] **[NEW] `models/career_state.py`** — `CareerState`, `StateObservation`, `StateTransition`, `LearningSession`
- [ ] Update `models/enums.py` — add `ObservationSource`

### 3.5.2 — Human State Engine

- [ ] **[NEW] `services/human_state_engine.py`** — The core engine
- [ ] Aggregate signals across 8 observation sources
- [ ] Derive StateObservations from raw AgentObservations (NOT raw emotions)
- [ ] Compute CareerState (confidence, momentum, engagement, consistency, growth_velocity, burnout_risk, interview_readiness, career_readiness)
- [ ] Detect StateTransitions (before → after with reasoning)
- [ ] Camera signals are optional — engine works without them

### 3.5.3 — Prediction Layer

- [ ] Integrated into human_state_engine.py
- [ ] `predict_burnout(career_state)` → burnout_probability
- [ ] `predict_dropout(career_state)` → dropout_probability
- [ ] `predict_interview_success(career_state)` → interview_success_probability
- [ ] `predict_skill_completion(career_state, skill)` → skill_completion_probability
- [ ] Predictions trigger agent actions BEFORE problems happen

### 3.5.4 — Agent Decision Engine

- [ ] **[NEW] `services/agent_decision_engine.py`**
- [ ] Consumes CareerState (NEVER raw signals)
- [ ] Checks prediction thresholds → generates recommendations
- [ ] Roadmap adjustments, workload changes, difficulty changes, reinforcement

### 3.5.5 — Behavior Endpoints

- [ ] **[NEW] `api/v1/endpoints/behavior.py`**
- [ ] `POST /behavior/session/start` — begin learning session
- [ ] `POST /behavior/session/stop` — end learning session
- [ ] `POST /behavior/event` — record observation from any source
- [ ] `GET /behavior/profile` — user behavioral profile
- [ ] `GET /behavior/state` — current CareerState + predictions

### 3.5.6 — Gamification Engine

- [ ] **[NEW] `services/gamification_engine.py`**
- [ ] Career XP calculation, levels, streaks
- [ ] Motivation reinforcement through progress visualization

## Phase 4 — Market & Trajectory ⬜ PLANNED

> Goal: Add the time and market dimensions that make NeuroSync truly intelligent.

### 4.1 — Market Intelligence Engine

- [ ] **[NEW] `services/market_intelligence_engine.py`**
- [ ] `get_skill_demand(skill)` → demand trend (↑37% / stable / ↓12%)
- [ ] `get_salary_signal(skills, role)` → market salary range
- [ ] `get_hiring_velocity(role, region)` → openings per month
- [ ] Phase 1: Static curated JSON snapshots
- [ ] Phase 2: API integrations (job posting analysis)
- [ ] Integrate into gap priority: "K8s demand ↑37% → upgrades from HIGH to CRITICAL"

### 4.2 — Career Trajectory Engine

- [ ] **[NEW] `services/career_trajectory_engine.py`**
- [ ] `record_snapshot(user_id, skills, score, timestamp)`
- [ ] `compute_growth_velocity(user_id)` → skills/month, score/month
- [ ] `predict_trajectory(user_id, target_role)` → estimated time to readiness
- [ ] `compare_roles(user_id, roles)` → multi-role fit comparison

### 4.3 — Adaptive Scorer

- [ ] **[NEW] `services/adaptive_scorer.py`**
- [ ] Default weights from config → adjusted by feedback data
- [ ] Per-role weight profiles (backend roles weight skills higher, PM roles weight semantic)
- [ ] Confidence-weighted scoring (lower confidence → wider recommendation bands)
- [ ] Weight evolution tracking (log weight changes over time)

### 4.4 — LLM Enhancer

- [ ] **[NEW] `services/llm_enhancer.py`**
- [ ] Optional layer — system works perfectly without it
- [ ] Providers: Gemini (default), OpenAI (fallback)
- [ ] Use cases: reasoning refinement, career advice generation, resume improvement suggestions
- [ ] Timeout: 5000ms, graceful fallback to non-LLM output
- [ ] Config: `NEUROSYNC_LLM_PROVIDER=gemini|openai|none`

---

## Phase 5 — Frontend ⬜ PLANNED

> Goal: Build the premium UI that makes the intelligence visible and actionable.
> Reference: [06_UI_UX_DESIGN_BRIEF.md](file:///c:/%E0%B9%80%E0%B8%AD%E0%B8%81%E0%B8%AA%E0%B8%B2%E0%B8%A3/neurosync/blueprints/06_UI_UX_DESIGN_BRIEF.md)

### 5.1 — Foundation

- [ ] Initialize React/Next.js project in `core/frontend/`
- [ ] Design system: CSS variables, typography, spacing (from design brief)
- [ ] Dark theme implementation
- [ ] Component library: ScoreRing, DecisionBadge, SkillChip, GapCard

### 5.2 — Core Pages

- [ ] Landing page with hero + "Analyze" CTA
- [ ] Upload/paste screen (resume + JD input)
- [ ] Results dashboard (full analysis visualization)
- [ ] Loading state (neural network animation)

### 5.3 — Interactive Features

- [ ] What-if simulation playground
- [ ] Gap card expand/collapse with reasoning
- [ ] Improvement path with "Simulate" buttons
- [ ] Feedback submission modal

### 5.4 — Polish

- [ ] Mobile responsive layout (all breakpoints)
- [ ] Micro-animations (score ring fill, stagger reveals)
- [ ] Accessibility (keyboard nav, screen reader, WCAG 2.1 AA)
- [ ] SEO meta tags

---

## Phase 6 — Scale & Production ⬜ PLANNED

> Goal: Make it production-ready, testable, and deployable.

### 6.1 — Testing

- [ ] `tests/test_skill_extractor.py` — all 4 extraction layers
- [ ] `tests/test_semantic_engine.py` — 3 similarity layers + fallback
- [ ] `tests/test_skill_gap_analyzer.py` — gap reasoning + clustering
- [ ] `tests/test_intelligence_engine.py` — full pipeline integration
- [ ] `tests/test_analyze_endpoint.py` — API contract + edge cases
- [ ] `tests/test_feedback.py` — feedback loop + calibration

### 6.2 — Authentication & Authorization

- [ ] JWT-based auth (optional — anonymous analysis still allowed)
- [ ] User registration + login endpoints
- [ ] API key auth for programmatic access
- [ ] Rate limiting: 100 req/min per IP (anonymous), 500/min (authenticated)

### 6.3 — Deployment

- [ ] `Dockerfile` for backend
- [ ] `docker-compose.yml` (app + Redis)
- [ ] Environment-specific configs (dev, staging, prod)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Health check + readiness probe

### 6.4 — Observability

- [ ] Structured JSON logging (ELK/CloudWatch ready)
- [ ] Per-component timing in response metadata
- [ ] Error tracking (Sentry integration)
- [ ] Metrics endpoint (Prometheus-compatible)

---

## Dependency Map

```text
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3 ──→ Phase 4
  ✅            ✅          ⬜           ⬜           ⬜
                                         │
                                         ├──→ Phase 5 (Frontend)
                                         │       ⬜
                                         └──→ Phase 6 (Production)
                                                 ⬜
```

- **Phases 0-3 are strictly sequential** (each depends on the previous)
- **Phase 4 can partially overlap with Phase 3** (market engine is independent)
- **Phase 5 can start after Phase 2** (API is stable enough for frontend work)
- **Phase 6 runs in parallel with Phase 4-5** (tests + deployment are independent)

---

## Current Status

```text
Phase 0: ████████████████████ 100%  ✅ Foundation complete (21 files, ~4160 lines)
Phase 1: ██████████████░░░░░░  70%  🟡 Bugs fixed; 7 MVP-tier services still unbuilt
Phase 2: ████████░░░░░░░░░░░░  40%  🟡 Deps + startup ✅ | validation quality ❌ → fixing in 2.6
Phase 3: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜ State + Reasoning + Insights + Feedback
Phase 4: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜ Market + Trajectory + Adaptive + LLM
Phase 5: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜ Frontend
Phase 6: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜ Production
```

**Next action**: Phase 2.6 — correctness fixes (D1 → D2 → D3), then 2.3/2.4, then 2.7.

---

*This plan is the living execution roadmap. Update status as each item completes. The detailed 1103-line architecture spec lives in the root `implementation_plan.md`.*
