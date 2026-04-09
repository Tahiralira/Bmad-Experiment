# Auth feature service - CRUD operations for users and magic link tokens
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel import Session, func, select

from app.core.security import get_password_hash, verify_password
from app.features.auth.models import (
    User,
    UserCreate,
    UserUpdate,
    Item,
    ItemCreate,
    MagicLinkToken,
    AUTH_METHOD_OAUTH,
    GroupBalanceSummary,
)


# Magic link token expiration time in minutes
MAGIC_LINK_EXPIRE_MINUTES = 15

# Rate limiting: max requests per email within time window
MAGIC_LINK_RATE_LIMIT_MAX = 3
MAGIC_LINK_RATE_LIMIT_HOURS = 1


def hash_token(token: str) -> str:
    """Hash a token using SHA256 for secure storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


# Item CRUD - temporarily kept here for backward compatibility
# Will be moved to expenses feature in future stories
def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# ============================================================================
# MAGIC LINK TOKEN OPERATIONS
# ============================================================================


def is_rate_limited(*, session: Session, email: str) -> bool:
    """
    Check if an email has exceeded the rate limit for magic link requests.
    Returns True if rate limited, False otherwise.
    """
    window_start = datetime.now(timezone.utc) - timedelta(hours=MAGIC_LINK_RATE_LIMIT_HOURS)
    statement = select(func.count()).select_from(MagicLinkToken).where(
        MagicLinkToken.email == email,
        MagicLinkToken.created_at >= window_start
    )
    count = session.exec(statement).one()
    return count >= MAGIC_LINK_RATE_LIMIT_MAX


def generate_magic_link_token(*, session: Session, email: str) -> tuple[MagicLinkToken, str]:
    """
    Generate a new magic link token for the given email.
    Tokens expire after MAGIC_LINK_EXPIRE_MINUTES.
    The token is stored hashed for security.

    Returns:
        Tuple of (MagicLinkToken, raw_token) - the raw token is needed for the email link.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRE_MINUTES)
    raw_token = MagicLinkToken.generate_token()
    hashed = hash_token(raw_token)

    token = MagicLinkToken(
        email=email,
        token=hashed,  # Store hashed token
        expires_at=expires_at
    )
    session.add(token)
    session.commit()
    session.refresh(token)
    return token, raw_token


def verify_magic_link_token(*, session: Session, token_str: str) -> MagicLinkToken | None:
    """
    Verify a magic link token is valid, not expired, and not already used.
    Returns the token if valid, None otherwise.
    """
    # Hash the incoming token to compare with stored hash
    hashed = hash_token(token_str)
    statement = select(MagicLinkToken).where(
        MagicLinkToken.token == hashed,
        MagicLinkToken.expires_at > datetime.now(timezone.utc),
        MagicLinkToken.used_at.is_(None)
    )
    return session.exec(statement).first()


def mark_token_as_used(*, session: Session, token: MagicLinkToken) -> MagicLinkToken:
    """
    Mark a magic link token as used by setting used_at timestamp.
    """
    token.used_at = datetime.now(timezone.utc)
    session.add(token)
    session.commit()
    session.refresh(token)
    return token


def cleanup_expired_tokens(*, session: Session) -> int:
    """
    Delete all expired and used magic link tokens.
    Returns the number of tokens deleted.
    Useful for periodic maintenance.
    """
    # Delete tokens that are either expired or already used
    statement = select(MagicLinkToken).where(
        (MagicLinkToken.expires_at <= datetime.now(timezone.utc)) |
        (MagicLinkToken.used_at.is_not(None))
    )
    tokens = session.exec(statement).all()
    count = len(tokens)
    for token in tokens:
        session.delete(token)
    session.commit()
    return count


# ============================================================================
# OAUTH USER OPERATIONS
# ============================================================================


def get_user_by_oauth(
    *, session: Session, provider: str, provider_id: str
) -> User | None:
    """
    Find a user by OAuth provider and provider ID.
    """
    statement = select(User).where(
        User.oauth_provider == provider,
        User.oauth_provider_id == provider_id
    )
    return session.exec(statement).first()


def find_or_create_oauth_user(
    *,
    session: Session,
    email: str,
    full_name: str | None,
    provider: str,
    provider_id: str
) -> User:
    """
    Find existing user or create new one for OAuth login.

    Logic:
    1. First try to find by oauth_provider + oauth_provider_id (exact match)
    2. Then try to find by email (account linking)
    3. If not found, create new user

    Returns the user (existing or newly created).
    """
    import secrets

    # Try to find by OAuth provider ID first (existing OAuth user)
    user = get_user_by_oauth(
        session=session, provider=provider, provider_id=provider_id
    )
    if user:
        return user

    # Try to find by email (potential account linking)
    user = get_user_by_email(session=session, email=email)
    if user:
        # Link OAuth to existing account
        user.oauth_provider = provider
        user.oauth_provider_id = provider_id
        # Keep original auth_method if it was password or magic_link
        # User can still use those methods
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    # Create new OAuth user with placeholder password
    placeholder_password = secrets.token_urlsafe(32)
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(placeholder_password),
        auth_method=AUTH_METHOD_OAUTH,
        oauth_provider=provider,
        oauth_provider_id=provider_id,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# ============================================================================
# DASHBOARD OPERATIONS (Story 2.4)
# ============================================================================


def get_user_dashboard(session: Session, user_id: uuid.UUID) -> list[GroupBalanceSummary]:
    """
    Get dashboard data for a user showing all groups with net balances.

    Net balance is calculated from confirmed expenses:
    - Positive = user is owed money (paid more than their share)
    - Negative = user owes money (paid less than their share)

    Uses a single aggregated SQL query to avoid N+1 issues.

    Args:
        session: Database session
        user_id: UUID of the user

    Returns:
        List of GroupBalanceSummary objects ordered by most recent activity
    """
    # NOTE: Import inside function to avoid circular dependency between
    # auth.service -> groups.models -> auth.models. This is intentional.
    from app.features.groups.models import ExpenseGroup, GroupMember

    # Subquery to count members per group
    member_count_subq = (
        select(GroupMember.group_id, func.count().label("member_count"))
        .group_by(GroupMember.group_id)
        .subquery()
    )

    # Main query to get user's groups with member counts
    statement = (
        select(
            ExpenseGroup.id,
            ExpenseGroup.name,
            ExpenseGroup.updated_at,
            member_count_subq.c.member_count,
        )
        .join(GroupMember, GroupMember.group_id == ExpenseGroup.id)
        .join(member_count_subq, member_count_subq.c.group_id == ExpenseGroup.id)
        .where(GroupMember.user_id == user_id)
        .order_by(ExpenseGroup.updated_at.desc())  # Most recent activity first
    )

    results = session.exec(statement).all()

    if not results:
        return []

    # Calculate net balances from confirmed expenses using a single aggregated query
    # Net balance = (sum of splits where user is payer) - (sum of user's own splits)
    from sqlalchemy import case, literal

    from app.features.expenses.models import Expense, ExpenseSplit, ExpenseStatus, SplitStatus

    group_ids = [row.id for row in results]

    # Single query: for each group, compute what user owes vs what they're owed
    # - user_owes: negative sum of user's confirmed splits (what they owe others)
    # - owed_to_user: sum of ALL confirmed splits on expenses where user is the payer
    all_balances = session.exec(
        select(
            Expense.group_id,
            func.sum(
                case(
                    (ExpenseSplit.user_id == user_id, -ExpenseSplit.amount_owed),
                    else_=literal(0),
                )
            ).label("user_owes"),
            func.sum(
                case(
                    (Expense.payer_id == user_id, ExpenseSplit.amount_owed),
                    else_=literal(0),
                )
            ).label("owed_to_user"),
        )
        .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
        .where(
            Expense.status == ExpenseStatus.CONFIRMED,
            ExpenseSplit.status == SplitStatus.CONFIRMED,
            Expense.group_id.in_(group_ids),
        )
        .group_by(Expense.group_id)
    ).all()

    balance_map = {
        row.group_id: float((row.owed_to_user or 0) + (row.user_owes or 0))
        for row in all_balances
    }

    summaries = [
        GroupBalanceSummary(
            group_id=row.id,
            group_name=row.name,
            net_balance=round(balance_map.get(row.id, 0.0), 2),
            last_activity=row.updated_at,
            member_count=row.member_count,
        )
        for row in results
    ]

    return summaries
