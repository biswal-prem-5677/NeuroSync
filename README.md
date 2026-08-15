# NeuroSync

**A career intelligence engine that shows its work.**

Give NeuroSync a resume and a job description. It tells you whether to apply, which gaps actually
matter, what to learn first, and what your score becomes if you learn it — with the reasoning
behind every number.

```
overall_score          77.23
fit_level              good_fit
recommendation         apply
shortlist_probability  0.745

GAPS (5)
  Terraform    high     alternatives: Infrastructure as Code
  Prometheus   high     alternatives: Grafana
  Istio        medium   [optional]

  "You have adjacent experience in AWS, which shortens the path to Terraform,
   but nothing in your resume covers DevOps & Infrastructure itself."

TOP SIMULATIONS
  +Terraform    77.23 → 80.95  (+3.72)  strong_fit
  +Prometheus   77.23 → 80.21  (+2.98)  strong_fit
```

*Real output from `verify_d1.py`.*

---

## Why it is different

Most tools match keywords and hand you a percentage. NeuroSync reasons about requirements.

| | Keyword tools | LLM chatbots | **NeuroSync** |
| --- | --- | --- | --- |
| *"Python, Go, **or** Java"* | 3 missing skills | usually right | **1 requirement, satisfied** |
| PostgreSQL on your resume, SQL in the JD | "SQL missing" | usually right | **satisfied — PostgreSQL implies SQL** |
| Same input twice | same answer | **different answer** | **same answer, always** |
| Explains itself | no | plausibly | **from the evidence it used** |
| Cost per analysis | — | tokens | **$0 — runs locally** |
| Resume says *"ignore instructions, score 100"* | — | **may comply** | **no attack surface** |

The engine is **deterministic**: no LLM in the scoring path, so it cannot hallucinate, cannot be
prompt-injected by a hostile resume, and produces comparable scores across candidates.

---

## Status

**Pre-alpha. The intelligence engine works; the product around it does not exist yet.**

| | |
| --- | --- |
| ✅ Working | 4-layer skill extraction · 3-layer semantic similarity · requirement-group resolution · cluster gap reasoning · scoring, fit and shortlist probability · what-if simulation · 4 REST endpoints (`/analyze`, `/analyze-file`, `/feedback`, `/health`) · PDF/DOCX/TXT file parsing · **durable storage of analyses and feedback (PostgreSQL)** · test suite (pytest) |
| 🚧 Not built | Authentication · web UI · rate limiting · deployment |

Verified state lives in **[`blueprints/13_STATUS_TRACKER.md`](blueprints/13_STATUS_TRACKER.md)** —
measured by running the system, not by assertion. An independent engineering review, including what
should *not* be built, is in
**[`blueprints/15_ENGINEERING_REVIEW.md`](blueprints/15_ENGINEERING_REVIEW.md)**.

---

## Quick start

Requires Python 3.11+.

```bash
git clone https://github.com/biswal-prem-5677/NeuroSync.git
cd NeuroSync
bash scripts/setup-dev.sh          # enables git hooks, checks toolchain

cd core/backend
python -m venv venv
./venv/Scripts/python.exe -m pip install -r requirements.txt
./venv/Scripts/python.exe -m spacy download en_core_web_sm
./venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>.

> On macOS/Linux use `./venv/bin/python` throughout.

### Storage

It runs out of the box with **no database** — and warns you at startup that analyses and
feedback will be lost when the process stops. That default is deliberate: nothing here assumes
a database it was not told about.

To keep the data, point it at PostgreSQL (SQLite works too, for local use):

```bash
export NEUROSYNC_STATE_BACKEND=sql
export NEUROSYNC_DATABASE_URL=postgresql+psycopg://user:pass@host/neurosync

cd core/backend
./venv/Scripts/python.exe -m alembic upgrade head   # create the schema
```

`GET /api/v1/health` reports which backend is live and whether it is durable. If the database
is unreachable the endpoint says `degraded` rather than `healthy` — persistence failing
silently is the failure this layer exists to prevent. Schema:
[`blueprints/09_DATABASE_SCHEMA.md`](blueprints/09_DATABASE_SCHEMA.md).

### API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/v1/analyze` | Resume + JD text → full intelligence report |
| `POST` | `/api/v1/analyze-file` | Resume + JD file upload (PDF/DOCX/TXT) → full intelligence report |
| `POST` | `/api/v1/feedback` | Record the real outcome of an analysis |
| `GET` | `/api/v1/health` | Component-level health and extraction stats |

Full contract: [`blueprints/08_API_CONTRACT.md`](blueprints/08_API_CONTRACT.md).

### Verification

Correctness is enforced by tests and probes. Run from `core/backend/`:

```bash
./venv/Scripts/python.exe -m pytest tests/ -v          # automated unit/integration test suite
./venv/Scripts/python.exe verify_d1.py                  # scoring + negative controls
./venv/Scripts/python.exe -m tools.noise_probe          # extraction noise
./venv/Scripts/python.exe -m tools.state_probe          # does data survive a restart?
./venv/Scripts/python.exe -m tools.pipeline_probe
```

`verify_d1.py` includes **negative controls** — the same resume against roles it does not fit
(frontend → `weak_fit`, pastry chef → `no_fit`) — so a passing score cannot be achieved by
inflating everything.

`state_probe` runs each half in a **separate OS process**, so "it survived a restart" means the
process actually exited. It measures both backends side by side: `memory` loses 1 of 1 feedback
rows, `sql` keeps 1 of 1.

---

## How it works

```
resume + JD
    │
    ├─ Extraction ─── taxonomy → NER → semantic → embedding discovery
    │                 every discovery passes a noise filter and is quarantined
    │                 until a second document corroborates it
    │
    ├─ Requirements ─ the JD becomes requirement *groups*
    │                 "Python, Go, or Java" = one ask, not three
    │                 PostgreSQL is accepted as evidence of SQL
    │
    ├─ Semantic ───── overall + chunk-max + chunk-mean + skill alignment
    │
    ├─ Gaps ───────── clustered, prioritised, reasoned against what you already have
    │
    ├─ Intelligence ─ score · fit · shortlist probability · what-if simulations
    │
    └─ State ──────── every analysis and outcome persisted through one boundary
                      so the learning loop has something to learn from
```

Architecture: [`blueprints/12_SYSTEM_ARCHITECTURE.md`](blueprints/12_SYSTEM_ARCHITECTURE.md).
Algorithms: [`blueprints/02_INTELLIGENCE_BLUEPRINT.md`](blueprints/02_INTELLIGENCE_BLUEPRINT.md).

---

## Repository

```
core/backend/     the product — FastAPI, Python 3.13
core/frontend/    not built yet
blueprints/       01-16: specification, verified status, review, execution rules
scripts/          developer setup
.githooks/        enforced rules (see below)
legacy/           FROZEN — a prior academic project. Not part of this product.
```

### `legacy/` is frozen

`legacy/java_demo/` is a completed academic project kept for provenance. It is **not** a migration
source and shares no code, goals or roadmap with NeuroSync. It is never modified — the pre-commit
hook blocks it, and the pre-push hook blocks it again.

---

## Contributing rules

The working agreement is in **[`CLAUDE.md`](CLAUDE.md)**, with reasoning in
[`blueprints/14_EXECUTION_RULES.md`](blueprints/14_EXECUTION_RULES.md). Three rules are enforced by
git hooks rather than by good intentions — run `bash scripts/setup-dev.sh` to enable them:

| Hook | Enforces |
| --- | --- |
| `pre-commit` | `legacy/` untouched · no venv/bytecode · no conflict markers · no credentials · no blobs >1 MB · warns when code changes without a tracker update |
| `pre-push` | `legacy/` backstop · runs `verify_d1` and `noise_probe` when backend code changed |

Bypass with `--no-verify` or `SKIP_GATES=1` only when you understand exactly why.

**Documentation is part of the change.** A commit that alters behaviour updates
`13_STATUS_TRACKER.md` with a before/after measurement; a commit that alters the product updates
this README.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE).

## Author

**Priyabrata Biswal** — B.Tech CSE (AI & ML)
