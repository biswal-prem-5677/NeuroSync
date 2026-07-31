# NeuroSync — Non-Functional Requirements (NFR)

This document establishes the quality targets, operational constraints, and architectural boundaries for NeuroSync.

---

## 1. Latency & Performance Targets

We enforce strict latency thresholds at the 95th percentile (P95) to ensure a premium user experience and prevent server exhaustion.

| Endpoint / Operation | P90 Target | P95 Target | Notes |
| --- | --- | --- | --- |
| `POST /api/v1/analyze` | < 1.5s | < 2.0s | Core pipeline (extract, semantic comparison, decision) |
| `GET /api/v1/health` | < 50ms | < 100ms | System dependency and health status probe |
| `POST /api/v1/feedback` | < 100ms | < 200ms | Asynchronous log and database ingestion |

---

## 2. Reliability & Availability Targets

- **System Uptime**: 99.9% availability per calendar month, excluding scheduled maintenance.
- **Degraded Operation**: If the Semantic Embedding engine is offline, the system must gracefully fall back to Taxonomy and NER matching. The overall score confidence metric should degrade, but the API must remain online.
- **Max Data Loss**: Recovery Point Objective (RPO) < 1 hour; Recovery Time Objective (RTO) < 4 hours.

---

## 3. Security & Multi-Tenancy

- **Data Isolation**: Multi-tenant database rows must be isolated using tenant identifiers. Query filters must enforce tenant scope at the database query layer.
- **Authentication**: JWT-based tokens (access token expires in 15 minutes, refresh token in 7 days).
- **Transport Security**: TLS 1.3 enforced for all external transit.
- **Upload Boundaries**: Strict payload limit of 5MB per upload. Uploaded documents (PDF/DOCX) must be scanned for magic byte verification to prevent execution attacks.

---

## 4. Scalability & Cost Constraints

- **Kubernetes Scaling**: Auto-scale API pods horizontally based on CPU utilization exceeding 70% or memory usage exceeding 80%.
- **Database Connection Pooling**: Max 20 connections per pod to avoid database connection exhaustion.
- **Caching**: Store frequent lookups and computed taxonomy embeddings in Redis with a TTL of 24 hours.
- **Resource Constraints**: Backend memory foot print must stay under 512MB per instance under normal load (excluding model cache in CPU/GPU memory).

---

## 5. Observability & Logging

- **Traceability**: Every request must carry a unique `X-Request-ID` header injected by middleware and propagated to all logs.
- **Metrics**: Standard Prometheus instrumentation for HTTP request durations, database connection pool status, and ML model inference latency.
- **Structured Logs**: JSON logs emitted to stdout containing `request_id`, `tenant_id`, and execution execution status.

---

## 6. Behavioral Data Privacy & Consent (Phase 2+) ★ NEW

> These requirements apply to the Human State Intelligence layer. They are non-negotiable.

### Camera Processing

- **Camera processing is permanently optional.** The system operates at 95% capability without camera signals.
- **Disabled by default** — camera is never enabled without explicit user action.
- **Explicit consent required** — a modal dialog with clear privacy policy must be accepted before camera activation.
- **Revocable at any time** — user can disable camera with a single click.

### Data Storage Rules

| Data Type | Stored? | Retention | Notes |
| --- | --- | --- | --- |
| Raw video frames | ❌ NEVER | N/A | Frames deleted immediately after inference |
| Raw camera images | ❌ NEVER | N/A | Deleted within the same request cycle |
| Derived camera signals | ✅ As AgentObservation | 90 days | attention_score, focus_score, engagement_level |
| Learning session data | ✅ As LearningSession | Indefinite | Duration, completion rate, engagement |
| CareerState | ✅ Current only | Updated in-place | Previous states preserved in StateTransitions |
| StateTransitions | ✅ History | 1 year | Before/after snapshots with reasoning |
| AgentObservations | ✅ History | 90 days | Source-tagged signal records |

### GDPR Readiness

- **Right to erasure**: `DELETE /api/v1/user/data` must cascade-delete all observations, states, transitions, and sessions.
- **Data portability**: `GET /api/v1/user/export` must return all behavioral data in machine-readable JSON.
- **Consent audit trail**: Every camera enable/disable action is logged with timestamp.
- **No third-party sharing**: Behavioral data is never sent to external services (except LLM enhancer, which receives only derived CareerState metrics — never raw observations).
