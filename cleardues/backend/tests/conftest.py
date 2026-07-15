"""
Test configuration.

SAFETY: the suite runs against a dedicated `<POSTGRES_DB>_test` database, never
the configured application database. The redirect happens BEFORE any app import
builds the engine, and tests refuse to run outside ENVIRONMENT=local.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine as _create_admin_engine
from sqlalchemy import text

# --- Test-DB redirect: must precede every other app import, because
# app.core.db builds the engine from settings at import time. ---
from app.core.config import settings

if settings.ENVIRONMENT != "local":
    raise RuntimeError(
        f"Refusing to run tests: ENVIRONMENT is '{settings.ENVIRONMENT}', not "
        "'local'. The suite drops and recreates its own database and must "
        "never point at a shared environment."
    )

if not settings.POSTGRES_DB.endswith("_test"):
    settings.POSTGRES_DB = f"{settings.POSTGRES_DB}_test"

# Per-IP rate limiting off for the suite (every request comes from the same
# testclient IP and would trip the auth tiers immediately). This must happen
# before app imports because the Limiter reads the setting at construction.
# The dedicated rate-limit test flips limiter.enabled back on for its scope.
settings.RATE_LIMIT_ENABLED = False


def _ensure_test_database_exists() -> None:
    """Create the dedicated test database if it doesn't exist yet."""
    admin_uri = str(settings.SQLALCHEMY_DATABASE_URI).rsplit("/", 1)[0] + "/postgres"
    admin_engine = _create_admin_engine(admin_uri, isolation_level="AUTOCOMMIT")
    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": settings.POSTGRES_DB},
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{settings.POSTGRES_DB}"'))
    admin_engine.dispose()


_ensure_test_database_exists()

# App imports come after the redirect so the engine targets the test DB.
from pathlib import Path  # noqa: E402

from alembic import command as alembic_command  # noqa: E402
from alembic.config import Config as AlembicConfig  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session  # noqa: E402

from app.core.db import engine, init_db  # noqa: E402
from app.main import app  # noqa: E402  # importing app.main registers every feature model
from tests.utils.user import authentication_token_from_email  # noqa: E402
from tests.utils.utils import get_superuser_token_headers  # noqa: E402

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    # Deterministic schema per run, built from the REAL alembic migrations —
    # not SQLModel.create_all — so tests exercise the schema production runs
    # (e.g. timezone-aware timestamp columns that the models alone would
    # declare naive). env.py reads the mutated settings, so this migrates the
    # test database.
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.commit()
    alembic_cfg = AlembicConfig(str(_BACKEND_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(_BACKEND_ROOT / "app" / "alembic"))
    alembic_command.upgrade(alembic_cfg, "head")
    with Session(engine) as session:
        init_db(session)
        yield session


@pytest.fixture(autouse=True)
def _recover_failed_session(db: Session) -> Generator[None, None, None]:
    """Roll the shared session back after each test.

    A test that dies mid-transaction otherwise leaves the session-scoped
    Session in a failed state, and every subsequent test errors with
    PendingRollbackError — one real failure cascades into dozens of phantom
    ones. Rolling back a healthy session is a no-op, so this is always safe.
    """
    yield
    db.rollback()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(db: Session) -> dict[str, str]:
    return get_superuser_token_headers(db)


@pytest.fixture(scope="module")
def normal_user_token_headers(db: Session) -> dict[str, str]:
    return authentication_token_from_email(email=settings.EMAIL_TEST_USER, db=db)


@pytest.fixture(scope="module")
def second_user_token_headers(db: Session) -> dict[str, str]:
    """Token headers for a second test user (for multi-user tests)."""
    return authentication_token_from_email(email="seconduser@example.com", db=db)
