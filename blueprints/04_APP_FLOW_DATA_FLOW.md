# NeuroSync — App Flow & Data Flow

**Version**: 1.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE

---

## 1. Primary User Flow — Resume Analysis

```text
┌─────────┐
│  USER   │
│ Uploads │
│ Resume  │
│  + JD   │
└────┬────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        API LAYER                                     │
│  POST /api/v1/analyze                                                │
│  ┌────────────┐                                                      │
│  │ Validate   │ → min length? alpha ratio? encoding? truncate?      │
│  │ Request    │ → Reject junk, accept clean text                     │
│  └─────┬──────┘                                                      │
│        │                                                             │
│        ▼                                                             │
│  ┌────────────┐                                                      │
│  │ Generate   │ → analysis_id = uuid[:12]                           │
│  │ Analysis ID│ → request_id from X-Request-ID header               │
│  └─────┬──────┘                                                      │
└────────┼─────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     INTELLIGENCE PIPELINE                            │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │ STEP 1: TEXT PREPROCESSING                      │                │
│  │                                                 │                │
│  │  resume_text ──→ clean_text() ──→ resume_clean  │                │
│  │  jd_text ─────→ clean_text() ──→ jd_clean       │                │
│  │                                                 │                │
│  │  Operations: strip HTML, remove control chars,  │                │
│  │  Unicode NFC normalize, collapse whitespace     │                │
│  └─────────────────────┬───────────────────────────┘                │
│                        │                                             │
│           ┌────────────┼────────────┐                                │
│           ▼            ▼            ▼                                │
│  ┌─────────────┐ ┌──────────┐ ┌───────────────┐                    │
│  │ STEP 2a:    │ │ STEP 2b: │ │ STEP 2c:      │                    │
│  │ Extract     │ │ Extract  │ │ Semantic       │  ← Run in parallel│
│  │ Resume      │ │ JD       │ │ Similarity     │                    │
│  │ Skills      │ │ Skills   │ │                │                    │
│  │             │ │          │ │ Section-aware  │                    │
│  │ 4-Layer:    │ │ 4-Layer: │ │ + Chunk-level  │                    │
│  │ Taxonomy    │ │ Same     │ │ + Skill-aligned│                    │
│  │ NER         │ │ pipeline │ │                │                    │
│  │ Semantic    │ │          │ │ Fallback:      │                    │
│  │ Discovery   │ │          │ │ TF-IDF cosine  │                    │
│  └──────┬──────┘ └────┬─────┘ └──────┬─────────┘                    │
│         │             │              │                               │
│         ▼             ▼              │                               │
│  ┌─────────────────────────┐         │                               │
│  │ STEP 2d: Cross-Document │         │                               │
│  │ Semantic Skill Matching │         │                               │
│  │                         │         │                               │
│  │ Find skills expressed   │         │                               │
│  │ differently in resume   │         │                               │
│  │ vs JD (paraphrases)     │         │                               │
│  └──────────┬──────────────┘         │                               │
│             │                        │                               │
│             ▼                        │                               │
│  ┌──────────────────────────────┐    │                               │
│  │ STEP 3: GAP ANALYSIS        │◄───┘                               │
│  │                              │                                    │
│  │ For each JD skill NOT in     │                                    │
│  │ resume:                      │                                    │
│  │  → Compute priority score    │                                    │
│  │  → Check related skills      │                                    │
│  │  → Generate reasoning chain  │                                    │
│  │  → Estimate learning time    │                                    │
│  │  → Group into clusters       │                                    │
│  └──────────┬───────────────────┘                                    │
│             │                                                        │
│             ▼                                                        │
│  ┌──────────────────────────────┐                                    │
│  │ STEP 4: DECISION ENGINE     │                                     │
│  │                              │                                    │
│  │ Inputs:                      │                                    │
│  │  • semantic_score            │                                    │
│  │  • skill_overlap (weighted)  │                                    │
│  │  • gap_penalty (importance-  │                                    │
│  │    weighted)                 │                                    │
│  │                              │                                    │
│  │ Computes:                    │                                    │
│  │  • Composite score (0-100)   │                                    │
│  │  • Fit level                 │                                    │
│  │  • Shortlist probability     │                                    │
│  │  • What-if simulations       │                                    │
│  │  • ROI improvement path      │                                    │
│  │  • Recommendation            │                                    │
│  │  • Multi-factor reasoning    │                                    │
│  └──────────┬───────────────────┘                                    │
│             │                                                        │
│             ▼                                                        │
│  ┌──────────────────────────────┐                                    │
│  │ STEP 5: CACHE DECISION      │                                     │
│  │ cache_analysis(id, decision) │                                    │
│  └──────────┬───────────────────┘                                    │
└─────────────┼────────────────────────────────────────────────────────┘
              │
              ▼
     ┌────────────────┐
     │ JSON Response  │ → analysis_id, decision, scoring, skills,
     │ to Client      │   gaps, improvement_path, strengths,
     │                │   weaknesses, simulations, evidence, meta
     └────────────────┘
```

---

## 2. Feedback Flow

```text
┌─────────┐
│  USER   │
│ Reports │
│ Outcome │
└────┬────┘
     │  "I got an interview" / "Rejected" / "Hired"
     ▼
┌──────────────────────────────────────────┐
│ POST /api/v1/feedback                    │
│                                          │
│ Body: {                                  │
│   analysis_id: "a1b2c3d4e5f6",          │
│   outcome: "interview",                 │
│   notes: "Got past screening round"     │
│ }                                        │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ LOOKUP CACHED DECISION                   │
│                                          │
│ get_cached_analysis(analysis_id)         │
│   ├── Found? → Use real Decision object │
│   └── Expired? → Use minimal stub       │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ INTELLIGENCE ENGINE                      │
│ record_feedback(decision, outcome)       │
│                                          │
│ Stores:                                  │
│  • recommendation vs actual outcome      │
│  • score vs outcome                      │
│  • shortlist_prob calibration data       │
│  • confidence accuracy                   │
│                                          │
│ Triggers (when N >= 50):                 │
│  • Weight recalibration                  │
│  • Probability curve adjustment          │
│  • Drift detection                       │
└──────────────┬───────────────────────────┘
               │
               ▼
     ┌────────────────┐
     │ Response       │
     │ { status,      │
     │   decision_    │
     │   found,       │
     │   feedback_    │
     │   stats }      │
     └────────────────┘
```

---

## 3. Skill Extraction Data Flow (Internal)

```text
                        Input Text
                            │
                   ┌────────▼────────┐
                   │  clean_text()   │
                   │  normalize()    │
                   │  detect_sections│
                   └────────┬────────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
        ┌────────────┐ ┌─────────┐ ┌──────────────┐
        │ LAYER 1    │ │ LAYER 2 │ │  LAYER 3     │
        │ TAXONOMY   │ │   NER   │ │  SEMANTIC    │
        │            │ │         │ │              │
        │ For each   │ │ spaCy   │ │ Embed chunks │
        │ section:   │ │ Phrase  │ │ vs taxonomy  │
        │  scan for  │ │ Matcher │ │ embeddings   │
        │  aliases   │ │    +    │ │ cosine > 0.75│
        │  from 294  │ │ Entity  │ │              │
        │  taxonomy  │ │ Ruler   │ │ Catches:     │
        │  skills    │ │         │ │ "ML pipelines│
        │            │ │ Catches:│ │ in prod" ≈   │
        │ Fast,      │ │ Unknown │ │ "machine     │
        │ precise    │ │ proper  │ │ learning     │
        │            │ │ nouns   │ │ engineering" │
        └─────┬──────┘ └────┬────┘ └──────┬───────┘
              │             │             │
              └──────┬──────┴─────────────┘
                     │
                     ▼
              ┌──────────────┐
              │  LAYER 4     │
              │  EMBEDDING   │
              │  DISCOVERY   │
              │              │
              │  Extract     │
              │  candidate   │
              │  terms →     │
              │  compare to  │
              │  all 294     │
              │  embeddings  │
              │              │
              │  Filter:     │
              │  • Blacklist │
              │  • Threshold │
              │  • Frequency │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  MERGE +     │
              │  DEDUPLICATE │
              │              │
              │ Canonical    │
              │ name merge   │
              │              │
              │ Per skill:   │
              │ • proficiency│
              │ • confidence │
              │ • sections   │
              │ • match_by   │
              │ • occurrences│
              └──────┬───────┘
                     │
                     ▼
              ExtractionResult
```

---

## 4. Semantic Similarity Data Flow (Internal)

```text
     resume_clean              jd_clean
          │                       │
          ▼                       ▼
   extract_sections()      embed(jd_clean)
          │                       │
          ▼                       │
   ┌──────────────┐              │
   │ LAYER 2a:    │              │
   │ Section-Aware│              │
   │              │              │
   │ For each     │              │
   │ section:     │              │
   │  chunk →     │◄─────────────┘
   │  embed →     │
   │  compare to  │
   │  JD embed    │
   │  weight by   │
   │  section     │
   │  importance  │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ LAYER 2b:    │
   │ Chunk-Level  │
   │              │
   │ resume_chunks│
   │  × jd_chunks │
   │  → similarity│
   │    matrix     │
   │  → best match│
   │    per JD     │
   │    chunk      │
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │ LAYER 2c:    │
   │ Skill-Aligned│
   │              │
   │ For each JD  │
   │ skill:       │
   │  find context│
   │  in resume   │
   │  (±150 chars)│
   │  embed context│
   │  vs "expert  │
   │  in {skill}" │
   └──────┬───────┘
          │
          ▼
   ┌──────────────────────┐
   │ AGGREGATION          │
   │                      │
   │ section * 0.45       │
   │ + chunk_best * 0.25  │
   │ + skill_align * 0.30 │
   │                      │
   │ → SemanticResult     │
   └──────────────────────┘
```

---

## 5. Scoring & Decision Data Flow (Internal)

```text
  semantic_score     skill_overlap      gap_penalty
  (0.0 - 1.0)       (0.0 - 1.0)        (0.0 - 1.0)
       │                  │                  │
       │    ┌─────────────┼──────────────────┘
       │    │             │
       ▼    ▼             ▼
  ┌────────────────────────────────┐
  │ COMPOSITE SCORING              │
  │                                │
  │ If semantic available:         │
  │   sem * w_sem                  │
  │   + overlap * w_skill          │
  │   + (-penalty) * w_gap         │
  │                                │
  │ Weights re-normalized if       │
  │ component missing              │
  │                                │
  │ Score clamped to [0, 100]      │
  └─────────────┬──────────────────┘
                │
       ┌────────┼─────────┐
       ▼        ▼         ▼
  ┌────────┐ ┌──────┐ ┌──────────┐
  │ Fit    │ │Short-│ │ What-If  │
  │ Level  │ │list  │ │Simulation│
  │        │ │Prob  │ │          │
  │ >=80 → │ │Sigmo-│ │For each  │
  │ STRONG │ │id    │ │critical/ │
  │ >=65 → │ │curve │ │high gap: │
  │ GOOD   │ │      │ │ add skill│
  │ >=50 → │ │Adjust│ │ recompute│
  │ POTEN. │ │for   │ │ full     │
  │ >=35 → │ │critic│ │ pipeline │
  │ WEAK   │ │al    │ │ → delta  │
  │ else → │ │gaps  │ │          │
  │ NO_FIT │ │      │ │          │
  └───┬────┘ └──┬───┘ └────┬─────┘
      │         │          │
      └─────────┼──────────┘
                │
                ▼
  ┌────────────────────────────────┐
  │ RECOMMENDATION ENGINE          │
  │                                │
  │ score + gaps + prob → decision │
  │                                │
  │ STRONG_APPLY                   │
  │ APPLY                          │
  │ APPLY_WITH_PREPARATION         │
  │ UPSKILL_THEN_APPLY             │
  │ DO_NOT_APPLY                   │
  └─────────────┬──────────────────┘
                │
                ▼
  ┌────────────────────────────────┐
  │ REASONING SYNTHESIS            │
  │                                │
  │ Assemble evidence chain:       │
  │  • semantic alignment claim    │
  │  • skill coverage claim        │
  │  • gap severity claim          │
  │  • strengths summary           │
  │  • weaknesses summary          │
  │  • top improvement action      │
  │                                │
  │ → Multi-factor reasoning text  │
  └─────────────┬──────────────────┘
                │
                ▼
            Decision
```

---

## 6. System Startup Flow

```text
uvicorn app.main:app
         │
         ▼
    create_app()
         │
    ┌────▼──────────────────────────────┐
    │ lifespan(app) — STARTUP           │
    │                                    │
    │ 1. get_taxonomy()                 │  Load 294 skills from JSON
    │         │                         │
    │ 2. get_semantic_model()           │  Load SentenceTransformer (~5s)
    │         │                         │
    │ 3. get_embedding_store()          │  Embed all 294 skills (~2s)
    │    └── initialize()               │
    │         │                         │
    │ 4. get_extractor()                │  Load spaCy + build PhraseMatcher
    │         │                         │
    │ 5. get_semantic_engine()          │  Ready with shared model
    │                                    │
    │ Total cold start: ~10-15 seconds  │
    └────────────────────────────────────┘
         │
         ▼
    Server ready on :8000
    Swagger UI at /docs
```

---

## 7. Future Flows (Planned)

### File Upload Flow

```text
User uploads PDF/DOCX
        ↓
file_parser.py → extract_text()
        ↓
Raw text → existing analysis pipeline
```

### Market Intelligence Flow

```text
Gap Analysis result
        ↓
market_intelligence_engine.get_skill_demand(skill)
        ↓
Demand trend + salary signal + hiring velocity
        ↓
Injected into gap priority scoring
        ↓
Enhanced recommendations
```

### Career Trajectory Flow

```text
User completes analysis #1 (Jan) → snapshot stored
User completes analysis #2 (Mar) → snapshot stored
User completes analysis #3 (Jun) → snapshot stored
        ↓
trajectory_engine.compute_growth_velocity()
        ↓
"You're gaining 5.7 score points/month"
"At this rate, STRONG_FIT by August"
```

### Human State Intelligence Flow (Phase 2+) ★ NEW

```text
Observation Sources (multi-signal)
│
├── RESUME:    skill extraction signals
├── JD:        role requirement signals
├── FEEDBACK:  hired / rejected / interview / ghosted
├── LEARNING:  session duration, completion rate, abandoned
├── PROJECT:   commit frequency, portfolio activity
├── INTERVIEW: mock/real interview performance
├── MARKET:    demand trends, salary signals
├── CAMERA:    attention, focus, engagement (OPTIONAL)
│
▼
AgentObservation records
│   (source-tagged, timestamped, confidence-scored)
│
▼
Human State Intelligence Engine
│
├── 1. Aggregate signals across sources
├── 2. Derive StateObservations (NOT raw emotions)
│      "struggling" (derived) NOT "frustrated" (raw)
├── 3. Compute CareerState (unified representation)
│      confidence, momentum, engagement, consistency,
│      growth_velocity, burnout_risk, interview_readiness,
│      career_readiness
├── 4. Detect StateTransitions (before → after)
│      confidence: 0.42 → 0.68
│      reason: "Completed 3 modules after roadmap adjustment"
└── 5. Run Prediction Layer
       burnout_probability: 0.78
       dropout_probability: 0.34
       interview_success_probability: 0.62
       skill_completion_probability: 0.81
│
▼
Agent Decision Engine
│
├── Consumes CareerState (NEVER raw signals)
├── Checks prediction thresholds
│   burnout_probability > 0.7 → pause roadmap
│   dropout_probability > 0.5 → add encouragement
│   interview_success < 0.3  → defer "apply now"
│
▼
Recommendations
│
├── Roadmap adjustments
├── Workload changes
├── Module difficulty changes
├── Reinforcement messages
└── "Apply now" / "Wait" decisions
```

---

*This document ensures every engineer can trace exactly how data moves through NeuroSync from input to output.*
