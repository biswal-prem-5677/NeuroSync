# NeuroSync — Product Requirements Document (PRD)

**Version**: 1.0.0  
**Author**: Priyabrata Biswal  
**Date**: June 2026  
**Status**: ACTIVE

---

## 1. Vision

> **NeuroSync is not a resume analyzer. It is a Career Intelligence Engine.**

NeuroSync exists to answer one question no other tool on the market answers well:

> "Given who you are right now, what is the smartest career move you can make — and how do you get there fastest?"

It is a system that *thinks*, not a tool that *matches*. It understands skills semantically, reasons about gaps contextually, simulates futures probabilistically, and learns from every decision it makes.

---

## 2. Problem Statement

### The Problem

Career decisions are made with broken tools:

- **Resume checkers** tell you what's wrong with your resume — not what's wrong with your career strategy.
- **Job portals** show you openings — but can't tell you which ones you actually have a shot at.
- **Skill platforms** teach you skills — but don't know which skill gives you the highest ROI for your target role.
- **ATS systems** are black boxes — candidates have zero insight into why they were rejected.

### The Gap

No existing platform combines:

1. **Deep skill understanding** (semantic, not keyword)
2. **Gap reasoning** (why this gap matters more than that one)
3. **Decision intelligence** (should you apply? what should you learn first?)
4. **Learning from outcomes** (was the recommendation correct? recalibrate)

### What Exists Today

| Platform | What It Does | What It Lacks |
| --- | --- | --- |
| Jobscan | ATS keyword matching | No reasoning, no intelligence, keyword-only |
| LinkedIn | Job suggestions based on profile | No gap analysis, no decision intelligence |
| Resumeworded | Resume scoring | Static rules, no semantic understanding |
| Skillsyncer | Resume-to-JD matching | Hardcoded skill lists, no learning |
| **SCA (our predecessor)** | Resume analysis + predictions | Substring matching, np.mean() fusion, no explainability |

NeuroSync fills the gap between **"what's wrong with my resume"** and **"what should I do with my career."**

---

## 3. Target Users

### Primary

| Persona | Description | Need |
| --- | --- | --- |
| **Job Seekers** | Students, fresh graduates, career changers | "Which jobs should I actually apply to? What should I learn?" |
| **Career Developers** | Working professionals planning next move | "Am I ready for a senior role? What's my biggest gap?" |

### Secondary

| Persona | Description | Need |
| --- | --- | --- |
| **Recruiters** | HR professionals screening candidates | "Which candidates are genuinely qualified vs keyword-stuffed?" |
| **Career Coaches** | Mentors helping clients navigate careers | "Data-backed guidance instead of intuition-based advice" |
| **University Placement Cells** | Placement officers matching students to companies | "Which students are best fits for which companies?" |

### Tertiary (Future)

| Persona | Description | Need |
| --- | --- | --- |
| **Enterprise HR** | Large companies doing talent gap analysis | "Where are our organizational skill gaps?" |
| **EdTech Platforms** | Course providers personalizing learning paths | "What courses should this user take based on their career target?" |

---

## 4. User Personas

### Persona 1: Arjun — The Anxious Final-Year Student

- **Background**: B.Tech CSE, 3rd year, has basic Python/ML projects, no internship
- **Goal**: Land a data science internship at a product company
- **Frustration**: "I apply to 50 jobs, hear back from 2. I don't know what I'm missing."
- **NeuroSync Value**: Tells Arjun exactly which 3 skills to learn in the next 30 days to maximize his shortlist probability for data science roles — with a projected score improvement for each skill.

### Persona 2: Priya — The Career Switcher

- **Background**: 4 years in manual QA, wants to move to DevOps/Cloud
- **Goal**: Transition to a cloud engineering role within 6 months
- **Frustration**: "I see 200 cloud roles on LinkedIn. I don't know which ones I'm close to qualifying for."
- **NeuroSync Value**: Analyzes Priya's current skills against 10 target JDs, identifies the 2 skills that unlock the most roles (e.g., "Learning Kubernetes opens 7/10 of your target roles"), and builds a priority learning roadmap.

### Persona 3: Kavita — The Recruiter

- **Background**: Technical recruiter at a mid-size startup
- **Goal**: Screen 200 applications for a backend engineer role in 2 hours
- **Frustration**: "Half the resumes are keyword-stuffed. I can't tell who actually knows Python at a production level."
- **NeuroSync Value**: Provides a proficiency-weighted score (not just "has Python" but "strong production Python evidence") with explainable reasoning, so Kavita can trust the shortlist.

---

## 5. Core Features

### 5.1 — Resume × JD Analysis Engine (MVP)

> Input: Resume text + Job Description text → Output: Complete intelligence report

| Feature | Description | SCA Comparison |
| --- | --- | --- |
| **4-Layer Skill Extraction** | Taxonomy → NER → Semantic → Embedding Discovery | SCA: substring matching against 200 hardcoded skills |
| **Section-Aware Semantic Similarity** | Weights experience (1.0) > projects (0.9) > skills (0.4) | SCA: flat cosine on entire document |
| **Proficiency-Weighted Scoring** | "Expert Python" counts more than "Basic Python" | SCA: binary present/absent |
| **Cluster-Based Gap Reasoning** | "Missing AWS but you have GCP → shorter learning curve" | SCA: flat list of missing skills |
| **What-If Simulation** | "If you learn Docker, score goes from 62 → 78" | SCA: none |
| **ROI-Ranked Improvement Path** | "Learn AWS first (+14 points, 3 weeks)" | SCA: none |
| **Decision Intelligence** | "APPLY_WITH_PREPARATION (67% shortlist probability)" | SCA: none |

### 5.2 — Feedback & Learning Loop

| Feature | Description |
| --- | --- |
| **Outcome Recording** | "Did you get the interview? Hired? Rejected?" |
| **Weight Recalibration** | Scoring weights adjust based on real outcomes |
| **Taxonomy Growth** | Skills missed by extraction get registered for future |
| **Calibration Drift Detection** | "Scores are 15% too optimistic — adjusting" |

### 5.3 — Market Intelligence (Phase 2)

| Feature | Description |
| --- | --- |
| **Skill Demand Trends** | "Docker demand ↑37% in last 6 months" |
| **Salary Signal** | "Your skill set maps to ₹12-18 LPA market range" |
| **Hiring Velocity** | "Backend roles in Bangalore: 2,400 openings this month" |

### 5.4 — Career Trajectory (Phase 3)

| Feature | Description |
| --- | --- |
| **Growth Tracking** | "You've gained 4 skills in 3 months — above average" |
| **Trajectory Prediction** | "At current rate, you'll reach STRONG_FIT for Senior Backend in 4 months" |
| **Multi-Role Comparison** | "You're closer to DevOps (78%) than ML Engineer (52%)" |

### 5.5 — Human State Intelligence (Phase 2-3)

> Input: Camera (optional) + Learning activity + Project progress + Interview results + Feedback → Output: CareerState + Agent decisions

| Feature | Description |
| --- | --- |
| **Career Momentum Tracking** | "Your growth velocity is 5.7 points/month — above average for career switchers" |
| **Learning Consistency Tracking** | "You've completed 4/5 weekly goals this month — strong consistency" |
| **Burnout Risk Detection** | "Engagement dropped 40% over 3 days — burnout risk HIGH — reducing workload" |
| **Engagement Analysis** | Multi-signal engagement score from learning sessions, project activity, response patterns |
| **Emotion-Aware Learning Guidance** | "Struggling with Kubernetes? Switching to a hands-on lab instead of theory" |
| **Adaptive Roadmap Difficulty** | Agent adjusts learning path difficulty based on completion rate and engagement |
| **Motivation Scoring** | Derived from consistency, engagement, and progress — not self-reported |
| **Career Readiness Assessment** | "You are 78% ready for Senior Backend roles — apply now or wait 3 weeks" |

> **Camera is permanently optional.** The system operates at 95% capability without it. Camera signals are one of 8+ observation sources — not the primary one.

### 5.6 — Full-Stack Frontend (Phase 2-3)

| Feature | Description |
| --- | --- |
| **Dashboard** | Score visualization, gap map, improvement radar |
| **Resume Upload** | PDF/DOCX drag-and-drop with real-time extraction |
| **Career Roadmap View** | Interactive timeline of skill acquisition plan |
| **Simulation Playground** | "What if I learn X?" interactive explorer |

---

## 6. Non-Goals (Explicit Exclusions)

| Non-Goal | Reason |
| --- | --- |
| Resume writing/generation | NeuroSync is analysis intelligence, not content creation |
| Job portal / job aggregation | We analyze fit, not list jobs |
| ATS system replacement | We complement ATS, not replace it |
| Interview preparation | Separate domain — may integrate later |
| Code evaluation / coding challenges | Out of scope for intelligence engine |
| Social networking features | Not a LinkedIn clone |

---

## 7. Success Metrics

### Accuracy Metrics

| Metric | Target | How Measured |
| --- | --- | --- |
| Skill extraction recall | ≥85% | Against manually annotated resume set |
| Skill extraction precision | ≥90% | False positive rate < 10% |
| Score prediction accuracy | ±10 points of human recruiter | A/B test against recruiter panel |
| Shortlist probability calibration | Within 15% of actual outcome | Feedback loop over 500+ analyses |

### Usage Metrics

| Metric | Target | Timeline |
| --- | --- | --- |
| Analyses per day | 100+ | Month 3 |
| Feedback submission rate | >20% of analyses | Month 3 |
| Repeat users | >40% return within 7 days | Month 6 |

### System Metrics

| Metric | Target |
| --- | --- |
| API latency (without LLM) | <500ms p95 |
| API latency (with LLM) | <3500ms p95 |
| Uptime | 99.5%+ |
| Cold start time | <30 seconds |

---

## 8. Product Roadmap

```text
Phase 1 — CORE ENGINE (Current)
├── 4-layer skill extraction ✅
├── 3-layer semantic similarity ✅
├── Cluster-based gap analysis ✅
├── Decision engine with simulations ✅
├── REST API (analyze/health/feedback) ✅
├── 294-skill taxonomy ✅
└── Startup validation + end-to-end test ⬜

Phase 2 — INTELLIGENCE EXPANSION (Next 4 weeks)
├── File parser (PDF/DOCX upload)
├── Reasoning engine (standalone evidence chains)
├── Insights engine (SWOT-style outputs)
├── Feedback processor (full learning loop)
├── State layer (memory → Redis persistence)
├── Market intelligence engine (skill demand data)
├── Adaptive scorer (learnable weights)
└── Formal response models

Phase 3 — FRONTEND + USER EXPERIENCE (Month 2-3)
├── React/Next.js dashboard
├── Interactive simulation playground
├── Career roadmap visualization
├── Resume upload with drag-and-drop
├── Real-time analysis feedback
└── Mobile-responsive design

Phase 4 — SCALE + LEARN (Month 3-6)
├── Redis-backed state for horizontal scaling
├── Trained scoring model (regression on feedback data)
├── Career trajectory engine
├── LLM-enhanced reasoning (optional Gemini/OpenAI)
├── Multi-role comparison
└── API rate limiting + auth

Phase 5 — PLATFORM (Month 6+)
├── Multi-tenant architecture
├── Recruiter portal
├── Batch analysis API
├── Webhook integrations
├── Analytics dashboard
└── SaaS billing
```

---

## 9. Competitive Analysis

| Dimension | Jobscan | Resumeworded | LinkedIn | SCA | **NeuroSync** |
| --- | --- | --- | --- | --- | --- |
| Skill matching | Keyword | Keyword | ML-assisted | Keyword + TF-IDF | **Semantic + NER + Embedding Discovery** |
| Gap intelligence | List of missing keywords | Generic tips | None | Flat list | **Prioritized + Reasoned + Simulated** |
| Explainability | None | Partial | None | None | **Full evidence chains** |
| Decision guidance | "Score: 72%" | "Add these keywords" | "You might like this job" | "Matched/Not matched" | **"Apply with preparation. Learn AWS first (+14 pts, 3 weeks)"** |
| Learning loop | None | None | Implicit (engagement) | None | **Explicit feedback → weight recalibration** |
| Proficiency detection | Binary (has/hasn't) | Binary | Endorsement count | Binary | **Context-based 0-1 proficiency** |
| Market context | None | None | Partial | None | **Skill demand trends + salary signals** |
| Pricing | $49/month | $29/month | $30/month (Premium) | Free (hackathon) | **Free core, Premium features** |

---

## 10. Why NeuroSync Exists

### The Core Belief

Career decisions are too important to be made with broken tools. A student choosing between "learn Docker" and "learn Kubernetes" shouldn't rely on Reddit threads — they should have a system that knows:

1. Which skill their target role demands more
2. Which skill has higher market demand
3. Which skill builds faster on their existing knowledge
4. Which skill improves their score more for this specific JD

### The Differentiator

Every other tool stops at "what's wrong." NeuroSync tells you **"what to do next and why."**

- Jobscan says: "Your resume is 72% matched."
- NeuroSync says: "Your resume is 72% matched. Learning AWS would push you to 86%. AWS has ↑37% demand growth. You already know GCP, so AWS will take ~3 weeks. Your shortlist probability goes from 55% to 78%. Action: Learn AWS first, then apply."

### The Name

**Neuro** = intelligence, neural processing, brain-like reasoning  
**Sync** = synchronization between human career state and market reality  

NeuroSync synchronizes what you are with what the market needs, and shows you the fastest path to alignment.

---

*This document is the source of truth for what NeuroSync is. All technical decisions trace back to this PRD.*
