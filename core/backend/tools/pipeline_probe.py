"""
NeuroSync — Pipeline Probe.

Reproducible in-process measurement of the defects tracked in
blueprints/13_STATUS_TRACKER.md §4 (D1-D5). Run before and after a change and
diff the output — the tracker requires before/after numbers, not assertions.

Usage (from core/backend/):
    ./venv/Scripts/python.exe tools/pipeline_probe.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

RESUME = """
Priyabrata Biswal
Software Engineer | Full Stack Developer

EXPERIENCE
Senior Software Engineer, TechCorp (2024-2026)
- Built production-grade REST APIs using Python and FastAPI, serving 10M+ requests/month
- Designed and implemented microservices architecture with Docker and Kubernetes on AWS
- Led migration of monolithic application to event-driven architecture using Apache Kafka
- Implemented CI/CD pipelines using GitHub Actions and ArgoCD
- Mentored 5 junior developers on clean code practices and system design

Software Developer, StartupXYZ (2022-2024)
- Developed full-stack web applications using React, TypeScript, and Node.js
- Built real-time data processing pipeline using Python, Pandas, and Apache Spark
- Designed PostgreSQL database schemas optimized for high-throughput analytics
- Integrated machine learning models for recommendation engine using scikit-learn

PROJECTS
NeuroSync - Career Intelligence Engine
- Built semantic similarity engine using sentence-transformers and spaCy NER
- Implemented 4-layer hybrid skill extraction with embedding discovery
- Designed cluster-based gap analysis with what-if simulation engine

SKILLS
Python, JavaScript, TypeScript, React, FastAPI, Django, Node.js, Docker, PostgreSQL,
MongoDB, Redis, AWS, Git, Linux, Machine Learning, Deep Learning, NLP, TensorFlow,
PyTorch, scikit-learn, Pandas, NumPy, Kafka, System Design, Agile

EDUCATION
B.Tech Computer Science, XYZ University (2018-2022) - CGPA: 8.5
"""

JD = """
Senior Backend Engineer - Cloud Infrastructure

We are looking for a Senior Backend Engineer to join our Cloud Infrastructure team.

Requirements:
- 3+ years of experience with Python, Go, or Java
- Strong experience with Kubernetes and container orchestration
- Experience with cloud platforms (AWS, GCP, or Azure)
- Experience with Terraform or similar infrastructure-as-code tools
- Strong understanding of microservices architecture and distributed systems
- Experience with CI/CD pipelines and DevOps practices
- Knowledge of monitoring tools like Prometheus and Grafana
- Experience with message queues (Kafka, RabbitMQ)
- Strong SQL and database design skills
- Experience with Redis or similar caching solutions

Nice to have:
- Experience with GraphQL
- Knowledge of service mesh (Istio, Linkerd)
- Experience with machine learning infrastructure
- Open source contributions

We offer competitive salary, remote work, and continuous learning opportunities.
"""

# Skills this candidate demonstrably holds or subsumes. A gap reported against
# any of these is a false positive (D1).
EXPECTED_NON_GAPS = {
    "python", "kubernetes", "aws", "microservices", "distributed systems",
    "ci/cd", "kafka", "apache kafka", "redis", "sql", "cloud computing",
    "devops", "postgresql", "docker", "machine learning",
}


def main() -> int:
    from fastapi.testclient import TestClient

    from app.main import app
    from app.utils.skill_taxonomy import SkillTaxonomy

    payload = {
        "resume_text": RESUME,
        "jd_text": JD,
        "include_simulations": True,
        "include_evidence": True,
    }

    with TestClient(app) as client:
        health = client.get("/api/v1/health").json()

        t0 = time.perf_counter()
        cold = client.post("/api/v1/analyze", json=payload)
        cold_ms = (time.perf_counter() - t0) * 1000

        # Second run on distinct text so the extraction cache cannot mask latency.
        warm_payload = dict(payload, resume_text=RESUME + "\nAdditional note.")
        t0 = time.perf_counter()
        client.post("/api/v1/analyze", json=warm_payload)
        warm_ms = (time.perf_counter() - t0) * 1000

        if cold.status_code != 200:
            print(f"FAILED: /analyze returned {cold.status_code}\n{cold.text}")
            return 1

        d = cold.json()
        dec, skills = d["decision"], d["skills"]
        gaps = d["gaps"]

        print("=" * 72)
        print("D1 — DECISION CORRECTNESS")
        print("=" * 72)
        print(f"  overall_score          {dec['overall_score']}")
        print(f"  recommendation         {dec['recommendation']}")
        print(f"  fit_level              {dec['fit_level']}")
        print(f"  shortlist_probability  {dec['shortlist_probability']}")
        print(f"  matched / jd_skills    {skills['matched']} / "
              f"{skills['matched'] + skills['missing']}")
        print(f"  overlap_score          {skills['overlap_score']}")
        print(f"  gap_penalty            {d['scoring']['gap_penalty']}")
        print(f"  total gaps             {len(gaps)}")

        false_gaps = [g["skill"] for g in gaps
                      if g["skill"].lower() in EXPECTED_NON_GAPS]
        print(f"  FALSE gaps ({len(false_gaps)}):        "
              f"{', '.join(false_gaps) if false_gaps else '(none)'}")
        print("  all gaps:")
        for g in gaps:
            flag = "  <-- FALSE" if g["skill"].lower() in EXPECTED_NON_GAPS else ""
            print(f"    [{g['priority']:8s}] {g['skill']}{flag}")

        print()
        print("=" * 72)
        print("D2 — TAXONOMY POLLUTION (runtime-registered skills)")
        print("=" * 72)
        taxonomy = SkillTaxonomy()
        runtime = sorted(e.canonical for e in taxonomy._runtime_skills.values())
        print(f"  runtime skills registered: {len(runtime)}")
        for name in runtime:
            print(f"    - {name}")

        print()
        print("=" * 72)
        print("D3 — GAP CLUSTER LABELS")
        print("=" * 72)
        for g in gaps[:5]:
            print(f"  {g['skill']}: {g['reasoning'][:180]}")

        print()
        print("=" * 72)
        print("D4 — LATENCY")
        print("=" * 72)
        print(f"  /analyze cold          {cold_ms:.0f}ms   (target < 2000ms)")
        print(f"  /analyze warm          {warm_ms:.0f}ms   (target < 2000ms)")

        print()
        print("=" * 72)
        print("D5 — HEALTH / CONTRACT")
        print("=" * 72)
        print(f"  health: {json.dumps(health, indent=2)[:600]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
