# NeuroSync — Execution Rules

**Version**: 1.0.0
**Date**: 2026-08-01
**Status**: ACTIVE — binding on every work session
**Companion**: `/CLAUDE.md` (the short form, auto-loaded each session)

> Blueprints 01–12 describe *what to build*. Doc 13 records *what is built*.
> This document governs *how work is done* — and, more importantly, **what we are aiming at**.

---

## 1. Why this document exists

A system that keeps growing without a destination does not become a product. It becomes a
codebase nobody can finish. NeuroSync is unusually exposed to this: the blueprints describe
an ambitious Career Intelligence Engine across 8 phases, and every phase is genuinely
interesting. That is precisely the danger — interest is not a priority signal.

Two failure modes are being guarded against:

| Failure | What it looks like here |
| --- | --- |
| **No destination** | Phases 3, 3.5, 4 all get partially built; nothing is ever usable by a real person |
| **Unbounded growth** | Every session adds a service; complexity rises, working surface does not |

The rules below exist to make those two outcomes structurally difficult.

---

## 2. The destination

### 2.1 v1.0 — the definition of "finished"

> **A person who is not the author opens NeuroSync in a browser, gives it their resume and a
> job description, and receives a decision they trust: apply or not, why, what to learn first,
> and what changes if they learn it.**

That sentence is the destiny. v1.0 is reached when it is true for a stranger, on a deployed
URL, without the author present. Anything that does not move toward that sentence is not v1.0
work — however well it is described in blueprints 01–12.

Everything beyond that sentence — market intelligence, trajectory simulation, human-state
modelling, gamification — is **post-v1.0**. Those are in the blueprints and they stay there.
They are the reason to build v1.0, not part of it.

### 2.2 Milestones

Milestones are defined by **user-visible capability**, not by architectural layer. This is a
deliberate departure from doc 07's phase order, which builds six backend phases before
anything is usable and puts the frontend at Phase 5. Under that ordering the project can be
80% "complete" and 0% usable. Decision logged in `10_DECISION_LOG.md`.

| # | Milestone | The question it answers | Exit criteria |
| --- | --- | --- | --- |
| **M1** | **Trustworthy Core** | "Is the answer correct?" | D1–D5 closed · latency within NFR 11 §1 · typed responses per doc 08 · test suite exists and passes |
| **M2** | **Usable Product** | "Can a stranger use it?" | File upload · frontend covering the doc 06 core flow · deployed · one non-author completes a real analysis end-to-end |
| **M3** | **Learning Loop** | "Does it improve itself?" | State layer persists across restarts · feedback recalibrates scoring · reasoning + insights engines · `analyze.py` thin (doc 12 Rules 1/3/5) |
| **M4** | **Career Intelligence** | "Is it the PRD's vision?" | Market intelligence · trajectory · human state — the PRD 01 §1 promise in full |

**v1.0 ships at the end of M2.** M3 and M4 are versions 1.1 and 2.0. Shipping M2 is what
converts this from an ambitious project into a product; everything after is improvement on a
thing that already exists and already has users.

### 2.3 Current position

**Active milestone: M1 — Trustworthy Core.**

| Item | Source | State |
| --- | --- | --- |
| D1 scoring miscalibration | 13 §4 | ✅ 2026-07-31 |
| D2 extraction noise | 13 §4 | ✅ 2026-07-31 |
| D3 gap cluster mislabeling | 13 §4 | ✅ 2026-07-31 |
| D4 latency + spaCy warm-up | 13 §4 | ⬜ **next** |
| D5 API contract drift | 13 §4 | ⬜ |
| `utils/file_parser.py` + `/analyze-file` | 07 §2.3 | ⬜ |
| `api/responses.py` typed models | 07 §2.4 | ⬜ |
| Edge-case hardening | 07 §2.5 | ⬜ |
| Test suite | 07 §6.1 | ⬜ |

M1 is the only list being worked. When an item here is closed it is committed, pushed, and
struck from this table in the same commit.

---

## 3. Rules

### R1 — `legacy/` is frozen

`legacy/java_demo/` is a completed academic project retained for provenance. It is never
read, edited, refactored, cited in a design, counted in an audit, or explained. It is not a
migration source. The only permitted interaction is leaving it alone.

If a request appears to require it, the request is mistaken — say so rather than complying.

### R2 — Every change reaches GitHub

The unit of work is not a working change; it is a **pushed** change.

```
verify  →  update doc 13  →  commit  →  push  →  report
```

- No session ends with uncommitted work.
- No batching "until it's all done" — a milestone item is one or more commits, each pushed.
- Commits are pushed to `origin/master` without asking. This authorization is standing.
- Commit messages state what changed **and the measurement that proves it**.

Stop and ask before: force-pushing or rewriting published history, committing anything
resembling a secret, deleting user data, or changing global git/system configuration.

### R3 — Done means measured

A claim of completion requires evidence produced in the same session:

1. The probe or test **ran**, and its output is visible.
2. A defect fix carries **before/after numbers on the same input**. The "before" is produced
   by disabling the fix and re-running — never by quoting an earlier note as if fresh.
3. Regression gates pass: `verify_d1.py` and `tools.noise_probe`.
4. Doc 13 is updated in the same commit as the code.

Unmeasured work is reported as unverified. ✅ is never written against something not run.
When a fix is impossible or blocked, that is stated plainly — a blocked item left honest is
worth more than a green tick that lies.

### R4 — One milestone, one task

Work the next open item of the **current** milestone. Not the most interesting item, not a
later milestone, not an appealing refactor noticed in passing.

Finish before starting. A half-built service is worse than an unbuilt one: it carries
maintenance cost and implies a capability that does not exist.

### R5 — Scope control

Every new idea meets one of three fates:

| Fate | When |
| --- | --- |
| Built now | It is an exit criterion of the **current** milestone |
| Recorded | It serves a later milestone → tracker backlog or `blueprints/vision/` |
| Declined | It serves neither → say so and move on |

No new file is created without naming the blueprint section that owns it. No owner means the
blueprint is amended first and the decision logged in `10_DECISION_LOG.md`.

Adding a service is a cost, not an achievement. The measure of a good session is capability
gained per unit of complexity added — sometimes the best change removes code.

### R6 — Documents stay honest

- Blueprints 01–12 = intent. Doc 13 = verified fact. Doc 14 = process and destination.
- On conflict: doc 13 wins on facts, blueprints win on intent. The wrong one is corrected in
  the same commit, and the correction is logged in `10_DECISION_LOG.md`.
- Doc 13 is never edited to look better than the code. A defect entry records its before/after
  measurement rather than being deleted.

### R7 — Report plainly

Each session's report states: what was done, the measurement proving it, what was skipped and
why, and the single next action. No progress theatre, no percentages that were not computed.

---

## 4. Session checklist

**Start** — read doc 13 §6 and §2.3 above; identify the one next item; confirm it belongs to
the active milestone.

**During** — measure before claiming; keep the change scoped to the item; note anything found
along the way in the backlog rather than fixing it opportunistically.

**End** — regression gates green · doc 13 updated · committed · **pushed** · working tree
clean · next action named.

---

## 5. Change log

| Date | Change |
| --- | --- |
| 2026-08-01 | Created. Destination defined; milestones reordered around user-visible capability (v1.0 = end of M2); `legacy/` frozen; push-per-change and measured-done rules made binding |
