import json
import logging
import sys
from contextvars import ContextVar
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from src.utils.time_helpers import utc_now_iso
from src.utils.validation import is_valid_request_id

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")
logger = logging.getLogger("src.api.http")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": utc_now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
            "process_id": record.process,
        }
        if record.exc_info:
            data["exception"] = self.formatException(record.exc_info)
        return json.dumps(data, ensure_ascii=False)


def configure_logging(level: str) -> None:
    # Own application roots, leaving Uvicorn/Taskiq host loggers unchanged.
    for name in ("src", "bootstrap"):
        application_logger = logging.getLogger(name)
        if not any(
            getattr(handler, "_backend_handler", False) for handler in application_logger.handlers
        ):
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JsonFormatter())
            handler._backend_handler = True  # type: ignore[attr-defined]
            application_logger.addHandler(handler)
        application_logger.setLevel(level.upper())
        application_logger.propagate = False


class RequestContextMiddleware:
    """Pure ASGI middleware preserves cancellation and streaming semantics."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        candidate = Headers(scope=scope).get("x-request-id", "")
        request_id = candidate if is_valid_request_id(candidate) else uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        token = request_id_context.set(request_id)
        started = perf_counter()
        status_code = 500

        async def send_with_context(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        finally:
            logger.info(
                "%s %s status=%s elapsed_ms=%.2f",
                scope["method"],
                scope["path"],
                status_code,
                (perf_counter() - started) * 1000,
            )
            request_id_context.reset(token)
