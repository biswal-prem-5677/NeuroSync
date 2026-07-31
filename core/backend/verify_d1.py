"""Temporary D1 verification harness — reproduces the tracker's §4 scenario in-process."""
import time
from fastapi.testclient import TestClient

from app.main import app

# Verbatim copies of the fixtures in test_pipeline.py, which cannot be imported
# because it fires HTTP requests at module scope.
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


UNRELATED_JD = """
Head Pastry Chef - Fine Dining

We are seeking an experienced Head Pastry Chef for our Michelin-starred restaurant.

Requirements:
- 5+ years in a professional pastry kitchen
- Mastery of laminated doughs, chocolate tempering, and sugar work
- Experience managing kitchen staff and rota scheduling
- Food hygiene certification and allergen management
- Menu costing and supplier negotiation
- Ability to work evenings, weekends and holidays
"""

ADJACENT_JD = """
Frontend Engineer - Design Systems

We are looking for a Frontend Engineer to own our component library.

Requirements:
- Strong React and TypeScript
- CSS architecture, accessibility (WCAG), responsive design
- Storybook, visual regression testing
- Collaborating closely with designers on Figma handoff
- Build tooling with Vite and bundle performance budgets
"""


def controls(client) -> list[tuple[str, dict | int]]:
    """A calibration that only inflates scores is not a fix. These must stay low."""
    out = []
    for label, jd in (("adjacent (frontend)", ADJACENT_JD),
                      ("unrelated (pastry chef)", UNRELATED_JD)):
        rc = client.post("/api/v1/analyze",
                         json={"resume_text": RESUME, "jd_text": jd})
        out.append((label, rc.json()["decision"] if rc.status_code == 200
                    else rc.status_code))
    return out


def main() -> None:
    with TestClient(app) as client:
        # Warm once so the reported timing is not the cold-start spike.
        client.post("/api/v1/analyze", json={"resume_text": RESUME, "jd_text": JD})

        start = time.perf_counter()
        r = client.post("/api/v1/analyze", json={
            "resume_text": RESUME, "jd_text": JD,
            "include_simulations": True, "include_evidence": True,
        })
        elapsed = (time.perf_counter() - start) * 1000
        control_results = controls(client)

    if r.status_code != 200:
        print("HTTP", r.status_code, r.text[:2000])
        return

    d = r.json()
    dec, sc, sk = d["decision"], d["scoring"], d["skills"]

    print("=" * 72)
    print("DECISION")
    print("=" * 72)
    print(f"  overall_score          {dec['overall_score']}")
    print(f"  fit_level              {dec['fit_level']}")
    print(f"  recommendation         {dec['recommendation']}")
    print(f"  shortlist_probability  {dec['shortlist_probability']}")
    print(f"  confidence             {dec['confidence']}")

    print("\nSCORING")
    print(f"  semantic       {sc['semantic_score']}")
    print(f"  skill_overlap  {sc['skill_overlap_score']}")
    print(f"  gap_penalty    {sc['gap_penalty']}")
    print(f"  {sc['explanation']}")

    print("\nCOVERAGE")
    print(f"  requirement groups   {sk['jd_count']} jd skills")
    print(f"  matched / missing    {sk['matched']} / {sk['missing']}")
    print(f"  overlap_score        {sk['overlap_score']}")
    if "implied_matches" in sk:
        print(f"  implied matches      {sk['implied_matches']}")
    if "requirements" in d:
        rq = d["requirements"]
        print(f"  total groups         {rq.get('total')}")
        print(f"  alternative groups   {rq.get('alternative')}")
        print(f"  optional groups      {rq.get('optional')}")

    print(f"\nGAPS ({len(d['gaps'])})")
    for g in d["gaps"]:
        alts = g.get("alternatives") or []
        alt_s = f"  alts={alts}" if alts else ""
        opt_s = "  [optional]" if g.get("optional") else ""
        print(f"  - {g['skill']:<28} {g['priority']:<9}{opt_s}{alt_s}")

    print("\nTOP SIMULATIONS")
    for s in d.get("simulations", []):
        print(f"  +{s['skill_added']:<24} {s['current_score']} -> "
              f"{s['projected_score']} ({s['delta']:+}) {s['new_fit_level']}")

    print(f"\nlatency (warm): {elapsed:.0f}ms   server: {d['meta']['processing_time_ms']}ms")

    print("\nD3 CHECK — cluster labels in reasoning")
    for g in d["gaps"][:3]:
        print(f"  * {g['skill']}: {g['reasoning'][:170]}")

    print("\n" + "=" * 72)
    print("NEGATIVE CONTROLS — same resume, jobs it does not fit")
    print("=" * 72)
    for label, dd in control_results:
        if isinstance(dd, int):
            print(f"  {label:<26} HTTP {dd}")
        else:
            print(f"  {label:<26} score={dd['overall_score']:<6} "
                  f"{dd['fit_level']:<14} {dd['recommendation']}")


if __name__ == "__main__":
    main()
