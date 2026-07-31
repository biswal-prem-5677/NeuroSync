# Existing Architecture (SCA)

- FastAPI backend
- Modular structure:
  - api/
  - services/
  - utils/
- ML models loaded via pickle
- JSON-based data storage

## Issues

- Loose coupling between modules
- No centralized intelligence engine
- Redundant logic across services
- No orchestration layer
