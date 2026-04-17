# Link-parser service — Python 3.12 + Playwright (Chromium) + FastAPI
# Build:  docker build -t tracktheticket-link-parser .
# Run:    docker run --rm -p 8000:8000 tracktheticket-link-parser

FROM python:3.12-slim-bookworm

# ── Python dependencies ───────────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium + all system dependencies via Playwright
# (--with-deps handles everything on Debian Bookworm)
RUN playwright install chromium --with-deps

# ── Application code ──────────────────────────────────────────────────────────
COPY main.py models.py parser.py url_decoder.py ./

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
