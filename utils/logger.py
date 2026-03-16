import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Any, Dict, List

import structlog
from starlette.requests import Request


def _resolve_log_level() -> int:

    level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
    return getattr(logging, level_name, logging.DEBUG)


def _build_handlers(level: int) -> List[logging.Handler]:

    handlers: List[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    debug_dir = os.getenv("DEBUG_LOG_DIR")
    if level == logging.DEBUG and debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
        date_suffix = datetime.utcnow().strftime("%Y%m%d")
        log_file_path = os.path.join(debug_dir, f"app-debug-{date_suffix}.log")
        max_bytes = int(os.getenv("LOG_FILE_MAX_BYTES", str(2 * 1024 * 1024)))  # 2MB default
        backup_count = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))
        handlers.append(RotatingFileHandler(log_file_path, maxBytes=max_bytes, backupCount=backup_count))

    return handlers


def _configure_logging():

    level = _resolve_log_level()
    handlers = _build_handlers(level)
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    processor_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper
        ]
    )

    for handler in handlers:
        handler.setFormatter(processor_formatter)

    logging.basicConfig(level=level, handlers=handlers)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )


_configure_logging()


def get_logger(name: Optional[str] = None):

    return structlog.get_logger(name or "tax_ai_agent")


def build_log_extra(request: Optional[Request] = None, *, ctid: Optional[str] = None, **attributes: Any) -> Dict[str, Any]:

    extra: Dict[str, Any] = {k: v for k, v in attributes.items() if v is not None}

    if ctid is not None:
        extra.setdefault("ctid", ctid)

    if request is not None:
        try:
            extra.setdefault("path", request.url.path)
        except Exception:
            pass

        method = getattr(request, "method", None)
        if method:
            extra.setdefault("method", method)

        client = getattr(request, "client", None)
        if client and getattr(client, "host", None):
            extra.setdefault("client_ip", client.host)

        headers = getattr(request, "headers", None)
        if headers:
            forwarded = headers.get("x-forwarded-for")
            if forwarded:
                extra.setdefault("forwarded_for", forwarded)
            user_agent = headers.get("user-agent")
            if user_agent:
                extra.setdefault("user_agent", user_agent)

    return extra
