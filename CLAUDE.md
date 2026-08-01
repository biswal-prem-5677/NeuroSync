# NeuroSync — Working Agreement

Loaded automatically every session. The full reasoning behind these rules lives in
`blueprints/14_EXECUTION_RULES.md`; this file is the short form that must be obeyed.

---

## 1. `legacy/` does not exist

`legacy/java_demo/` is a finished academic project, kept for provenance only.

**Never** read it, edit it, refactor it, reference it in a design, count it in an audit, or
spend a single token explaining it. It is not a migration source and has no future in this
product. If a task seems to require it, the task is wrong — say so instead.

The only permitted interaction is leaving it alone.

## 2. Every change ends on GitHub

A change is not done when it works. It is done when it is **committed and pushed**.

```
verify → update tracker → update README if the product changed → commit → push → report
```

No session ends with uncommitted work in the tree. No "I'll batch these up." Standing
authorization: commit and push to `origin/master` without asking, provided §3 passes.

Exception — stop and ask first if the change touches secrets, deletes user data, rewrites
published history (`push --force`), or changes global git/system config.

**README is part of the deliverable.** If a change alters what the product does, how it is run,
or what is working, `README.md` is updated in the same commit. It is the only document most
people will ever read; a stale README is a bug.

**These rules are enforced by git hooks**, not by memory — `.githooks/pre-commit` and
`.githooks/pre-push`, installed via `bash scripts/setup-dev.sh`. Never bypass with
`--no-verify` or `SKIP_GATES=1` without saying so explicitly in the report.

## 3. Done means measured, not asserted

Before any commit:

- The relevant probe or test **ran**, and its output is in the transcript.
- A defect fix carries a **before/after number** on the same input. Reproduce the "before" by
  disabling the fix — never quote an old note as if freshly measured.
- No regression: `tools/noise_probe.py` and `verify_d1.py` still pass.
- `blueprints/13_STATUS_TRACKER.md` is updated in the same commit as the code.

If it wasn't measured, report it as unverified. Never write ✅ against something not run.

## 4. One milestone. One task. Finish it.

Current destination and milestone live in `blueprints/14_EXECUTION_RULES.md` §2, mirrored in
the tracker. Work the current milestone's next open item — not the most interesting one.

Anything outside the current milestone goes to `blueprints/vision/` or the tracker backlog.
It does **not** get built now, however good the idea. Scope growth is this project's main
risk, not slow progress.

Before adding any new file, name the blueprint section that owns it. No owner → don't build
it; amend the blueprint first and log the decision in `10_DECISION_LOG.md`.

## 5. Blueprints are the constitution, the tracker is the truth

- Blueprints 01–12 say what the system **should** be.
- `13_STATUS_TRACKER.md` says what it **actually is**, verified by running it.
- On conflict, the tracker wins for facts and the blueprint wins for intent. Fix the doc that
  is wrong, in the same commit, and log it.

## 6. Project shape

```
core/backend/     the product — FastAPI, Python 3.13, venv at core/backend/venv
core/frontend/    not built yet (milestone M2)
blueprints/       01-14 constitution + tracker + vision
legacy/           frozen. see §1.
```

Run anything from `core/backend/` with `./venv/Scripts/python.exe`.

| Command | Purpose |
| --- | --- |
| `./venv/Scripts/python.exe verify_d1.py` | Scoring correctness + negative controls |
| `./venv/Scripts/python.exe -m tools.noise_probe` | Extraction noise |
| `./venv/Scripts/python.exe -m tools.pipeline_probe` | End-to-end pipeline |
