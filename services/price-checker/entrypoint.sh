#!/bin/sh
# Wrap the Lambda runtime with xvfb-run so Chrome has a virtual display.
# This is the approach Playwright explicitly recommends:
#   "use xvfb-run <your-playwright-app> before running Playwright"
# By wrapping here (at OS level, before Python even starts), DISPLAY is set
# for every process in the Lambda invocation — no Python subprocess magic needed.
exec xvfb-run --auto-servernum --server-args="-screen 0 1280x1024x24 -ac" \
    /lambda-entrypoint.sh "$@"
