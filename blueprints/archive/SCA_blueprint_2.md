# 🔬 Smart Career Advisor — Zero-Loss Technical Blueprint (Part 2/3)

## 7. ML Prediction Pipeline — Complete Internals

### 7.1 Model Inventory

| Model File | Algorithm | Training Data | Features | Target | Accuracy | Location |
| --- | --- | --- | --- | --- | --- | --- |
| `ml_pipeline_xgboost_*.pkl` | XGBoost | 6,241 HuggingFace resume-job pairs | 10,012 (TF-IDF + statistical) | Good Fit / No Fit / Potential Fit | 78.14% | `models/` |
| `gradient_boosting_salary.pkl` | GradientBoostingRegressor | 1,000 synthetic samples | 5 (Age, Gender, Education, Job, Experience) | Continuous salary | N/A (synthetic) | `src/` |
| `domain_fit_model.pkl` | RandomForestClassifier | 1,000 synthetic samples | 7 (Age, Academic, Certs, Intern, Skill×3) | 4 domains | N/A (synthetic) | `src/` |
| `domain_fit_encoder.pkl` | LabelEncoder | — | — | Encodes domain labels | — | `src/` |
| `job_role_model.pkl` | sklearn Pipeline (StandardScaler + OneHotEncoder + RF) | 1,000 synthetic samples | 12 (academic + categorical) | 5 job roles | N/A (synthetic) | `src/` |
| `skill_recommender.pkl` | Unknown (loaded externally) | External | 13 features | Binary match | N/A | `src/` |
| `xgboost_pipeline.pkl` | XGBoost | External | 6 academic features | Placed/Not Placed | N/A | `backend/` or `models/` |

### 7.2 Advanced Fit Classifier — Triple Fallback Chain

**File**: `src/fit_classifier.py` — `AdvancedFitClassifier` class

```text
Prediction Request
       │
       ▼
┌─────────────────────────────┐
│ 1. Advanced ML (XGBoost)    │  ← Requires: resume_text + job_description + loaded model
│    predict_advanced()       │
│    Uses: TF-IDF + stats     │
│    10,012 features          │
└─────────┬───────────────────┘
          │ Falls through if: model not loaded OR prediction error
          ▼
┌─────────────────────────────┐
│ 2. Basic ML (RandomForest)  │  ← Requires: match_score + num_matched + num_missing
│    predict_basic()          │
│    Uses: 3 numeric features │
│    Auto-trains if no .pkl   │
└─────────┬───────────────────┘
          │ Falls through if: missing inputs OR prediction error
          ▼
┌─────────────────────────────┐
│ 3. Hardcoded Fallback       │  ← Always available
│    Returns: "No Fit", 0.5   │
│    model_type: "fallback"   │
└─────────────────────────────┘
```

**Advanced Model Loading** (`_load_advanced_model`):

```python
models_dir = Path(__file__).parent.parent / 'models'
model_files = list(models_dir.glob('ml_pipeline_xgboost_*.pkl'))
latest_model = max(model_files, key=os.path.getctime)  # Most recent by creation time
pipeline_data = joblib.load(latest_model)
# Extracts: model, vectorizers, label_encoder, feature_columns, target_names
```

**Feature Engineering** (`_create_text_features`):

1. **Text preprocessing**: lowercase → strip non-alpha → collapse whitespace
2. **Statistical features** (per text column, 6 each = 12 total):
   - `text_length`, `word_count`, `unique_words`
   - `avg_word_length`, `sentence_count`, `capital_ratio`
3. **TF-IDF features**: Transform via stored vectorizers → ~5,000 features per text column
4. **Missing feature padding**: Fill absent columns with 0
5. **Column reordering**: Match training feature order exactly

### 7.3 Placement Prediction — Safety Guard System

**File**: `backend/main.py` → `predict_placement()` endpoint

```python
# Model loading with MockPipeline fallback
try:
    pipeline = joblib.load("models/xgboost_pipeline.pkl")  # or backend/xgboost_pipeline.pkl
except:
    pipeline = MockPipeline()  # Always returns "Placed" with 70% confidence

# Input features: [ssc_p, hsc_p, degree_p, workex, etest_p, mba_p]
# All are floats except workex (0/1 binary)

# Post-prediction safety guards:
if degree_p < 50: probability *= 0.6     # -40% for low degree
if etest_p < 50:  probability *= 0.7     # -30% for low test score
if ssc_p < 40 and hsc_p < 40:
    probability *= 0.5                    # -50% for dual-low secondary scores
probability = max(0.05, min(0.95, probability))  # Clamp to [5%, 95%]
```

### 7.4 Synthetic Model Training (`fix_models.py`)

This utility generates 3 ML models from synthetic data when real `.pkl` files are unavailable:

| Function | Model | Features | Target Formula |
| --- | --- | --- | --- |
| `train_salary_model()` | GradientBoostingRegressor(100 estimators) | Age, Gender, Education, Job, Experience | `30000 + Exp×2000 + Edu×5000 + Job×10000 + noise` |
| `train_domain_fit_model()` | RandomForestClassifier(50 estimators) | Age, Academic, Certs, Intern, Skill×3 | `(Skill1+Skill2+Skill3) % 4` → domain index |
| `train_job_role_model()` | Pipeline(StandardScaler+OneHotEncoder+RF(100)) | 12 features (5 numeric, 7 categorical) | Random choice from 5 roles |

---

## 8. LLM Orchestration Layer

### 8.1 Gemini API Key Rotation + Model Fallback

**File**: `src/llm_utils.py`

```text
API Key Pool (comma-separated from env)
       │
       ▼
┌──────────────────┐
│ Shuffle keys     │  ← Random order each call to distribute load
│ randomly         │
└──────┬───────────┘
       │
       ▼  For each key:
┌──────────────────────────────────────────────┐
│ Try models in priority order:                 │
│   1. gemini-3-flash-preview                   │
│   2. gemini-2.0-flash                         │
│   3. gemini-flash-latest                      │
│   4. gemini-2.5-flash                         │
│                                               │
│ For each model:                               │
│   Retry up to 1 time (max_retries=1)          │
│   On 429/quota → sleep(1s) → retry or next    │
│   On other error → next model                 │
│   On success → return response.text           │
└──────────────────────────────────────────────┘
       │ All keys × all models exhausted
       ▼
Return "I'm currently receiving too many requests. Please try again later! ⏳"
```

### 8.2 `get_ai_response()` vs `get_ai_json()`

| Function | Temperature | Post-processing | Fallback |
| --- | --- | --- | --- |
| `get_ai_response(prompt, 0.7)` | 0.7 | Returns `response.text` raw | Static error string |
| `get_ai_json(prompt, 0.5, fallback_data)` | 0.5 | Strips ```json fences → `json.loads()` | Returns `fallback_data` dict or `{error: "quota_exceeded"}` |

### 8.3 LLM-Powered Features

| Feature | Function | Prompt Strategy | Mock Fallback |
| --- | --- | --- | --- |
| Resume Enhancement | `llm_enhancer.enhance_resume_section()` | "ATS-friendly Resume Writer" persona, truncates input to 2000 chars | Static tips about skill integration |
| Project Ideas | `project_ideas.generate_project_ideas()` | "Senior Tech Career Mentor" persona, 3 portfolio projects | Rule-based: Python→Streamlit, React→E-commerce |
| Company Prep Plan | `llm_utils.generate_company_prep_plan()` | "Placement Mentor" persona, structured JSON with weeks/days | 4-week hardcoded plan with DSA/System Design |
| Report Card Analysis | `llm_utils.generate_report_card_analysis()` | "Career Data Scientist" persona, complex JSON schema | Comprehensive mock report with scores 60-85 |
| Career Chat (ADVICE) | `backend/main.py` → `chat_query()` | Dynamic prompt based on user query | Static suggestion list |
| Role-Based Questions | `backend/main.py` → endpoint | "Technical Interviewer" persona | Generic interview questions |

---

## 9. Skill Extraction System — Dual Pipeline

### 9.1 Rule-Based Extraction (`src/skills.py`)

```python
COMMON_SKILLS = [...]  # 250+ skills across 7 categories

def extract_skills(text, skills=COMMON_SKILLS):
    text_normalized = re.sub(r'[^a-z0-9]', '', text.lower())
    for skill in skills:
        skill_norm = re.sub(r'[^a-z0-9]', '', skill.lower())
        if skill_norm in text_normalized:
            found.add(skill)
    return sorted(found)
```

**Skill Categories**: Programming Languages (27), Web & Frameworks (80+), Full Stack (12), Data & ML (15), Databases (20+), Cloud & DevOps (30+), Tools (35+), LLM & AI (12), Soft Skills & Methodologies (15+)

> [!WARNING]
> **False positive risk**: Substring matching means "R" matches any word containing "r" after normalization. The `normalize_skill()` function strips ALL non-alphanumeric characters, so "c#" becomes "c" and "c++" becomes "c" — potential collisions.

### 9.2 NER-Based Extraction (`src/ner_skill_extractor.py`)

```python
def extract_skills_ner(text):
    nlp = spacy.load("en_core_web_sm")  # Cached after first load
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(skill) for skill in COMMON_SKILLS]
    matcher.add("SKILLS", patterns)
    matches = matcher(doc)
    return list(set([doc[start:end].text for _, start, end in matches]))
```

**Name Extraction** (`extract_name_ner`):

1. Process first 1000 chars with spaCy
2. Find first `PERSON` entity → return `.title()`
3. Fallback to `fallback_name_extraction()`:
   - Look for "name:" pattern in first 20 lines
   - Match `^[A-Z][a-z]+ [A-Z][a-z]+` pattern in first 10 lines
   - Ultimate fallback: return `"Candidate"`

### 9.3 Extraction Priority in Backend

```python
# backend/main.py → analyze_files():
try:
    skills = extract_skills_ner(text)        # Try NER first
except:
    skills = extract_skills(text)            # Fall back to regex
    # Also uses: from skills import COMMON_SKILLS for direct matching
```

---

## 10. Learning Resources & Skill Recommendations

### 10.1 Resource Mapping (`src/learning_resources.py`)

**`SKILL_RESOURCES`**: Dict of 120+ skill→URL mappings (Coursera, Codecademy, official docs)

**Lookup Strategy** (`get_learning_resources()`):

1. Direct case-insensitive match
2. Alias mapping (50+ variations): `"js"→"javascript"`, `"k8s"→"kubernetes"`, `"sklearn"→"scikit-learn"`
3. Partial match: substring containment in both directions

**`RELATED_SKILLS`**: Dict of 30+ skill→recommendation arrays

**Recommendation Logic** (`get_related_skills()`):

1. Direct match on skill key
2. Word-level partial match (`skill_lower in key.split()`)
3. Remove already-known skills from recommendations
4. Return top 8 unique recommendations

---

## 11. Resume & Document Generation

### 11.1 HTML Resume Generator (`src/resume_generator.py`)

**Function**: `generate_resume_html(data)` → returns complete HTML string

**Layout**: Two-column design

- **Left sidebar** (32%): Contact info, Skills (tag grid), Education
- **Right main** (68%): Name (H1), Role title, Professional Profile, Work Experience

**Styling**: Inter font (Google Fonts), CSS custom properties, hover states

### 11.2 Question Generator (`src/resume_generator.py`)

**Function**: `generate_questions(jd_text)` → returns list of 4 questions

1. Extracts skills from JD via `extract_skills_ner()`
2. Randomly selects up to 3 skills
3. Applies random template: `"Can you describe a project where you utilized **{skill}**..."`
4. Appends generic cultural fit question
5. Fallback: 3 generic behavioral questions if no skills found

### 11.3 Question Bank (`src/question_bank.py`)

| Function | Pool Size | Format |
| --- | --- | --- |
| `get_aptitude_question()` | 5 | `{q, options[], correct}` |
| `get_technical_question()` | 5 | `{q, options[], correct}` |
| `get_coding_problem()` | 5 | String description |
| `get_interview_question()` | 5 | String question |

All use `random.choice()` for selection.

### 11.4 Code Problems (`src/code_problems.py`)

**`PROBLEMS`**: 3 problems (Two Sum, Palindrome, Reverse Linked List) with:

- `id`, `title`, `difficulty`, `description`
- `example_input`, `example_output`
- `starter_code` (Python + JavaScript)

**`evaluate_code()`**: Simulated evaluator

- `time.sleep(1.5)` to simulate execution
- If `len(code) < 20` → Syntax Error result
- Else → random score 70-100, random 3-5 passed cases out of 5

---

## 12. HR Email System

### 12.1 Company Database (`src/hr_data.json`)

15 demo companies with HR contacts:

| Company | HR Name | Location | Hiring Domains | Notes (drives email personalization) |
| --- | --- | --- | --- | --- |
| TCS | Ananya Sharma | Bangalore | SE, DA, Cloud | "concise resumes" |
| Infosys | Rohit Verma | Hyderabad | Java, Frontend, AI/ML | "GitHub + project links" |
| Wipro | Sneha Nair | Pune | Python, DevOps, QA | "ATS-friendly" |
| Microsoft | Riya Mukherjee | Hyderabad | SDE, DS, Product Intern | "Demo data for hackathon" |
| Amazon | Arjun Patel | Bangalore | SDE-1, Support, Data Eng | "DSA + system design" |
| *(+ 10 more)* | | | | |

### 12.2 Email Generation Logic (`src/hr_email_generator.py`)

```python
def generate_personalized_content(hr_info, user_name, skills_text, ...):
    # Base template with user name, skills, target role
    # Conditional paragraphs based on hr_info['notes']:
    if 'github' in notes:        → Add GitHub paragraph
    elif 'ats-friendly' in notes: → Add ATS paragraph
    elif 'cloud + ai' in notes:   → Add cloud/AI paragraph
    elif 'dsa + system design':   → Add DSA paragraph
    # ... 10 total conditional branches
    # Closing with resume attachment mention
```

---

## 13. Activity Logging System

**File**: `src/activity_logger.py`

**Storage**: `backend/user_activity.json`

```json
{
    "user@email.com": [
        {
            "timestamp": "2026-05-01T10:30:00.000000",
            "type": "resume_scan",
            "details": {"score": 85, "skills_matched": 12}
        }
    ]
}
```

| Function | Purpose |
| --- | --- |
| `log_activity(email, type, details)` | Append activity entry. If email is empty, uses "guest" |
| `get_user_activity(email)` | Return activity list for user |
| `load_activity_log()` | Read JSON file (returns `{}` on error) |
| `save_activity_log(data)` | Write JSON file with indent=4 |

---

## 14. Static Data Schemas

### 14.1 Jobs Database (`src/jobs.json`)

```json
{
    "machine_learning_jobs": [
        {
            "domain": "Machine Learning Engineering",
            "roles": [
                {
                    "job_title": "Machine Learning Engineer",
                    "company": "Google DeepMind",
                    "location": "Mountain View, CA / Remote",
                    "package": "$180k - $320k + Equity",
                    "description": "Build and deploy ML models...",
                    "how_to_get": "1. Master Python & PyTorch...",
                    "apply_link": "https://careers.google.com/..."
                }
            ]
        }
    ]
}
```

**4 domains**: ML Engineering (4 roles), Data Science (3 roles), NLP (2 roles), Computer Vision (1 role)

### 14.2 User Store (`backend/users.json`)

```json
{
    "email@example.com": {
        "email": "email@example.com",
        "password": "salt_hex$pbkdf2_hash_hex"
    }
}
```

> [!CAUTION]
> **File-based user store is not concurrent-safe**. Multiple simultaneous writes can corrupt the JSON file. No file locking is implemented.

---

*Continued in Part 3: Frontend Architecture, Component Tree, State Management, and Security Audit.*
