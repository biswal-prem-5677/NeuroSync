# NeuroSync — Intelligence Blueprint

**Version**: 1.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE

> **This is the most important document in the project.**  
> It answers: *How does NeuroSync think?*

---

## 1. Intelligence Philosophy

### The Core Principle

> **"Every score must be explainable. Every recommendation must be reasoned. Every decision must be improvable."**

NeuroSync is not a pipeline that produces numbers. It is a **reasoning system** that:

1. **Observes** — extracts signals from unstructured text
2. **Understands** — builds semantic understanding of what the candidate knows and what the role needs
3. **Reasons** — computes why gaps matter, not just that they exist
4. **Decides** — makes probabilistic recommendations with confidence bounds
5. **Learns** — adjusts its own weights based on real-world outcomes

### SCA vs NeuroSync Intelligence

```text
SCA (What it was):
  Input → Extract → Compare → Score → Output
  (Linear, stateless, no reasoning, no learning)

NeuroSync (What we build):
  Input → Extract → Understand → Reason → Predict → Decide → Explain → Learn → Evolve
  (Multi-layered, stateful, reasoned, self-improving)
```

---

## 2. The Seven Intelligence Layers

```text
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 8: ADAPTIVE LEARNING                   │
│              System improves with every interaction              │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 7: DECISION INTELLIGENCE               │
│          Apply? When? What to learn? Expected outcome?          │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 6: PREDICTION INTELLIGENCE              │
│     Burnout risk, dropout risk, interview success, readiness     │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 5: HUMAN STATE INTELLIGENCE        ★    │
│       Career state, momentum, engagement, burnout, readiness    │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 4: MARKET INTELLIGENCE                 │
│           Skill demand trends, salary signals, velocity          │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 3: GAP INTELLIGENCE                    │
│      Priority reasoning, cluster analysis, impact simulation     │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 2: SEMANTIC UNDERSTANDING               │
│    Section-aware similarity, chunk alignment, skill context       │
├─────────────────────────────────────────────────────────────────┤
│                    LAYER 1: SKILL EXTRACTION                    │
│       Taxonomy + NER + Semantic Matching + Embedding Discovery   │
└─────────────────────────────────────────────────────────────────┘
```

Each layer builds on the layer below. No layer operates in isolation.

> **Layer 5 (Human State Intelligence) is the key upgrade** — it transforms NeuroSync from "Resume Intelligence" to "Human + Career Intelligence" by adding behavioral signals, career state modeling, and predictive capabilities.

---

## 3. Layer 1 — Skill Extraction (Perception)

> **Question answered: "What skills does this person have? What skills does this role need?"**

### The 4-Layer Extraction Architecture

```text
                    Input Text
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │ Layer 1a │  │ Layer 1b │  │ Layer 1c │
    │ Taxonomy │  │   NER    │  │ Semantic │
    │ Matching │  │  (spaCy) │  │ Cross-Doc│
    │ (Fast)   │  │ (Discover│  │ (Deep)   │
    └────┬─────┘  └────┬─────┘  └────┬─────┘
         │             │             │
         └──────┬──────┴─────────────┘
                ▼
         ┌──────────┐
         │ Layer 1d │
         │ Embedding│
         │ Discovery│
         │ (Unknown │
         │  Skills) │
         └────┬─────┘
              ▼
      ExtractionResult
      (deduplicated,
       confidence-scored,
       section-aware)
```

### What Makes This Different from SCA

| Aspect | SCA | NeuroSync |
| --- | --- | --- |
| **Skill list** | 200 hardcoded strings | 294-skill taxonomy with aliases + runtime discovery |
| **Matching** | `if skill in text.lower()` | Normalized matching → NER → Semantic cosine → Embedding proximity |
| **Unknown skills** | Ignored forever | Discovered via embedding proximity, registered at runtime |
| **Proficiency** | Binary (has/hasn't) | 0-1 proficiency from context ("expert in" → 0.9, "basic" → 0.3) |
| **Section awareness** | None | Skills in Experience section weighted higher than Skills section |
| **Evidence** | None | Each skill tagged with: match_method, confidence, sections, occurrences |

### Key Design Decisions

- **Proficiency is inferred, not declared**: "Built production ML pipelines" → proficiency 0.85, "Python (basic)" → 0.30
- **Section weighting**: Experience (1.0) > Projects (0.9) > Summary (0.7) > Skills list (0.4) > Education (0.3)
- **Embedding discovery threshold**: 0.65 (tunable) — prevents noise while catching real skills
- **Blacklist**: Common English words that survive NER but aren't skills ("Team", "System", "Data")

---

## 4. Layer 2 — Semantic Understanding (Comprehension)

> **Question answered: "How well does this resume speak the language of this job?"**

### The 3-Layer Semantic Architecture

```text
Layer 2a: Section-Aware Embedding
  Experience section → embed → compare to JD embedding
  Projects section → embed → compare to JD embedding
  Each section weighted by importance

Layer 2b: Chunk-Level Similarity Matrix
  Resume chunks × JD chunks → similarity matrix
  Best match per JD chunk → coverage score
  Captures local alignment even if overall doc diverges

Layer 2c: Skill-Aligned Context Depth
  For each JD skill found in resume:
    Extract ±150 chars around mention
    Embed context → compare to "extensive experience with {skill}"
    Measures HOW DEEPLY a skill is discussed, not just mentioned
```

### Aggregation Formula

```text
overall = section_weighted * 0.45
        + chunk_best * 0.25
        + skill_alignment * 0.30
```

### Why This Matters

- **SCA**: `cosine_similarity(embed(resume), embed(jd))` = one number, no insight
- **NeuroSync**: Knows WHICH sections align, WHERE the strongest matches are, and HOW deeply skills are discussed

---

## 5. Layer 3 — Gap Intelligence (Reasoning)

> **Question answered: "Which missing skills matter most, and why?"**

### The Reasoning Engine

For each missing skill, NeuroSync doesn't just say "missing." It reasons:

```text
Evidence Chain for "Missing: Kubernetes"
├── Frequency Signal: mentioned 4× in JD (weight: 0.3)
├── Position Signal: appears in first paragraph (weight: 0.2)  
├── Category Signal: infrastructure skill → core for DevOps (weight: 0.15)
├── Related Skill Credit: has Docker (similarity: 0.78) → partial credit (weight: -0.1)
├── Taxonomy Importance: weight 0.85 (critical infrastructure skill)
└── SYNTHESIZED: Priority = CRITICAL
    Reasoning: "Kubernetes is mentioned 4× and appears in the opening requirements.
    Your Docker experience (related, 78% similar) means a shorter learning curve,
    but K8s is a distinct deployment orchestration skill that requires dedicated study.
    Estimated learning time: 3-4 weeks given your Docker foundation."
```

### Priority Formula

```python
priority_score = (
    frequency_weight * 0.25
    + position_weight * 0.15
    + category_weight * 0.15
    + taxonomy_importance * 0.30
    - related_skill_credit * 0.15
)
```

### Gap Clustering

Skills aren't analyzed in isolation. They're grouped into clusters:

```text
Cluster: "Cloud/Infrastructure"
├── Missing: Kubernetes (CRITICAL)
├── Missing: Terraform (HIGH)
├── Present: Docker ✓
├── Present: AWS EC2 ✓
└── Cluster Gap Score: 0.45 (you have foundations but lack orchestration)
```

This enables insights like: "You have cloud foundations (Docker, EC2) but lack the orchestration layer (Kubernetes, Terraform). This cluster gap is the biggest barrier to DevOps roles."

---

## 6. Layer 4 — Market Intelligence (Context)

> **Question answered: "What does the market actually value right now?"**

### Data Signals

| Signal | Source | Impact |
| --- | --- | --- |
| **Skill Demand Trend** | Job posting analysis | "Kubernetes demand ↑37% in 6 months" → upgrades gap priority |
| **Salary Signal** | Market data | "Your skills map to ₹12-18 LPA range" → anchors expectations |
| **Hiring Velocity** | Regional data | "Backend roles in Bangalore: 2,400 openings this month" → urgency signal |
| **Skill Combination Value** | Co-occurrence analysis | "Python + AWS + Docker = premium combination" → suggests bundles |

### Integration Point

Market intelligence feeds INTO gap analysis:

- Static gap: "Kubernetes is mentioned in JD → it's important"
- Market-enhanced gap: "Kubernetes is mentioned in JD AND demand is ↑37% across the market → it's CRITICAL and increasingly so"

### Implementation Phases

- **Phase 1 (Now)**: Static curated JSON snapshots
- **Phase 2**: API integrations (job posting analysis)
- **Phase 3**: Real-time market data providers

---

## 7. Layer 5 — Career Intelligence (Trajectory)

> **Question answered: "Where are you going, and how fast?"**

### Time Dimension

NeuroSync doesn't just analyze a snapshot — it tracks trajectories:

```text
Snapshot 1 (Jan): Skills=[Python, SQL, Pandas], Score for "Data Scientist"=52
Snapshot 2 (Mar): Skills=[Python, SQL, Pandas, TensorFlow, Docker], Score=71
Snapshot 3 (Jun): Skills=[Python, SQL, Pandas, TensorFlow, Docker, AWS, MLOps], Score=86

Growth velocity: 5.7 score points/month
Trajectory prediction: STRONG_FIT for "Data Scientist" by August
```

### Career Intelligence Outputs

- **Growth Velocity**: skills per month, score improvement rate
- **Trajectory Prediction**: estimated time to target role readiness
- **Multi-Role Comparison**: "You're closer to DevOps (78%) than ML Engineer (52%)"
- **Skill ROI Across Roles**: "Learning AWS helps in 7 of your 10 target roles"

---

## 7.5. Layer 5 — Human State Intelligence (The Human Layer) ★ NEW

> **Question answered: "What is the human behind the resume actually experiencing?"**

This is the layer that transforms NeuroSync from a Resume Intelligence system into a **Human + Career Intelligence** platform. It observes signals beyond text — learning behavior, project activity, interview results, engagement patterns, and optionally camera-derived signals — to build a unified **CareerState** representation.

### Observation Sources

Every signal entering this layer carries an `ObservationSource` tag. The agent doesn't care WHERE a signal came from — it reasons over CareerState.

```text
ObservationSource Enum:
  RESUME           → Skill signals from resume analysis
  JD               → Role requirement signals
  FEEDBACK         → Hiring outcomes (interview/hired/rejected)
  LEARNING         → Course completion, session duration, engagement
  PROJECT          → Code commits, portfolio activity, project completion
  INTERVIEW        → Mock/real interview performance signals
  MARKET           → Skill demand, salary, hiring velocity
  CAMERA           → Attention, focus, engagement (OPTIONAL, consent-required)
```

> **Camera is permanently optional.** The system operates at 95% capability without camera signals. Most users will use resume + learning + projects + feedback + interview results and never enable a webcam.

### Signal → State Architecture

```text
Raw Signals (noisy, source-specific)
│
├── CAMERA: attention_low, focus_dropping
├── LEARNING: completion_rate=0.3, session_abandoned
├── PROJECT: no_commits_7_days
├── INTERVIEW: communication_weak
├── FEEDBACK: rejected_3_consecutive
│
│   AgentObservation records (source-tagged, timestamped)
│
▼
Human State Intelligence Engine
│
│   Aggregates signals across sources
│   Derives stable state (NOT raw emotions)
│   Detects state transitions
│
▼
CareerState (stable, derived, decision-ready)
│
│   state = "struggling"       (derived)
│   NOT emotion = "frustrated"  (raw)
│
▼
Agent Decision Engine
```

### CareerState Model

The unified state representation that all agent decisions consume:

```python
class CareerState(BaseModel):
    user_id: str
    confidence_score: float          # 0.0 - 1.0 — how confident in their abilities
    momentum_score: float            # 0.0 - 1.0 — rate of improvement
    engagement_score: float          # 0.0 - 1.0 — active participation level
    consistency_score: float         # 0.0 - 1.0 — regularity of effort
    growth_velocity: float           # score points/month
    burnout_risk: float              # 0.0 - 1.0 — predicted burnout probability
    interview_readiness: float       # 0.0 - 1.0 — can they pass an interview?
    career_readiness: float          # 0.0 - 1.0 — should they apply now?
    updated_at: datetime
```

> **Agent decisions operate on CareerState, never on raw signals.** Raw signals are noisy. CareerState is stable.

### StateObservation

Derived observations (NOT raw events):

```python
class StateObservation(BaseModel):
    id: str
    user_id: str
    signal: str                      # "engagement_low", "completion_drop", "focus_high"
    derived_from: list[ObservationSource]  # [CAMERA, LEARNING]
    confidence: float                # 0.0 - 1.0
    timestamp: datetime
```

### StateTransition

Agent memory of growth — tracks before/after:

```python
class StateTransition(BaseModel):
    id: str
    user_id: str
    previous_state: CareerState
    new_state: CareerState
    reason: str                      # "3 consecutive learning sessions completed"
    timestamp: datetime
```

Example:

```text
StateTransition:
  confidence:  0.42 → 0.68  (+0.26)
  momentum:   0.31 → 0.76  (+0.45)
  burnout_risk: 0.72 → 0.35 (-0.37)
  reason: "Completed 3 learning modules in 5 days after roadmap adjustment"
```

### Prediction Layer ★

The Human State Engine doesn't just observe — it **predicts**:

```text
Observe → Understand → PREDICT → Decide → Act → Learn
                         │
                         ├── burnout_probability: 0.78
                         ├── dropout_probability: 0.34
                         ├── interview_success_probability: 0.62
                         └── skill_completion_probability: 0.81
```

**Predictions trigger agent actions BEFORE problems happen:**

| Prediction | Threshold | Agent Action |
| --- | --- | --- |
| `burnout_probability > 0.7` | HIGH | Pause roadmap, reduce workload, switch to easier module |
| `dropout_probability > 0.5` | MEDIUM | Send encouragement, highlight recent wins, add gamification |
| `interview_success_probability < 0.3` | LOW | Defer "apply now" recommendation, add prep modules |
| `skill_completion_probability < 0.4` | LOW | Simplify current module, add reinforcement exercises |

### Example: Burnout Detection

```text
User is learning: AWS, Docker, Kubernetes

Day 1-4: Normal engagement
  LEARNING: completion_rate=0.85, session_duration=45min
  CAMERA (if enabled): attention=high, focus=steady

Day 5-7: Engagement drop
  LEARNING: completion_rate=0.30, session_duration=12min, abandoned=2
  PROJECT: no_commits_3_days
  CAMERA (if enabled): attention=low, focus=dropping

Human State Engine detects:
  CareerState.engagement:  0.82 → 0.34
  CareerState.burnout_risk: 0.15 → 0.78
  Prediction: burnout_probability = 0.82

Agent Decision:
  1. Pause Kubernetes module
  2. Switch to hands-on Docker lab (easier, more engaging)
  3. Reduce daily target from 2 hours to 45 minutes
  4. Add reinforcement: "You've mastered 12 concepts this week — great progress"

StateTransition recorded:
  burnout_risk: 0.15 → 0.78
  reason: "Engagement dropped 60% over 3 days across LEARNING + PROJECT signals"
```

---

## 8. Layer 6 — Decision Intelligence (Action)

> **Question answered: "What should I actually do?"**

### The Decision Model

```text
Inputs:
├── Composite Score (from scoring engine)
├── Gap Analysis (from gap intelligence)
├── Market Context (from market intelligence)
├── Career Trajectory (from trajectory engine)
└── Historical Accuracy (from feedback loop)

Decision Output:
├── Recommendation: STRONG_APPLY | APPLY | APPLY_WITH_PREPARATION | UPSKILL_THEN_APPLY | DO_NOT_APPLY
├── Confidence: 0-100%
├── Shortlist Probability: 0-100%
├── Top 3 What-If Simulations
├── ROI-Ranked Improvement Path (top 5 skills to learn)
├── Evidence Chain (every factor explained)
└── Time-to-Ready Estimate
```

### Recommendation Logic (Current: Heuristic → Future: Probabilistic)

```text
Phase 1 (Current):
  score >= 80 AND critical_gaps == 0 → STRONG_APPLY
  score >= 65 AND critical_gaps <= 1 → APPLY
  score >= 50 AND critical_gaps <= 2 → APPLY_WITH_PREPARATION
  score >= 35 AND shortlist_prob >= 15% → UPSKILL_THEN_APPLY
  else → DO_NOT_APPLY

Phase 2 (With feedback data):
  Logistic regression on (score, gap_count, semantic_score, market_demand) → P(shortlist)
  Threshold P(shortlist) for recommendations calibrated against real outcomes

Phase 3 (With sufficient data):
  Learned decision model trained on feedback outcomes
  Per-industry calibration
```

### What-If Simulation

For each critical/high gap, the system runs a FULL scoring pipeline simulation:

```text
"If you learn AWS":
  1. Add AWS to your skill set (proficiency: 0.7)
  2. Recompute weighted overlap
  3. Recompute gap penalty (one fewer gap)
  4. Recompute composite score
  5. Re-estimate shortlist probability
  → Score: 62 → 78 (+16)
  → Fit: POTENTIAL_FIT → GOOD_FIT
  → Shortlist Probability: 35% → 64%
```

---

## 9. Layer 7 — Adaptive Learning (Evolution)

> **Question answered: "How does the system get smarter over time?"**

### The Learning Loop

```text
User submits resume + JD
        ↓
NeuroSync produces Decision (score=72, recommendation=APPLY, shortlist_prob=55%)
        ↓
User follows recommendation
        ↓
Outcome: INTERVIEW (or REJECTED or HIRED or GHOSTED)
        ↓
Feedback recorded
        ↓
System learns:
├── Shortlist probability was calibrated correctly? (72→interview at 55% prob ✓)
├── Scoring weights need adjustment? (semantic was underweighted?)
├── Gap priorities accurate? (the "CRITICAL" gap didn't matter?)
├── New skills discovered? (candidate had "Terraform" — not in taxonomy)
└── Recalibration triggered when N≥50 feedbacks accumulated
```

### Weight Evolution

```text
Day 1:    weights = {semantic: 0.40, skill: 0.35, gap: 0.25}  ← config defaults
Week 4:   weights = {semantic: 0.38, skill: 0.37, gap: 0.25}  ← 50 feedbacks
Month 3:  weights = trained_model.predict(components)          ← 500+ feedbacks
```

### Taxonomy Evolution

```text
Day 1:    294 skills (curated JSON)
Week 2:   294 + 12 runtime-discovered skills (from embedding proximity)
Month 1:  294 + 47 skills (runtime) + 8 promoted to permanent (from feedback)
Month 6:  500+ skills (curated + discovered + feedback-validated)
```

---

## 10. Intelligence Data Flow (Complete)

```text
Resume Text + JD Text + Behavioral Signals + Learning Events + Feedback
        │
        ▼
┌─────────────────────────┐
│   TEXT PREPROCESSING    │  clean, normalize, section-detect, chunk
└───────────┬─────────────┘
            │
   ┌────────┼────────┐
   ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────────┐
│Resume│ │  JD  │ │ Semantic │    LAYER 1 + 2
│Skills│ │Skills│ │Similarity│    (Extraction + Understanding)
└──┬───┘ └──┬───┘ └────┬─────┘
   │        │          │
   └────┬───┘          │
        ▼              │
┌──────────────┐       │
│  GAP ANALYSIS│◄──────┘         LAYER 3 (Gap Intelligence)
│  (Reasoning) │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   MARKET     │                 LAYER 4 (Market Intelligence)
│ INTELLIGENCE │
└──────┬───────┘
       │
       ▼
┌────────────────────────┐
│ HUMAN STATE INTELLIGENCE │     LAYER 5 ★ NEW
│  (CareerState derivation) │
│  + Prediction Layer       │
│                          │◄──── Camera, Learning, Project,
│  Signals → Observations   │       Interview, Feedback signals
│  Observations → State     │
│  State → Predictions      │
└────────────┬───────────┘
             │
             ▼
┌──────────────┐
│  COMPOSITE   │
│   SCORING    │◄──── Adaptive Weights (Layer 8)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  DECISION    │                 LAYER 7 (Decision Intelligence)
│   ENGINE     │
│  + Reasoning │◄──── CareerState (from Layer 5)
│  + Simulation│
└──────┬───────┘
       │
       ▼
   Decision
   (recommendation + evidence + improvement path + CareerState)
       │
       ▼
┌──────────────┐
│  FEEDBACK    │                 LAYER 8 (Adaptive Learning)
│    LOOP      │
│ (outcomes →  │
│  recalibrate)│
└──────────────┘
```

---

## 11. Intelligence Principles (Non-Negotiable)

1. **No magic numbers without explanation**: Every threshold, weight, and score must have a documented rationale.

2. **No template reasoning**: Reasoning is always synthesized from evidence chains, never hardcoded strings.

3. **Graceful degradation, not failure**: If semantic engine crashes, system still works with taxonomy + NER. Score confidence drops, but never crashes.

4. **Proficiency > Presence**: "Has Python" is worth less than "Expert in Python." Every skill carries a proficiency signal.

5. **Gaps are opportunities, not failures**: Gap analysis produces improvement paths, not just deficiency lists.

6. **Market context > Static rules**: A skill's importance is partly determined by real-world demand, not just JD frequency.

7. **Every decision is simulatable**: Users can ask "what if I learn X?" and get a real answer, not a guess.

8. **The system learns**: Feedback doesn't just get logged — it changes how the system weights, scores, and prioritizes.

9. **Careers are not emotions**: CareerState (confidence, momentum, engagement) is the decision surface — not raw emotions (happy, sad, angry). Derived state is stable. Raw signals are noisy.

10. **Predict before it happens**: Burnout, dropout, interview failure — the system should predict these and intervene BEFORE they occur. That is where the real intelligence appears.

---

*This blueprint is the brain architecture of NeuroSync. Every service, every algorithm, every design decision traces back to these seven layers.*
