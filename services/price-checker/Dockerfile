FROM public.ecr.aws/lambda/python:3.12

# Tell Playwright where to store browser binaries.
# Setting this before pip install ensures the path is baked into the image,
# not in the user home directory (which may not be writable in Lambda).
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Install system packages required by Chromium on Amazon Linux 2023.
# These are the same packages that `playwright install --with-deps` would install
# but listed explicitly to avoid relying on the auto-detection which can fail on AL2023.
RUN dnf install -y \
    atk \
    at-spi2-atk \
    cups-libs \
    gtk3 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXScrnSaver \
    libXtst \
    libdrm \
    mesa-libgbm \
    pango \
    alsa-lib \
    libxkbcommon \
    nss \
    nspr \
    && dnf clean all

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium browser binary into PLAYWRIGHT_BROWSERS_PATH
# This bakes the ~170MB Chromium into the Docker image (not downloaded at runtime).
# Lambda container images support up to 10 GB so this is fine.
RUN playwright install chromium

# Wrap the Chrome binary to always pass flags required in AWS Lambda.
# Lambda's seccomp profile blocks the syscalls Chrome uses for its Zygote subprocess
# and setuid sandbox, causing an immediate crash without these flags.
# browser-use 0.1.48 BrowserConfig.extra_chromium_args does not reliably forward
# flags to the actual Chrome process, so we patch the binary directly.
RUN CHROME_BIN=$(find /ms-playwright -name "chrome" -type f | head -1) && \
    mv "$CHROME_BIN" "${CHROME_BIN}.real" && \
    printf '#!/bin/sh\nexec "%s.real" --disable-setuid-sandbox --no-zygote "$@"\n' "$CHROME_BIN" > "$CHROME_BIN" && \
    chmod +x "$CHROME_BIN"

COPY . .

CMD ["lambda_handler.handler"]
