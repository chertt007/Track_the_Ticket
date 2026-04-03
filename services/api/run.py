"""
Local development runner.

Sets WindowsProactorEventLoopPolicy BEFORE uvicorn creates the event loop —
this is required for Playwright to spawn Chromium subprocesses on Windows.
On Linux/macOS this is a no-op.
"""
import sys

if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
