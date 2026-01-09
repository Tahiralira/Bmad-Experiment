from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, MagicLinkToken, User
from app.features.groups.models import ExpenseGroup, GroupInvite, GroupMember
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import get_superuser_token_headers


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db(session)
        yield session
        # Clean up in correct order (respect foreign key constraints)
        statement = delete(GroupInvite)
        session.execute(statement)
        statement = delete(GroupMember)
        session.execute(statement)
        statement = delete(ExpenseGroup)
        session.execute(statement)
        statement = delete(Item)
        session.execute(statement)
        statement = delete(MagicLinkToken)
        session.execute(statement)
        statement = delete(User)
        session.execute(statement)
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client, email=settings.EMAIL_TEST_USER, db=db
    )


@pytest.fixture(scope="module")
def second_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    """Token headers for a second test user (for multi-user tests)."""
    return authentication_token_from_email(
        client=client, email="seconduser@example.com", db=db
    )
