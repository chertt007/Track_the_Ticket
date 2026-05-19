#!/bin/bash
set -e

# Start a virtual display so headed Chromium (HEADLESS=False) can render.
# Both airline_url_finder (browser_use) and price_checker (Playwright) need this.
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp &
export DISPLAY=:99

exec python run.py
