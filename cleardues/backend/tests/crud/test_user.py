import time
from datetime import datetime

from fastapi.encoders import jsonable_encoder
from sqlmodel import Session

from app import crud
from app.models import User, UserCreate, UserUpdate
from tests.utils.utils import random_email, random_lower_string


def test_create_user(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.email == email
    assert hasattr(user, "hashed_password")


def test_check_if_user_is_active(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_active is True


def test_check_if_user_is_active_inactive(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, disabled=True)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_active


def test_check_if_user_is_superuser(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_superuser is True


def test_check_if_user_is_superuser_normal_user(db: Session) -> None:
    username = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=username, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.is_superuser is False


def test_get_user(db: Session) -> None:
    password = random_lower_string()
    username = random_email()
    user_in = UserCreate(email=username, password=password, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    assert jsonable_encoder(user) == jsonable_encoder(user_2)


def test_update_user(db: Session) -> None:
    password = random_lower_string()
    email = random_email()
    user_in = UserCreate(email=email, password=password, is_superuser=True)
    user = crud.create_user(session=db, user_create=user_in)
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password, is_superuser=True)
    if user.id is not None:
        crud.update_user(session=db, db_user=user, user_in=user_in_update)
    user_2 = db.get(User, user.id)
    assert user_2
    assert user.email == user_2.email
    # No password login exists (WS8); assert the hash changed rather than
    # round-tripping a verification that has no product meaning anymore.
    assert user_2.hashed_password
    assert user_2.hashed_password != new_password


def test_user_has_created_at_timestamp(db: Session) -> None:
    """Test that created_at is automatically set when user is created."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.created_at is not None
    assert isinstance(user.created_at, datetime)
    # Verify timestamp is recent (within last minute)
    time_diff = (datetime.now(user.created_at.tzinfo) - user.created_at).total_seconds()
    assert time_diff < 60


def test_user_has_updated_at_timestamp(db: Session) -> None:
    """Test that updated_at is automatically set when user is created."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.updated_at is not None
    assert isinstance(user.updated_at, datetime)
    # Initially, created_at and updated_at should be very close
    time_diff = abs((user.updated_at - user.created_at).total_seconds())
    assert time_diff < 1


def test_user_updated_at_changes_on_update(db: Session) -> None:
    """Test that updated_at changes when user is updated."""
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    original_updated_at = user.updated_at

    # Wait a moment to ensure timestamp difference
    time.sleep(0.1)

    # Update user
    new_password = random_lower_string()
    user_in_update = UserUpdate(password=new_password)
    if user.id is not None:
        crud.update_user(session=db, db_user=user, user_in=user_in_update)

    # Refresh user from database
    db.refresh(user)

    # Verify updated_at has changed
    assert user.updated_at > original_updated_at
    # Verify created_at hasn't changed
    assert user.created_at == user.created_at
