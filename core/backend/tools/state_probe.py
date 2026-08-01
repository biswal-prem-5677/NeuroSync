"""
NeuroSync — State Persistence Probe (doc 15 R3 / doc 14 M1).

Answers one question with a number: **does recorded feedback survive a restart?**

The restart is real. Each phase runs in its own OS process, so nothing carries
over in module globals — which is exactly how the old `_feedback_log` list
appeared to work in a single test run and lost everything in production.

Both backends are measured on the same script, so the "before" column is a live
run of the volatile path rather than a quotation from an earlier note:

    memory  → feedback recorded, then gone after the restart
    sql     → feedback recorded, still there after the restart

Usage (from core/backend/):
    ./venv/Scripts/python.exe -m tools.state_probe
    ./venv/Scripts/python.exe -m tools.state_probe --backend sql   # one backend

Internal (spawned by the orchestrator, not for direct use):
    --phase analyze | feedback
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.pipeline_probe import JD, RESUME  # noqa: E402  (path set above)

STATE_FILE = "analysis_id.txt"      # how phase 1 tells phase 2 what to look up


# =========================================================================
# PHASES — each runs in a fresh process
# =========================================================================

def phase_analyze(workdir: Path) -> int:
    """Boot the app, run one analysis, record feedback against it, then exit."""
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={
            "resume_text": RESUME,
            "jd_text": JD,
            "include_simulations": False,
            "include_evidence": False,
        })
        response.raise_for_status()
        body = response.json()
        analysis_id = body["analysis_id"]
        (workdir / STATE_FILE).write_text(analysis_id, encoding="utf-8")

        # Record an outcome *before* the restart. This is the row whose survival
        # is being measured; everything else is setup.
        feedback = client.post("/api/v1/feedback", json={
            "analysis_id": analysis_id,
            "outcome": "interview",
            "notes": "state probe — written before restart",
        })
        feedback.raise_for_status()

    print(json.dumps({
        "analysis_id": analysis_id,
        "score": round(body["decision"]["overall_score"], 2),
        "decision_found": feedback.json()["decision_found"],
        "feedback_count": feedback.json()["feedback_stats"]["count"],
    }))
    return 0


def phase_feedback(workdir: Path) -> int:
    """
    Fresh process — the restart.

    Reads `/health` *before* writing anything, so the feedback count it reports
    is what survived, not what this process just created.
    """
    from fastapi.testclient import TestClient
    from app.main import app

    analysis_id = (workdir / STATE_FILE).read_text(encoding="utf-8").strip()

    with TestClient(app) as client:
        boot_health = client.get("/api/v1/health").json()
        survived = boot_health["components"]["feedback"].get("count", 0)

        # A correction to the earlier outcome. On a durable backend this updates
        # the existing row (one outcome per analysis), so the count stays put.
        feedback = client.post("/api/v1/feedback", json={
            "analysis_id": analysis_id,
            "outcome": "hired",
            "notes": "state probe — written after restart",
        })
        feedback.raise_for_status()
        body = feedback.json()

        health = client.get("/api/v1/health").json()

    print(json.dumps({
        "analysis_id": analysis_id,
        "feedback_at_boot": survived,
        "decision_found": body["decision_found"],
        "feedback_stats": body["feedback_stats"],
        "state": health["components"]["state"],
    }))
    return 0


# =========================================================================
# ORCHESTRATOR
# =========================================================================

def _run_phase(phase: str, workdir: Path, env: dict[str, str]) -> dict:
    """Run one phase in a child process and return its JSON verdict."""
    result = subprocess.run(
        [sys.executable, "-m", "tools.state_probe",
         "--phase", phase, "--workdir", str(workdir)],
        cwd=str(Path(__file__).resolve().parent.parent),
        env=env, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit(f"phase '{phase}' failed with exit code {result.returncode}")
    # The app logs to stderr; stdout carries only the JSON verdict.
    return json.loads(result.stdout.strip().splitlines()[-1])


def _migrate(database_url: str, env: dict[str, str]) -> None:
    """Build the schema with the real Alembic migration, not `create_all`."""
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(Path(__file__).resolve().parent.parent),
        env={**env, "NEUROSYNC_DATABASE_URL": database_url},
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit("alembic upgrade head failed")
    print("  migration: alembic upgrade head OK")


def measure(backend: str, workdir: Path) -> dict:
    """Run analyze → restart → feedback for one backend."""
    env = {**os.environ, "NEUROSYNC_STATE_BACKEND": backend}
    workdir.mkdir(parents=True, exist_ok=True)

    if backend == "sql":
        # Forward slashes: a Windows backslash path is not a valid SQLAlchemy URL.
        db_path = (workdir / "probe.db").as_posix()
        database_url = f"sqlite:///{db_path}"
        env["NEUROSYNC_DATABASE_URL"] = database_url
        _migrate(database_url, env)

    print("  process 1: analyze + record feedback …")
    first = _run_phase("analyze", workdir, env)
    print(f"    analysis_id={first['analysis_id']} score={first['score']} "
          f"feedback_written={first['feedback_count']}")

    print("  process 2: RESTART, then read …")
    second = _run_phase("feedback", workdir, env)
    print(f"    feedback visible at boot={second['feedback_at_boot']} "
          f"analysis_found={second['decision_found']}")

    return {
        "backend": backend,
        "durable": second["state"].get("durable"),
        "written_before": first["feedback_count"],
        "survived": second["feedback_at_boot"],
        "analysis_survived": second["decision_found"],
        "feedback_count": second["feedback_stats"].get("count", 0),
        "avg_score": second["feedback_stats"].get("avg_score"),
        "state": second["state"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("analyze", "feedback"))
    parser.add_argument("--workdir")
    parser.add_argument("--backend", choices=("memory", "sql"), action="append")
    args = parser.parse_args()

    if args.phase:
        return {"analyze": phase_analyze, "feedback": phase_feedback}[args.phase](
            Path(args.workdir)
        )

    backends = args.backend or ["memory", "sql"]

    print("=" * 72)
    print("NeuroSync — state persistence probe")
    print("Each backend: analyze in one process, feedback in a NEW process.")
    print("=" * 72)

    results = []
    with tempfile.TemporaryDirectory(prefix="neurosync_state_probe_") as tmp:
        for backend in backends:
            print(f"\n[{backend}]")
            results.append(measure(backend, Path(tmp) / backend))

    print()
    print("=" * 72)
    print(f"{'backend':<10}{'durable':<10}{'feedback written':<19}"
          f"{'survived restart':<19}{'analysis survived':<18}")
    print("-" * 72)
    for r in results:
        print(f"{r['backend']:<10}{str(r['durable']):<10}{r['written_before']:<19}"
              f"{r['survived']:<19}{str(r['analysis_survived']):<18}")
    print("=" * 72)

    # A backend claiming durability must actually be durable.
    failures = [
        r for r in results
        if r["durable"] and not (r["analysis_survived"] and r["survived"] >= r["written_before"] >= 1)
    ]
    if failures:
        print("VERDICT: FAIL — a durable backend lost data across a restart")
        return 1

    sql = next((r for r in results if r["backend"] == "sql"), None)
    if sql is not None:
        print(f"VERDICT: PASS — sql retained the analysis and {sql['survived']} "
              f"feedback row(s) across a restart")
    else:
        print("VERDICT: PASS (no durable backend measured)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
