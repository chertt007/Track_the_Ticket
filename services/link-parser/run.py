import sys
import asyncio

# Must be set before uvicorn creates the event loop.
# On Windows, SelectorEventLoop does not support subprocesses,
# which Playwright needs to launch Chromium.
# NOTE: reload=True spawns a subprocess that does NOT inherit this policy,
# so we run without reload. Restart honcho manually after backend changes.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
