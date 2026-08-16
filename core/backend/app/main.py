"""
NeuroSync — FastAPI Application Factory.
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — pre-warms all core singletons."""
    config = get_settings()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("NeuroSync v%s starting (engine v%s)", config.versions.api, config.versions.engine)

    # Pre-warm singletons in dependency order:
    # 0. State backend (opens the database — fails fast if it is unreachable)
    # 1. Taxonomy (loads skill_taxonomy.json)
    # 2. Semantic model (loads SentenceTransformer)
    # 3. Embedding store (indexes all taxonomy skills — requires model)
    # 4. Extractor (requires taxonomy + embedding_store + model)
    # 5. Semantic engine (requires model)
    from app.api.deps import (
        get_taxonomy, get_semantic_model, get_embedding_store,
        get_extractor, get_semantic_engine, get_state_backend,
        close_state_backend,
    )
    state = get_state_backend()
    logger.info("State backend: %s (durable=%s)",
                state.name, state.health().get("durable"))
    get_taxonomy()
    get_semantic_model()
    get_embedding_store()
    extractor = get_extractor()
    extractor.warm_up()
    get_semantic_engine()
    logger.info("All core services initialized — system ready")

    yield

    close_state_backend()
    logger.info("NeuroSync shutting down")


def create_app() -> FastAPI:
    config = get_settings()

    app = FastAPI(
        title="NeuroSync — Career Intelligence Engine",
        description="Production-grade resume analysis with semantic understanding, "
                    "skill gap intelligence, and career decision guidance.",
        version=config.versions.engine,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate Limiting
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)


    # Request ID + timing middleware
    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{elapsed:.1f}"
        logger.info("[%s] %s %s — %.1fms", request_id, request.method, request.url.path, elapsed)
        return response

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        rid = getattr(request.state, "request_id", "unknown")
        logger.error("[%s] Unhandled error: %s", rid, exc, exc_info=True)
        return JSONResponse(status_code=500, content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "request_id": rid,
        })

    # Register routers
    from app.api.v1.router import router as v1_router
    app.include_router(v1_router, prefix="/api/v1")

    # Mount frontend static files if built
    import os
    from fastapi.staticfiles import StaticFiles
    frontend_dist_candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/dist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist")),
    ]
    frontend_dist = next((p for p in frontend_dist_candidates if os.path.isdir(p)), None)
    if frontend_dist:
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
        logger.info("Mounted frontend static files from %s", frontend_dist)
    else:
        logger.warning("Frontend dist directory not found in candidates: %s", frontend_dist_candidates)

    return app




app = create_app()
