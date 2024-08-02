ARG PYTHON_VERSION=3.12.4
FROM python:${PYTHON_VERSION}-slim AS python-base

ARG UID=1001
ARG VERSION
ARG REVISION=""

LABEL org.opencontainers.image.title="ridiwise" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.url="https://github.com/bskim45/ridiwise" \
    org.opencontainers.image.source="https://github.com/bskim45/ridiwise" \
    org.opencontainers.image.authors="Bumsoo Kim <bskim45@gmail.com>"

ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    VENV_PATH=/opt/venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV PATH="$VENV_PATH/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN useradd -m -u 1001 noroot


FROM python-base AS build-venv

WORKDIR /build

RUN python -m venv $VENV_PATH

# Install python dependencies
COPY pyproject.toml requirements.lock /build/
COPY LICENSE README.md /build/
COPY src/ridiwise/__init__.py /build/src/ridiwise/__init__.py
RUN pip install --no-cache-dir -r requirements.lock


FROM python-base AS build-playwright

# Install playwright with system dependencies
COPY --from=build-venv $VENV_PATH $VENV_PATH
RUN playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*


FROM build-playwright AS runtime

WORKDIR /app

COPY src .

USER noroot

ENV RIDIWISE_CONFIG_DIR=/app/.config/ridiwise
ENV RIDIWISE_CACHE_DIR=/app/.cache/ridiwise

ENTRYPOINT ["python", "-m", "ridiwise"]
