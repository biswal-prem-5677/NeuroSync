# 🔬 Smart Career Advisor — Zero-Loss Technical Blueprint (Part 1/3)

## System Identity & Metadata

| Attribute | Value |
| --- | --- |
| **Project Name** | Smart Career Advisor |
| **Codename** | CareerMind |
| **Type** | Full-Stack AI Career Decision Engine |
| **Architecture** | Bifurcated Client-Server (React SPA ↔ FastAPI REST) |
| **Legacy Frontend** | Streamlit (retained at `app/main.py`, port 8501) |
| **Primary Frontend** | React 19 + Vite 7 + TailwindCSS 4 (port 5173) |
| **Backend** | FastAPI + Uvicorn (port 8000) |
| **ML Runtime** | XGBoost, scikit-learn, joblib |
| **LLM Provider** | Google Gemini (via `google-generativeai`) |
| **Voice AI** | Retell AI (WebRTC SDK) |
| **NLP Engine** | spaCy (en_core_web_sm), NLTK |
| **Auth** | Custom OTP via SMTP + PBKDF2 password hashing |
| **Persistence** | JSON files (users.json, user_activity.json) |
| **Package Manager** | pip (backend), npm (frontend) |

---

## 1. High-Level Architecture

```text
┌──────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │ React SPA    │  │ Retell Voice │  │ Streamlit (Legacy)     │ │
│  │ :5173        │  │ WebRTC SDK   │  │ :8501                  │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬─────────────┘ │
└─────────┼────────────────┼───────────────────────┼──────────────┘
          │ Vite Proxy     │ WebRTC               │ Direct
          │ /api → :8000   │                      │
┌─────────▼────────────────▼───────────────────────▼──────────────┐
│                     FastAPI Backend (:8000)                       │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────────┐ │
│  │ Auth    │ │ ML Pred  │ │ LLM Orch │ │ File Processing     │ │
│  │ Module  │ │ Pipeline │ │ (Gemini) │ │ (PDF/DOCX/TXT)      │ │
│  └────┬────┘ └────┬─────┘ └────┬─────┘ └─────────┬───────────┘ │
│       │           │            │                  │              │
│  ┌────▼────┐ ┌────▼─────┐ ┌───▼──────┐ ┌────────▼──────────┐  │
│  │users    │ │.pkl      │ │Gemini API│ │PyPDF2, python-docx│  │
│  │.json    │ │models    │ │(Remote)  │ │spaCy NER          │  │
│  └─────────┘ └──────────┘ └──────────┘ └───────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow Summary

1. **Frontend → Backend**: All API calls route through Vite's dev proxy (`/api` → `http://localhost:8000`)
2. **Backend → LLM**: `llm_utils.py` manages Gemini API key rotation + model fallback
3. **Backend → ML**: `.pkl` model files loaded at startup via `joblib`
4. **Backend → Persistence**: JSON file reads/writes for users and activity logs
5. **Backend → External**: Retell AI (voice), SMTP (email OTP)

---

## 2. Complete Directory Structure

```text
Smart-Career-Advisor/
├── .devcontainer/
│   └── devcontainer.json          # GitHub Codespaces config (Python 3.11, Streamlit auto-start)
├── .streamlit/
│   └── config.toml                # Streamlit config: CORS disabled, no usage stats
├── app/
│   └── main.py                    # [513 lines] Legacy Streamlit frontend (resume analyzer UI)
├── backend/
│   ├── .env                       # Environment secrets (GEMINI_API_KEY, EMAIL_USER, etc.)
│   ├── main.py                    # [2212 lines] PRIMARY FastAPI app — ALL API routes
│   ├── users.json                 # User credential store {email: {email, password_hash}}
│   └── user_activity.json         # Activity log per user (auto-created by activity_logger)
├── frontend/
│   ├── package.json               # React 19, Vite 7, TailwindCSS 4, Recharts, Retell SDK
│   ├── vite.config.js             # Dev proxy /api→:8000, TailwindCSS plugin, HMR config
│   ├── src/
│   │   ├── main.jsx               # React entry point (StrictMode → App)
│   │   ├── index.css              # Global CSS: dark theme, glassmorphism, animations
│   │   ├── App.jsx                # [319 lines] Root component: auth gate, routing, sidebar
│   │   ├── api/
│   │   │   └── api.js             # [349 lines] Axios API client with fallback data
│   │   ├── context/
│   │   │   ├── ReportCardContext.jsx  # Feature usage tracking (localStorage-backed)
│   │   │   └── VisualEffectsContext.jsx # Snowfall + AntiGravity toggle state
│   │   ├── components/
│   │   │   ├── ChatBot.jsx        # [324 lines] AI job search chatbot with typewriter effect
│   │   │   ├── VoiceAssistant.jsx # [140 lines] Retell AI WebRTC voice assistant
│   │   │   ├── FileUpload.jsx     # Resume + JD file upload component
│   │   │   ├── SkillAnalysis.jsx  # Skill match visualization
│   │   │   ├── AIRecommendations.jsx  # AI-powered suggestions display
│   │   │   ├── MarketTrends.jsx   # Market data visualization
│   │   │   ├── AIPipelineViz.jsx  # ML pipeline visualization
│   │   │   ├── Footer.jsx         # App footer with navigation
│   │   │   ├── UserProfile.jsx    # User profile dropdown
│   │   │   ├── dashboard/
│   │   │   │   ├── ProfileSummary.jsx  # User profile card
│   │   │   │   ├── CareerFitRadar.jsx  # Radar chart component
│   │   │   │   ├── ProgressTracker.jsx # Progress visualization
│   │   │   │   └── IndustryMatch.jsx   # Industry matching display
│   │   │   ├── effects/
│   │   │   │   ├── Snowfall.jsx        # Particle snow effect
│   │   │   │   └── AntiGravityCursor.jsx # Cursor gravity effect
│   │   │   └── pages/
│   │   │       ├── LoginPage.jsx       # OTP-based auth UI
│   │   │       ├── LandingPage.jsx     # Hero + feature cards
│   │   │       ├── AboutPage.jsx       # About the platform
│   │   │       ├── HelpPage.jsx        # Help/FAQ
│   │   │       ├── ResumeBuilder.jsx   # Multi-step resume builder
│   │   │       ├── JobsPage.jsx        # Domain job explorer
│   │   │       ├── JobPreparation.jsx  # Interview prep module
│   │   │       ├── InterviewRoadmap.jsx # Success roadmap (7/30/90 days)
│   │   │       ├── CareerRoadmap.jsx   # Domain-based career roadmap
│   │   │       ├── CompanyPreparation.jsx # Company-specific prep
│   │   │       ├── ModelPredictionHub.jsx # ML prediction hub (5 models)
│   │   │       ├── PlacementPrediction.jsx
│   │   │       ├── JobRolePrediction.jsx
│   │   │       ├── SalaryPrediction.jsx
│   │   │       ├── DomainFitPrediction.jsx
│   │   │       ├── SkillMatchPrediction.jsx
│   │   │       ├── ReportCard.jsx      # Career readiness report
│   │   │       └── HREmailGenerator.jsx # Auto HR email generation
├── models/
│   ├── ml_pipeline_xgboost_20250619_172840.pkl  # Production XGBoost pipeline (~10K features)
│   ├── model_info_20250619_172840.txt           # Model metadata (78.14% acc, 0.8957 AUC)
│   └── production_predictor.py                  # Standalone predictor class (NLTK-based)
├── notebooks/
│   ├── ml_evaluation.py           # [225 lines] Training + evaluation script
│   └── train_advanced_model.ipynb # Jupyter notebook for model training
├── src/
│   ├── skills.py                  # [37 lines] Rule-based skill extraction (250+ skills)
│   ├── parsing.py                 # [17 lines] PDF/DOCX/TXT text extraction
│   ├── ner_skill_extractor.py     # [85 lines] spaCy NER skill + name extraction
│   ├── llm_utils.py               # [399 lines] Gemini API orchestration (key rotation + fallback)
│   ├── llm_enhancer.py            # [61 lines] AI resume enhancement
│   ├── fit_classifier.py          # [275 lines] Advanced ML fit classifier (XGBoost + basic fallback)
│   ├── learning_resources.py      # [287 lines] Skill→resource URL mapping + related skills
│   ├── resume_generator.py        # [269 lines] HTML resume generator + question generator
│   ├── project_ideas.py           # [50 lines] AI project idea generator
│   ├── question_bank.py           # [42 lines] Static aptitude/technical/coding questions
│   ├── code_problems.py           # [81 lines] Coding problems + simulated evaluator
│   ├── auth_utils.py              # [30 lines] PBKDF2 password hashing
│   ├── activity_logger.py         # [64 lines] JSON-based user activity logging
│   ├── hr_email_generator.py      # [140 lines] HR email generation with company DB lookup
│   ├── hr_data.json               # [153 lines] 15 company HR contacts (demo data)
│   ├── jobs.json                  # [114 lines] Curated ML/DS/NLP/CV job listings
│   ├── domainfit.py               # [51 lines] Standalone FastAPI for domain fit prediction
│   ├── salary.py                  # [46 lines] Standalone FastAPI for salary prediction
│   ├── jobrole.py                 # [46 lines] Standalone FastAPI for job role prediction
│   ├── jobmatch.py                # [53 lines] Standalone FastAPI for skill match prediction
│   └── fix_models.py              # [138 lines] Synthetic model training utility
├── requirements.txt               # Python dependencies (19 packages)
├── setup.bat                      # Windows batch launcher
├── start_project.ps1              # PowerShell launcher (health checks + dual server start)
├── debug_gemini.py                # Gemini API key validator
├── HOW_TO_RUN.md                  # Quick-start guide
└── README.md                      # Project documentation
```

---

## 3. Environment Variable Contract

**File**: `backend/.env` (loaded by `python-dotenv`)

| Variable | Type | Required | Consumer | Purpose |
| --- | --- | --- | --- | --- |
| `GEMINI_API_KEY` | CSV string | **Yes** | `llm_utils.py` | Comma-separated Gemini API keys for rotation |
| `EMAIL_USER` | string | No | `backend/main.py` | SMTP sender email for OTP dispatch |
| `EMAIL_PASS` | string | No | `backend/main.py` | SMTP app password |
| `RETELL_API_KEY` | string | No | `backend/main.py` | Retell AI voice assistant API key |

> [!WARNING]
> If `GEMINI_API_KEY` is missing, ALL LLM features return static mock data silently.
> If `EMAIL_USER`/`EMAIL_PASS` are missing, OTP codes are printed to console (insecure).
> If `RETELL_API_KEY` is missing, voice assistant calls fail with HTTP error.

---

## 4. Backend API Surface — Complete Endpoint Map

**Entry point**: `backend/main.py` → `app = FastAPI()` → `uvicorn backend.main:app --port 8000`

### 4.1 Authentication Endpoints

| Endpoint | Method | Request Schema | Response Schema | Logic |
| --- | --- | --- | --- | --- |
| `/api/signup` | POST | `{email, password}` JSON | `{message}` or `{detail}` | 1. Validates email not in `users.json` 2. Hashes password via `auth_utils.hash_password()` (PBKDF2-SHA256, 100K iterations, random 16-byte hex salt) 3. Stores `{email: {email, hash}}` in `users.json` 4. Generates 6-digit OTP → stores in `otp_storage[email]` (in-memory dict) 5. Sends OTP via SMTP or prints to console |
| `/api/verify-otp` | POST | `{email, otp}` JSON | `{message, user: {email}}` | Compares `otp_storage[email]` with provided OTP. On match: returns user object. On fail: 400 error |
| `/api/login` | POST | `{email, password}` JSON | `{message, user: {email}}` | 1. Loads `users.json` 2. Calls `auth_utils.verify_password()` 3. On success: returns user object |
| `/api/resend-otp` | POST | `{email}` JSON | `{message}` | Regenerates 6-digit OTP, re-sends via SMTP |

**Auth Implementation Details (from `auth_utils.py`)**:

```python
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)          # 32 hex chars
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${key.hex()}"          # Format: "salt$hash"

def verify_password(stored_password: str, provided_password: str) -> bool:
    salt, key = stored_password.split('$')
    new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
    return new_key.hex() == key
```

**OTP Dispatch Logic** (`backend/main.py`):

```python
otp_storage = {}  # In-memory! Lost on restart

def send_otp_email(email, otp):
    # Uses smtplib → smtp.gmail.com:587 → TLS
    # Fallback: print(f"OTP for {email}: {otp}") to console
```

### 4.2 File Analysis Endpoints

| Endpoint | Method | Request | Response | Logic |
| --- | --- | --- | --- | --- |
| `/api/analyze-files` | POST | `multipart/form-data` with `resume` (optional) + `jd` (required) | `{score, match_percentage, skills_matched[], skills_missing[], resume_skills[], jd_skills[], fit_prediction{}, recommendations[], enhancement_text, project_ideas, resources{}, related_skills[], candidate_name}` | **Critical Path**: 1. Extracts text via `parsing.py` (PDF→PyPDF2, DOCX→python-docx) 2. Extracts skills via `ner_skill_extractor.extract_skills_ner()` with fallback to `skills.extract_skills()` 3. Computes `matched = resume∩jd`, `missing = jd-resume`, `score = \|matched\|/\|jd\|×100` 4. Calls `fit_classifier.predict_fit()` (advanced XGBoost → basic RF → hardcoded fallback) 5. Calls `llm_enhancer.enhance_resume_section()` 6. Calls `project_ideas.generate_project_ideas()` 7. Gets `learning_resources.get_learning_resources()` + `get_related_skills()` 8. Extracts candidate name via `ner_skill_extractor.extract_name_ner()` |
| `/api/enhance-resume` | POST | `{resume_text, jd_text, missing_skills[]}` JSON | `{enhanced_text}` | Calls `llm_enhancer.enhance_resume_section()` → Gemini prompt for 3 actionable bullet rewrites |
| `/api/project-ideas` | POST | `{resume_text, resume_skills[]}` JSON | `{ideas}` (markdown string) | Calls `project_ideas.generate_project_ideas()` → Gemini prompt for 3 portfolio projects |

### 4.3 Resume Builder Endpoints

| Endpoint | Method | Request | Response |
| --- | --- | --- | --- |
| `/api/resume/generate` | POST | `{personal_info{name,email,phone,location,linkedin}, summary, experience[{role,company,duration,description}], education[{degree,institution,year}], skills[]}` | `{html_content}` — Premium HTML resume with Inter font, sidebar layout |
| `/api/resume/questions` | POST | `{jd_text}` | `{questions[]}` — 3-4 skill-targeted interview questions from JD |
| `/api/resume/role-questions` | POST | `{target_role}` | `{questions[]}` — Gemini-generated role-specific questions |
| `/api/resume/generate-role-based` | POST | Same as `/generate` + `{target_role}` | `{html_content}` — Role-optimized HTML resume |
| `/api/analyze-resume` | POST | `{personal_info, summary, experience[], education[], skills[]}` | `{score, advice[], missing_skills[], resources{}}` — AI resume scoring |

### 4.4 ML Prediction Endpoints

| Endpoint | Method | Request Schema | ML Model | Response |
| --- | --- | --- | --- | --- |
| `/api/predict/placement` | POST | `{ssc_p, hsc_p, degree_p, workex(0/1), etest_p, mba_p}` | `xgboost_pipeline.pkl` or `MockPipeline` | `{prediction, probability, safety_checks{}, academic_metrics{}}` |
| `/api/predict/job-role` | POST | `{gender, ssc_p, ssc_b, hsc_p, hsc_b, hsc_s, degree_p, degree_t, workex, etest_p, specialisation, mba_p}` | `job_role_model.pkl` (sklearn Pipeline) | `{prediction, probabilities}` |
| `/api/predict/salary` | POST | `{age, gender, education, job_title, experience}` | `gradient_boosting_salary.pkl` | `{predicted_salary}` |
| `/api/predict/domain-fit` | POST | `{Age, Gender, Vocational_Program, Academic_Performance, Certifications_Count, Internship_Experience, Skill_1, Skill_2, Skill_3}` | `domain_fit_model.pkl` + `domain_fit_encoder.pkl` | `{domain_fit, confidence}` |
| `/api/predict/skill-match` | POST | `{age, academic_performance, certifications_count, internship_experience, skill_1..3, required_skill_1..5, min_experience_months}` | `skill_recommender.pkl` | `{match, match_label}` |

### 4.5 Placement Prediction — MockPipeline Fallback

```python
class MockPipeline:
    """Used when xgboost_pipeline.pkl fails to load"""
    def predict(self, X):
        return [1]  # Always predicts "Placed"
    def predict_proba(self, X):
        return [[0.3, 0.7]]  # 70% confidence

# Safety guards in predict_placement():
if degree_p < 50: probability *= 0.6   # Academic penalty
if etest_p < 50:  probability *= 0.7   # Test score penalty
if ssc_p < 40 and hsc_p < 40: probability *= 0.5  # Dual-low penalty
```

### 4.6 Chat & Voice Endpoints

| Endpoint | Method | Request | Response | Logic |
| --- | --- | --- | --- | --- |
| `/api/chat-query` | POST | `{query}` JSON | `{response, roles[], suggestions[]}` | 1. LLM intent detection (JOB_SEARCH vs ADVICE) 2. JOB_SEARCH → loads `jobs.json` → fuzzy keyword match → returns role cards 3. ADVICE → Gemini free-form response 4. Fallback: static suggestions array |
| `/api/chat-analyze` | POST | `multipart/form-data` with `file` | `{response, roles[]}` | Extracts text from uploaded resume → skill extraction → job matching |
| `/api/create-web-call` | POST | None | `{access_token}` | Creates Retell AI web call → returns access token for WebRTC |

### 4.7 Company Prep & Report Endpoints

| Endpoint | Method | Request | Response |
| --- | --- | --- | --- |
| `/api/company-prep` | POST | `{company_type, company_name, time_period}` | `{insights{}, weeks[]}` — Gemini-generated prep plan with mock fallback |
| `/api/report/analyze` | POST | `{report_data{}}` | Full report card JSON (readiness_score, breakdown, gap_analysis, improvement_plan, future_snapshot) |
| `/api/report/download-pdf` | POST | `{report_data{}}` | Binary PDF response (generated via `fpdf`) |

### 4.8 HR Email Endpoints

| Endpoint | Method | Request | Response |
| --- | --- | --- | --- |
| `/api/hr-emailer/analyze` | POST | `multipart/form-data` with `file` | `{name, skills[], summary, suggested_roles[]}` |
| `/api/hr-emailer/generate` | POST | `{company, hr_name, user_name, target_role, skills[], projects[]}` | `{success, hr_info{}, email_content, subject}` |
| `/api/hr-emailer/companies` | GET | None | `[{company, hr_name, designation, email, linkedin, hiring_domains[], notes}]` |

---

## 5. CORS & Proxy Configuration

**Backend CORS** (`backend/main.py`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # ⚠️ Wide open — suitable for dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Frontend Proxy** (`frontend/vite.config.js`):

```javascript
server: {
    proxy: {
        '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
            secure: false,
        }
    }
}
```

> [!IMPORTANT]
> The frontend `api.js` uses `API_BASE_URL = ''` (empty string), meaning all `/api/*` calls go through the Vite proxy in dev mode. In production, this must be configured to the actual backend URL.

---

## 6. Startup Pipeline

### PowerShell (`start_project.ps1`)

```text
[0/5] Check backend/.env exists
[1/5] Verify Python in PATH
[2/5] pip install -r requirements.txt
[3/5] npm install (if no node_modules/)
[4/5] Start-Process: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
[5/5] Start-Process: cd frontend && npm run dev
→ Opens http://localhost:5173 in browser
```

### Batch (`setup.bat`)

Same flow but uses `start cmd /k` for new windows.

### DevContainer (`.devcontainer/devcontainer.json`)

- Image: `mcr.microsoft.com/devcontainers/python:1-3.11-bullseye`
- Auto-install: `requirements.txt` + `streamlit`
- Auto-start: `streamlit run app/main.py` on port 8501
- **Note**: This starts the LEGACY Streamlit frontend, not the React app

---

*Continued in Part 2: ML Pipeline, LLM Orchestration, Skill Extraction, and Data Schemas*
*Continued in Part 3: Frontend Architecture, Component Tree, State Management, and Security Audit*
