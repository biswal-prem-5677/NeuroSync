# NeuroSync — Owner Actions

**Version**: 1.0.0
**Date**: 2026-08-01
**Status**: ACTIVE — living register, updated as items are answered or closed
**Owner**: Priyabrata Biswal (this document is *for you*, not about the code)

> Everything in this repository that an engineer can do, gets done without asking.
> This file holds the remainder: **things that are blocked on you** — an account, a
> credential, a person, a legal call, or a decision no engineer is entitled to make.
>
> Nothing here is a request for permission to write code. It is the list of doors I
> cannot open.

**How to use it**: answer inline in the `Your answer` column, or just tell me and I will
record it here and in `10_DECISION_LOG.md`. Items move to §7 when closed.

---

## 0. The short version

If you only do three things, do these, in this order:

| Priority | Action | Unblocks | Your effort |
| --- | --- | --- | --- |
| **1** | Create a free managed PostgreSQL and give me the connection URL | Proving M1's persistence layer actually works on PostgreSQL | ~15 min |
| **2** | Answer **Q4** (§4) — do you have access to real resume/JD pairs and people to rate them? | **M3, the phase doc 15 §21 says most likely kills this project** | 5 min to answer, weeks to source |
| **3** | Answer **Q1** and **Q3** (§4) — business model, and B2C or B2B first | M4, and the shape of M2's screens | Thinking, not typing |

Everything else in this document can wait.

---

## 1. Blocking now — M1 (Trustworthy Core)

### A1 — A real PostgreSQL instance 🔴 **blocking**

**What I need**: a connection URL of the form
`postgresql+psycopg://user:password@host:5432/dbname`

**Why**: the persistence layer shipped on 2026-08-01 (doc 13 D6) is verified end-to-end on
SQLite and verified on PostgreSQL **only as generated DDL** — I rendered the migration for the
PostgreSQL dialect and read it, but no PostgreSQL server has ever executed it. There is none in
this development environment, and no embeddable PostgreSQL exists as a Windows wheel.

Until a real instance runs `alembic upgrade head`, doc 13 D6 says "strongly indicated, not
measured", and it will keep saying that. That is the honest state, and I will not upgrade the
wording without the measurement.

**Options, cheapest first**:

| Option | Cost | Notes |
| --- | --- | --- |
| **Neon** (neon.tech) | $0 | Free tier, serverless Postgres, ~2 min signup. **Recommended for now** |
| **Supabase** | $0 | Free tier; you get an auth system too, which may matter at M2 |
| **Render** | $0 (90-day free) / $7 | Convenient if Render also becomes the app host (see A5) |
| **Docker Desktop locally** | $0 | No account needed, but it is not currently installed here |
| **PostgreSQL installed on this machine** | $0 | Heaviest option; also fine |

This does **not** have to be the production database. A throwaway free-tier instance is enough
to close the verification gap.

**How to hand it to me safely**: put it in `core/backend/.env` — that file is gitignored and
will not be committed. Do **not** paste a live credential into chat. If you would rather not
share a real one at all, create a throwaway database whose credentials you rotate afterwards.

> Small task I own, not you: `app/config.py` does not currently read a `.env` file — env vars
> must be exported in the shell. I will wire `.env` loading when there is a URL to load.

### A2 — Nothing else in M1 is blocked on you

The remaining M1 items — thinning `analyze.py`, the test suite, typed responses (D5), the file
parser, the latency fix — are ordinary engineering and I will keep working them in order.

---

## 2. Needed before M2 can ship (Usable Product = v1.0)

None of these block me today. All of them have lead time, and several depend on DNS or a
payment method, which only you have. Starting them early costs nothing.

| # | What I need | Why | Your effort |
| --- | --- | --- | --- |
| **A3** | A **domain name** | The deployed URL, and email sending needs a verified domain | ~20 min, ~$1/mo amortised (doc 15 §10) |
| **A4** | A **transactional email account** (Resend or Postmark) **+ the DNS records added** | Magic-link auth is the M2 auth model. Only you can edit DNS for your domain | ~30 min, $0 to ~3k emails/mo |
| **A5** | A **hosting account** (Render / Fly / Railway) | M2's exit criterion is a deployed URL a stranger can open. Needs ~1 GB always-on because the ML models stay resident | ~20 min, $20–25/mo (doc 15 §10) |
| **A6** | A **Sentry** account | Doc 15 §13 lists error monitoring as a V1 production requirement | ~10 min, $0 free tier |
| **A7** | **A privacy policy and ToS** (this is doc 15 **Q7**) | Resumes are personal data. You cannot lawfully process a stranger's resume on a public URL without one. Blocks public launch, not development | Depends on **Q2** below; may need a lawyer's read |
| **A8** | **5 strangers** willing to try it unaided | It *is* M2's exit criterion (doc 14 §2.2): ≥4 of 5 finish and say the result was useful | Recruitment, not engineering |

**A8 is the one people skip.** Doc 14 wrote it as a hard exit criterion on purpose. Five people
who are not you, given no help, is the cheapest honest test this product will ever get.

---

## 3. The one that decides the project — M3 (Validated)

### A9 — Ground truth 🔴 **the highest-consequence item in this document**

**What I need**: 50–100 resume/JD pairs, each with a human judgement of how good the match is.

**Why**: the scoring constants — `semantic_floor`, `semantic_ceiling`, `coverage_presence_floor`,
the gap penalty — were fitted against **one** resume-JD pair (doc 15 R2, Critical). They produce
77.23 for a good match and 0.0 for a pastry chef, and the negative controls hold. That is
evidence the direction is right. It is not evidence the *number* means anything.

Doc 15 §21 names this as the single most likely cause of the project failing, and doc 14 placed
M3 **before** M4 so the product cannot be sold on an unvalidated number.

**What I can build without you**: the annotation harness, the rater UI, the correlation
measurement, and a regression suite that fails when the score drifts. All of it.

**What I cannot do**: source real resumes, obtain consent to use them, or supply human raters.

**If real data is genuinely unavailable**, say so and I will propose the fallback — synthetic
pairs built from public JDs and constructed resumes, rated by you against a written rubric. It
is weaker evidence and I would record it in doc 13 as weaker evidence. It is still far better
than n=1.

---

## 4. Decisions only you can make (doc 15 §23, still open)

These were raised by the engineering review on 2026-08-01 and **none has been answered**. I have
added what each one currently costs me, because an unanswered question is not free — it is a
guess I am making silently, or work I am not sequencing.

| # | Question | Blocks | What I am doing meanwhile | Your answer |
| --- | --- | --- | --- | --- |
| **Q1** | What is the **business model**? Free/paid, price, who pays | M4, all unit economics | Assuming nothing. No payment or quota code exists | |
| **Q2** | Will NeuroSync serve **EU/UK** users? | A7, whole compliance posture | Assuming yes (strictest case). The emotion layer is already removed permanently, so the Critical exposure is closed either way | |
| **Q3** | **B2C individuals** or **B2B institutions** first? | Auth model, tenancy, the M2 screens | Assuming B2C single-user. If it is B2B, tenancy has to be designed *before* auth, not after | |
| **Q4** | Access to **annotated pairs or willing raters**? | M3, A9 above | Building toward M3 as if the answer is yes. If it is no, tell me early — the fallback changes what I build | |
| **Q5** | Realistic **weekly time budget** on your side? | Every estimate in doc 15 §11 | Assuming this matters mostly for *your* items (§2 above), not mine | |
| **Q6** | **Software roles only**, or all roles? | Taxonomy scope | Assuming software only. The taxonomy has 294 software skills; "all roles" is a different and much larger problem | |
| **Q7** | Is a **privacy policy / ToS** in place? | Public launch (A7) | Assuming not. Nothing in the repo suggests one exists | |

**Q3 is the one with a hidden deadline.** If NeuroSync is B2B (placement cells, coaches),
multi-tenancy has to exist before auth does — and auth is early in M2. Answering it after M2
starts means rework; answering it now costs nothing.

---

## 5. Small local-environment items (optional, low value)

These are papercuts. Fix them if you feel like it; none blocks anything.

| # | Item | Why it is yours, not mine | Fix |
| --- | --- | --- | --- |
| **A10** | Every `git push` prints `git: 'credential-manager-core' is not a git command` | Global git config is on the "stop and ask first" list (CLAUDE.md §2) | `git config --global credential.helper manager` — the helper was renamed; the binary at `/mingw64/bin/git-credential-manager` is installed and fine. Pushes already work; this is noise |
| **A11** | **Docker Desktop** is not installed | Installing software on your machine | Would give a local PostgreSQL (A1) and let me test the container build for M2 |
| **A12** | The repo lives at `C:\เอกสาร\neurosync` (non-ASCII path) | Moving your files | Some tooling mangles the path in output (pip already does). Nothing has broken. Only worth moving if something does |

---

## 6. Decisions I made for you — please confirm or overrule

I made these because blocking on them would have stopped work, and doc 14 R4 says finish the
item. Each is reversible and each is logged. **Silence = accepted**; say the word and I will
change any of them.

| # | Decision | Where logged | Overrule if… |
| --- | --- | --- | --- |
| **C1** | Persistence is **PostgreSQL**, not the Redis the architecture specified | doc 10 D-007 | You want horizontal scaling sooner than durability |
| **C2** | **3 tables**, not doc 09's 10 or doc 15's 4. `skill_taxonomy_overrides` deferred: persisting promoted skill discoveries would make a promotion permanent, and the D2 noise quarantine is calibrated for a per-process lifetime | doc 10 D-007 §2 | You want discovered skills to accumulate across restarts — it is defensible, it just needs its own measurement |
| **C3** | `users` table built now, **without `password_hash`**, because auth is magic-link | doc 10 D-007 §5 | You want password auth after all (changes Q3's answer too) |
| **C4** | Synchronous SQLAlchemy, not async | doc 10 D-007 §3 | Never, realistically — at ~1 ms per write beside a ~260 ms analysis it is not measurable |
| **C5** | The n=1 scoring calibration **stands until M3** | doc 13 §4 D1 | You want to stop and validate now. Defensible, but M3 needs A9 first |

**Still unowned, awaiting your nod** (doc 13 §2.2 — these three files have no blueprint section
that owns them, which doc 14 R5 says is not allowed to persist):

- `core/backend/test_pipeline.py` — ad-hoc HTTP smoke script. **I propose**: fold into `tests/`
  when the test suite lands, delete the standalone file.
- `core/backend/expand_taxonomy.py` — taxonomy generation script. **I propose**: move to
  `tools/`, where the other probes live, and name it in doc 12's file map.
- `core/backend/app/agents/` — an empty package, 0 bytes. **I propose**: delete it. It implies a
  capability that does not exist, which doc 14 R4 calls worse than nothing.

---

## 7. Answered / closed

*(empty — nothing has been answered yet)*

| Date | Item | Answer | Recorded in |
| --- | --- | --- | --- |

---

## 8. Change log

| Date | Change |
| --- | --- |
| 2026-08-01 | Created after the M1 persistence item landed. 12 owner actions (A1–A12), doc 15 §23's 7 open questions carried forward, 5 engineer-made decisions listed for confirmation |
