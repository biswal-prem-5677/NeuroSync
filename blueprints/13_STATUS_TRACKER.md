# NeuroSync — Completion Status Tracker

**Version**: 1.0.0
**Date**: 2026-07-27
**Status**: ACTIVE — update this file as work lands
**Scope**: Verified state of the codebase measured strictly against blueprints 01–12.

> This is the single source of truth for **what is actually built**, as opposed to what the
> blueprints *say* is built. Every claim below was verified by reading the code and by running
> the pipeline in-process — no status was copied from another document.

---

## 0. How This Was Verified

| Check | Method | Result |
| --- | --- | --- |
| Code inventory | File walk of `core/backend/app/` (excluding `venv/`) | 21 Python files, ~4,160 lines + 3,842-line taxonomy JSON |
| Dependency state | `venv/Lib/site-packages` listing | fastapi 0.136.1, pydantic 2.13.3, torch 2.11.0, spacy 3.8.14, sentence-transformers 5.4.1, scikit-learn 1.8.0, redis 8.0.0, numpy 2.4.4 |
| Models | Cache inspection | `en_core_web_sm` 3.8.0 installed; `all-MiniLM-L6-v2` present in HF cache |
| App boot | `python -c "from app.main import app"` | Imports clean in 0.7s; 3 v1 routes registered |
| Live pipeline | FastAPI `TestClient` — health → analyze → feedback | All HTTP 200; full response captured (see §4) |
| Taxonomy | JSON parse | version 2.0.0, **294 skills**, **9 categories** |

| Persistence | `tools/state_probe.py` — analyze in one process, restart, read in another | `sql` keeps 1/1 feedback rows and finds the prior analysis; `memory` keeps 0/1 |

**Re-verify command** (from `core/backend/`):

```bash
./venv/Scripts/python.exe -c "
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    print(c.get('/api/v1/health').json())
"
```

---

## 1. Phase Completion — Real vs Documented

| Phase | Doc 07 claims | **Verified reality** | Delta |
| --- | --- | --- | --- |
| **0** Foundation & Scaffolding | ✅ 100% | ✅ **100%** | None — accurate |
| **1** Bug Fixes & Cleanup | ✅ 100% | 🟡 **Partial** | 3 bug fixes real; but 7 services that doc 12 §10 scopes to Phase 1 do not exist (§3) |
| **2** Validate & Harden | ⬜ 0% | 🟡 **~40%** | 2.1 done, 2.2 half-done; doc 07 is stale |
| **3** Intelligence Expansion | ⬜ 0% | ⬜ **0%** | Accurate |
| **3.5** Human State Intelligence | ⬜ 0% | ⬜ **0%** | Accurate |
| **4** Market & Trajectory | ⬜ 0% | ⬜ **0%** | Accurate |
| **5** Frontend | ⬜ 0% | ⬜ **0%** | Accurate — `core/frontend/` does not exist |
| **6** Scale & Production | ⬜ 0% | ⬜ **0%** | Accurate — no `tests/`, no Dockerfile, no CI |

```text
Phase 0: ████████████████████ 100%  ✅ Foundation (21 files, ~4,160 lines)
Phase 1: ██████████████░░░░░░  70%  🟡 Bugs fixed; MVP-scope services still missing
Phase 2: ████████░░░░░░░░░░░░  40%  🟡 Deps + startup done; validation quality FAILED
Phase 3: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜
Phase 3.5:░░░░░░░░░░░░░░░░░░░░  0%  ⬜
Phase 4: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜
Phase 5: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜
Phase 6: ░░░░░░░░░░░░░░░░░░░░   0%  ⬜
```

---

## 2. What Is DONE — Verified

### 2.1 Built and working

| Blueprint | Item | Evidence |
| --- | --- | --- |
| 12 §2 L1 | `api/deps.py` — lazy singletons, analysis cache | Warms 5 singletons in lifespan; feedback lookup returned `decision_found: true` |
| 12 §2 L1 | `main.py` — app factory, CORS, request-ID middleware, global error handler | `X-Request-ID` + `X-Response-Time-Ms` emitted per request |
| 12 §2 L1 | `config.py` — Pydantic Settings, env-driven | 84 lines, `ScoringWeights` + `VersionConfig` nested |
| 12 §2 L2 | `utils/text_processor.py` — cleaning, sections, chunking | 184 lines |
| 12 §2 L3 | `services/skill_extractor.py` — 4-layer hybrid | 734 lines; live run: 42 resume skills / 25 JD skills, methods `taxonomy, ner, embedding_discovery` |
| 12 §2 L3 | `services/semantic_engine.py` — 3-layer similarity | 488 lines; live: `overall 0.4166 / chunk_max 0.6165 / chunk_mean 0.5320 / skill_alignment 0.2794`, `degraded: false` |
| 12 §2 L3 | `services/skill_gap_analyzer.py` — cluster gap reasoning | 567 lines; live: 17 gaps in 1.1ms, contextual (non-template) reasoning confirmed |
| 12 §2 L3 | `utils/skill_taxonomy.py` + `data/skill_taxonomy.json` | 294 skills / 9 categories, alias + relationship lookup, runtime registration |
| 12 §2 L3 | `utils/embedding_store.py` | 294 skills indexed in 996ms at startup |
| 12 §2 L4 | `services/intelligence_engine.py` — scoring, fit, shortlist prob, what-if, feedback store | 794 lines; live: 5-step improvement path + 3 simulations with score deltas |
| 08 §2 | `POST /api/v1/analyze` | HTTP 200, all 12 contract sections present |
| 08 §3 | `POST /api/v1/feedback` | HTTP 200, `feedback_stats` with `recalibrate_at: 50` |
| 08 §4 | `GET /api/v1/health` | HTTP 200, component-level report |
| 07 P1 | 3 critical bug fixes (DI arg order, `initialize()` call, feedback stub) | All three confirmed fixed in code and at runtime |
| 07 P1 | 12 dead files deleted | Confirmed absent |
| 07 P2.1 | Deps + spaCy model + startup test | Confirmed (see §0) |
| 12 §2 State | `state/base.py` + `state/memory_state.py` + `state/sql_state.py` | Built 2026-08-01. `tools/state_probe.py`: sql retains 1/1 feedback rows and the prior analysis across a real process restart; memory retains 0/1 |
| 09 §4 | `alembic/` + revision `0001_core_tables` — `users`, `analyses`, `feedback` | `alembic upgrade head` applied cleanly; PostgreSQL DDL verified by offline render (see D6) |
| 12 §2 State | `db/models.py` + `db/session.py` — SQLAlchemy 2.0 ORM | JSONB on PostgreSQL, JSON on SQLite; one migration serves both |

### 2.2 Present but undocumented in any blueprint

| File | Note |
| --- | --- |
| `core/backend/test_pipeline.py` | Ad-hoc HTTP smoke script (108 lines) at backend root — belongs in `tests/` per doc 07 §6.1 |
| `core/backend/expand_taxonomy.py` | Taxonomy generation script (254 lines) — not in doc 12 §10 file map |
| `core/backend/app/agents/` | Empty package (0-byte `__init__.py`) — no owner in doc 12 §2 |

---

## 3. Blueprint Contradictions (must be settled before building)

### 3.1 Doc 07 vs Doc 12 — 7 missing services

Doc 12 §10 marks these **Phase 1 / "Build"**, and §11 states *"What is built in Phase 1? Everything except:
decision_engine, trajectory, market, redis, file_parser, human_state"*. Doc 07 places them in **Phase 3**.
**None exist on disk:**

| File | Doc 12 §10 | Doc 07 | On disk |
| --- | --- | --- | --- |
| `services/reasoning_engine.py` | Phase 1 Build | Phase 3.1 | ❌ |
| `services/insights_engine.py` | Phase 1 Build | Phase 3.2 | ❌ |
| `services/feedback_processor.py` | Phase 1 Build | Phase 3.3 | ❌ |
| `services/adaptive_scorer.py` | Phase 1 Build | Phase 4.3 | ❌ |
| `services/llm_enhancer.py` | Phase 1 Build (graceful null) | Phase 4.4 | ❌ |
| `state/base.py` | Phase 1 Build | Phase 3.4 | ❌ |
| `state/memory_state.py` | Phase 1 Build | Phase 3.4 | ❌ |

Therefore doc 07's *"Phase 1 ✅ COMPLETE"* is false against the constitutional document.

### 3.2 Architecture law violations

| Rule (doc 12 §4) | Violation |
| --- | --- |
| **Rule 1** — IntelligenceEngine is the ONLY orchestrator | `api/v1/endpoints/analyze.py:40-81` calls extractor → cross-doc → semantic engine → gap analyzer → intelligence engine directly |
| **Rule 3** — API endpoints are THIN | `analyze.py` is 206 lines of pipeline orchestration + manual response assembly |
| **Rule 5** — StateBackend is the ONLY persistence | ✅ **RESOLVED 2026-08-01** — was: feedback + analysis cache in module-level dicts (`deps.py:27`, inside `intelligence_engine.py`). Both are gone; `app/state/` is the only persistence. See D6 |

### 3.3 Factual errors inside the docs

| Doc | Claim | Reality |
| --- | --- | --- |
| 07 line 61 | "SkillCategory (15)" | `models/enums.py` defines **9** categories; taxonomy JSON uses 9 |
| 07 line 62 | "MatchMethod (5)" | **4** members |
| 07 §Phase 0 | "19 files, ~4,059 lines" | 21 files, ~4,160 lines (close, but the file map omits `agents/`, `data/`) |
| 07 header | Phase 2 = "NEXT / 0%" | Phase 2.1 fully done, 2.2 partially done |

---

## 4. Defects Found in the Live Run

**Test input**: senior full-stack resume (Python, FastAPI, Docker, Kubernetes, AWS, Kafka, Redis,
PostgreSQL, CI/CD, microservices, ML) vs *Senior Backend Engineer — Cloud Infrastructure* JD.

**Result**: `overall_score 20.85` · `recommendation: do_not_apply` · `fit_level: no_fit` ·
`shortlist_probability: 0.0` — an inverted answer for a near-ideal candidate.

### D1 — Scoring miscalibration (BLOCKER, severity: critical) — ✅ **RESOLVED 2026-07-31**

| Symptom | Root cause | Blueprint reference | Status |
| --- | --- | --- | --- |
| Only **8 of 25** JD skills matched (`overlap_score 0.32`) | JD alternative groups not parsed — *"Python, Go, or Java"* and *"AWS, GCP, or Azure"* each yield 2 phantom gaps | 02 §3 (extraction), 02 §5 (gap priority) | ✅ `RequirementParser` |
| `SQL` reported missing while PostgreSQL is present | No parent/child skill resolution | 02 §5, taxonomy `relationships` | ✅ `CoverageResolver` |
| `Cloud Computing` missing while AWS is present | Same — no hierarchy rollup | 02 §5 | ✅ |
| `DevOps` missing while CI/CD + GitHub Actions present | Same | 02 §5 | ✅ |
| 17 gaps → gap penalty dominates the composite score | Penalty tuned against inflated gap counts | 02 §8, 03 §7 | ✅ recalibrated |

**Before / after** — identical input (senior full-stack resume vs *Senior Backend Engineer — Cloud Infrastructure*):

| Measure | Before (2026-07-27) | After (2026-07-31) |
| --- | --- | --- |
| `overall_score` | 20.85 | **77.23** |
| `fit_level` | `no_fit` | **`good_fit`** |
| `recommendation` | `do_not_apply` | **`apply`** |
| `shortlist_probability` | 0.0 | **0.745** |
| Gaps reported | 17 | **5** |
| Requirements met | 8 / 25 raw skills | **12 / 17 groups** (4 via implied) |
| `skill_overlap` | 0.32 | 0.684 |
| Warm `/analyze` latency | 546ms (extraction only) | 261ms end-to-end |

**Negative controls** (same resume, roles it does not fit) — proves the change is a calibration, not an inflation:

| JD | Score | Fit | Recommendation |
| --- | --- | --- | --- |
| Frontend Engineer — Design Systems (adjacent) | 35.82 | `weak_fit` | `do_not_apply` |
| Head Pastry Chef (unrelated) | 0.0 | `no_fit` | `do_not_apply` |

**What was built**

| File | Role |
| --- | --- |
| `services/requirement_resolver.py` (new) | `RequirementParser` — JD → requirement *groups*, so "Python, Go, or Java" is one ask, not three; `CoverageResolver` — accepts a subsuming skill as evidence |
| `data/skill_implications.json` (new) | Directed subsumption graph — 150 skills → 247 transitively-closed edges. Kept separate from `related` (symmetric) because `implies` is directed |
| `utils/skill_taxonomy.py` | Loads implications with a cycle-safe transitive closure; separator-insensitive lookup |
| `models/domain.py` | `RequirementGroup` / `RequirementSet` / `RequirementCoverage` / `CoverageResult`; gaps gained `alternatives`, `optional` |
| `services/skill_gap_analyzer.py` | Unit of analysis is now the requirement group, not the JD skill |
| `services/intelligence_engine.py` | Scores off resolved coverage; gap penalty normalized against *total* requirement importance; what-if re-resolves coverage instead of decrementing counters |

**Two calibration defects found while fixing D1** (both were capping every achievable score):

1. *Proficiency scaled credit from zero.* A resume covering **every** requirement at the default inferred proficiency (0.5) scored 0.50 — indistinguishable from covering half the role perfectly. Blueprint 02 §11 says "Proficiency > Presence", not that presence is worthless. Presence now earns `coverage_presence_floor` (0.70) of the credit; proficiency modulates the remaining 30%.
2. *Raw cosine consumed as a percentage.* The semantic composite is compressed by construction (02 §4 blends three sub-cosines; `skill_alignment` compares against a synthetic phrase and rarely clears 0.35), so it cannot approach 1.0 however well a resume matches. Measured band:

   | Pair | Composite |
   | --- | --- |
   | resume vs itself (unreachable ceiling) | 0.666 |
   | resume vs well-matched backend JD | 0.418 |
   | resume vs adjacent frontend JD | 0.294 |
   | resume vs unrelated pastry-chef JD | 0.138 |

   `semantic_floor` = 0.15 and `semantic_ceiling` = 0.45 map this band onto 0–1. The raw cosine is still what `/analyze` reports; only the scoring input is calibrated. **Config weights were left at the blueprint's Day-1 values** ({semantic 0.40, skill 0.35, gap 0.25}) — the fix is in the signals, not the weights.

Re-verify: `./venv/Scripts/python.exe verify_d1.py` from `core/backend/`.

### D2 — Extraction noise polluting the taxonomy (severity: high) — ✅ **RESOLVED 2026-07-31**

Before: the NER and embedding-discovery layers had no noise filter, and every false positive was
written permanently into the in-memory taxonomy, where it stayed for the life of the process and
leaked into every later analysis. Violates doc 02 §3 "Key Design Decisions".

**Before / after** — same two documents (`tools/pipeline_probe.py` resume + JD), measured with
`tools/noise_probe.py`. The "before" column is a real run with `SkillNoiseFilter.judge` neutralised,
not the original audit's notes:

| Measure | Before | After |
| --- | --- | --- |
| Noisy skills emitted across both docs | 9 | **0** |
| Taxonomy writes attempted | 9 (1 promoted, 8 quarantined) | **0** |
| Resume skills extracted | 39 (34 real + 5 noise) | **34** |
| JD skills extracted | 27 (24 real + 3 noise) | **24** |

Noise present before, all gone after: `Mentored` (`soft_skill`, 0.82) · `Designed Postgresql`
(`database`, 0.77) · `Computer Science` (filed under `ml_ai` from a 0.68 cosine) · `Implemented Ci` ·
`Strong Sql` · `Ci` · plus three chunk artefacts that spanned a newline
(`"Skills\nPython"`, `"Cloud Infrastructure\n\nWe"`, `"Agile\n\nEducation\nB.Tech"`).

**What was built**

| File | Role |
| --- | --- |
| `services/skill_noise_filter.py` (new) | `SkillNoiseFilter` — seven ordered rules, each rejection carrying a reason. Deterministic: no LLM, no network, no inference |
| `utils/skill_taxonomy.py` | Discovery is now *quarantined*: `register_runtime_skill` holds a term as provisional until it recurs in `discovery_promotion_sightings` (2) distinct documents. Per-document noise expires; real skills accumulate |
| `services/skill_extractor.py` | Owns no noise policy any more — the inline blacklist moved into the filter. Both discovery layers (2 and 4) call `judge()` |
| `config.py` | `discovery_min_confidence` 0.70, `alias_absorption_threshold` 0.88, `discovery_category_confidence` 0.80, `discovery_promotion_sightings` 2 — every gate tunable, `1` restores pre-D2 behaviour |
| `tools/noise_probe.py` (new) | The before/after measurement above |

Blueprint 02 §3 asks for a blacklist of "common English words that survive NER". A word list alone
could not hold: the observed failures are *structural* — an inflected verb (`Mentored`), a phrase
wrapping a known skill (`Designed Postgresql`), an academic field, an employer name. So the filter
classifies by structure and keeps the word lists only for the residue.

Two rules earned their keep beyond the original defect list:

1. *Category inheritance was unconditional.* A discovery adopted its nearest neighbour's category
   whatever the distance — which is how `Computer Science` was filed under `ml_ai` from a 0.68
   cosine, close enough to notice and nowhere near close enough to classify. Below
   `discovery_category_confidence` the honest answer is `OTHER`.
2. *Compound fragments corroborate themselves.* A bare-acronym scan splits `CI/CD` and offers `Ci`,
   which then recurs in every document that mentions CI/CD — so quarantine alone would have promoted
   it, and did (it was the one term to survive into the taxonomy on the first filtered run). A term
   is rejected as a fragment when every occurrence in the document is glued to more text by a
   skill-internal separator. A separator only counts as glue when word characters continue past it:
   `.` joins in `Vue.js` but ends a sentence in "deployed with Terraform.", and treating those alike
   condemned every skill unlucky enough to land before a full stop.

Precision check — 24 terms judged against a document containing all of them, 0 misclassified.
`Python`, `scikit-learn`, `Vue.js`, `React Native`, `Terraform`, `Kubernetes`, `Rust`, `Go`, `Kafka`,
`Pulumi`, `GitHub Actions`, `Redis` all accepted; `Ci`, `Cd`, `Scikit`, `Vue`, `Mentored`,
`Designed PostgreSQL`, `Computer Science`, `TechCorp Inc`, `B.Tech Computer Science`, `Team`,
`Experience`, `Strong Ability` all rejected, each with its reason.

No D1 regression: `overall_score` 77.23, `good_fit`, `apply`, 5 gaps — unchanged. Negative controls
still hold (frontend 38.61 `weak_fit`, pastry chef 0.0 `no_fit`).

Re-verify: `./venv/Scripts/python.exe -m tools.noise_probe` from `core/backend/`.

### D3 — Gap cluster mislabeling (severity: medium) — ✅ **RESOLVED 2026-07-31**

Before: *"strong coverage in **Programming Languages** (Docker, Kubernetes, Microservices)"* — every
related skill was cited as coverage of the cluster regardless of which cluster it belonged to.

After: `skill_gap_analyzer._generate_reasoning()` partitions `related_present` into skills that
actually resolve to the cluster being discussed versus merely *adjacent* ones, and words them
differently. Live output:

> *"You have adjacent experience in **AWS**, which shortens the path to Terraform, but nothing in
> your resume covers **DevOps & Infrastructure** itself."*
>
> *"Your existing **Kubernetes** knowledge creates a foundation, but without Prometheus, your
> **Container & Orchestration** capability has a significant gap."*

### D4 — Latency exceeds both budgets (severity: high)

| Measurement | Target | Source |
| --- | --- | --- |
| `/analyze` total **9,413ms** | < 2,000ms P95 | 11 §1 |
| — of which extraction **6,221ms** cold / 546ms warm | < 200ms (500ms timeout) | 03 §7 |
| — semantic ≈ 2,600ms | < 150ms (300ms timeout) | 03 §7 |
| — gap analysis 1.1ms | < 50ms | 03 §7 ✅ |
| `/health` 28ms | < 100ms | 11 §1 ✅ |
| `/feedback` 3.6ms | < 200ms | 11 §1 ✅ |

Primary cause of the cold spike: spaCy is lazy-loaded on **first request**, not in `lifespan`
(doc 12 §7 "Startup Sequence" requires warm-up).

### D6 — State was volatile; every recorded outcome died on restart (BLOCKER, severity: critical) — ✅ **RESOLVED 2026-08-01**

Not from the live run — raised by the engineering review as **doc 15 R3** and pulled into M1 by
doc 14 §2.3. Feedback accumulated in `IntelligenceEngine._feedback_log` (a list on the instance)
and analyses in `deps.py::_analysis_cache` (a module-level dict). Both are process-local, so the
product's central claim — that it learns from outcomes — was false: the data was discarded on
every deploy, crash and restart, and nothing in the API said so.

**Before / after** — same script, both columns produced by running it
(`tools/state_probe.py`). The "before" is the `memory` backend, which is the pre-change
behaviour preserved deliberately as the dev/test implementation, not a quotation from an
earlier note. Each row: one process records an analysis and one feedback outcome, the process
**exits**, a second process boots and reads before writing anything.

| Measure | Before (`memory`) | After (`sql`) |
| --- | --- | --- |
| Feedback rows written before restart | 1 | 1 |
| Feedback rows visible after restart | **0** | **1** |
| Prior analysis found (`decision_found`) | **false** | **true** |
| `/health` reports `state.durable` | false | true |
| Analysis score, both processes | 77.23 | 77.23 |

**What was built**

| File | Role |
| --- | --- |
| `app/state/base.py` (new) | `StateBackend` ABC + the persistence records (`AnalysisRecord`, `FeedbackRecord`, `FeedbackStats`). Doc 12 §4 Rule 5 becomes a reviewable boundary instead of a convention |
| `app/state/memory_state.py` (new) | The old volatile behaviour, now **named** and logging a warning at startup that data will be lost |
| `app/state/sql_state.py` (new) | SQLAlchemy 2.0 implementation. PostgreSQL in production, SQLite locally |
| `app/db/models.py`, `app/db/session.py` (new) | ORM for blueprint 09's `users` / `analyses` / `feedback`; engine settings per dialect. Importable only by `sql_state.py` |
| `alembic/` + `alembic.ini` (new) | Blueprint 09 §4. Revision `0001_core_tables`. URL from `NEUROSYNC_DATABASE_URL`, never from the ini file |
| `api/deps.py` | `_analysis_cache` and `cache_analysis()` **deleted**; `get_state_backend()` added. `sql` without a database URL raises rather than silently falling back to volatile storage |
| `services/intelligence_engine.py` | `_feedback_log` **deleted**. The engine now owns no storage; `record_feedback()` writes through `StateBackend` and takes the `analysis_id` it belongs to |
| `api/v1/endpoints/feedback.py` | Rebuilds the real `Decision` from the stored analysis instead of a zero-valued stub. Doc 08 §3.2's `decision_found: false` path is kept for genuinely unknown ids |
| `api/v1/endpoints/health.py` | Reports `state` (backend, durability, row counts) and degrades overall status when the database is unreachable |
| `tools/state_probe.py` (new) | The measurement above. Each phase is a separate OS process, so nothing survives in module globals — which is exactly how the old design passed single-process tests |

Three tables were built, not doc 09's ten or doc 15 §4's four. `career_profiles` and
`analysis_history` are dropped (the `analyses` JSONB payload covers them), the four Human-State
tables were removed permanently by doc 14 §2.2, and `skill_taxonomy_overrides` is **deferred to
the backlog with a reason**: persisting promoted discoveries would make a promotion permanent,
while D2's quarantine is calibrated against a per-process lifetime. Full rationale and every
schema deviation from doc 09: **doc 10 D-007**.

**What is NOT verified.** The PostgreSQL path has never touched a live PostgreSQL server —
there is none in the development environment, and no Windows wheel exists for an embeddable
one. What *was* verified is the generated DDL, rendered offline for the PostgreSQL dialect:

```bash
NEUROSYNC_DATABASE_URL=postgresql+psycopg://user:pass@host/neurosync \
    ./venv/Scripts/python.exe -m alembic upgrade head --sql
```

emits valid PostgreSQL — `payload JSONB NOT NULL`, `TIMESTAMP WITH TIME ZONE DEFAULT now()`,
both foreign keys with their `ON DELETE` actions, and all six indexes. The end-to-end path
(migration → ORM → endpoints → restart) is verified on SQLite. **First deployment must run
`alembic upgrade head` against a real instance before this is called proven**; until then, treat
"works on PostgreSQL" as strongly indicated, not measured.

Re-verify: `./venv/Scripts/python.exe -m tools.state_probe` from `core/backend/`.

No regression: `verify_d1.py` exit 0 (`overall_score` 77.23, 5 gaps, negative controls 38.61
`weak_fit` / 0.0 `no_fit`) and `tools.noise_probe` exit 0 (0 noise terms, 0 taxonomy writes),
both re-run after the change.

### D5 — API contract drift (severity: medium)

| Doc 08 says | Code emits | Location |
| --- | --- | --- |
| `simulations[].new_shortlist_prob` | `new_shortlist_probability` | `analyze.py:161` |
| `simulations[].roi_rank` | *(absent)* | `analyze.py:154-164` |
| health → `feedback.avg_score`, `feedback.recalibrate_at` | absent from `/health` (present only in `/feedback`) | `intelligence_engine.get_feedback_stats()` |
| health → `ner_available: true` | `false` at startup (spaCy not warmed) | `health.py` |
| `analysis_id` length 12 | `"92bb1053-76d"` — truncated UUID keeps its hyphen | `analyze.py:33` |
| Response models typed (doc 07 §2.4) | Hand-built `dict` | `analyze.py:89-197` |

---

## 5. Not Built At All

| Blueprint | Surface | Status |
| --- | --- | --- |
| 09 (all) | Database — core tables, migrations, ORM | 🟡 **3 of 3 in-scope tables built** 2026-08-01 (`users`, `analyses`, `feedback`) + Alembic + SQLAlchemy ORM. `skill_taxonomy` deferred; `career_profiles` / `analysis_history` / the 4 Human-State tables cancelled (doc 09 §0) |
| 06 (all) | Frontend — design system, 4 pages, simulation playground | ❌ `core/frontend/` does not exist |
| 12 §2 L3.5 | Human State: `human_state_engine`, `agent_decision_engine`, `gamification_engine`, `models/career_state.py`, `models/observation.py`, `endpoints/behavior.py` | ❌ |
| 08 §5 | 5 behavior endpoints | ❌ |
| 12 §2 L5–L7 | `reasoning_engine`, `insights_engine`, `feedback_processor`, `adaptive_scorer`, `llm_enhancer`, `market_intelligence_engine`, `career_trajectory_engine`, `decision_engine` | ❌ |
| 12 §2 State | `state/base.py`, `state/memory_state.py`, `state/sql_state.py` | ✅ 2026-08-01. `redis_state.py` removed from the architecture (doc 10 D-007) |
| 12 §2 L2 | `utils/file_parser.py` + `/analyze-file` | ❌ |
| 03 §5 / 11 §3 | JWT auth, tenant isolation, rate limiting, upload magic-byte checks | ❌ |
| 03 §9 / 07 §6.3 | Dockerfile, docker-compose, CI/CD, env configs | ❌ |
| 07 §6.1 | Test suite (6 test modules) | ❌ no `tests/` directory |
| 11 §5 | Structured JSON logs, Prometheus metrics | ❌ plain-text logging only |

---

## 6. Execution Order (ACTIVE)

> **Sequencing is owned by [14_EXECUTION_RULES.md](14_EXECUTION_RULES.md) §2.** Steps 1–5 below are
> milestone **M1 — Trustworthy Core**; step 6 belongs to **M3**. The frontend and file upload move
> ahead of the intelligence layers, because v1.0 ships at the end of **M2 — Usable Product**.

Rationale: **correctness before expansion.** Building reasoning and insights layers on a scorer that
answers `do_not_apply` to a 90% match only makes the wrong answer more articulate.

| # | Step | Blueprint | Status |
| --- | --- | --- | --- |
| **0** | Reconcile doc 07 ↔ doc 12; correct factual errors; log the decision | 07, 10, 12 | ⬜ |
| **1** | Fix D1 — JD alternative-group parsing, parent/child skill resolution, gap-penalty recalibration | 02 §3, §5, §8 | ✅ 2026-07-31 |
| **1b** | Fix D2 — noise filter for NER + embedding discovery; stop polluting the taxonomy | 02 §3 | ✅ 2026-07-31 |
| **1c** | Fix D3 — correct gap cluster labels | 02 §5 | ✅ 2026-07-31 |
| **1d** | Fix D6 — `state/` + StateBackend + Postgres/Alembic; closes doc 15 R3 and doc 12 Rule 5 | 12 §2, 09 §4 | ✅ 2026-08-01 |
| **1e** | `analyze.py` thin — doc 12 Rules 1 and 3 | 12 §4, §3.2 | ⬜ **next** |
| **2** | Phase 2.3 `utils/file_parser.py` + `POST /analyze-file` | 07 §2.3, 12 §2 L2 | ⬜ |
| **3** | Phase 2.4 `api/responses.py` typed models — closes D5 | 07 §2.4, 08 | ⬜ |
| **4** | Fix D4 — warm spaCy in `lifespan`, fix `/health`, re-measure against NFR | 11 §1, 12 §7 | ⬜ |
| **5** | Phase 2.5 edge-case hardening (empty, non-English, binary, 50K chars) | 07 §2.5 | ⬜ |
| **6** | Phase 3 in doc-12 layer order: `state/` → `reasoning_engine` → `insights_engine` → `feedback_processor` → `adaptive_scorer`, refactoring `analyze.py` thin (fixes Rules 1/3/5) | 12 §4, 07 §3 | ⬜ |

Phases 3.5, 4, 5, 6 remain as documented in doc 07 and are unchanged by this tracker.

---

## 7. Change Log

| Date | Change |
| --- | --- |
| 2026-07-27 | Initial tracker created from full codebase audit + live pipeline run |
| 2026-07-31 | D1 resolved — requirement groups + coverage resolution; score 20.85 → 77.23 |
| 2026-07-31 | D3 resolved — gap reasoning distinguishes in-cluster coverage from adjacent skills |
| 2026-07-31 | D2 resolved — `SkillNoiseFilter` + discovery quarantine; 9 noise terms → 0, no D1 regression |
| 2026-08-01 | D6 resolved — `StateBackend` + PostgreSQL/Alembic; feedback surviving a restart 0/1 → 1/1. Doc 12 Rule 5 satisfied. Docs 09 and 12 amended (doc 10 D-007) |

---

*Update the status columns in §1 and §6 as each item lands. When a defect in §4 is fixed, record the
before/after measurement rather than deleting the entry.*
