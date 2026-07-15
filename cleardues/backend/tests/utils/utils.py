import random
import string
from datetime import timedelta

from sqlmodel import Session, select

from app.core import security
from app.core.config import settings
from app.models import User


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def token_headers_for_user(user: User) -> dict[str, str]:
    """Mint a JWT for a user directly.

    There is no password login endpoint anymore (WS8 deleted the template's
    password-auth stack), so tests create tokens the same way the magic-link
    and OAuth flows do.
    """
    token = security.create_access_token(user.id, expires_delta=timedelta(hours=1))
    return {"Authorization": f"Bearer {token}"}


def get_superuser_token_headers(db: Session) -> dict[str, str]:
    user = db.exec(select(User).where(User.email == settings.FIRST_SUPERUSER)).one()
    return token_headers_for_user(user)
