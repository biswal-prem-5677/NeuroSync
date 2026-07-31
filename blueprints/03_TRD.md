# NeuroSync — Technical Requirements Document (TRD)

**Version**: 1.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE

---

## 1. System Architecture

### High-Level Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │React/Next│  │  Mobile  │  │ CLI Tool │  │ External API │    │
│  │Dashboard │  │   App    │  │          │  │  Consumers   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘    │
└───────┼──────────────┼──────────────┼───────────────┼────────────┘
        │              │              │               │
        └──────────────┼──────────────┼───────────────┘
                       │              │
              ┌────────▼──────────────▼────────┐
              │        API GATEWAY              │
              │  (CORS, Auth, Rate Limiting)    │
              └────────────────┬────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │         FASTAPI SERVER          │
              │  ┌─────────────────────────┐    │
              │  │     /api/v1/ Router     │    │
              │  │  ┌─────┐┌──────┐┌─────┐│    │
              │  │  │Analy││Health││Feed- ││    │
              │  │  │ze   ││      ││back  ││    │
              │  │  └──┬──┘└──────┘└──┬───┘│    │
              │  └─────┼──────────────┼────┘    │
              │        │              │         │
              │  ┌─────▼──────────────▼─────┐   │
              │  │   INTELLIGENCE PIPELINE  │   │
              │  │                          │   │
              │  │  Extractor → Semantic    │   │
              │  │  → Gap → Decision        │   │
              │  └──────────────┬───────────┘   │
              │                │                │
              │  ┌─────────────▼──────────┐     │
              │  │     STATE LAYER        │     │
              │  │  Memory │ Redis │ PG   │     │
              │  └─────────────────────────┘    │
              └─────────────────────────────────┘
```

### Service Architecture

```text
core/backend/
├── app/
│   ├── main.py                          # App factory + lifespan + middleware
│   ├── config.py                        # Pydantic Settings (zero hardcoding)
│   │
│   ├── api/                             # Thin controllers (no business logic)
│   │   ├── deps.py                      # DI container (lazy singletons)
│   │   ├── schemas.py                   # API request/response schemas
│   │   └── v1/
│   │       ├── router.py               # Mounts all v1 endpoints
│   │       └── endpoints/
│   │           ├── analyze.py          # POST /api/v1/analyze
│   │           ├── feedback.py         # POST /api/v1/feedback
│   │           └── health.py           # GET /api/v1/health
│   │
│   ├── models/                          # Internal domain models
│   │   ├── domain.py                   # Skill, ExtractionResult, ScoringBreakdown
│   │   └── enums.py                    # SkillCategory, GapPriority, FitLevel
│   │
│   ├── services/                        # Intelligence layer (all business logic)
│   │   ├── skill_extractor.py          # 4-layer hybrid extraction
│   │   ├── semantic_engine.py          # 3-layer semantic similarity
│   │   ├── skill_gap_analyzer.py       # Cluster-based gap reasoning
│   │   ├── intelligence_engine.py      # Central decision brain
│   │   ├── reasoning_engine.py         # Evidence-chain reasoning [PLANNED]
│   │   ├── insights_engine.py          # SWOT analysis [PLANNED]
│   │   ├── feedback_processor.py       # Learning loop [PLANNED]
│   │   ├── adaptive_scorer.py          # Learnable weights [PLANNED]
│   │   ├── human_state_engine.py       # Human State Intelligence [PLANNED]
│   │   ├── agent_decision_engine.py    # Agentic decision layer [PLANNED]
│   │   ├── gamification_engine.py      # Career XP + motivation [PLANNED]
│   │   └── llm_enhancer.py            # Optional LLM layer [PLANNED]
│   │
│   ├── utils/                           # Shared utilities
│   │   ├── text_processor.py           # Text cleaning, section detection, chunking
│   │   ├── skill_taxonomy.py           # Taxonomy loader (singleton, thread-safe)
│   │   ├── embedding_store.py          # Skill embedding cache + discovery
│   │   └── file_parser.py             # PDF/DOCX/TXT extraction [PLANNED]
│   │
│   ├── models/                          # Domain models
│   │   ├── domain.py                   # Skill, ExtractionResult, etc.
│   │   ├── enums.py                    # SkillCategory, GapPriority, etc.
│   │   ├── career_state.py             # CareerState, StateObservation, StateTransition [PLANNED]
│   │   └── observation.py              # ObservationSource enum, AgentObservation [PLANNED]
│   │
│   ├── state/                           # Pluggable persistence [PLANNED]
│   │   ├── base.py                     # Abstract state interface
│   │   ├── memory_state.py            # In-memory (dev/testing)
│   │   └── redis_state.py             # Redis (production)
│   │
│   └── data/
│       └── skill_taxonomy.json         # 294 skills with aliases + relationships
│
├── tests/                               # [PLANNED]
├── requirements.txt
└── README.md
```

---

## 2. Backend Design

### Technology Stack

| Layer | Technology | Version | Rationale |
| --- | --- | --- | --- |
| **Runtime** | Python | 3.11+ | Async support, type hints, ecosystem |
| **Framework** | FastAPI | ≥0.110 | Async, auto-docs, Pydantic integration |
| **Server** | Uvicorn | ≥0.27 | ASGI, production-ready |
| **Validation** | Pydantic | v2.5+ | Performance, strict validation |
| **Config** | Pydantic Settings | ≥2.1 | Env-driven, zero hardcoding |
| **NLP** | spaCy | ≥3.7 | NER, PhraseMatcher |
| **Embeddings** | sentence-transformers | ≥2.2 | all-MiniLM-L6-v2 (384-dim) |
| **Numeric** | NumPy | ≥1.24 | Vector operations |
| **Fallback ML** | scikit-learn | ≥1.3 | TF-IDF fallback |
| **Cache/State** | Redis | ≥5.0 | Production state backend |

### Design Principles

1. **Dependency Injection**: All services receive dependencies via constructor — fully testable
2. **Lazy Singletons**: Services created on first access, warmed during lifespan
3. **Stateless API Layer**: No state in endpoints — everything goes through state backend
4. **Configuration-Driven**: Every threshold, weight, model name → env var overridable
5. **Graceful Degradation**: Every service has a fallback path — system never fully crashes

---

## 3. API Standards

### Base URL

```text
Production:  https://api.neurosync.dev/api/v1/
Development: http://localhost:8000/api/v1/
```

### Endpoints

| Method | Path | Description | Auth |
| --- | --- | --- | --- |
| `POST` | `/api/v1/analyze` | Full resume-to-JD analysis | Optional |
| `POST` | `/api/v1/feedback` | Record analysis outcome | Optional |
| `GET` | `/api/v1/health` | System health + component status | None |
| `POST` | `/api/v1/quick-score` | Fast score without full analysis | Optional |
| `GET` | `/api/v1/career-roadmap` | Career improvement roadmap | Required |
| `GET` | `/api/v1/market-intelligence` | Skill demand data | Required |

### Request/Response Standards

- **Content-Type**: `application/json` only
- **Max Request Body**: 1MB
- **Response Format**: Always JSON with consistent envelope
- **Error Format**: Structured validation errors with field-level detail
- **Request ID**: Every request gets `X-Request-ID` header (generated or forwarded)
- **Timing**: Every response includes `X-Response-Time-Ms` header

### Response Envelope

```json
{
  "analysis_id": "a1b2c3d4e5f6",
  "decision": { ... },
  "scoring": { ... },
  "skills": { ... },
  "gaps": [ ... ],
  "improvement_path": [ ... ],
  "meta": {
    "processing_time_ms": 423.7,
    "extraction_degraded": false,
    "semantic_available": true,
    "versions": {
      "engine": "1.0.0",
      "taxonomy": "1.0.0"
    }
  }
}
```

### Error Response

```json
{
  "error": "validation_error",
  "detail": [
    {
      "field": "resume_text",
      "message": "String should have at least 50 characters",
      "input_length": 12
    }
  ],
  "request_id": "abc123"
}
```

---

## 4. Data Contracts

### Skill Object

```json
{
  "name": "react",
  "canonical": "React",
  "category": "frontend",
  "confidence": 0.95,
  "matched_by": "taxonomy",
  "proficiency_score": 0.82,
  "evidence_strength": 0.88,
  "occurrence_count": 3,
  "found_in_sections": ["experience", "projects"]
}
```

### Gap Object

```json
{
  "skill": "Kubernetes",
  "category": "infrastructure",
  "priority": "critical",
  "reasoning": "Kubernetes is mentioned 4× in the JD and appears in opening requirements. Your Docker experience (78% similar) provides a foundation, but K8s is a distinct orchestration skill requiring dedicated study.",
  "learning_time_estimate": "3-4 weeks",
  "related_present": ["Docker", "AWS"],
  "confidence": 0.92
}
```

### Decision Object

```json
{
  "recommendation": "apply_with_preparation",
  "confidence": 0.78,
  "shortlist_probability": 0.55,
  "fit_level": "potential_fit",
  "overall_score": 62.4,
  "reasoning": "Viable match, but preparation needed. Overall fit score: 62/100..."
}
```

---

## 5. Security Architecture

### Input Security

| Threat | Mitigation |
| --- | --- |
| **Injection via text** | HTML tag stripping, control char removal, Unicode NFC normalization |
| **Oversized payloads** | Max 50K chars resume, 20K chars JD, 1MB body limit |
| **Junk/binary input** | Alpha ratio check (>30% alphabetic required) |
| **Rate limiting** | Per-IP throttling (planned: 100 req/min) |

### API Security

| Threat | Mitigation |
| --- | --- |
| **Unauthorized access** | JWT auth (planned Phase 2) |
| **CORS abuse** | Configurable allowed origins (currently open for dev) |
| **API key leakage** | LLM API keys in env vars, never in code |
| **DDoS** | Request body size limits, timeout enforcement |

### Data Security

| Threat | Mitigation |
| --- | --- |
| **Resume PII exposure** | Resumes processed in-memory, never persisted to disk by default |
| **Log leakage** | Resume text never logged — only analysis_id, scores, timing |
| **State backend** | Redis auth required in production, TLS for connections |

---

## 6. Scalability Architecture

### Horizontal Scaling

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

- **API layer is fully stateless** — any pod can serve any request
- **ML models loaded per-pod** at startup — no shared GPU required
- **State backend pluggable**: `memory → redis → postgres` via config
- **Embedding store**: Per-pod in-memory (294 skills × 384 dims ≈ 450KB — negligible)

### Estimated Capacity Per Pod

| Component | Memory | CPU | Throughput |
| --- | --- | --- | --- |
| SentenceTransformer (MiniLM) | ~250MB | 1 core | ~50 encodings/sec |
| spaCy (en_core_web_sm) | ~50MB | 0.5 core | ~100 docs/sec |
| Embedding store | ~1MB | negligible | O(1) lookup |
| Taxonomy | ~5MB | negligible | O(1) lookup |
| **Total per pod** | **~310MB** | **2 cores** | **~10-20 analyses/sec** |

---

## 7. Performance Targets

### Response Time Budget

| Component | Target | Timeout |
| --- | --- | --- |
| Text preprocessing | <10ms | N/A |
| Skill extraction (all layers) | <200ms | 500ms |
| Semantic similarity | <150ms | 300ms |
| Gap analysis | <50ms | N/A |
| Scoring + decision | <30ms | N/A |
| Reasoning generation | <30ms | N/A |
| LLM enhancement (optional) | <3000ms | 5000ms |
| **Total (without LLM)** | **<500ms** | |
| **Total (with LLM)** | **<3500ms** | |

### Caching Strategy

| Cache | Scope | Size | TTL |
| --- | --- | --- | --- |
| Taxonomy skill embeddings | Per-pod | 294 vectors | Permanent (until restart) |
| Text embeddings | Per-request | N chunks | Request lifecycle |
| Skill resolution | Per-pod | 1024 entries | Until taxonomy update |
| Extraction results | Per-pod | 1024 entries | LRU eviction |

---

## 8. AI Architecture

### Model Stack

| Model | Purpose | Size | Loading |
| --- | --- | --- | --- |
| `all-MiniLM-L6-v2` | Document + skill embeddings | 80MB | Startup (shared singleton) |
| `en_core_web_sm` | NER + PhraseMatcher | 12MB | Startup (per-extractor) |
| TF-IDF (sklearn) | Semantic fallback | In-memory | On-demand (fallback only) |
| Gemini/OpenAI (optional) | LLM reasoning enhancement | API | Per-request (when enabled) |

### Embedding Dimensions

- **Document embeddings**: 384-dim (MiniLM)
- **Skill embeddings**: 384-dim (same model)
- **Similarity metric**: Cosine (normalized dot product)
- **Normalization**: All embeddings L2-normalized at encode time

### Semantic Thresholds

| Threshold | Value | Purpose |
| --- | --- | --- |
| Skill semantic match | 0.75 | Cross-document skill matching (Layer 3) |
| Embedding discovery | 0.65 | Unknown skill detection (Layer 4) |
| Section similarity | 0.40 | Minimum section-level relevance |
| Skill alignment depth | 0.50 | Context depth for matched skills |

---

## 9. Deployment Architecture

### Development

```bash
cd core/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

### Production (Planned)

```text
┌─────────────────────────────────────┐
│           Load Balancer             │
│         (nginx / ALB)               │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│  Pod 1 │ │  Pod 2 │ │  Pod N │
│uvicorn │ │uvicorn │ │uvicorn │
│workers │ │workers │ │workers │
└───┬────┘ └───┬────┘ └───┬────┘
    │          │          │
    └──────────┼──────────┘
               │
        ┌──────▼──────┐
        │   Redis     │
        │  Cluster    │
        └─────────────┘
```

### Container (Planned)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm
COPY app/ app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `NEUROSYNC_EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `NEUROSYNC_SPACY_MODEL_NAME` | `en_core_web_sm` | spaCy model |
| `NEUROSYNC_STATE_BACKEND` | `memory` | `memory` / `redis` |
| `NEUROSYNC_REDIS_URL` | `None` | Redis connection string |
| `NEUROSYNC_LLM_PROVIDER` | `None` | `gemini` / `openai` / `None` |
| `NEUROSYNC_LLM_API_KEY` | `None` | LLM API key (never in code) |
| `NEUROSYNC_FEEDBACK_ENABLED` | `True` | Enable feedback collection |

---

## 10. Monitoring & Observability

### Logging

- **Format**: Structured (JSON-ready) with timestamp, level, service, request_id
- **Levels**: ERROR (failures), WARNING (degradation), INFO (requests, timings)
- **Rule**: Resume/JD text NEVER logged — only analysis_id, scores, and timing

### Metrics (Planned)

| Metric | Type | Purpose |
| --- | --- | --- |
| `analysis_duration_ms` | Histogram | Track processing time distribution |
| `component_timing_ms` | Histogram | Per-component latency |
| `extraction_degraded_total` | Counter | How often extraction degrades |
| `semantic_fallback_total` | Counter | How often TF-IDF fallback activates |
| `feedback_count` | Counter | Total feedbacks received |
| `active_taxonomy_skills` | Gauge | Taxonomy size (static + runtime) |

### Health Check

`GET /api/v1/health` returns component-level status:

```json
{
  "status": "healthy",
  "taxonomy_loaded": true,
  "taxonomy_skill_count": 294,
  "embedding_model_loaded": true,
  "spacy_model_loaded": true,
  "embedding_store_ready": true,
  "feedback_count": 0,
  "versions": { "engine": "1.0.0", "taxonomy": "1.0.0" }
}
```

---

*This document defines HOW NeuroSync is built. All implementation decisions trace back to this TRD.*
