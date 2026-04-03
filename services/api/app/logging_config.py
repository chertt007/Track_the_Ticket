import logging
import sys
from pythonjsonlogger.jsonlogger import JsonFormatter
import colorlog


# ── Formatters ────────────────────────────────────────────────────────────────

class PrettyColorFormatter(colorlog.ColoredFormatter):
    """
    Human-readable colored formatter for local development.

    Example output:
      2026-04-02 10:15:30  INFO     [auth        ] ✅ User authenticated  user_id=42
      2026-04-02 10:15:31  WARNING  [subscriptions] ⚠️  Subscription not found  id=999
      2026-04-02 10:15:32  ERROR    [main        ] ❌ Unhandled exception  ...
    """

    LEVEL_ICONS = {
        "DEBUG":    "🔍",
        "INFO":     "✅",
        "WARNING":  "⚠️ ",
        "ERROR":    "❌",
        "CRITICAL": "🔥",
    }

    # Standard LogRecord attribute names — we exclude these when building the
    # extra_fields string so only user-supplied extra={} keys are shown.
    _STANDARD_ATTRS = frozenset({
        "name", "msg", "args", "created", "filename", "funcName", "levelname",
        "levelno", "lineno", "module", "msecs", "pathname", "process",
        "processName", "relativeCreated", "stack_info", "thread", "threadName",
        "taskName", "exc_info", "exc_text", "message", "asctime",
        "icon", "log_color", "reset", "bold_log_color",
    })

    def format(self, record: logging.LogRecord) -> str:
        # Attach icon so it can be referenced in the format string
        record.icon = self.LEVEL_ICONS.get(record.levelname, "  ")

        # Build extra_fields string from any user-supplied extra={} keys
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in self._STANDARD_ATTRS and not k.startswith("_")
        }
        if extras:
            record.extra_fields = "  " + "  ".join(f"{k}={v!r}" for k, v in extras.items())
        else:
            record.extra_fields = ""

        return super().format(record)


class StructuredJsonFormatter(JsonFormatter):
    """
    JSON formatter for production (Lambda → CloudWatch).
    Every log line is a single JSON object — CloudWatch Insights can query it.

    Fixed fields added to every record:
      - timestamp  (ISO-8601)
      - level      (INFO / WARNING / ERROR …)
      - logger     (which module emitted the log)
      - message
    Extra fields (user_id, subscription_id, …) are passed via extra={} or
    LoggerAdapter and appear automatically alongside the fixed fields.
    """

    def add_fields(
        self,
        log_record: dict,
        record: logging.LogRecord,
        message_dict: dict,
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Rename asctime → timestamp for clarity in CloudWatch
        log_record["timestamp"] = log_record.pop("asctime", record.asctime if hasattr(record, "asctime") else "")
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Remove fields that are redundant or noisy in JSON output
        for field in ("levelname", "name", "taskName"):
            log_record.pop(field, None)


# ── Setup function ─────────────────────────────────────────────────────────────

def setup_logging(environment: str = "local", log_level: str = "INFO") -> None:
    """
    Call once at application startup (lifespan in main.py).

    Args:
        environment: "local" → pretty colors, anything else → JSON for CloudWatch.
        log_level:   "DEBUG" | "INFO" | "WARNING" | "ERROR"
    """

    level = getattr(logging, log_level.upper(), logging.INFO)

    if environment == "local":
        formatter: logging.Formatter = PrettyColorFormatter(
            fmt=(
                "%(log_color)s%(asctime)s  %(levelname)-8s%(reset)s "
                "%(cyan)s[%(name)-12s]%(reset)s "
                "%(icon)s %(white)s%(message)s%(reset)s"
                "%(blue)s%(extra_fields)s%(reset)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG":    "bold_white",
                "INFO":     "bold_green",
                "WARNING":  "bold_yellow",
                "ERROR":    "bold_red",
                "CRITICAL": "bold_purple",
            },
            reset=True,
            style="%",
        )
    else:
        # Production: one JSON object per line → CloudWatch Insights
        formatter = StructuredJsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure the root logger — all child loggers inherit this
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = []   # remove any handlers added before our setup
    root.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


# ── Per-module logger helper ───────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """
    Convenience wrapper — use instead of logging.getLogger() directly.

    Usage:
        from app.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("subscription created", extra={"subscription_id": 7, "user_id": 42})
    """
    return logging.getLogger(name)
