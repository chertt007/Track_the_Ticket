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

COPY . .

CMD ["lambda_handler.handler"]
