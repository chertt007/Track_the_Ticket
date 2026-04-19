"""
Backend launcher — starts the only HTTP service we have: `api` (FastAPI).

link_parser and price_checker are libraries, not processes — they are imported
by api and invoked on demand. There is nothing else to run on startup.
"""
import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above services/).
# Must happen before any agent/LLM code imports, so env vars are available.
load_dotenv(Path(__file__).parent.parent / ".env")

# On Windows, SelectorEventLoop cannot spawn subprocesses (Playwright needs that
# to launch Chromium). Must be set before uvicorn creates the event loop.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

services_dir = Path(__file__).parent
sys.path.insert(0, str(services_dir))          # for `from common...`, `from link_parser...`
sys.path.insert(0, str(services_dir / "api"))  # for `from schemas import ...`

# Observability must be wired BEFORE main/browser-use imports openai.
from common.observability import setup_observability
setup_observability()

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
