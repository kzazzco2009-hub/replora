"""Request IDs, JSON logs and PII scrubbing (P0.11, S‑87, T0.7)."""

import json
import logging
import re
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from starlette.types import ASGIApp, Message, Receive, Scope, Send

REQUEST_ID_HEADER = "x-request-id"
_VALID_ID = re.compile(r"[A-Za-z0-9._-]{1,64}")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_SENSITIVE = ("password", "token", "secret", "cookie", "authorization", "code", "email")
_LOG_RECORD = logging.LogRecord("", 0, "", 0, "", None, None)
_RECORD_FIELDS = set(vars(_LOG_RECORD)) | {"message", "color_message"}

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
access_log = logging.getLogger("app.access")


class RequestIdMiddleware:
    """Give each request an ID, return it as `X-Request-ID`, and write one access-log line.

    A well-formed incoming ID (for example from a proxy) is kept; anything else is replaced.
    The access log holds the method, path, status and duration only: no query, body or headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        incoming = dict(scope["headers"]).get(REQUEST_ID_HEADER.encode(), b"").decode("latin-1")
        current = incoming if _VALID_ID.fullmatch(incoming) else str(uuid.uuid7())
        request_id.set(current)
        status = 500
        started = time.perf_counter()

        async def send_with_id(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = list(message.get("headers", []))
                if not any(name.lower() == REQUEST_ID_HEADER.encode() for name, _ in headers):
                    headers.append((REQUEST_ID_HEADER.encode(), current.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 1)
            access_log.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status": status,
                    "duration_ms": duration_ms,
                },
            )


class JsonFormatter(logging.Formatter):
    """One JSON object per line, with the request ID. Sensitive fields and emails are scrubbed."""

    def format(self, record: logging.LogRecord) -> str:
        line: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": _EMAIL.sub("[email]", record.getMessage()),
            "request_id": request_id.get(),
        }
        extra = {key: value for key, value in vars(record).items() if key not in _RECORD_FIELDS}
        line |= _scrub(extra)
        if record.exc_info:
            line["exception"] = _EMAIL.sub("[email]", self.formatException(record.exc_info))
        return json.dumps(line, default=str, ensure_ascii=False)


def _scrub(fields: dict[str, Any]) -> dict[str, Any]:
    """Redact values under sensitive keys, recursively; replace emails in other strings."""
    scrubbed: dict[str, Any] = {}
    for key, value in fields.items():
        if any(word in key.lower() for word in _SENSITIVE):
            scrubbed[key] = "[redacted]"
        elif isinstance(value, dict):
            scrubbed[key] = _scrub(value)
        elif isinstance(value, str):
            scrubbed[key] = _EMAIL.sub("[email]", value)
        else:
            scrubbed[key] = value
    return scrubbed


def configure_logging() -> None:
    """Send all logs (ours and uvicorn's) to stderr as JSON; our access log replaces uvicorn's.

    Uvicorn's own access log is turned off because it records the client IP (S‑87: IPs hashed).
    """
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True
