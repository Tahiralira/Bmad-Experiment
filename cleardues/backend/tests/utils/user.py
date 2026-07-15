from sqlmodel import Session

from app import crud
from app.models import User, UserCreate
from tests.utils.utils import random_email, random_lower_string, token_headers_for_user


def create_random_user(db: Session) -> User:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    return user


def authentication_token_from_email(*, email: str, db: Session) -> dict[str, str]:
    """
    Return a valid token for the user with given email.

    If the user doesn't exist it is created first. Tokens are minted
    directly (WS8: no password login endpoint exists to round-trip through).
    """
    user = crud.get_user_by_email(session=db, email=email)
    if not user:
        user_in_create = UserCreate(email=email, password=random_lower_string())
        user = crud.create_user(session=db, user_create=user_in_create)
    return token_headers_for_user(user)
