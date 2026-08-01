# NeuroSync — Independent Engineering Review Board

**Version**: 1.0.0
**Date**: 2026-08-01
**Reviewers**: Engineering Review Board (CTO · Staff/Principal Eng · SRE · DevOps · DBA · Security · QA · PM · UX · FinOps · Legal)
**Subject**: Is NeuroSync buildable, launchable, maintainable, scalable, and commercially viable?
**Verdict**: 🟡 **Build After Simplifying** (Overall Reality Score **46/100**)

> **How to read this.** Every claim is tagged **FACT** (verified in the repo this session),
> **ASSUMPTION** (stated so you can challenge it), or **RECOMMENDATION**. Nothing is inferred
> from missing information — §23 lists exactly what is missing and what it blocks.

---

## 0. Evidence base

| Measurement | Value | Method |
| --- | --- | --- |
| Backend code | **6,451 lines** Python | `find core -name '*.py'`, venv excluded |
| Blueprint documentation | **8,957 lines** across 15 docs | `wc -l blueprints/` |
| Docs-to-code ratio | **1.39 : 1** | derived |
| Largest single document | `vision/AGENTIC_EVOLUTION_ROADMAP.md`, **1,680 lines** | larger than any implemented subsystem |
| Database tables built | **0 of 10** specified | doc 13 §5 |
| Frontend files | **0** | `core/frontend/` does not exist |
| Automated tests | **0** | no `tests/` directory |
| Auth / rate limiting / tenancy | **0** | doc 13 §5 |
| Dockerfile / CI pipeline | **0** | doc 13 §5 |
| Working endpoints | **3** (`/analyze`, `/feedback`, `/health`) | live run |
| Warm `/analyze` latency | **512 ms** end-to-end | `verify_d1.py`, this session |
| Cold `/analyze` latency | **~2,550 ms** | live TestClient run |
| Skill taxonomy | 294 skills, hand-maintained JSON | `skill_taxonomy.json` |
| Business model artefacts | **0 documents**; one competitor-table cell reading "Free core, Premium features" | grep across blueprints |

**FACT**: the engine works and its correctness has been measured. **FACT**: everything required to
put it in front of a paying user — persistence, auth, UI, tests, deployment — does not exist.

---

## 1. Product feasibility

### Problem severity — **Real, but episodic**

**FACT** (PRD §2): the stated problem is that job seekers apply blindly and get no signal back.
That problem is real and widely felt.

**ASSUMPTION we challenge**: that this pain is *chronic*. It is **acute and short-lived**. A user
is in acute pain for the 4–12 weeks of a job search, then the pain disappears entirely —
by success. This single characteristic drives most of the commercial findings below.

### Existing alternatives

| Alternative | Price | Why users tolerate it |
| --- | --- | --- |
| Jobscan | ~$49/mo | ATS keyword match; the incumbent habit |
| Resumeworded | ~$29/mo | Cheap, instant, good enough for a score |
| Teal / Huntr | Free–$9/mo | Tracker-first; analysis is a bonus |
| **ChatGPT / Claude** | $0–20/mo | **Paste both documents, ask "what's missing?"** |
| LinkedIn Premium | ~$30/mo | Bundled with a network people already use |

**The competitive analysis in PRD §9 omits general-purpose LLMs.** That is the most serious
omission in the document. A user pasting a resume and a JD into a chatbot they already pay for
gets a fluent, personalised gap analysis in 10 seconds, for a marginal cost of zero. NeuroSync
must be better than *that*, not better than Jobscan.

### Competitive advantage — narrower than claimed, but real

**FACT**: the requirement-group parser and the skill-implication graph (`requirement_resolver.py`,
`skill_implications.json`) are genuine engineering. Recognising that *"Python, Go, or Java"* is one
requirement rather than three, and that PostgreSQL evidences SQL, is something keyword tools get
wrong and LLMs get **inconsistently** right.

**That inconsistency is the moat, and it is a narrow one**: NeuroSync is *deterministic*. The same
resume and JD always produce the same score. An LLM does not. For any use where the answer must be
defensible or comparable across candidates — a placement cell ranking 300 students, a coach
tracking a client over months — determinism matters. For a single anxious student asking "what am I
missing?", it does not.

### Willingness to adopt — **High.** Willingness to pay — **Low.**

**ASSUMPTION (high confidence)**: job seekers are among the worst-monetising consumer segments —
low disposable income (PRD Persona 1 is an unemployed student), extreme urgency, and **churn by
design**: the product succeeds and the user leaves. LTV is structurally capped at a few months.

**FACT**: PRD §4's three personas are two students/switchers (low ability to pay) and one recruiter
(high ability to pay, entirely different product surface).

### Product-market fit likelihood

| Segment | PMF likelihood | Reasoning |
| --- | --- | --- |
| Individual job seekers (B2C) | **Low–Medium** | Real pain, no budget, structural churn, LLM substitution |
| University placement cells | **Medium–High** | Budget exists, 300 students/yr, determinism and comparability matter, annual contract |
| Bootcamps / career coaches | **Medium–High** | Sells outcomes, needs defensible evidence, low volume high value |
| Recruiters (B2B) | **Medium** | Real budget, but competing with entrenched ATS and needing compliance work |

**RECOMMENDATION**: keep building the B2C product — it is the cheapest way to validate the engine
and generate the feedback data — but **the business case should be tested against placement cells
and coaches first**. They are the only listed persona with both a budget and a reason to need
determinism. This is a product decision and is flagged for the owner in §23.

### Ratings

| Dimension | Score | Justification |
| --- | --- | --- |
| **Technical Feasibility** | **8 / 10** | Core pipeline already runs and is measured. No unsolved research. −2 for calibration validated at n=1 (§21). |
| **Commercial Feasibility** | **3 / 10** | No business model exists in the repo. Worst-paying segment, structural churn, free LLM substitute, crowded field. |
| **User Value** | **7 / 10** | "Learn Terraform first, +3.7 points, then apply" is real, actionable value that competitors do not deliver. Capped by episodic need. |

---

## 2. Feature review

Scope: every feature named in PRD §5, doc 07, and `vision/`.

| # | Feature | Feasible | Complexity | Maint. | Business value | Ship in | Rating |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4-layer skill extraction | ✅ built | High | **High** | Core | V1 | ✅ Ready |
| 2 | Semantic similarity (3-layer) | ✅ built | Med | Low | Core | V1 | ✅ Ready |
| 3 | Requirement groups + implication graph | ✅ built | Med | Med | **Differentiator** | V1 | ✅ Ready |
| 4 | Cluster gap reasoning | ✅ built | Med | Low | Core | V1 | ✅ Ready |
| 5 | What-if simulation | ✅ built | Low | Low | **Differentiator** | V1 | ✅ Ready |
| 6 | ROI-ranked improvement path | ✅ built | Low | Low | **Differentiator** | V1 | ✅ Ready |
| 7 | File upload (PDF/DOCX) | Easy | Low | Low | **Adoption blocker** | V1 | ✅ Ready |
| 8 | Typed API responses | Easy | Low | Low | Correctness | V1 | ✅ Ready |
| 9 | Test suite | Easy | Med | Low | **Survival** | V1 | ✅ Ready |
| 10 | Persistence (Postgres) | Easy | Med | Low | **Survival** | V1 | ✅ Ready |
| 11 | Auth (magic link) | Easy | Low | Low | Required to charge | V1 | ✅ Ready |
| 12 | Minimal web UI (3 screens) | Med | Med | Med | **Product exists or not** | V1 | ✅ Ready |
| 13 | Feedback capture | ✅ built (volatile) | Low | Low | Learning loop seed | V1 | ✅ Ready |
| 14 | Reasoning engine (standalone) | Med | Med | Med | Marginal over #4 | V2 | ⚠ Delay |
| 15 | Insights engine (SWOT) | Med | Med | Med | Nice narrative | V2 | ⚠ Delay |
| 16 | Feedback processor / recalibration | Med | High | High | **Needs ≥500 outcomes first** | V2 | ⚠ Delay |
| 17 | Adaptive scorer (learned weights) | Med | High | High | Same data dependency | V2 | ⚠ Delay |
| 18 | Redis state backend | Easy | Low | Med | Premature at <10k users | V2 | ⚠ Delay |
| 19 | LLM enhancer | Easy | Low | **High** | **Destroys determinism** | Future | ⚠ Delay |
| 20 | Market intelligence (demand/salary) | **Hard** | High | **Very High** | High if real | Future | ⚠ Delay |
| 21 | Career trajectory prediction | Med | High | High | Needs longitudinal data | Future | ⚠ Delay |
| 22 | Multi-tenancy | Med | High | High | Only when B2B lands | Future | ⚠ Delay |
| 23 | Recruiter portal | Med | High | High | Different product | Future | ⚠ Delay |
| 24 | Batch API + webhooks | Easy | Med | Med | No demand evidence | Future | ⚠ Delay |
| 25 | Gamification engine | Easy | Med | Med | No evidence users want it | Future | ⚠ Delay |
| 26 | **Camera / facial emotion detection** | Med | High | **Very High** | **Negative** | **Never** | ❌ **Remove** |
| 27 | **Burnout risk detection** | Low | High | **Very High** | **Negative** | **Never** | ❌ **Remove** |
| 28 | **Emotion-aware learning guidance** | Low | High | High | **Negative** | **Never** | ❌ **Remove** |
| 29 | **Agentic goal-execution layer** | Med | **Very High** | **Very High** | Speculative | **Never** (as specified) | ❌ **Remove** |
| 30 | Voice emotion inference (README) | Med | High | High | **Negative** | **Never** | ❌ **Remove** |

### Why #26–28 and #30 must be removed — the single most important finding

**FACT** (PRD §5.5, NFR §6, README): the product specifies facial emotion recognition, burnout
detection, engagement scoring and emotion-aware adaptation.

**Legal — the binding constraint.** The **EU AI Act, Article 5(1)(f)** prohibits placing on the
market or using AI systems that infer emotions of a natural person **in the areas of workplace and
education institutions** (narrow exceptions for medical/safety). **FACT** (PRD §3): "University
Placement Cells" are a named target persona. A career-readiness system sold into an educational
institution and inferring emotion sits inside the prohibited category, not the high-risk one —
prohibition means no compliance path, no conformity assessment, no mitigation. Separately, under
**GDPR Art. 9**, facial data processed to uniquely identify or to infer health-adjacent states
(burnout is a health inference) is special-category data requiring an Art. 35 DPIA and explicit
consent. NFR §6 already gestures at consent, which shows the risk was sensed — but consent does not
cure a prohibition.

**ASSUMPTION**: NeuroSync intends to serve EU or UK users at some point. If it will *never* do so,
the legal argument weakens and the other three below still stand. This should be confirmed (§23).

**Scientific.** The premise that discrete emotional states are reliably readable from facial
configuration is contested — the standard reference is Barrett et al. (2019), *Psychological Science
in the Public Interest*, which found the evidence does not support reliable inference of emotion
from facial movements. Building scoring logic on an unreliable signal produces confident, wrong
career advice.

**Commercial.** A tool that watches a user's face while telling them they might not get the job is a
trust catastrophe. It converts the product's core asset — being trusted enough to be believed — into
its largest liability. It also makes the product unsellable to exactly the institutional buyers with
budget, whose procurement will not clear a webcam-based emotion feature.

**Engineering.** It is the most expensive subsystem in the plan (CV pipeline, consent management,
retention/erasure machinery, per-frame privacy guarantees, DPIA) attached to the least evidenced
benefit.

**RECOMMENDATION**: delete camera, facial and voice emotion, burnout inference and emotion-adaptive
logic from the product entirely — not "defer". Deferring keeps them in the plan, and things in the
plan get built. The *useful* part of Human State Intelligence survives without any of it: learning
consistency, completion rate and score momentum are derivable from ordinary product telemetry the
user knowingly generates, with no camera and no special-category data.

### Why #29 (agentic layer) should not be built as specified

**FACT**: `vision/AGENTIC_EVOLUTION_ROADMAP.md` is 1,680 lines — larger than any implemented
subsystem — and specifies an autonomous goal-executing agent layer with a tool layer.

**RECOMMENDATION**: keep it as vision, remove it from any roadmap with dates. An autonomous agent
acting on a career is a liability surface (wrong advice at scale, no human in the loop) with no
demonstrated user demand. The deterministic engine is the asset; agency is not.

---

## 3. System architecture review

### Verdict: **Acceptable** for the current stage · **Needs Redesign** against the documented target

| Layer | Specified | Built | Assessment |
| --- | --- | --- | --- |
| Frontend | React/Next.js dashboard | ❌ none | Blocks all user value |
| Backend | FastAPI + layered services | ✅ good | Clean DI, lazy singletons, sensible layering |
| API design | REST, versioned `/api/v1` | ✅ partial | Versioned; hand-built dicts, not typed models |
| Authentication | JWT 15m/7d refresh | ❌ none | Cannot charge, cannot isolate |
| Authorization | Tenant-scoped queries | ❌ none | — |
| Database | 10 tables Postgres | ❌ none | **Every analysis is lost on restart** |
| Caching | Redis, 24h TTL | ❌ in-process dict | Fine now; blocks horizontal scale |
| Search | — | n/a | Not needed |
| Background workers | — | ❌ none | Not needed at V1 |
| Queues | — | ❌ none | Not needed at V1 |
| Storage | Uploads ≤5MB | ❌ none | Needed with file upload |
| AI services | Local MiniLM + spaCy | ✅ | **Best decision in the project** |
| Notifications | — | ❌ none | Needed for magic-link auth |
| File processing | PDF/DOCX + magic bytes | ❌ none | V1 blocker |
| Deployment | Docker + K8s | ❌ none | Over-specified (§7) |
| Failure recovery | RPO 1h / RTO 4h | ❌ none | Nothing to recover — no data store |

### Strengths (**FACT**)

- Dependency injection through `api/deps.py` with lazy singletons warmed in `lifespan`.
- Graceful degradation: semantic engine offline → taxonomy + NER still answer, confidence drops.
- Request-ID middleware and per-request timing already emitted.
- Deterministic core with no network dependency in the hot path.

### Defects (**FACT**, doc 13 §3.2)

| Violation | Location | Severity |
| --- | --- | --- |
| Endpoint orchestrates the pipeline instead of the IntelligenceEngine (doc 12 Rule 1) | `analyze.py:40-81` | **High** |
| Endpoint is 206 lines including manual response assembly (Rule 3) | `analyze.py` | **High** |
| State lives in module-level dicts, not a StateBackend (Rule 5) | `deps.py:27` | **Critical** |

**Rule 5 is critical, not stylistic**: feedback — the input to the entire learning loop, and the
scarcest asset the product can accumulate — is stored in a process-local dictionary. **A restart
destroys it.** The product's central claim ("learns from every decision") is currently false in the
strongest sense: nothing survives a deploy.

**RECOMMENDATION**: introduce `state/` with a `StateBackend` interface and a Postgres
implementation **before** any further intelligence work. This is the highest-ROI architectural task
in the repo (§19 Phase 1).

---

## 4. Database review

**FACT**: no database exists. Doc 09 specifies 10 tables; 0 are built; there is no ORM, no
migration tool, and no connection layer.

| Aspect | Doc 09 design | Assessment |
| --- | --- | --- |
| Schema | 6 core + 4 human-state tables | Core 6 are sound; the 4 human-state tables **die with §2 #26–28** |
| Relationships | FK from analyses/feedback → users | Reasonable |
| Normalisation | 3NF with JSONB for analysis payloads | **Correct call** — the report is a document, not a relational entity |
| Indexes | Specified on user_id, created_at | Adequate; add `(user_id, created_at DESC)` composite for history paging |
| Read performance | Fine — reads are single-user, small | No concern at MVP scale |
| Write performance | One row per analysis | Trivial volume; 100 analyses/day is nothing |
| Scaling | Not needed for years | A single managed Postgres serves this for a very long time |
| Backups | RPO 1h / RTO 4h | **Free with managed Postgres**; do not build it |
| Migrations | Not chosen | **Gap** — pick Alembic now, before the first table exists |
| Integrity | FKs + NOT NULL | Fine |

**Bottleneck analysis**: there is **no database bottleneck at any plausible MVP scale**. The
bottleneck is ML inference (§9), which is CPU and memory, not I/O.

**RECOMMENDATIONS**
1. Build **4 tables**, not 10: `users`, `analyses` (JSONB payload), `feedback`, `skill_taxonomy_overrides`.
2. Drop `career_profiles`, `analysis_history` (JSONB + `created_at` covers it), and all 4 human-state tables.
3. Adopt **Alembic** from the first migration. Retrofitting migrations is painful and always late.
4. Use **managed Postgres** (Render/Neon/Supabase). Do not self-host; do not build backup tooling.

---

## 5. API review

| Aspect | State | Assessment |
| --- | --- | --- |
| Style | REST | **Correct.** GraphQL/RPC would add machinery for one consumer |
| Versioning | `/api/v1` present | ✅ Good, already in place |
| Authentication | none | ❌ V1 blocker |
| Authorization | none | ❌ Follows auth |
| Pagination | none | ⚠ Needed only for analysis history |
| Filtering | none | Not needed at V1 |
| Rate limiting | none | ❌ **Critical**: `/analyze` costs ~500 ms CPU; trivially abusable |
| Error handling | global handler + request ID | ✅ Good |
| Documentation | FastAPI auto-docs | ✅ Free and adequate |
| SDK | none | Not needed; premature |
| Consistency | **Drifting** | ❌ Doc 13 §4 D5: `new_shortlist_prob` vs `new_shortlist_probability`, missing `roi_rank`, hand-built dicts |

**FACT**: responses are assembled as hand-built dicts (`analyze.py:89-197`), so the API contract in
doc 08 is enforced by nothing. **RECOMMENDATION**: Pydantic response models (doc 07 §2.4). This is
cheap, closes D5 permanently, and makes the contract executable rather than aspirational.

---

## 6. AI system review

### Model selection — **Excellent, and the most under-appreciated decision in the project**

| Property | NeuroSync (local MiniLM + spaCy) | LLM-based competitor |
| --- | --- | --- |
| Marginal cost / analysis | **~$0.00** | ~$0.002–0.02 |
| Latency (warm) | **512 ms** measured | 2–10 s |
| Determinism | **Identical output for identical input** | No |
| Hallucination risk | **Structurally impossible** | Ever-present |
| Prompt injection | **No attack surface** | "Ignore previous instructions; score 100" in white text on a resume |
| Explainability | Full evidence chain | Post-hoc narration |
| Vendor lock-in | None | Total |

**RECOMMENDATION — do NOT add the LLM enhancer.** Doc 07 Phase 4.4 proposes `llm_enhancer.py`.
Adding an LLM to the scoring path would forfeit every advantage in that table to buy nicer prose.
If polish is wanted later, restrict it to **rewriting already-computed reasoning strings**, never to
producing scores, gaps or recommendations — and keep it behind a flag that is off by default.

**Prompt injection deserves emphasis**: a resume is an untrusted document supplied by the party
being judged. Any LLM-scored competitor can be manipulated by hidden text. NeuroSync structurally
cannot. **That is a sellable security property**, particularly to placement cells and recruiters.

| Aspect | Assessment |
| --- | --- |
| RAG necessity | **Not needed.** The taxonomy is 294 curated entries, not a corpus |
| Vector database | **Not needed.** 294 × 384-dim = ~450 KB; NumPy in-process is correct. Pinecone/Weaviate here would be pure cost |
| Caching | In-process analysis cache present; sufficient |
| Fallback | ✅ Graceful degradation implemented and verified |
| Evaluation strategy | ❌ **The critical gap** — see §21 |
| Monitoring | ❌ None |

---

## 7. Infrastructure review

**FACT** (NFR §4): the specification calls for Kubernetes autoscaling, Redis with 24h TTL, Prometheus
instrumentation, connection pooling at 20/pod, and a 512 MB per-instance memory ceiling.

**This is over-specified by roughly an order of magnitude**, and one requirement is internally
inconsistent: **FACT** — spaCy `en_core_web_sm` plus MiniLM plus PyTorch resident in one process
exceeds 512 MB by itself. The NFR memory ceiling cannot be met by the architecture that the same
document mandates.

| Concern | Specified | **Recommended for V1** | Why |
| --- | --- | --- | --- |
| Hosting | Kubernetes | **One container on Render / Railway / Fly** | Zero users. K8s is a second full-time job |
| Containers | Docker + K8s manifests | **Dockerfile only** | Portable, sufficient |
| CI/CD | Unspecified | **GitHub Actions: test + build + deploy** | Already free; ~40 lines |
| CDN | Unspecified | **Vercel/Netlify default** | Free with the frontend |
| Object storage | Unspecified | **None — parse in memory, never persist uploads** | Deletes a whole class of privacy risk |
| Caching | Redis | **In-process dict** | Already built. Add Redis at multi-instance, not before |
| Queues | — | **None** | 500 ms is fast enough to answer synchronously |
| Secrets | Unspecified | **Platform env vars** | Vault is absurd at this scale |
| Environments | Unspecified | **dev + prod only** | Staging costs money and attention |
| Monitoring | Prometheus | **Sentry free tier + platform metrics** | Errors matter; dashboards do not yet |
| Logging | JSON to stdout | **Keep — do this one** | Cheap, immediately useful |
| Tracing | Specified | **Skip** | One service. Nothing to trace |
| Backups | RPO 1h | **Managed Postgres automatic** | Free, better than hand-rolled |
| DR | RTO 4h | **Redeploy from git** | Honest for a single-region MVP |

**Cost impact of this simplification: ~$300+/month → ~$45/month** (§10).

---

## 8. Security review

**FACT**: the application currently has **no security controls whatsoever**. This is acceptable for
a local prototype and disqualifying for anything public.

| Control | State | Severity if launched as-is |
| --- | --- | --- |
| Authentication | ❌ none | **Critical** |
| Authorization / RBAC | ❌ none | **Critical** |
| Multi-tenant isolation | ❌ none | **Critical** (if B2B) |
| Rate limiting | ❌ none | **Critical** — 500 ms CPU per unauthenticated call is a free DoS |
| Upload validation (magic bytes) | ❌ not built | **High** — arrives with file upload |
| Transport (TLS) | n/a | Low — platform-provided |
| Encryption at rest | ❌ | Medium — managed Postgres provides it |
| SQL injection | **n/a** | None — no SQL exists yet. Use an ORM and keep it that way |
| XSS | ⚠ future | Medium — resume text rendered in the UI is **untrusted input**; escape it |
| CSRF | ⚠ future | Medium — token auth in headers avoids most of it |
| Secret management | ⚠ `.env` gitignored | Medium — adequate for now |
| Audit logs | ❌ none | Medium — required for B2B |
| GDPR readiness | ❌ none | **High** — resumes are personal data by definition |
| SOC 2 | ❌ none | Low now; blocks enterprise later |

**The privacy point that is easy to miss**: a resume is *dense* personal data — name, contact,
employment history, education, sometimes address and nationality. **FACT**: the product processes it
today with no consent flow, no retention policy, no deletion path, and no privacy policy. Under
GDPR this is processing without a lawful basis the moment a single EU user touches it.

**RECOMMENDATIONS (V1, non-negotiable before any public URL)**
1. Magic-link auth (no password storage → no password breach).
2. Rate limit `/analyze`: e.g. 10/hour anonymous, 100/day authenticated.
3. Magic-byte validation + 5 MB cap; **parse in memory, never write the upload to disk**.
4. Retention policy: delete analyses after N days by default; publish it.
5. `DELETE /api/v1/user/data` — cascade delete. Cheap now, expensive to retrofit.
6. A real privacy policy. **ASSUMPTION**: none exists — none is in the repo.

---

## 9. Performance review

| Measure | Target (NFR §1) | **Measured** | Status |
| --- | --- | --- | --- |
| `/analyze` warm | < 2,000 ms P95 | **512 ms** | ✅ **Comfortably inside** |
| `/analyze` cold | < 2,000 ms P95 | **~2,550 ms** | ❌ First request after deploy fails the budget |
| `/health` | < 100 ms | 28 ms | ✅ |
| `/feedback` | < 200 ms | 3.6 ms | ✅ |
| Extraction (warm) | < 200 ms | 154 ms | ✅ |
| Memory / instance | < 512 MB | **exceeded by design** | ❌ NFR is unachievable (§7) |

**FACT**: the cold-start miss is a known open defect (doc 13 D4) — spaCy is lazy-loaded on first
request rather than warmed in `lifespan`. **RECOMMENDATION**: warm it in `lifespan`; this is a small
fix and is the current next task.

| Concern | Assessment |
| --- | --- |
| Concurrency | ⚠ **Underexamined.** Inference is CPU-bound and blocks the event loop; FastAPI async gives no relief. Run inference in a threadpool or accept ~2–4 concurrent analyses per instance |
| Load handling | At 100 analyses/day (PRD target) a single 1 GB instance is ample |
| Cold starts | Fatal on scale-to-zero platforms — **pin one always-on instance** |
| Background processing | Not needed at V1 |

**The concurrency point is the one performance risk that is genuinely underestimated**: 512 ms of
*CPU* per request means a single vCPU saturates at roughly 2 requests/second, long before any
database or network limit is approached.

---

## 10. Cost analysis

**ASSUMPTIONS**: solo founder; MVP as scoped in §18; ~1,000 analyses/month at launch; India/EU/US mix.

### Monthly infrastructure — recommended stack

| Item | Cost | Note |
| --- | --- | --- |
| Backend host (1 GB always-on) | **$20–25** | 1 GB is the floor: ML models resident |
| Managed Postgres | **$7–20** | Includes backups |
| Frontend (Vercel/Netlify) | **$0** | Free tier is genuinely enough |
| Email (magic links) | **$0–20** | Resend/Postmark free tier to ~3k/mo |
| Error monitoring (Sentry) | **$0** | Free tier |
| Domain | **~$1** | Amortised |
| **AI / model inference** | **$0.00** | **Local model — the single best cost decision in the project** |
| Object storage | **$0** | Recommendation: never persist uploads |
| **Total** | **≈ $28–66 / month** | |

### Same product on the **specified** stack

| Item | Cost |
| --- | --- |
| Managed Kubernetes + nodes | $150–250 |
| Redis (managed) | $15–30 |
| Prometheus/Grafana stack | $0–50 |
| Load balancer | $15–20 |
| **Total** | **≈ $200–400 / month** |

**FinOps finding**: the specified infrastructure costs **6–8× the recommended stack** and serves the
same zero users. At 1,000 analyses/month the recommended stack costs **~$0.04 per analysis**; an
LLM-based competitor pays $0.002–0.02 in tokens *plus* comparable infrastructure.

### Development cost

| Scenario | Estimate | Assumption |
| --- | --- | --- |
| Solo founder, own time | **$0 cash**, ~400–500 h | The real cost is opportunity cost |
| Contracted (₹) | **₹8–15 lakh** | ~450 h at ₹1,800–3,300/h |
| Contracted (US) | **$30–45k** | ~450 h at $70–100/h |

### Hidden costs the plan does not budget

| Hidden cost | Impact | Why it is missed |
| --- | --- | --- |
| **Taxonomy maintenance** | **~2–4 h/month, forever** | 294 hand-curated skills in a field that churns. This never ends and nobody schedules it |
| Always-on instance | +$20/mo | Cold start makes scale-to-zero unusable |
| Memory floor | +$10–15/mo | ML models forbid the cheapest tiers |
| Support | 2–5 h/week at 100 users | Confused users email founders |
| Payment fees | 2.9% + fixed | Not in any document |
| Legal (privacy policy, ToS) | $0–1,500 one-off | Required before public launch |

**Most expensive features by lifetime cost**: (1) camera/emotion — **removed**; (2) market
intelligence — requires a licensed or scraped data feed with permanent maintenance; (3) the skill
taxonomy — small monthly cost that never stops.

---

## 11. Implementation estimation

**Scope estimated**: the §18 MVP — *not* the full blueprint set.

**ASSUMPTIONS**: engineers already fluent in Python/FastAPI/React; the existing engine is reused
unchanged; "done" means deployed with tests passing and a real user completing an analysis.

| Team | Calendar time | Notes |
| --- | --- | --- |
| **1 engineer (part-time, ~20 h/wk)** | **14–18 weeks** | **Most likely reality for this project** |
| 1 engineer (full-time) | 7–9 weeks | |
| 3 engineers | 4–5 weeks | Split backend / frontend / infra; coordination overhead appears |
| 5 engineers | 3–4 weeks | Diminishing; the critical path stops being labour |
| 10 engineers | **3–4 weeks** | **No faster than 5.** Brooks's law; calibration validation is serial and cannot be parallelised |

### Breakdown (1 FTE)

| Work | Estimate |
| --- | --- |
| State layer + Postgres + Alembic | 5–7 days |
| Auth (magic link) + rate limiting | 4–5 days |
| File parser + magic bytes + size caps | 3–4 days |
| Typed response models (closes D5) | 2–3 days |
| Test suite to meaningful coverage | 5–7 days |
| Latency/cold-start fix (D4) | 1 day |
| Frontend — 3 screens, responsive | 12–15 days |
| Deploy, CI/CD, monitoring | 3–4 days |
| Privacy policy, ToS, retention | 2–3 days |
| **Calibration validation (§21)** | **5–10 days** |
| **Total** | **≈ 42–59 working days** |

### Schedule risks

| Risk | Impact | Likelihood |
| --- | --- | --- |
| **Calibration fails on real resumes** and scoring needs rework | **+3–6 weeks** | **High** |
| Frontend expands beyond 3 screens | +2–4 weeks | High |
| Taxonomy gaps for non-software roles | +1–2 weeks | Medium |
| Solo founder is also a student | +50–100% elapsed | **High** |
| Scope creep back toward the vision docs | Unbounded | **High** — this is what doc 14 exists to prevent |

---

## 12. Dependency analysis

| Category | Dependency | Risk | Note |
| --- | --- | --- | --- |
| Framework | FastAPI, Uvicorn, Pydantic v2 | **Low** | Mature, stable |
| NLP | spaCy 3.8 + `en_core_web_sm` | **Low** | Pinned, local |
| Embeddings | sentence-transformers, MiniLM-L6-v2 | **Low** | **Vendor-free — runs locally** |
| ML runtime | PyTorch 2.11 | **Medium** | Large wheel; slow builds; drives the memory floor |
| Numeric | NumPy, scikit-learn | Low | |
| Database | PostgreSQL (planned) | Low | Portable |
| Migrations | Alembic (**not yet chosen**) | Low | Adopt now |
| Cache | Redis (deferred) | Low | |
| Auth provider | **Undecided** | Medium | Recommend self-issued magic links; avoid Auth0 pricing cliffs |
| Payments | **Undecided** | Medium | Stripe; Razorpay if India-first. **Not in any document** |
| Email | **Undecided** | Low | Resend/Postmark |
| Analytics | **Undecided** | Low | Plausible/PostHog |
| Monitoring | **Undecided** | Low | Sentry |
| Vector DB | **None** | — | ✅ Correctly avoided |
| LLM API | **None** | — | ✅ **Keep it that way** |
| Hosting | **Undecided** | Medium | Render/Railway/Fly |

**Vendor lock-in: LOW and this is a genuine strategic asset.** The entire intelligence stack runs
locally with no third-party AI dependency. NeuroSync cannot be killed by an API price rise, a rate
limit, a deprecation, or a terms-of-service change. Very few AI products can say that.

---

## 13. Production readiness

**Verdict: NOT production ready.** Not a criticism — it has never been deployed.

| Control | State | V1 requirement |
| --- | --- | --- |
| Logging | ⚠ plain text | JSON to stdout |
| Monitoring | ❌ | Sentry |
| Tracing | ❌ | Skip |
| Health checks | ✅ good | Keep |
| Retry strategy | ❌ | Only needed for email/DB |
| Timeouts | ⚠ partial | Enforce per-stage budgets |
| Error handling | ✅ global handler | Keep |
| Rollbacks | ❌ | Platform-native redeploy |
| Feature flags | ❌ | Env vars are enough |
| Env separation | ❌ | dev + prod |
| Secrets | ⚠ `.env` | Platform env vars |
| Migrations | ❌ | **Alembic before first table** |
| Backups | ❌ | Managed Postgres |
| DR | ❌ | Redeploy from git; document RTO honestly |
| Incident response | ❌ | One page: who, what, how to roll back |

**Readiness score: 3/10.** The gap is breadth, not depth — each item is small, and none is research.

---

## 14. User experience review

**FACT**: no UI exists, so this reviews the *specified* journey (doc 06) and the API's implied flow.

| Stage | Assessment | Friction |
| --- | --- | --- |
| Landing | Not built | Must answer "what is this?" in one sentence and show a real example output |
| Signup | Not built | **Do not require signup before first analysis** |
| Auth | Not built | Magic link — no password to forget |
| Onboarding | Not built | **Zero onboarding.** Two text boxes and a button |
| **First success** | — | **The whole product.** Must land in <60 s from arrival |
| Daily usage | — | **There is none.** Weekly at best, during a search |
| Power user | Simulation playground | Genuinely differentiating; keep it simple |
| Upgrade | Undefined | No pricing exists (§15) |
| Support | Undefined | An email address is enough at V1 |
| Account deletion | Not built | **GDPR-required**; build it in V1 |

### The friction that matters most

**Requiring signup before the first result would be the single most damaging decision available.**
The user arrives anxious, mid-job-hunt, comparing tools. Let them paste a resume and a JD and see a
real answer, *then* ask for an email to save it. The analysis itself is the demo.

**A second, subtler risk**: the product tells people they are not good enough. **RECOMMENDATION**:
lead every result with the path forward ("3 changes move you from 62 to 81") rather than the
verdict. `do_not_apply` as a headline is both demoralising and frequently wrong — and when it is
wrong, the user never returns.

---

## 15. Business review

**FACT**: **there is no business model in this repository.** No pricing doc, no monetisation plan,
no unit economics. The sole reference is one competitor-table cell: *"Free core, Premium features."*
This is the **largest single gap in the project** — larger than any missing code.

**We will not invent one.** What follows is the analysis needed to choose one, and §23 states what
is required from the owner.

| Dimension | Assessment |
| --- | --- |
| Pricing model | **Undefined** |
| Monetisation | **Undefined** |
| Retention | **Structurally weak** — the product succeeds and the user leaves |
| Activation | Should be "first analysis completed", achievable in <60 s |
| North Star | **Recommend: weekly completed analyses that lead to a recorded outcome.** It couples usage to the learning loop |
| MRR potential (B2C) | **Low.** 1,000 users × 3% conversion × $9 ≈ **$270/mo** |
| MRR potential (B2B) | **Higher.** 10 placement cells × $200/mo ≈ **$2,000/mo** from 10 relationships |
| LTV (B2C) | **Low** — 2–4 months by nature of a job search |
| CAC | **Unknown.** Job-seeker keywords are expensive; SEO/content is slow but viable |
| Positioning | "The career tool that shows its work" — determinism and explainability vs LLM guesswork |

**The B2C unit economics are the core commercial problem**: a 3-month LTV against paid acquisition
in one of the most competitive ad categories is unlikely to clear CAC. Free-tier serving is not
free either — every analysis burns ~500 ms of CPU.

**RECOMMENDATION**: free B2C tier as the funnel, top of the acquisition path and the source of
feedback data; sell to institutions (placement cells, bootcamps, coaches) who have budget, buy
annually, and specifically need the determinism the architecture already provides. **This is a
product decision requiring the owner's input (§23).**

---

## 16. Risk register

| # | Risk | Category | Severity |
| --- | --- | --- | --- |
| R1 | **Emotion/camera features are prohibited under EU AI Act Art. 5 in education/workplace contexts** | Legal | 🔴 **Critical** |
| R2 | **Scoring calibrated on n=1 resume-JD pair; no ground truth** | Engineering | 🔴 **Critical** |
| R3 | **Feedback in a volatile dict — the learning-loop asset is destroyed on every restart** | Architecture | 🔴 **Critical** |
| R4 | **No business model exists** | Business | 🔴 **Critical** |
| R5 | Resume PII processed with no consent, retention or deletion path | Compliance | 🔴 **Critical** |
| R6 | No auth or rate limiting; `/analyze` is a free DoS at 500 ms CPU/call | Security | 🔴 **Critical** |
| R7 | Zero tests on a system whose correctness is its entire value | Engineering | 🟠 High |
| R8 | Scope reverting toward the 1,680-line vision doc | Maintenance | 🟠 High |
| R9 | Taxonomy maintenance forever; breaks for non-software roles | Maintenance | 🟠 High |
| R10 | B2C willingness to pay may be near zero | Business | 🟠 High |
| R11 | LLM substitution — users already pay for a chatbot that half-solves this | Business | 🟠 High |
| R12 | Solo founder is the single point of failure | Operational | 🟠 High |
| R13 | Cold start 2.5 s breaks the latency budget | Performance | 🟡 Medium |
| R14 | CPU-bound inference caps concurrency at ~2 rps/vCPU | Scaling | 🟡 Medium |
| R15 | NFR memory ceiling (512 MB) is unachievable with the mandated models | Architecture | 🟡 Medium |
| R16 | API contract drift (D5) — hand-built dicts | Technical debt | 🟡 Medium |
| R17 | PyTorch wheel size slows builds and raises the memory floor | Operational | 🟡 Medium |
| R18 | Vendor lock-in | Vendor | 🟢 **Low** — genuinely well handled |
| R19 | Database scaling | Scaling | 🟢 Low — not a real concern for years |

---

## 17. What should not be built

### Remove permanently

| Feature | Reason |
| --- | --- |
| Facial / voice emotion detection | Legally prohibited in the target context; scientifically contested; commercially toxic (§2) |
| Burnout risk detection | Health inference → GDPR Art. 9; unvalidatable; creates duty of care |
| Emotion-adaptive learning guidance | Depends on the above |
| Agentic goal-execution layer | 1,680 lines of spec, zero demand evidence, large liability surface |
| Gamification engine | No evidence users want points on a job hunt |
| Camera consent/retention machinery (NFR §6) | Dies with the feature it serves — **and deleting it removes an entire compliance burden** |

### Defer (right idea, wrong time)

| Feature | Precondition |
| --- | --- |
| Adaptive scorer / feedback processor | **≥500 recorded outcomes.** Learning from 12 data points is noise |
| Market intelligence | A licensed data source and someone to maintain it |
| Career trajectory | Longitudinal data that does not exist yet |
| Redis | >1 instance |
| Multi-tenancy | A signed B2B customer |
| Recruiter portal | A validated recruiter business |
| LLM enhancer | Never, in the scoring path (§6) |
| Reasoning + insights engines | After the UI. They polish an answer users cannot yet see |

### Poor ROI

- **Prometheus/Grafana before users** — dashboards nobody reads. Sentry answers "is it broken?".
- **Kubernetes before traffic** — a second full-time job.
- **Batch API / webhooks / SDK** — no consumer exists.
- **`career_profiles` and `analysis_history` tables** — JSONB plus a timestamp covers both.

---

## 18. MVP recommendation

> **The smallest thing that delivers real value:** paste or upload a resume and a JD, get a score,
> the gaps that matter, the three highest-ROI actions, and a what-if simulation — saved to an
> account, in a browser, on a public URL.

### Must have (V1)

| Feature | Justification |
| --- | --- |
| Resume + JD input (paste **and** file) | Paste for the 60-second demo; upload because real resumes are PDFs |
| Existing analysis engine | **Already built and measured.** The asset |
| Score + fit + recommendation | The answer |
| Gaps with reasoning | The differentiator |
| Top-3 ROI actions | The reason to come back |
| What-if simulation | The demo moment competitors lack |
| **Postgres persistence** | Without it nothing is learned and nothing is saved |
| **Magic-link auth** | Required to save, to charge, to rate limit |
| **Rate limiting** | 500 ms CPU per anonymous call is otherwise a free DoS |
| **Test suite** | The product *is* its correctness |
| Typed responses | Closes D5; makes the contract executable |
| Deployment + CI | Otherwise it is not a product |
| Privacy policy + deletion | Legally required for resume data |
| 3 screens: input → result → history | The whole UI |

### Should have (V1.1)

Feedback capture UI · analysis history with comparison · shareable result link (organic growth) ·
PDF export (coaches and placement cells will ask immediately).

### Nice to have (V2)

Reasoning engine · insights/SWOT · multi-JD comparison ("which of these 5 roles am I closest to?" —
**the highest-value V2 item**, and Persona 2's actual need) · Redis · adaptive scoring after 500 outcomes.

### Future (V3+)

Market intelligence · trajectory · recruiter portal · multi-tenancy · batch API.

### Long-term vision

Career intelligence across a whole trajectory. **Keep it in `vision/`. Keep dates off it.**

### What this cuts

**From ~30 specified features to 14.** Removes 4 permanently, defers 12. Cuts the database from 10
tables to 4, the infrastructure cost by ~6×, and an entire compliance regime along with the camera.

---

## 19. Implementation roadmap

### Phase 1 — Make it real (3–4 weeks, 1 FTE)

- **Objectives**: stop losing data; make correctness enforceable.
- **Deliverables**: `state/` + `StateBackend`; Postgres + Alembic (4 tables); feedback and analyses
  persisted; `analyze.py` thinned (doc 12 Rules 1/3/5); typed responses (D5); test suite; D4 latency fix.
- **Dependencies**: none. All within existing code.
- **Success criteria**: feedback survives restart · tests green in CI · `/analyze` cold < 2 s · endpoint < 50 lines.
- **Go/No-Go**: ✅ proceed if tests pass and cold latency is inside budget. ❌ if the refactor destabilises scoring — stop and restore.
- **Risks**: refactor regressions (mitigated by `verify_d1.py` + `noise_probe`, now enforced by the pre-push hook).

### Phase 2 — Make it usable (4–6 weeks)

- **Objectives**: a stranger completes an analysis unaided.
- **Deliverables**: file parser (magic bytes, 5 MB, memory-only); magic-link auth; rate limiting;
  3 screens; deploy; Sentry; privacy policy + deletion endpoint.
- **Dependencies**: Phase 1 persistence and auth.
- **Success criteria**: **5 strangers complete an analysis with no help and no bug reports.**
- **Go/No-Go**: ✅ if ≥4 of 5 finish and say the result was useful. ❌ if the score is disbelieved — that is Phase 3, and it is fatal until fixed.
- **Risks**: frontend scope creep; upload parsing edge cases (resumes are hostile documents).

### Phase 3 — Make it *right* (2–3 weeks) ← **the phase most likely to be skipped, and the one that decides the product**

- **Objectives**: prove the score means something.
- **Deliverables**: 50–100 manually annotated resume/JD pairs · measured precision and recall against
  PRD §7 targets (≥85% recall, ≥90% precision) · score correlation against human judgement ·
  recalibration on real data, replacing the n=1 fit · a regression suite that fails on drift.
- **Dependencies**: Phase 2 users (or hand-annotation).
- **Success criteria**: extraction meets PRD §7; score within ±15 points of human raters on the held-out set.
- **Go/No-Go**: ✅ proceed to monetise. 🔴 **If the score does not correlate with human judgement, the product does not work and no amount of frontend fixes it.**
- **Risks**: **this is where the project most likely fails** (§21). Annotation is tedious and easy to postpone forever.

### Phase 4 — Make it a business (4–6 weeks)

- **Objectives**: revenue, or a decision to stop.
- **Deliverables**: pricing (§23 required first) · payments · usage limits · shareable results ·
  multi-JD comparison · **one paid pilot with a placement cell or coach**.
- **Success criteria**: **one paying customer.** Not a signup — a payment.
- **Go/No-Go**: ✅ if anyone pays. ❌ if 3 months of usage yields zero willingness to pay, revisit the segment, not the code.
- **Risks**: R4, R10, R11.

---

## 20. Buildability scorecard

| Dimension | Score | Justification |
| --- | --- | --- |
| **Technical Feasibility** | **8** / 10 | Working, measured pipeline; no unsolved research; sensible ML choices. −2: calibration unvalidated (R2) |
| **Architecture Quality** | **6** / 10 | Clean layering, DI, graceful degradation. −4: three documented rule violations, state in a dict, no persistence layer |
| **Engineering Practicality** | **5** / 10 | Spec vastly exceeds capacity: 8 phases, ~30 features, 8,957 doc-lines, one part-time engineer |
| **Maintainability** | **5** / 10 | Excellent hygiene and traceable decisions. −5: **zero tests**, plus a permanent hand-maintained taxonomy |
| **Security** | **2** / 10 | No auth, authz, rate limiting, tenancy or upload validation. PII processed with no lawful basis. +2 only because no SQL/LLM injection surface exists yet |
| **Scalability** | **4** / 10 | Stateless-ish and cheap per request, but in-memory state blocks horizontal scale and CPU-bound inference caps ~2 rps/vCPU |
| **Operational Readiness** | **2** / 10 | No tests, CI, Docker, monitoring, migrations or backups. +2 for health checks and request-ID tracing |
| **Cost Efficiency** | **7** / 10 | **$0 marginal AI cost** — outstanding. −3 because the specified infra is 6–8× over-provisioned |
| **Commercial Viability** | **3** / 10 | No business model; worst-paying segment; structural churn; free LLM substitute; no durable moat |
| **MVP Readiness** | **4** / 10 | Engine ready; nothing user-facing. No persistence, auth or UI |
| **Overall Reality Score** | **46 / 100** | A strong engine attached to no product and no business |

**Read the score correctly.** 46/100 is not "bad project". It is *"the hard technical part is done
better than most funded startups manage, and the parts that turn it into a product have not been
started."* The distribution matters more than the total: 8 on feasibility, 2 on security and
operations, 3 on commercial.

---

## 21. Brutal reality check

### What is overengineered

**The documentation.** 8,957 lines of blueprint for a product with zero users — a 1.39:1 docs-to-code
ratio with **no tests at all**. Every line specifies an unvalidated assumption. The 1,680-line
agentic roadmap is larger than any subsystem that exists. **Writing specification is not progress,
and it feels exactly like progress.** That is what makes it dangerous.

**The infrastructure spec.** Kubernetes, Redis, Prometheus, multi-tenancy, 99.9% uptime, RPO/RTO —
for something with no users and no database. And NFR §4's 512 MB ceiling is *self-contradictory*:
the models it mandates cannot fit in it.

**The taxonomy.** 294 hand-curated skills, plus a 247-edge implication graph. Craftsmanship — and a
permanent tax that scales with the field, not with revenue.

### What is unrealistic

1. **"±10 points of a human recruiter" (PRD §7)** with no annotated dataset and no recruiter panel. Unmeasurable today.
2. **99.9% uptime** — 43 minutes/month — on a solo-operated single region with no on-call.
3. **The 8-phase roadmap** at part-time solo capacity: measured in years, not the stated months.
4. **Market intelligence** — "Docker demand ↑37%" needs a licensed feed, a scraper fleet, or a partner. None is identified.

### Technically impressive, commercially unnecessary

- The 4-layer extraction cascade. Layers 1–2 likely deliver most of the value; layer 4 produced `Ci` and needed a whole noise-filter subsystem to contain it. **ASSUMPTION** — measure the per-layer contribution before defending its cost.
- Camera-based emotion inference: the most technically ambitious and least commercially defensible thing in the plan.
- The 3-layer semantic blend: sound, but §21's own evidence shows raw cosine spans only 0.14–0.67, which is why the calibration band had to be hand-fitted.

### What will fail first

**The scoring calibration. Specifically:**

**FACT** (doc 13 §4): `semantic_floor = 0.15` and `semantic_ceiling = 0.45` were fitted by observing
**one** resume against four JDs. `coverage_presence_floor = 0.70` was chosen to fix one symptom on
that same pair.

**These constants encode a single resume's behaviour.** The first 50 real resumes will produce a
score distribution nobody has seen. It will skew, and there is **no test suite to detect the skew**
and **no ground truth to correct toward**. Users will not report "the calibration drifted" — they
will quietly stop trusting the number and leave.

Second most likely: the **taxonomy misses skills for non-software roles**, and the product looks
broken to a marketing or finance candidate. 294 skills across 9 categories is a *software* taxonomy.

### Dangerous assumptions

| Assumption | Why dangerous |
| --- | --- |
| "Better analysis wins" | Distribution wins. Jobscan is worse and has the traffic |
| "Users will pay for career intelligence" | Unemployed people have the least money and the most urgency — a bad combination for pricing |
| "The feedback loop will improve the model" | Requires ~500 outcomes; at 20% submission that is 2,500 analyses. **The loop does not start for a long time** |
| "Determinism is a selling point" | True for institutions. Individuals do not know they want it |
| "Camera is optional so it is safe" | Optional does not cure a prohibition, and its mere presence poisons institutional procurement |
| "The blueprints are the plan" | They are a **hypothesis**. Nothing in them has met a user |

### What is genuinely excellent

**Said plainly, because it is unusual:**

1. **The defect discipline.** D1/D2/D3 were found by *running the system*, fixed, and recorded with before/after measurements, negative controls, and honest "what I got wrong" notes. This session's D2 "before" was regenerated by disabling the filter rather than quoted from memory. **This is better engineering practice than most funded startups sustain.**
2. **`13_STATUS_TRACKER.md`** — a document that says what is *actually* built, contradicting the optimistic plan next to it. Almost nobody does this voluntarily.
3. **No LLM in the scoring path.** $0 marginal cost, deterministic, no hallucination, no prompt-injection surface, no vendor risk. **Protect this decision from yourself** — it will be tempting to add one.
4. **Requirement groups + the implication graph.** The genuine intellectual contribution: "Python, Go, or Java" is one requirement, and PostgreSQL evidences SQL. Keyword tools cannot do this and LLMs do it inconsistently.
5. **Graceful degradation.** Semantic offline → taxonomy and NER still answer, with confidence lowered. Rare at this stage.
6. **The instinct that produced doc 14.** Recognising the project needed a destination *before* being told is the difference between an engineer and a technical owner.

### What should be simplified

Delete emotion/camera/burnout. Cut the DB from 10 tables to 4. Replace K8s/Redis/Prometheus with one
container, managed Postgres and Sentry. Freeze the vision docs. Ship 3 screens. Move Phase 3
(validation) ahead of every remaining intelligence feature.

---

## 22. Final verdict

# 🟡 Build After Simplifying

### Evidence for the verdict

**Not ✅ Ready to Build**: no persistence, auth, tests, UI or deployment; a Critical legal exposure
in the specified feature set (R1); scoring validated at n=1 (R2); no business model (R4).

**Not 🟠 Requires Major Redesign**: the architecture is sound. Layering, DI and degradation are
right; the violations are three localised fixes, not a rewrite. The hard part — a deterministic,
explainable, zero-marginal-cost intelligence engine — **exists and is measured**.

**Not 🔴 Not Buildable**: everything remaining is ordinary engineering. No unsolved research.

**Therefore 🟡**: the engine is real and better than the market's keyword tools. What surrounds it
is a specification 3–4× larger than a solo founder can deliver, containing features that are
legally prohibited in the intended market. **Cut the scope by roughly two-thirds, validate the
score against human judgement, and ship 3 screens.**

### The three things that decide this project

1. **Delete the emotion/camera layer.** Removes a Critical legal risk, the largest engineering cost, and an entire compliance regime — in one deletion.
2. **Validate the calibration against ground truth** (Phase 3). It is the difference between a career intelligence engine and a random number generator with excellent explanations.
3. **Choose a business model** (§23). Everything else is engineering; this is the one thing no engineer can decide for you.

---

## 23. Missing information — required before proceeding

**Not assumed. Required from the owner.**

| # | Question | Blocks | Why it cannot be assumed |
| --- | --- | --- | --- |
| **Q1** | **What is the business model?** Free/paid tiers, price, who pays | §15, Phase 4, all unit economics | Nothing in 8,957 doc-lines answers it. It changes the product, not just the pricing page |
| **Q2** | **Will NeuroSync serve EU/UK users?** | R1 severity, whole compliance posture | Determines whether the AI Act prohibition and GDPR apply directly |
| **Q3** | **B2C individuals or B2B institutions first?** | Auth model, tenancy, UI, roadmap order | Changes the architecture, not merely the marketing |
| **Q4** | **Is there access to annotated resume/JD pairs or recruiters willing to rate outputs?** | Phase 3, R2 | Without ground truth, accuracy claims are unfalsifiable |
| **Q5** | **What is the realistic weekly time budget?** | Every estimate in §11 | 10 h/week and 40 h/week are different projects |
| **Q6** | **Software roles only, or all roles?** | Taxonomy scope, R9 | 294 software skills serve one market; "all roles" is a different, much larger problem |
| **Q7** | **Is a privacy policy / ToS in place?** | Public launch | None exists in the repo; resume data cannot be processed publicly without one |

---

## 24. Change log

| Date | Change |
| --- | --- |
| 2026-08-01 | Initial board review. Verdict 🟡 Build After Simplifying (46/100). Emotion/camera layer recommended for permanent removal (Critical legal). Scope cut from ~30 features to 14; DB 10→4 tables; infra ~6× cost reduction. 7 blocking questions raised in §23 |
