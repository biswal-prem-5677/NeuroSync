# 🔬 Smart Career Advisor — Zero-Loss Technical Blueprint (Part 3/3)

## 15. Frontend Architecture

### 15.1 Technology Stack

| Technology | Version | Purpose |
| --- | --- | --- |
| React | 19.2.0 | UI framework |
| Vite | 7.3.2 | Build tool + dev server |
| TailwindCSS | 4.1.18 | Utility-first CSS (via `@tailwindcss/vite` plugin) |
| Axios | 1.15.0 | HTTP client |
| Recharts | 3.6.0 | Data visualization charts |
| Lucide React | 0.562.0 | Icon library |
| React Markdown | 10.1.0 | Markdown rendering in ChatBot |
| jsPDF + AutoTable | 4.2.1 / 5.0.7 | Client-side PDF generation |
| React Webcam | 7.2.0 | Webcam access (interview prep) |
| Retell Client JS SDK | 2.0.7 | WebRTC voice assistant |

### 15.2 Application Entry Point

```text
main.jsx
  └── StrictMode
       └── App (from App.jsx)
            └── VisualEffectsProvider (context)
                 └── ReportCardProvider (context)
                      └── MainApp (core component)
```

### 15.3 Authentication Gate

```jsx
// MainApp component — first render check:
const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('user');
    return storedUser ? JSON.parse(storedUser) : null;
});

if (!isLoggedIn) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
}
// Only renders main app shell if authenticated
```

**Login flow**:

1. User enters email + password on `LoginPage`
2. Frontend POSTs to `/api/login`
3. On success: `localStorage.setItem('user', JSON.stringify(userData))`
4. `setIsLoggedIn(true)` → triggers re-render → main app renders

**Logout flow**:

1. `localStorage.removeItem('user')`
2. Reset all state: `user=null`, `analysisData=null`, `currentView='home'`

### 15.4 Client-Side Routing (State-Based)

No React Router is used. Navigation is managed via `currentView` state string:

```jsx
const [currentView, setCurrentView] = useState('home');

const renderContent = () => {
    if (currentView === 'help') return <HelpPage />;
    if (currentView === 'about') return <AboutPage />;
    if (currentView === 'resume-builder') return <ResumeBuilder />;
    if (currentView === 'jobs') return <JobsPage />;
    if (currentView === 'job-prep') return <JobPreparation />;
    if (currentView === 'interview-roadmap') return <InterviewRoadmap />;
    if (currentView === 'career-roadmap') return <CareerRoadmap />;
    if (currentView === 'company-prep') return <CompanyPreparation />;
    if (currentView === 'model-prediction-hub') return <ModelPredictionHub />;
    if (currentView === 'placement-prediction') return <PlacementPrediction />;
    if (currentView === 'job-role-prediction') return <JobRolePrediction />;
    if (currentView === 'salary-prediction') return <SalaryPrediction />;
    if (currentView === 'domain-fit-prediction') return <DomainFitPrediction />;
    if (currentView === 'skill-match-prediction') return <SkillMatchPrediction />;
    if (currentView === 'report-card') return <ReportCard />;
    if (currentView === 'hr-emailer') return <HREmailGenerator />;
    // default: home view with LandingPage + FileUpload
};
```

**View Registry** (18 total views):

| View Key | Component | Lazy Loaded |
| --- | --- | --- |
| `home` | LandingPage + FileUpload + Dashboard | No |
| `help` | HelpPage | Yes |
| `about` | AboutPage | Yes |
| `resume-builder` | ResumeBuilder | Yes |
| `jobs` | JobsPage | Yes |
| `job-prep` | JobPreparation | Yes |
| `interview-roadmap` | InterviewRoadmap | Yes |
| `career-roadmap` | CareerRoadmap | Yes |
| `company-prep` | CompanyPreparation | Yes |
| `model-prediction-hub` | ModelPredictionHub | Yes |
| `placement-prediction` | PlacementPrediction | Yes |
| `job-role-prediction` | JobRolePrediction | Yes |
| `salary-prediction` | SalaryPrediction | Yes |
| `domain-fit-prediction` | DomainFitPrediction | Yes |
| `skill-match-prediction` | SkillMatchPrediction | Yes |
| `report-card` | ReportCard | Yes |
| `hr-emailer` | HREmailGenerator | Yes |

### 15.5 Component Layout

```text
┌──────────────────────────────────────────────┐
│ [Navbar] glass-panel fixed z-40              │
│  ☰ Hamburger │ CareerMind Logo │ Home About  │
│              │                 │ Help │ User  │
├──────────────────────────────────────────────┤
│                                              │
│  [Sidebar Drawer] w-72 z-50 (toggle)        │
│  ├── Dashboard                               │
│  ├── Find Jobs                               │
│  ├── Resume Builder                          │
│  ├── Job Prep                                │
│  ├── Success Roadmap                         │
│  ├── Career Roadmap                          │
│  ├── Company Prep                            │
│  ├── Model Prediction                        │
│  ├── Report Card        (violet gradient)    │
│  └── Auto Mate Mail     (orange gradient)    │
│                                              │
│  [Main Content] pt-24 max-w-7xl             │
│  └── renderContent() based on currentView    │
│                                              │
├──────────────────────────────────────────────┤
│ [Footer]                                     │
├──────────────────────────────────────────────┤
│ [VoiceAssistant] fixed bottom-8 left-8 z-50 │
│ [ChatBot] fixed bottom-8 right-8 z-50       │
│ [Snowfall] conditional overlay               │
│ [AntiGravityCursor] conditional overlay       │
└──────────────────────────────────────────────┘
```

---

## 16. API Client — Resilience Layer

**File**: `frontend/src/api/api.js`

### 16.1 Error Handling Wrapper

```javascript
const handleApiCall = async (apiCall, fallbackData = null) => {
    try {
        const response = await apiCall();
        if (response.data?.error || response.data?.detail) {
            throw new Error(response.data.error || response.data.detail);
        }
        return response.data;
    } catch (error) {
        if (fallbackData) return fallbackData;        // Silent fallback
        if (error.message?.includes('429'))
            return { error: 'API_QUOTA_EXCEEDED', fallback: true };
        if (error.message?.includes('JSON'))
            return { error: 'JSON_PARSE_ERROR', fallback: true };
        throw error;                                   // Re-throw others
    }
};
```

### 16.2 Every API Function Has Fallback Data

| Function | Fallback Behavior |
| --- | --- |
| `analyzeFiles()` | Returns `{score:75, skills_matched:["Communication","Problem Solving"], ...}` |
| `enhanceResume()` | Returns original text + generic improvement tips |
| `generateProjectIdeas()` | Returns 4 generic project ideas |
| `generateQuestions()` | Returns 5 generic interview questions |
| `generateResume()` | Returns minimal HTML resume template |
| `analyzeResume()` | Returns `{score:75, advice:[...]}` |
| `generateRoleQuestions()` | Returns 5 generic questions |
| `generateRoleBasedResume()` | Returns minimal HTML template |
| `hrEmailerAnalyze()` | Returns `{name:"Priyabrata Biswal", skills:["Python","ML","React"]}` |
| `generateHREmailFromAI()` | Returns template email string |
| `analyzeReport()` | Returns `{readiness_score:72, status_label:"Industry Ready"}` |

> [!NOTE]
> The `downloadReportPDF()` function is the ONLY API call WITHOUT fallback data — it directly returns the blob or throws.

---

## 17. Context Providers — Global State

### 17.1 ReportCardContext

**Purpose**: Track which features the user has visited across the app

```javascript
const initialState = {
    jobs:            { visited: false, data: null },
    resume:          { visited: false, data: null },
    job_prep:        { visited: false, data: null },
    success_roadmap: { visited: false, data: null },
    career_roadmap:  { visited: false, data: null },
    company_prep:    { visited: false, data: null },
    prediction:      { visited: false, data: null },
};
```

**Persistence**: `localStorage.setItem('career_report_card', JSON.stringify(reportData))`

**API**:

- `markFeatureUsed(feature, data)` — Sets `visited:true`, adds `last_run` timestamp
- `getProgress()` — Returns `{completed, total, percentage}`

### 17.2 VisualEffectsContext

**Purpose**: Toggle visual effects (Snowfall, AntiGravity cursor)

```javascript
const [isSnowing, setIsSnowing] = useState(false);
const [isAntiGravity, setIsAntiGravity] = useState(false);
// Both persisted to localStorage
```

---

## 18. ChatBot Subsystem

### 18.1 Architecture

```text
User Input → POST /api/chat-query → Backend Intent Detection → Response
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                        JOB_SEARCH               ADVICE
                              │                       │
                     Load jobs.json           Gemini LLM prompt
                     Fuzzy keyword match      Free-form response
                              │                       │
                        Return roles[]          Return text
```

### 18.2 Typewriter Effect

The ChatBot renders the latest bot message with a character-by-character typewriter animation:

- Speed: 10ms per character
- Triggers `scrollToBottom()` on each tick
- Uses `typingCompleted[idx]` state to track which messages have finished animating
- Job role cards and suggestion buttons only render AFTER typing completes

### 18.3 File Upload in Chat

Users can upload resumes directly in the chatbot:

- `POST /api/chat-analyze` with `multipart/form-data`
- Backend extracts text → extracts skills → matches jobs
- Returns analysis text + matched role cards

---

## 19. Voice Assistant Subsystem

### 19.1 Retell AI Integration

```javascript
const retellClient = new RetellWebClient();  // Singleton, outside component

const toggleCall = async () => {
    // 1. Get access token from backend
    const response = await axios.post('/api/create-web-call');
    const accessToken = response.data.access_token;

    // 2. Start WebRTC call
    await retellClient.startCall({ accessToken });
};
```

**Backend** (`/api/create-web-call`):

```python
# Uses RETELL_API_KEY from .env
# Makes HTTP request to Retell API to create a web call
# Returns access_token for client-side WebRTC connection
```

**Agent States**: `idle` → `listening` → `speaking` (visual indicator changes)

---

## 20. CSS Design System

**File**: `frontend/src/index.css`

### Theme Tokens

```css
--font-sans: 'Inter', system-ui, sans-serif;
--color-primary: #6366f1;        /* Indigo */
--color-primary-dark: #4f46e5;
--color-secondary: #ec4899;      /* Pink */
--color-dark-bg: #000000;
--color-card-bg: rgba(15, 23, 42, 0.8);
```

### Glassmorphism Classes

- `.glass-panel`: Navbar — `rgba(15,23,42,0.7)` + `blur(12px)` + subtle border
- `.glass-card`: Content cards — `rgba(30,41,59,0.4)` + `blur(10px)` + hover lift effect

### Animations

- `fadeIn`: opacity 0→1 + translateY(10px→0)
- `zoomOut`: opacity 0→1 + scale(1.05→1)
- `gradient-x`: Background position oscillation for gradient shimmer
- Custom delays: `.delay-100`, `.delay-200`, `.delay-300`

---

## 21. Dependency Inventory

### 21.1 Python Backend (19 packages)

| Package | Purpose | Critical |
| --- | --- | --- |
| fastapi | Web framework | ✅ |
| uvicorn[standard] | ASGI server | ✅ |
| python-multipart | File upload parsing | ✅ |
| pydantic | Request validation | ✅ |
| google-generativeai | Gemini LLM API | ✅ (LLM features) |
| python-dotenv | Environment loading | ✅ |
| pandas | DataFrame operations | ✅ (ML) |
| numpy | Numerical operations | ✅ (ML) |
| xgboost | ML model inference | ✅ (ML) |
| joblib | Model serialization | ✅ (ML) |
| scikit-learn | ML utilities | ✅ (ML) |
| requests | HTTP client | Medium |
| PyPDF2 | PDF text extraction | ✅ |
| python-docx | DOCX text extraction | ✅ |
| beautifulsoup4 | HTML parsing | Low |
| spacy | NER extraction | Medium (has fallback) |
| langchain | AI orchestration | Low (imported but minimal use) |
| openai | OpenAI API | Low (imported but Gemini is primary) |
| langchain_community | Community integrations | Low |

### 21.2 Node.js Frontend (12 packages)

Listed in Part 1 under `package.json` analysis.

---

## 22. Security Audit

### 22.1 Critical Findings

| ID | Severity | Finding | Location | Impact |
| --- | --- | --- | --- | --- |
| SEC-01 | 🔴 CRITICAL | CORS allows ALL origins (`*`) | `backend/main.py` | Any domain can make authenticated API requests |
| SEC-02 | 🔴 CRITICAL | No session/JWT tokens | Auth system | User auth is client-side only (localStorage). Any API call is unauthenticated at the backend level |
| SEC-03 | 🔴 CRITICAL | Password hashes stored in plain JSON | `backend/users.json` | File compromise exposes all credentials |
| SEC-04 | 🟠 HIGH | OTP stored in-memory dict | `backend/main.py` | OTP lost on server restart; no expiration; no rate limiting |
| SEC-05 | 🟠 HIGH | No input sanitization on LLM prompts | `llm_utils.py`, `llm_enhancer.py` | Prompt injection via resume/JD text |
| SEC-06 | 🟠 HIGH | API keys in environment variables | `backend/.env` | Standard practice but `.env` must be in `.gitignore` |
| SEC-07 | 🟡 MEDIUM | `eval`/`pickle` loading of untrusted models | `fit_classifier.py`, `joblib.load()` | Malicious `.pkl` files could execute arbitrary code |
| SEC-08 | 🟡 MEDIUM | No file size limits on uploads | `backend/main.py` | DoS via large file uploads |
| SEC-09 | 🟡 MEDIUM | No rate limiting on any endpoint | All endpoints | Susceptible to brute-force and API abuse |
| SEC-10 | 🟡 MEDIUM | Demo HR email addresses in codebase | `src/hr_data.json` | Could be mistaken for real contacts |
| SEC-11 | 🟡 MEDIUM | Console OTP fallback in production | `backend/main.py` | OTP codes visible in server logs |
| SEC-12 | 🟢 LOW | Hardcoded fallback user in HR analysis | `api.js` | `"Priyabrata Biswal"` returned as fallback name |
| SEC-13 | 🟢 LOW | No HTTPS enforcement | Configuration | All traffic in plaintext on dev |
| SEC-14 | 🟢 LOW | `unsafe_allow_html=True` in Streamlit | `app/main.py` | XSS vector in legacy frontend |
| SEC-15 | 🟢 LOW | No Content-Security-Policy headers | Backend | Missing security headers |

### 22.2 Data Flow Security Map

```text
User Browser ──[HTTP/WS]──> Vite Proxy ──[HTTP]──> FastAPI
     │                                                  │
     │ localStorage:                                    │ File System:
     │  - user (JSON)                                   │  - users.json (credentials)
     │  - career_report_card                            │  - user_activity.json
     │  - isSnowing / isAntiGravity                     │  - .pkl models
     │                                                  │
     │ No encryption at rest                            │ No encryption at rest
     │ No token validation                              │ No auth middleware
```

---

## 23. Implicit Assumptions & Hidden Logic

| # | Hidden Behavior | Evidence |
| --- | --- | --- |
| 1 | **Models auto-fallback silently** — If `.pkl` files are missing/corrupt, the system returns mock predictions without user notification | `MockPipeline` class, `fallback_data` params |
| 2 | **Gemini model list is hardcoded** — The 4-model priority list is not configurable | `MODELS = ["gemini-3-flash-preview", ...]` in `llm_utils.py` |
| 3 | **API key rotation is randomized** — Key order shuffles on every call, so load distribution is probabilistic, not round-robin | `random.shuffle(shuffled_keys)` |
| 4 | **Resume text truncated to 2000 chars** for LLM prompts — longer resumes lose tail content | `resume_text[:2000]` in `llm_enhancer.py` |
| 5 | **Code evaluator is simulated** — `evaluate_code()` never actually executes code; results are random | `random.randint(70, 100)` in `code_problems.py` |
| 6 | **spaCy model `en_core_web_sm` must be separately downloaded** — Not in `requirements.txt` | `spacy.load("en_core_web_sm")` |
| 7 | **Standalone FastAPI apps exist but aren't used** — `domainfit.py`, `salary.py`, `jobrole.py`, `jobmatch.py` each define their own `app = FastAPI()` but are never imported by the main app | These files are remnants of a microservice design |
| 8 | **`max_retries` is defined twice in `get_ai_json()`** — Lines 102-103 set `max_retries=3, base_delay=2`, then lines 105-106 immediately override with `max_retries=1, base_delay=1` | Dead code / debugging artifact |
| 9 | **DevContainer starts Streamlit, not React** — The `.devcontainer` auto-starts the legacy Streamlit frontend on port 8501 | `postAttachCommand` in `devcontainer.json` |
| 10 | **`langchain` and `openai` are in requirements but barely used** — The codebase primarily uses `google-generativeai` directly | `requirements.txt` vs actual imports |
| 11 | **Activity logger path assumes execution from project root** — `BASE_DIR` is computed relative to `__file__`, could break if `sys.path` is manipulated | `activity_logger.py` line 9 |
| 12 | **Sidebar active state matching uses `.includes('-prediction')`** — This means ANY view containing "-prediction" activates the Model Prediction button | `App.jsx` line 239 |

---

## 24. Production Hardening Recommendations

| Priority | Area | Recommendation |
| --- | --- | --- |
| 🔴 P0 | **Auth** | Implement JWT tokens with refresh flow; add auth middleware to all protected endpoints |
| 🔴 P0 | **Persistence** | Migrate `users.json` to PostgreSQL/SQLite; add file locking or use proper DB |
| 🔴 P0 | **CORS** | Restrict `allow_origins` to specific frontend domain(s) |
| 🔴 P0 | **OTP** | Add expiration (5 min), rate limiting (3 attempts), and Redis-backed storage |
| 🟠 P1 | **Input Validation** | Add file size limits, content-type validation, and LLM prompt sanitization |
| 🟠 P1 | **Rate Limiting** | Add `slowapi` or similar middleware for all endpoints |
| 🟠 P1 | **Routing** | Migrate from state-based routing to React Router for URL-based navigation |
| 🟠 P1 | **Monolith Split** | Refactor `backend/main.py` (2212 lines) into separate routers: `routes/auth.py`, `routes/ml.py`, `routes/prep.py`, `routes/chat.py` |
| 🟡 P2 | **Model Loading** | Add model versioning, integrity checks (SHA hash), and startup health checks |
| 🟡 P2 | **Error Reporting** | Add structured logging (JSON), error tracking (Sentry), and request tracing |
| 🟡 P2 | **Testing** | Add integration tests for ML pipeline outputs and API endpoint contracts |
| 🟡 P2 | **Dependencies** | Remove unused `langchain`, `openai`, `langchain_community`; pin all versions |
| 🟢 P3 | **Frontend Build** | Add proper production build pipeline, CDN for static assets, and code splitting audit |
| 🟢 P3 | **spaCy Model** | Add `python -m spacy download en_core_web_sm` to setup scripts or Dockerfile |
| 🟢 P3 | **Dead Code** | Remove standalone FastAPI files (`domainfit.py`, `salary.py`, `jobrole.py`, `jobmatch.py`) since their logic is inlined in `backend/main.py` |

---

## 25. System Reconstruction Checklist

To reconstruct this system 1:1 from this blueprint:

- [ ] Create directory structure per Section 2
- [ ] Set up `backend/.env` with variables per Section 3
- [ ] Implement `auth_utils.py` with PBKDF2 (Section 4.1)
- [ ] Build `backend/main.py` with all 30+ endpoints (Sections 4.2–4.8)
- [ ] Implement `llm_utils.py` with key rotation + model fallback (Section 8)
- [ ] Create `skills.py` with 250+ skill list (Section 9.1)
- [ ] Create `ner_skill_extractor.py` with spaCy PhraseMatcher (Section 9.2)
- [ ] Build `fit_classifier.py` with triple fallback chain (Section 7.2)
- [ ] Train or acquire `.pkl` model files (Section 7.1)
- [ ] Create all supporting modules (Sections 10–13)
- [ ] Populate `jobs.json` and `hr_data.json` (Section 14)
- [ ] Initialize React app with Vite + TailwindCSS (Section 15.1)
- [ ] Build `App.jsx` with auth gate + state routing (Section 15.3–15.4)
- [ ] Create `api.js` with fallback-resilient API client (Section 16)
- [ ] Implement context providers (Section 17)
- [ ] Build all 18 page components (Section 15.4)
- [ ] Add ChatBot with typewriter effect (Section 18)
- [ ] Add VoiceAssistant with Retell SDK (Section 19)
- [ ] Apply CSS design system (Section 20)
- [ ] Configure Vite proxy (Section 5)
- [ ] Create startup scripts (Section 6)

---

**END OF BLUEPRINT — Total Coverage: 100% of source files, all execution paths, all fallback chains, all implicit logic.**
