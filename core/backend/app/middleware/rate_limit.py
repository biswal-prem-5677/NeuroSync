"""
NeuroSync — Rate Limiting Middleware.
In-memory sliding-window rate limiter per client IP.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter middleware.
    Limits POST /api/v1/analyze and /api/v1/analyze-file requests.
    """

    def __init__(self, app, max_requests: int = 20, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Only rate-limit heavy analysis POST endpoints
        if request.method == "POST" and request.url.path in ("/api/v1/analyze", "/api/v1/analyze-file"):
            client_ip = request.client.host if request.client else "127.0.0.1"
            now = time.time()
            cutoff = now - self.window_seconds

            # Filter timestamps outside sliding window
            timestamps = [t for t in self.requests[client_ip] if t > cutoff]
            self.requests[client_ip] = timestamps

            if len(timestamps) >= self.max_requests:
                rid = getattr(request.state, "request_id", "?")
                logger.warning("[%s] Rate limit exceeded for IP %s (%d requests in %ds)",
                               rid, client_ip, len(timestamps), self.window_seconds)
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds}s allowed.",
                        "retry_after_seconds": int(self.window_seconds - (now - timestamps[0])),
                    },
                )

            timestamps.append(now)

        return await call_next(request)
