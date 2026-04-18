"""Centralized logging setup: colored [FUNCTION: name] tag in all log lines."""
import logging
import sys

# ANSI escape codes — modern terminals (Windows Terminal, PowerShell 7+, bash) handle these natively.
_YELLOW = "\033[33m"
_RESET  = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Prepends [FUNCTION: <caller>] in yellow to every log line."""

    def format(self, record: logging.LogRecord) -> str:
        record.funcTag = f"{_YELLOW}[FUNCTION: {record.funcName}]{_RESET}"
        return super().format(record)


def setup_logging(level: int = logging.DEBUG) -> None:
    """Configure the root logger. Safe to call multiple times — replaces existing handlers."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColoredFormatter(
        fmt="%(asctime)s %(funcTag)s %(name)s — %(message)s"
    ))
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
