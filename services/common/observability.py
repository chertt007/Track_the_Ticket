"""
Langfuse observability setup.

Must be called BEFORE anything imports `openai` (directly or via browser-use),
because OpenAIInstrumentor patches the openai SDK at import time.
"""
import logging
import os

logger = logging.getLogger(__name__)

_initialized = False


def setup_observability() -> None:
    """Wire Langfuse + OpenAI OTEL instrumentation. Safe to call once at startup."""
    global _initialized
    if _initialized:
        return

    if not os.environ.get("LANGFUSE_PUBLIC_KEY") or not os.environ.get("LANGFUSE_SECRET_KEY"):
        logger.warning("[observability] LANGFUSE_* keys not set — skipping Langfuse init")
        return

    from langfuse import get_client
    from openinference.instrumentation.openai import OpenAIInstrumentor

    # get_client() reads LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY / LANGFUSE_HOST
    # from env and installs a global OTEL TracerProvider that exports to Langfuse.
    langfuse = get_client()

    # Patch the openai SDK globally so every call (including those inside
    # browser-use's ChatOpenRouter) emits OTEL spans that Langfuse picks up.
    OpenAIInstrumentor().instrument()

    _initialized = True
    logger.info(f"[observability] Langfuse + OpenAI instrumentation ready (host={os.environ.get('LANGFUSE_HOST')})")
