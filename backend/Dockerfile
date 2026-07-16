# Hardened runtime (WS9/S6-H4): slim base (python:3.10 full was ~1 GB and
# EOL 2026-10), non-root user, no tests, no dev deps in production.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app/

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#using-the-environment
ENV PATH="/app/.venv/bin:$PATH"

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Production images carry no pytest/mypy/ruff; the local override compose
# builds with INSTALL_DEV=true so `docker compose exec backend pytest` works.
ARG INSTALL_DEV=false

# Install dependencies
# --locked (S6-H1): FAIL the build if uv.lock is out of sync with
# pyproject.toml instead of silently re-resolving inside the image —
# that silent re-resolve is how unpinned crypto/OAuth libs shipped for months.
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    sh -c 'if [ "$INSTALL_DEV" = "true" ]; then uv sync --locked --no-install-project; else uv sync --locked --no-install-project --no-dev; fi'

ENV PYTHONPATH=/app

COPY ./scripts /app/scripts

COPY ./pyproject.toml ./uv.lock ./alembic.ini /app/

COPY ./app /app/app
# NOTE: tests/ deliberately NOT copied (S6-H4) — the local override compose
# bind-mounts ./backend/tests into the container instead.

# Sync the project (also --locked — see note above)
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    sh -c 'if [ "$INSTALL_DEV" = "true" ]; then uv sync --locked; else uv sync --locked --no-dev; fi'

# Non-root runtime user (S6-H4). The app writes nothing to disk (logs go to
# stdout); read access to /app is all it needs.
RUN groupadd -r app && useradd -r -g app -d /app app
USER app

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
