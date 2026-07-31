# NeuroSync API Contract

**Version**: 1.0.0  
**Base Path**: `/api/v1`  
**Protocol**: HTTP/S  
**Content-Type**: `application/json`

---

## 1. Endpoints Overview

| Method | Path | Description | Authentication |
| --- | --- | --- | --- |
| `POST` | `/api/v1/analyze` | Full resume-to-JD analysis pipeline | None (Dev/Phase 1) |
| `POST` | `/api/v1/feedback` | Record application/hiring outcomes | None (Dev/Phase 1) |
| `GET` | `/api/v1/health` | Service and component status monitoring | None |
| `POST` | `/api/v1/behavior/session/start` | Begin a learning session | JWT (Phase 2+) |
| `POST` | `/api/v1/behavior/session/stop` | End a learning session | JWT (Phase 2+) |
| `POST` | `/api/v1/behavior/event` | Record a behavioral observation | JWT (Phase 2+) |
| `GET` | `/api/v1/behavior/profile` | Get user behavioral profile | JWT (Phase 2+) |
| `GET` | `/api/v1/behavior/state` | Get current CareerState | JWT (Phase 2+) |

---

## 2. POST /api/v1/analyze

Performs full analysis on a raw resume text against a Job Description (JD).

### 2.1 Request Schema

```json
{
  "resume_text": "string (min_length=50, max_length=50000) - Required",
  "jd_text": "string (min_length=20, max_length=20000) - Required",
  "include_simulations": "boolean (default=true) - Optional",
  "include_evidence": "boolean (default=true) - Optional"
}
```

### 2.2 Response Schema

```json
{
  "analysis_id": "string (length=12)",
  "decision": {
    "recommendation": "strong_apply | apply | apply_with_preparation | upskill_then_apply | do_not_apply",
    "confidence": "number (float, 0.0 - 1.0)",
    "shortlist_probability": "number (float, 0.0 - 1.0)",
    "fit_level": "strong_fit | good_fit | potential_fit | weak_fit | no_fit",
    "overall_score": "number (float, 0.0 - 100.0)",
    "reasoning": "string"
  },
  "scoring": {
    "semantic_score": "number (float, 0.0 - 1.0) or null",
    "skill_overlap_score": "number (float, 0.0 - 1.0)",
    "gap_penalty": "number (float, 0.0 - 1.0)",
    "final_score": "number (float, 0.0 - 100.0)",
    "explanation": "string"
  },
  "skills": {
    "resume_count": "integer",
    "jd_count": "integer",
    "matched": "integer",
    "missing": "integer",
    "overlap_score": "number (float, 0.0 - 1.0)",
    "resume_skills": [
      {
        "name": "string (canonical skill name)",
        "category": "programming | framework | database | cloud | devops | ml_ai | soft_skill | domain | other",
        "confidence": "number (float, 0.0 - 1.0)",
        "proficiency": "number (float, 0.0 - 1.0)",
        "evidence_strength": "number (float, 0.0 - 1.0)",
        "occurrences": "integer",
        "matched_by": "taxonomy | ner | semantic | embedding_discovery",
        "sections": ["string (found sections, e.g., 'experience', 'skills')"]
      }
    ]
  },
  "gaps": [
    {
      "skill": "string (canonical skill name)",
      "category": "string (SkillCategory enum)",
      "priority": "critical | high | medium | low",
      "reasoning": "string (contextual explanation)",
      "learning_time": "string (e.g. '2-4 weeks')",
      "related_present": ["string (related skills possessed by candidate)"],
      "confidence": "number (float, 0.0 - 1.0)"
    }
  ],
  "improvement_path": [
    {
      "rank": "integer (1 = highest ROI)",
      "skill": "string (canonical skill name)",
      "impact": "number (float, expected score increase)",
      "learning_time": "string",
      "reasoning": "string"
    }
  ],
  "strengths": ["string"],
  "weaknesses": ["string"],
  "simulations": [
    {
      "skill_added": "string (canonical skill name)",
      "current_score": "number (float)",
      "projected_score": "number (float)",
      "delta": "number (float)",
      "new_fit_level": "string (FitLevel enum)",
      "new_shortlist_prob": "number (float)",
      "roi_rank": "integer"
    }
  ],
  "evidence": [
    {
      "source": "string (e.g. 'semantic_engine', 'skill_extractor')",
      "claim": "string",
      "weight": "number (float)",
      "confidence": "number (float)"
    }
  ],
  "semantic": {
    "overall": "number (float)",
    "chunk_max": "number (float)",
    "chunk_mean": "number (float)",
    "skill_alignment": "number (float)",
    "confidence": "number (float)",
    "degraded": "boolean",
    "sections": [
      {
        "section": "string",
        "score": "number (float)",
        "weight": "number (float)"
      }
    ]
  },
  "meta": {
    "processing_time_ms": "number (float)",
    "extraction_degraded": "boolean",
    "semantic_available": "boolean"
  }
}
```

### 2.3 Response Example

```json
{
  "analysis_id": "8a6d2652a912",
  "decision": {
    "recommendation": "apply",
    "confidence": 0.95,
    "shortlist_probability": 0.72,
    "fit_level": "good_fit",
    "overall_score": 74.5,
    "reasoning": "Good match — apply. Minor gaps are compensable..."
  },
  "scoring": {
    "semantic_score": 0.78,
    "skill_overlap_score": 0.82,
    "gap_penalty": 0.15,
    "final_score": 74.5,
    "explanation": "semantic=0.78 (w=0.40) | skill_overlap=0.82 (w=0.35) | gap_deduction=-5.25pts (penalty=0.15, w=0.25)"
  },
  "skills": {
    "resume_count": 22,
    "jd_count": 15,
    "matched": 12,
    "missing": 3,
    "overlap_score": 0.8,
    "resume_skills": [
      {
        "name": "Python",
        "category": "programming",
        "confidence": 1.0,
        "proficiency": 0.9,
        "evidence_strength": 0.95,
        "occurrences": 6,
        "matched_by": "taxonomy",
        "sections": ["experience", "skills"]
      }
    ]
  },
  "gaps": [
    {
      "skill": "Terraform",
      "category": "devops",
      "priority": "high",
      "reasoning": "Your existing AWS knowledge creates a foundation, but without Terraform, your infrastructure-as-code capability has a gap...",
      "learning_time": "2-4 weeks (accelerated – you already know AWS)",
      "related_present": ["AWS"],
      "confidence": 0.85
    }
  ],
  "improvement_path": [
    {
      "rank": 1,
      "skill": "Terraform",
      "impact": 5.4,
      "learning_time": "2-4 weeks",
      "reasoning": "Learning Terraform has the highest ROI: score jumps from 74.5 to 79.9 (+5.4)..."
    }
  ],
  "strengths": [
    "Python (proficiency: 90%)",
    "AWS (proficiency: 80%)"
  ],
  "weaknesses": [
    "Missing Terraform (high priority)"
  ],
  "simulations": [
    {
      "skill_added": "Terraform",
      "current_score": 74.5,
      "projected_score": 79.9,
      "delta": 5.4,
      "new_fit_level": "good_fit",
      "new_shortlist_prob": 0.81,
      "roi_rank": 1
    }
  ],
  "meta": {
    "processing_time_ms": 420.5,
    "extraction_degraded": false,
    "semantic_available": true
  }
}
```

---

## 3. POST /api/v1/feedback

Records the real-world outcome of a job application to feed back into the learning loop.

### 3.1 Request Schema

```json
{
  "analysis_id": "string - Required",
  "outcome": "hired | rejected | interview | ghosted | user_disagrees - Required",
  "notes": "string (max_length=1000) - Optional"
}
```

### 3.2 Response Schema

```json
{
  "status": "recorded",
  "analysis_id": "string",
  "outcome": "string",
  "decision_found": "boolean (true if active in cache, false if fallback stub used)",
  "feedback_stats": {
    "count": "integer (total feedback items recorded)",
    "outcomes": {
      "outcome_name": "integer (count of this outcome)"
    },
    "avg_score": "number (float, average score of entries with feedback)",
    "recalibrate_at": "integer (threshold for recalibration trigger)"
  }
}
```

### 3.3 Response Example

```json
{
  "status": "recorded",
  "analysis_id": "8a6d2652a912",
  "outcome": "interview",
  "decision_found": true,
  "feedback_stats": {
    "count": 12,
    "outcomes": {
      "interview": 5,
      "rejected": 4,
      "ghosted": 3
    },
    "avg_score": 71.2,
    "recalibrate_at": 50
  }
}
```

---

## 4. GET /api/v1/health

Verifies server status and internal sub-service readiness.

### 4.1 Response Schema

```json
{
  "status": "healthy | unhealthy",
  "version": "string (engine version)",
  "api_version": "string (router version)",
  "components": {
    "extractor": {
      "taxonomy_skills": "integer",
      "embedding_store_ready": "boolean",
      "embedding_store_has_data": "boolean",
      "ner_available": "boolean",
      "ner_failed": "boolean",
      "cache_size": "integer",
      "cache_max": "integer"
    },
    "semantic_engine": "available | unavailable",
    "intelligence_engine": "available | unavailable",
    "feedback": {
      "count": "integer",
      "outcomes": {},
      "avg_score": "number",
      "recalibrate_at": "integer"
    }
  }
}
```

### 4.2 Response Example

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_version": "v1",
  "components": {
    "extractor": {
      "taxonomy_skills": 294,
      "embedding_store_ready": true,
      "embedding_store_has_data": true,
      "ner_available": true,
      "ner_failed": false,
      "cache_size": 2,
      "cache_max": 1024
    },
    "semantic_engine": "available",
    "intelligence_engine": "available",
    "feedback": {
      "count": 0,
      "outcomes": {},
      "avg_score": 0.0,
      "recalibrate_at": 50
    }
  }
}
```

---

## 5. Human State Intelligence Endpoints (Phase 2+) ★ NEW

> All behavior endpoints require JWT authentication. Camera signals are optional.

### 5.1 POST /api/v1/behavior/session/start

Begin tracking a learning session.

```json
// Request
{
  "skill_focus": "string - Canonical skill being studied",
  "roadmap_id": "string | null - Associated roadmap"
}

// Response (200)
{
  "session_id": "string (UUID)",
  "started_at": "ISO 8601 timestamp",
  "skill_focus": "string"
}
```

### 5.2 POST /api/v1/behavior/session/stop

End a learning session and record metrics.

```json
// Request
{
  "session_id": "string (UUID)",
  "completion_rate": "number (float, 0.0 - 1.0)",
  "abandoned": "boolean (default=false)"
}

// Response (200)
{
  "session_id": "string",
  "duration_minutes": "integer",
  "engagement_score": "number (float, 0.0 - 1.0) - Derived",
  "state_impact": "string | null - e.g., 'momentum_increased'"
}
```

### 5.3 POST /api/v1/behavior/event

Record an observation from any source. This is the primary agent memory endpoint.

```json
// Request
{
  "source": "resume | jd | feedback | learning | project | interview | market | camera",
  "signal": "string - e.g., 'engagement_low', 'completion_drop', 'focus_high'",
  "confidence": "number (float, 0.0 - 1.0)",
  "raw_data": "object | null - Optional metadata (NEVER raw video/images)"
}

// Response (200)
{
  "observation_id": "string (UUID)",
  "source": "string",
  "signal": "string",
  "processed": "boolean",
  "state_transition": {
    "occurred": "boolean",
    "field": "string | null - e.g., 'burnout_risk'",
    "previous": "number | null",
    "current": "number | null"
  }
}
```

### 5.4 GET /api/v1/behavior/profile

Get the user's behavioral profile — aggregated observation history.

```json
// Response (200)
{
  "user_id": "string",
  "total_sessions": "integer",
  "total_observations": "integer",
  "observation_sources_used": ["learning", "feedback", "project"],
  "recent_state_observations": [
    {
      "signal": "accelerating",
      "derived_from": ["learning", "project"],
      "confidence": 0.84,
      "timestamp": "ISO 8601"
    }
  ],
  "recent_transitions": [
    {
      "field": "momentum_score",
      "previous": 0.42,
      "current": 0.68,
      "reason": "3 consecutive learning sessions completed",
      "timestamp": "ISO 8601"
    }
  ]
}
```

### 5.5 GET /api/v1/behavior/state

Get the current CareerState — the unified decision surface.

```json
// Response (200)
{
  "user_id": "string",
  "career_state": {
    "confidence_score": 0.68,
    "momentum_score": 0.76,
    "engagement_score": 0.82,
    "consistency_score": 0.71,
    "growth_velocity": 5.7,
    "burnout_risk": 0.15,
    "interview_readiness": 0.62,
    "career_readiness": 0.58
  },
  "predictions": {
    "burnout_probability": 0.12,
    "dropout_probability": 0.08,
    "interview_success_probability": 0.62,
    "skill_completion_probability": 0.81
  },
  "updated_at": "ISO 8601",
  "observation_count": 47,
  "camera_enabled": false
}
```
