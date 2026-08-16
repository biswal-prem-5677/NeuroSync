# ==========================================
# Stage 1: Build React Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY core/frontend/package*.json ./
RUN npm ci

COPY core/frontend/ ./
RUN npm run build

# ==========================================
# Stage 2: Python Backend & Production Runtime
# ==========================================
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY core/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy backend code
COPY core/backend/ ./core/backend/

# Copy built frontend assets to where main.py expects them
COPY --from=frontend-builder /app/frontend/dist ./core/frontend/dist

# Set working directory to core/backend
WORKDIR /app/core/backend

EXPOSE 8000

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
