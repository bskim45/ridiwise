ARG PYTHON_VERSION=3.12.4
ARG UV_VERSION=0.7.15

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

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
    VENV_PATH=/app/.venv \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

ENV PATH="$VENV_PATH/bin:$PATH"
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN useradd -m -u 1001 noroot

FROM python-base AS build-venv
ARG UV_VERSION

# Install uv
COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /app

# Install python dependencies
COPY pyproject.toml uv.lock /app/
RUN uv sync --frozen --no-cache --no-dev --no-install-project


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
