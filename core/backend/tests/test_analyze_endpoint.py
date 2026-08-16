"""
NeuroSync — Tests for /analyze and /analyze-file endpoints.
"""
import io
import pytest


def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "components" in data
    assert data["components"]["extractor"]["ner_available"] in (True, False)



def test_analyze_endpoint_success(client, sample_resume, sample_jd):
    response = client.post(
        "/api/v1/analyze",
        json={"resume_text": sample_resume, "jd_text": sample_jd},
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis_id" in data
    assert data["decision"]["fit_level"] in ("good_fit", "strong_fit")
    assert data["decision"]["overall_score"] > 60.0
    assert len(data["gaps"]) > 0
    assert "simulations" in data
    assert "meta" in data
    assert "versions" in data["meta"]


def test_analyze_endpoint_validation_short_text(client):
    response = client.post(
        "/api/v1/analyze",
        json={"resume_text": "Short resume", "jd_text": "Short JD"},
    )
    assert response.status_code == 422


def test_analyze_endpoint_junk_text(client):
    junk = "1234567890 !@#$%^&*() _+-=[]{}|;':\",./<>? 9999999999 8888888888 7777777777"
    response = client.post(
        "/api/v1/analyze",
        json={"resume_text": junk, "jd_text": "Python developer needed with 5 years experience in FastAPI."},
    )
    assert response.status_code == 422


def test_analyze_file_endpoint_txt(client, sample_resume, sample_jd):
    files = {
        "resume_file": ("resume.txt", io.BytesIO(sample_resume.encode("utf-8")), "text/plain"),
    }
    data = {
        "jd_text": sample_jd,
    }
    response = client.post("/api/v1/analyze-file", files=files, data=data)
    assert response.status_code == 200
    res = response.json()
    assert res["meta"]["resume_filename"] == "resume.txt"
    assert res["meta"]["resume_format"] == "txt"
    assert res["decision"]["overall_score"] > 60.0
