"""Quick end-to-end pipeline test."""
import requests
import json

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

r = requests.post(
    "http://127.0.0.1:8000/api/v1/analyze",
    json={"resume_text": RESUME, "jd_text": JD, "include_simulations": True, "include_evidence": True},
)
d = r.json()

print("=== DECISION ===")
dec = d["decision"]
print(f"  Score:          {dec['overall_score']}")
print(f"  Recommendation: {dec['recommendation']}")
print(f"  Fit Level:      {dec['fit_level']}")
print(f"  Shortlist Prob: {dec['shortlist_probability']}")
print(f"  Confidence:     {dec['confidence']}")
print()
print("=== SCORING ===")
print(f"  {d['scoring']['explanation']}")
print()
print("=== RESUME SKILLS ===")
for s in d["skills"]["resume_skills"][:10]:
    print(f"  {s['name']:25s} {s['proficiency']:.0%}  (via {s['matched_by']})")
print(f"  ... {d['skills']['resume_count']} total")
print()
print("=== GAPS ===")
for g in d["gaps"][:8]:
    print(f"  [{g['priority'].upper():8s}] {g['skill']:25s} {g['learning_time'] or ''}")
print(f"  ... {len(d['gaps'])} total gaps")
print()
print("=== IMPROVEMENT PATH ===")
for i in d["improvement_path"]:
    print(f"  #{i['rank']} {i['skill']:15s} +{i['impact']:.1f} pts  {i['learning_time']}")
print()
print("=== SIMULATIONS ===")
for s in d["simulations"]:
    print(f"  Learn {s['skill_added']:15s}: {s['current_score']:.1f} -> {s['projected_score']:.1f} (+{s['delta']:.1f})")
print()
print("=== STRENGTHS ===")
for s in d["strengths"]:
    print(f"  + {s}")
print()
print("=== WEAKNESSES ===")
for w in d["weaknesses"]:
    print(f"  - {w}")
print()
print(f"Processing time: {d['meta']['processing_time_ms']:.0f}ms")
print(f"Semantic available: {d['meta']['semantic_available']}")
