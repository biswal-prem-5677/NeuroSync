# NeuroSync — Architectural Decision Log

This log documents key architectural and engineering decisions, their rationale, trade-offs, and outcomes.

---

## 2026-06-02

### Why Skill Graph over Vector-Only Approach

#### Context

In designing the candidate-to-job matching engine, we had to decide between a vector-only approach (e.g., encoding entire documents or list of skills and running cosine similarity) versus a structured skill graph and taxonomy-based reasoning system.

#### Reason

- **Explainability**: Every match score and priority must be explainable. A vector cosine similarity is a "black box" that gives a single float (e.g., `0.76`) without explaining why or what is missing. A skill graph allows us to point to specific missing competencies and explain their importance.
- **Deterministic Reasoning**: Allows us to write rules for section importance, proficiency extraction, and taxonomy relationships that produce predictable and consistent results.
- **Better Simulations**: Enables real "what-if" simulations (e.g., "If I learn Kubernetes, how does my score improve?") by dynamically updating the nodes and recalculating the graph overlap.

#### Tradeoff

- **More Maintenance**: Requires seeding, expanding, and keeping the taxonomy and skill relationship matrix up-to-date, whereas a vector-only approach requires zero metadata curation.

#### Decision

- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal

---

## 2026-06-06

### Why Human State Intelligence Exists

#### Context

When integrating behavioral concepts from the legacy Java project (camera-based emotion detection), we had to decide whether NeuroSync should remain a pure Resume Intelligence system or expand to include behavioral signals (learning activity, project engagement, interview performance, optionally camera-derived attention/focus).

#### Reason

- **Career success is not just skills**: Consistency, motivation, engagement, confidence, and learning behavior are equally important predictors of career outcomes.
- **Agentic capability**: A true career intelligence agent must observe human state — not just parse documents. Burnout prediction, dropout prevention, and adaptive difficulty require behavioral signals.
- **Legacy transformation**: The Java project's emotion detection was shallow (Camera → Happy/Sad → Action). The upgrade transforms this into multi-signal state inference (8 observation sources → CareerState → Agent Decision).

#### Tradeoff

- **Additional complexity**: Adds observation ingestion, state computation, and prediction layers that increase system surface area.
- **Camera privacy concerns**: Requires GDPR-ready design, explicit consent, and ephemeral data handling. Mitigated by making camera permanently optional (system is 95% functional without it).

#### Decision

- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal

---

### Why CareerState Exists

#### Context

When designing the Human State Intelligence layer, we had to decide whether the Agent Decision Engine should consume raw signals directly (emotion=frustrated, completion_rate=0.3, attention=low) or operate on a unified derived state representation.

#### Reason

- **Raw signals are noisy**: Individual observations fluctuate. A single bad session doesn't mean burnout. CareerState aggregates across time and sources to produce stable metrics.
- **Source independence**: The agent should reason the same way regardless of whether engagement data came from camera, learning sessions, or project activity. CareerState abstracts the source away.
- **Predictability**: Derived state (confidence=0.42, momentum=0.31, burnout_risk=0.78) produces more stable and predictable agent decisions than raw events.
- **Architectural cleanliness**: `AgentObservation → StateObservation → CareerState → StateTransition` forms a clean data hierarchy where each level adds stability and meaning.

#### Tradeoff

- **Information loss**: Aggregation into CareerState discards some granularity from raw signals. Mitigated by retaining AgentObservation records as the agent memory layer.

#### Decision

- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal

---

## 2026-07-27

### Why "Phase" Means Scope in Doc 12 and Sequence in Doc 07

#### Context

A codebase audit found that [12_SYSTEM_ARCHITECTURE.md](12_SYSTEM_ARCHITECTURE.md) §10 marks seven services as **Phase 1 "Build"** (`reasoning_engine`, `insights_engine`, `feedback_processor`, `adaptive_scorer`, `llm_enhancer`, `state/base.py`, `state/memory_state.py`) while [07_IMPLEMENTATION_PLAN.md](07_IMPLEMENTATION_PLAN.md) schedules the same files in Phases 3–4 and simultaneously declared Phase 1 "✅ COMPLETE". None of the seven exist on disk, so the two documents could not both be true.

#### Reason

- **Two different questions**: doc 12 answers *"what must the v1.0 architecture contain?"*; doc 07 answers *"in what order do we build it?"*. Collapsing both into a column named `Phase` created the contradiction.
- **Doc 12 must stay declarative**: it is the architectural constitution. Making it track build status would force it to churn on every commit and would weaken its authority.
- **A third artifact was missing**: neither document recorded *measured* state. [13_STATUS_TRACKER.md](13_STATUS_TRACKER.md) now owns that, verified by running the pipeline rather than by assertion.

#### Tradeoff

- **Three documents to keep in sync** instead of two. Mitigated by a strict precedence rule: doc 12 wins on *what must exist*, doc 07 wins on *when it is built*, doc 13 wins on *what is built today*.

#### Decision

- Doc 12 §10 `Phase` column is clarified in prose as **MVP scope tier** (1 = required for v1.0, 2 = deferred beyond v1.0).
- Doc 07 Phase 1 is downgraded from COMPLETE to **PARTIAL** and stays open until the seven tier-1 services land in Phase 3.
- Doc 07 Phase 2 is corrected from 0% to **in progress** (2.1 done, 2.2 partially done).
- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal

---

### Why Correctness Fixes Precede Phase 3

#### Context

A live pipeline run (2026-07-27) scored a senior candidate holding Python, FastAPI, Docker, Kubernetes, AWS, Kafka, Redis, PostgreSQL and CI/CD against a Senior Backend / Cloud Infrastructure JD at **20.85/100 → `do_not_apply`, `no_fit`, 0% shortlist probability**. Only 8 of 25 JD skills matched. Doc 07 would have moved next to Phase 3 (reasoning and insights engines).

#### Reason

- **Wrong answers do not improve with better prose**: `ReasoningEngine` and `InsightsEngine` synthesise explanations *of the score*. Built on top of an inverted score, they would produce fluent, confident, wrong career advice.
- **The root causes sit in Layer 3, not Layer 5**: JD alternative groups ("Python, Go, **or** Java") are parsed as three separate requirements, and no parent/child resolution exists (PostgreSQL does not satisfy SQL), which inflates gap counts and lets the gap penalty dominate the composite score.
- **`AdaptiveScorer` cannot rescue it**: feedback-driven weight tuning corrects *weighting*, not *false gaps*. A garbage gap set would poison the learning loop from day one.

#### Tradeoff

- **Phase 3 slips** by the duration of the fix work. Accepted: doc 01 §7 sets accuracy as the primary success metric, and every downstream layer consumes these outputs.

#### Decision

- New sub-phases **2.6 (Correctness Fixes)** and **2.7 (Latency & Warm-Up)** are inserted into doc 07 and block Phase 3.
- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal

---

### Milestones Are Defined by User-Visible Capability, Not by Layer

#### Context

Doc 07 orders work by architectural layer: six backend phases, with the frontend at Phase 5
and production concerns at Phase 6. Under that ordering the project reaches "80% of phases
complete" while remaining 0% usable by anyone who is not running Python locally. The risk
named by the project owner (2026-08-01) is that NeuroSync becomes "a random ambitious project
that has no destiny and keeps growing" — complexity accumulating faster than capability.

#### Reason

- **Layer-ordered plans have no shipping point**: nothing in doc 07's sequence produces a
  moment where the product is usable. Phases 3, 3.5 and 4 each add intelligence to a system
  that still cannot be opened in a browser.
- **Interest is not a priority signal**: every remaining phase is genuinely interesting, which
  makes "what next?" unanswerable without an external criterion. User-visible capability is
  that criterion.
- **Feedback requires users**: the PRD's learning loop (01 §1, "learns from every decision")
  cannot be validated without real decisions from real people, which requires shipping first.
- **The vision is the destination, not the deliverable**: market intelligence, trajectory
  simulation and human-state modelling are the reason to build v1.0 — not part of it.

#### Tradeoff

- **The intelligence layers slip behind the frontend.** Doc 07's Phase 3 (reasoning, insights,
  state) now falls after the UI in M3. Accepted: a correct, explainable score in a browser is
  more valuable than an elaborate reasoning engine reachable only by `curl`.
- **Doc 07's phase numbering no longer matches execution order.** Mitigated by precedence:
  doc 07 keeps its phases as *work packages*; doc 14 owns *sequencing*.

#### Decision

- [14_EXECUTION_RULES.md](14_EXECUTION_RULES.md) is created and owns the destination and
  milestone sequence: **M1 Trustworthy Core → M2 Usable Product → M3 Learning Loop →
  M4 Career Intelligence**.
- **v1.0 ships at the end of M2**, defined as: a non-author, on a deployed URL, completing a
  real resume-vs-JD analysis and receiving a decision they trust.
- Doc 07 phases are retained as work packages; doc 14 §2.2 governs order.
- `legacy/java_demo/` is declared frozen — out of scope permanently, never read or modified.
- Every change is committed and pushed on completion; completion requires a measurement.
- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal

---

## 2026-08-01

> From this entry onward decisions carry a stable **D-nnn** id so code comments can
> cite them. The six entries above predate the convention and are referenced by title.

### D-007 — Persistence Is PostgreSQL Behind `StateBackend`, Not Redis

#### Context

Doc 12 §2 (Cross-Cutting: State) specifies `state/base.py`, `state/memory_state.py` and
`state/redis_state.py`. None existed. In their absence, feedback accumulated in a list on the
`IntelligenceEngine` instance and analyses in a module-level dict in `api/deps.py` — so every
recorded outcome was destroyed on restart (doc 15 R3, Critical). Doc 15 §4 reviewed the
database design and doc 14 §2.3 moved persistence out of M3 and into **M1**, on the grounds
that the product's central claim — that it learns from outcomes — is false until this is fixed,
and every day it runs unfixed discards the scarcest asset the product can accumulate.

#### Reason

- **Redis is a cache; this data is the asset.** `redis_state.py` was specified for sharing state
  across pods, which is a horizontal-scaling concern the product does not have and will not have
  for years (doc 15 §4: "no database bottleneck at any plausible MVP scale"). What it does have
  is data worth keeping. Durability is the requirement; a shared cache does not supply it.
- **Alembic before the first table.** Doc 09 §4 and doc 15 §13 both say it, and retrofitting
  migrations is painful and always late. There is now a migration and no `create_all` in the
  application path.
- **The interface is what makes it a rule.** `StateBackend` exists so doc 12 §4 Rule 5
  ("StateBackend is the ONLY persistence") is enforceable by review rather than remembered.

#### What was decided

1. **`state/sql_state.py` replaces `state/redis_state.py`** in doc 12 §2 and §10. Redis is
   removed from the file map and from `requirements.txt` — nothing imported it.
2. **Three tables, not doc 09's ten or doc 15's four**: `users`, `analyses`, `feedback`.
   Doc 15 §4 R1 also lists `skill_taxonomy_overrides`; it is **deferred to the backlog**, not
   built. Persisting promoted discoveries would make a promotion permanent, and D2's quarantine
   (2 sightings) is calibrated against a *per-process* lifetime — a noise term that survives
   quarantine once would then never expire. That trade needs its own measurement, and an
   unused table with unused backend methods is a half-built feature (doc 14 R4).
3. **Synchronous SQLAlchemy 2.0.** The service layer is sync CPU-bound code; a single-row INSERT
   is ~1 ms beside a ~260 ms analysis. An async driver would have forced async-ifying the whole
   service layer inside a persistence task.
4. **SQLite is a supported dialect, PostgreSQL is the target.** The same migration and the same
   `SqlState` run on both. This is not a production option — it is what makes the durable path
   testable without a server, which is how `tools/state_probe.py` measures restart survival.
5. **Deviations from doc 09's DDL**, each with a reason, mirrored in `app/db/models.py`:
   - **`VARCHAR(36)` primary keys, not native `UUID`.** `analysis_id` is a truncated UUID
     (`"92bb1053-76d"`, doc 13 §4 D5) and is not a valid UUID value. Typing the column as UUID
     would force a change to the public id format inside the persistence task rather than inside
     D5, which owns the contract.
   - **No `users.password_hash`.** Auth is magic-link (doc 15 §18); a `NOT NULL` column no code
     can fill is a lie in the schema.
   - **`feedback.analysis_id` is nullable.** Doc 08 §3.2 documents `decision_found: false` for
     feedback whose analysis is unknown; a `NOT NULL` FK makes that documented response
     impossible to store. `UNIQUE` is kept — SQL permits repeated NULLs, which gives exactly
     "one outcome per analysis, plus any number of orphan reports".
   - **`feedback` carries a decision snapshot.** Calibration statistics must survive deletion of
     the analysis row under an M2 deletion request, and it removes a join from `/feedback`.
   - **`career_profiles` and `analysis_history` are dropped** (doc 15 §4 R2) — the `analyses`
     JSONB payload plus `created_at` covers both. The four Human-State tables die with doc 14
     §2.2's permanent removal of that layer.
6. **`state_backend=memory` remains the default, and `sql` refuses to start without
   `NEUROSYNC_DATABASE_URL`.** No silent fallback: a downgrade to volatile storage that nobody
   notices is the exact failure this decision exists to end.

#### Tradeoff

- **A managed Postgres is now an operational dependency** for any deployment that matters, at
  roughly $0–20/month (doc 15 §10). Accepted — doc 15 §4: do not self-host, do not build backup
  tooling.
- **The Postgres path is verified by generated DDL, not by a live server** (see doc 13 §4 D6),
  because no PostgreSQL instance exists in the development environment. First deployment must
  run `alembic upgrade head` against a real instance before this is called proven.

#### Decision

- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal
- **Measured by**: `./venv/Scripts/python.exe -m tools.state_probe` — memory loses 1 of 1
  feedback rows across a process restart; sql retains 1 of 1 and finds the prior analysis.

---

### D-008 — Owner-Blocked Work Gets Its Own Register

#### Context

Doc 15 §23 raised seven questions that "cannot be assumed" and require the owner. None has been
answered. Since then the work has accumulated a second, different category of blocker: not
questions but *doors* — a PostgreSQL instance, a domain, DNS records, an email provider, human
raters, five strangers. Doc 15 is a dated board review with its own change log; appending live
operational blockers to it would falsify it as a record of what the board found on 2026-08-01.

The immediate trigger: doc 13 §4 D6 shipped with an honest but permanent-looking caveat — the
PostgreSQL path is verified as generated DDL, not against a live server, because none exists in
the development environment. That is not an engineering problem. It is a fifteen-minute signup
that only the owner can perform, and there was nowhere to write it down.

#### Reason

- **An unanswered question is not free.** It is either a silent assumption or unsequenced work.
  Doc 15 §23 records the questions but not what each one is currently costing, and not what
  assumption is being made in its absence. Both belong next to the question.
- **Blockers were living in session reports.** A report is read once. A register is checked.
- **Doc 14 R3 requires blocked items to stay honest**: "a blocked item left honest is worth more
  than a green tick that lies." Honesty needs an address.
- **Decisions made unilaterally need a review surface.** Doc 14 R4 says finish the item rather
  than block on the owner, which means engineer-made calls accumulate. They are logged here, but
  a log is chronological and grows; the owner needs a short list of *currently unconfirmed* ones.

#### Tradeoff

- **A sixteenth blueprint document**, in a project whose named risk is unbounded growth
  (doc 14 §1). Accepted on the grounds that this one *reduces* work rather than adding it: it
  has no implementation, and it exists to close questions rather than open them. It is a
  living register, not a specification — the first document here that is expected to shrink.
- **Two places now discuss owner questions.** Mitigated by precedence: doc 15 §23 keeps the
  original wording as the board asked it; doc 16 §4 owns the *status* of each answer and points
  back. Same rule as doc 13 vs the blueprints.

#### Decision

- [16_OWNER_ACTIONS.md](16_OWNER_ACTIONS.md) is created and owns everything blocked on the
  owner: external accounts and credentials, legal artifacts, people, and open questions.
- Doc 15 §23 remains the canonical wording of Q1–Q7 and is **not** edited to add answers; doc 16
  §4 tracks their status.
- §6 of doc 16 lists engineer-made decisions awaiting confirmation. **Silence is acceptance** —
  otherwise the register becomes a second blocking queue, which is the thing it exists to drain.
- **Status**: ACCEPTED
- **Owner**: Priyabrata Biswal
