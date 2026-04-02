import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import get_logger

logger = get_logger("request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming HTTP request and its response.

    Logged fields:
      - request_id   unique UUID per request (useful for tracing in CloudWatch)
      - method       GET / POST / DELETE …
      - path         /subscriptions/42
      - status_code  200 / 201 / 404 …
      - duration_ms  how long the handler took
      - client_ip    caller's IP address

    Skipped paths: /health  (too noisy, Lambda does health checks often)
    """

    SKIP_PATHS = {"/health"}

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())[:8]   # short 8-char ID, easier to read
        start = time.perf_counter()

        logger.info(
            "→ incoming request",
            extra={
                "request_id": request_id,
                "method":     request.method,
                "path":       request.url.path,
                "client_ip":  request.client.host if request.client else "unknown",
            },
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "💥 unhandled exception",
                extra={
                    "request_id":  request_id,
                    "method":      request.method,
                    "path":        request.url.path,
                    "duration_ms": duration_ms,
                    "error":       str(exc),
                },
                exc_info=True,   # attaches full traceback to the log record
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        log_fn = logger.info if response.status_code < 400 else logger.warning
        if response.status_code >= 500:
            log_fn = logger.error

        log_fn(
            "← response sent",
            extra={
                "request_id":  request_id,
                "method":      request.method,
                "path":        request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        # Attach request_id to response headers — useful for debugging
        response.headers["X-Request-ID"] = request_id
        return response
