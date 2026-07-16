from app.core.config import Settings

# Init kwargs take precedence over env vars in pydantic-settings, so these
# tests are immune to the container's POSTGRES_* environment.
_BASE = dict(
    PROJECT_NAME="test",
    SECRET_KEY="test-secret",
    FIRST_SUPERUSER="admin@example.com",
    FIRST_SUPERUSER_PASSWORD="test-password",
    POSTGRES_SERVER="db.example.com",
    POSTGRES_USER="user",
    POSTGRES_PASSWORD="pw",
    POSTGRES_DB="app",
)


def test_dsn_unchanged_without_sslmode() -> None:
    s = Settings(**_BASE)
    dsn = str(s.SQLALCHEMY_DATABASE_URI)
    assert "sslmode" not in dsn
    assert dsn.startswith("postgresql+psycopg://")


def test_dsn_carries_sslmode_when_set() -> None:
    # WS9.5: Neon (managed Postgres) requires TLS; POSTGRES_SSLMODE=require
    # must land in the DSN query string.
    s = Settings(**_BASE, POSTGRES_SSLMODE="require")
    assert str(s.SQLALCHEMY_DATABASE_URI).endswith("/app?sslmode=require")
