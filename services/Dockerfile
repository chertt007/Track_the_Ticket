# Backend image — Python 3.12 + Playwright (Chromium) + FastAPI.
# Builds the api service with common/ and link_parser/ available as importable packages.
#
# Build:  docker build -t tracktheticket-api -f services/Dockerfile services/
# Run:    docker run --rm -p 8000:8000 -v api_data:/data tracktheticket-api

FROM python:3.12-slim-bookworm

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Playwright Chromium + system libs (--with-deps handles apt packages on Bookworm)
RUN playwright install chromium --with-deps

# Application code: launcher at /app/run.py, packages under /app/
COPY run.py ./
COPY common/ ./common/
COPY link_parser/ ./link_parser/
COPY api/ ./api/

EXPOSE 8000
CMD ["python", "run.py"]
