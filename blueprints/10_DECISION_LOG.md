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
