"""Request/response logging middleware — like Log4j MDC + access log.

Logs every HTTP request with:
  - Request:  method, path, query, client IP, user-agent
  - Response: status code, response time (ms)
  - Error:    full traceback on 5xx

This provides the same visibility as a Log4j Web Filter or Spring
Boot's request logging.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("app.middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every request/response cycle.

    Log format:
      → [req_id] POST /api/v1/auth/otp/request 192.168.1.1 Mozilla/5.0...
      ← [req_id] 200 OK 45ms
    """

    # Paths to skip (health checks, static, docs)
    SKIP_PATHS = frozenset({"/", "/docs", "/openapi.json", "/favicon.ico", "/v1/models"})

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip noisy endpoints
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        # Generate request ID for correlation (like Log4j MDC)
        req_id = str(uuid.uuid4())[:8]
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "-")[:80]
        query = f"?{request.url.query}" if request.url.query else ""

        # Log incoming request
        logger.info(
            "-> [%s] %s %s%s %s %s",
            req_id, request.method, request.url.path, query, client_ip, user_agent,
        )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = (time.perf_counter() - start_time) * 1000

            # Choose log level based on status code
            if response.status_code >= 500:
                logger.error(
                    "← [%s] %d %s %.1fms",
                    req_id, response.status_code, request.url.path, elapsed_ms,
                )
            elif response.status_code >= 400:
                logger.warning(
                    "← [%s] %d %s %.1fms",
                    req_id, response.status_code, request.url.path, elapsed_ms,
                )
            else:
                logger.info(
                    "← [%s] %d %s %.1fms",
                    req_id, response.status_code, request.url.path, elapsed_ms,
                )

            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = req_id
            return response

        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "✖ [%s] UNHANDLED %s %s %.1fms -> %s",
                req_id, request.method, request.url.path, elapsed_ms, str(exc),
            )
            raise
