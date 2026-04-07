#!/bin/sh
# Lambda entrypoint.
# headless=True mode — no Xvfb needed, Chrome uses built-in headless renderer.
exec /lambda-entrypoint.sh "$@"
