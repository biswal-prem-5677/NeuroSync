"""
NeuroSync — Test Fixtures (conftest.py).
Shared fixtures for FastAPI TestClient and test documents.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    """FastAPI TestClient session fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def sample_resume():
    return """
Priyabrata Biswal
Software Engineer | Full Stack Developer

EXPERIENCE
Senior Software Engineer, TechCorp (2024-2026)
- Built production-grade REST APIs using Python and FastAPI, serving 10M+ requests/month
- Designed and implemented microservices architecture with Docker and Kubernetes on AWS
- Led migration of monolithic application to event-driven architecture using Apache Kafka
- Implemented CI/CD pipelines using GitHub Actions and ArgoCD

Software Developer, StartupXYZ (2022-2024)
- Developed full-stack web applications using React, TypeScript, and Node.js
- Built real-time data processing pipeline using Python, Pandas, and Apache Spark
- Designed PostgreSQL database schemas optimized for high-throughput analytics
- Integrated machine learning models for recommendation engine using scikit-learn

SKILLS
Python, JavaScript, TypeScript, React, FastAPI, Django, Node.js, Docker, PostgreSQL,
MongoDB, Redis, AWS, Git, Linux, Machine Learning, Deep Learning, NLP, TensorFlow,
PyTorch, scikit-learn, Pandas, NumPy, Kafka, System Design, Agile

EDUCATION
B.Tech Computer Science, XYZ University (2018-2022)
"""


@pytest.fixture(scope="session")
def sample_jd():
    return """
Senior Backend Engineer - Cloud Infrastructure

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
"""
