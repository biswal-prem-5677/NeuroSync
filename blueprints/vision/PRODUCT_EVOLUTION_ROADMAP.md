# NeuroSync — Product Evolution Roadmap

**Product Horizon**: 2026 - 2029  
**Core Mission**: Transition candidate assessment from reactive keyword searching to active, predictive, and agentic career engineering.

---

## Roadmap Overview

```text
    [ V1: Resume Intelligence ]
                 │
                 ▼
    [ V2: Career + Human Intelligence ]
                 │
                 ▼
    [ V3: Market Intelligence ]
                 │
                 ▼
      [ V4: Career Copilot ]
                 │
                 ▼
 [ V5: Autonomous Career Agent ]
```

---

## V1 — Resume Intelligence (Current Foundation)

**Focus**: Accurate, explainable parsing, gap identification, and matching logic.

### 🚀 Capabilities (V1)

* **Hybrid 4-Layer Skill Extraction**: Standardized taxonomy mapping, spaCy Named Entity Recognition (NER), cross-document semantic extraction, and automatic skill discovery.
* **Explainable Gap Analytics**: Explain why a gap matters based on industry weights and resume context rather than template strings.
* **Score Simulation Playground**: Interactive mock additions to see instant scores and shortlist probability deltas.
* **ROI-Ranked Upskilling**: Order missing skills by fit impact vs. estimated learning time.

### 📊 Data & Models (V1)

* 294-item seed skill taxonomy.
* Local spaCy NER pipelines and lightweight sentence-transformers (`all-MiniLM-L6-v2`).
* Static priority heuristics.

---

## V2 — Career + Human Intelligence (Dynamic Growth, Persistence, & Human State)

**Focus**: Track user development over time, build closed-loop personalization, and understand the human behind the resume.

### 🚀 Capabilities (V2)

* **Persistent User Profiles & Growth Vectors**: Log scans historically to analyze a user's skill growth velocity and scoring trajectory.
* **Adaptive Weight Scoring**: Adjust importance weights automatically based on recorded feedback (Hired / Interview / Rejected).
* **Targeted Upskilling Roadmaps**: Generate multi-week learning paths complete with curated resources (books, docs, videos) for specific target jobs.
* **SWOT Engine Integration**: Automate structured Strengths, Weaknesses, Opportunities (stack completions), and Threats (skill deprecation) matrices.
* **Human State Intelligence** ★ NEW:
  * **CareerState Modeling**: Unified state representation (confidence, momentum, engagement, consistency, growth_velocity, burnout_risk, interview_readiness, career_readiness)
  * **ObservationSource Signals**: 8 signal sources (Resume, JD, Feedback, Learning, Project, Interview, Market, Camera)
  * **Career Momentum Tracking**: Growth velocity, consistency scoring, engagement analytics
  * **Burnout Detection & Prevention**: Prediction layer detecting burnout/dropout probability before they happen
  * **Adaptive Roadmap Difficulty**: Agent adjusts learning path based on engagement and completion rate
  * **Career Readiness Assessment**: "Should I apply now?" — a different question than "Can I pass an interview?"
  * **Camera Integration** (optional): Attention and focus signals — permanently optional, consent-required, GDPR-ready

### 📊 Data & Models (V2)

* PostgreSQL relational schemas (Users, Profiles, Analyses, History, Feedback).
* Simple feedback-recalibration models (regression weights based on outcomes).

---

## V3 — Market Intelligence (Real-Time Signals)

**Focus**: Connect matching logic with live macroeconomic trends and pricing data.

### 🚀 Capabilities (V3)

* **Live Job Market Ingestion**: Automatically update taxonomy weights based on scrapers assessing active job postings.
* **Skill Demand Volatility Indexes**: Track if a skill is in high demand (e.g., PyTorch ↑34%) or deprecating (e.g., older frameworks).
* **Salary Signals**: Project candidate salary valuation based on specific skill combinations.
* **Location-Based Dynamics**: Calibrate matching scores to regional demands and remote availability variations.

### 📊 Data & Models (V3)

* Integrations with career portals and hiring aggregator APIs.
* Timeseries data store tracking skill popularity and demand frequencies.

---

## V4 — Career Copilot (Interactive Refinement)

**Focus**: Conversational guidance and active resume enhancement.

### 🚀 Capabilities (V4)

* **Interactive AI Career Chatbot**: Allow users to query their gap analysis, ask for specific roadmap adjustments, and iterate in real-time.
* **Contextual Resume Writing Assistant**: LLM-guided suggestions to rephrase experience bullet points to match the semantic patterns of specific job descriptions.
* **Mock Interview Simulator**: Conduct coding and behavioural tests tailored to the specific gaps identified in target roles.
* **HR Communication Suite**: Auto-generate customized application emails and cover letters matching extracted keywords.

### 📊 Data & Models (V4)

* Large Language Models (Gemini Pro / Claude 3.5 Sonnet) with fine-tuned RAG pipelines.
* Conversational state memory.

---

## V5 — Autonomous Career Agent (Agentic Automation)

**Focus**: Set-and-forget job hunting and automated upskilling loop.

### 🚀 Capabilities (V5)

* **Autonomous Job Sourcing Agents**: Continuously scrape and rank new roles based on dynamic fit updates, sending applications on behalf of the user.
* **Micro-Learning Automation**: Assemble personalized short-course modules on missing skills by curating code sandbox exercises and learning components.
* **Automated Portfolio Builder**: Propose, structure, and verify custom Git projects that demonstrate the user's growing competencies in gap areas.
* **Direct Talent Portal Synced Agents**: Direct negotiation support, routing recruiter inquiries directly into user-validated response scripts.

### 📊 Data & Models (V5)

* Autonomous multi-agent coordination frameworks (LangGraph, CrewAI).
* Multi-modal models verifying completed portfolio projects.
