# Groups feature service - CRUD operations for groups
import uuid

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.currency import normalize_currency
from app.features.auth.models import utc_now
from app.features.auth.models import User
from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupWithMembers,
    GroupInvite,
    GroupMember,
    GroupMemberPublic,
    GroupSettings,
    GROUP_ROLE_MEMBER,
    GROUP_ROLE_OWNER,
)


def create_expense_group(
    session: Session,
    group_in: ExpenseGroupCreate,
    creator_id: uuid.UUID,
) -> ExpenseGroup:
    """
    Create a new expense group and add creator as owner.

    Args:
        session: Database session
        group_in: Group creation data
        creator_id: UUID of the user creating the group

    Returns:
        Created ExpenseGroup with creator as member
    """
    # Create the group
    group = ExpenseGroup(
        name=group_in.name,
        created_by=creator_id,
    )
    session.add(group)
    session.flush()  # Get the group.id before creating member

    # Add creator as owner member
    member = GroupMember(
        group_id=group.id,
        user_id=creator_id,
        role=GROUP_ROLE_OWNER,
    )
    session.add(member)

    # WS10.1: seed the settings row with the client's locale-detected currency
    # (normalize_currency falls back to the default on empty/unknown codes) so
    # the group starts denominated correctly instead of always in USD.
    # WS10.4: an onboarding template may also preset strict_mode; when omitted,
    # fall back to the GroupSettings default (False) rather than forcing a value.
    settings = GroupSettings(
        group_id=group.id,
        currency=normalize_currency(group_in.currency),
    )
    if group_in.strict_mode is not None:
        settings.strict_mode = group_in.strict_mode
    session.add(settings)

    session.flush()  # Flush member + settings to DB within transaction
    session.refresh(group)
    # Note: Caller is responsible for commit (handled by FastAPI session dependency)

    return group


def get_group_currency(session: Session, group_id: uuid.UUID) -> str:
    """The group's ISO-4217 currency (WS10.1), or the default if unset.

    Read-only — does NOT create a settings row (unlike
    get_or_create_group_settings), so it's safe on hot read paths.
    """
    currency = session.exec(
        select(GroupSettings.currency).where(GroupSettings.group_id == group_id)
    ).first()
    return normalize_currency(currency)


def get_group_by_id(session: Session, group_id: uuid.UUID) -> ExpenseGroup | None:
    """Get a group by ID."""
    return session.get(ExpenseGroup, group_id)


def get_user_groups(session: Session, user_id: uuid.UUID) -> list[ExpenseGroup]:
    """Get all groups where user is a member."""
    statement = (
        select(ExpenseGroup)
        .join(GroupMember)
        .where(GroupMember.user_id == user_id)
        .order_by(ExpenseGroup.updated_at.desc())
    )
    return list(session.exec(statement).all())


def is_group_member(
    session: Session, *, group_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Check if user is a member of the group.

    The ONLY membership helper — its former twin
    (expenses.service.is_user_group_member) took the same two UUIDs in the
    opposite order and caused a swapped-argument bug (review B-C1/B-M10).
    Arguments are keyword-only so call sites can never silently transpose them.
    """
    statement = select(GroupMember).where(
        GroupMember.group_id == group_id, GroupMember.user_id == user_id
    )
    return session.exec(statement).first() is not None


def get_group_member_count(session: Session, group_id: uuid.UUID) -> int:
    """Get the count of members in a group using efficient SQL COUNT."""
    statement = (
        select(func.count())
        .select_from(GroupMember)
        .where(GroupMember.group_id == group_id)
    )
    return session.exec(statement).one()


def get_user_groups_with_member_count(
    session: Session, user_id: uuid.UUID
) -> list[ExpenseGroupWithMembers]:
    """
    Get all groups where user is a member, with member counts in a single query.

    Uses a subquery to efficiently count members without N+1 problem.
    """
    # Subquery to count members per group
    member_count_subq = (
        select(GroupMember.group_id, func.count().label("member_count"))
        .group_by(GroupMember.group_id)
        .subquery()
    )

    # Main query joining groups with member counts
    statement = (
        select(
            ExpenseGroup.id,
            ExpenseGroup.name,
            ExpenseGroup.created_by,
            ExpenseGroup.created_at,
            ExpenseGroup.updated_at,
            member_count_subq.c.member_count,
        )
        .join(GroupMember, GroupMember.group_id == ExpenseGroup.id)
        .join(member_count_subq, member_count_subq.c.group_id == ExpenseGroup.id)
        .where(GroupMember.user_id == user_id)
        .order_by(ExpenseGroup.updated_at.desc())
    )

    results = session.exec(statement).all()

    return [
        ExpenseGroupWithMembers(
            id=row.id,
            name=row.name,
            created_by=row.created_by,
            created_at=row.created_at,
            updated_at=row.updated_at,
            member_count=row.member_count,
        )
        for row in results
    ]


# === Invite Functions ===


def create_group_invite(
    session: Session,
    group_id: uuid.UUID,
    creator_id: uuid.UUID,
    max_uses: int = 10,
) -> GroupInvite:
    """
    Create a new invite token for a group.

    Args:
        session: Database session
        group_id: UUID of the group to create invite for
        creator_id: UUID of the user creating the invite (must be owner)
        max_uses: how many joins this link allows (WS8/S5-M4)

    Returns:
        Created GroupInvite with token
    """
    invite = GroupInvite(
        group_id=group_id,
        token=GroupInvite.generate_token(),
        expires_at=GroupInvite.default_expiration(),
        max_uses=max_uses,
        created_by=creator_id,
    )
    session.add(invite)
    session.flush()
    session.refresh(invite)
    return invite


def get_invite_by_token(session: Session, token: str) -> GroupInvite | None:
    """Get an invite by its token."""
    statement = select(GroupInvite).where(GroupInvite.token == token)
    return session.exec(statement).first()


def is_invite_valid(invite: GroupInvite) -> tuple[bool, str]:
    """
    Check if an invite is valid (not expired / revoked / used up — WS8/S5-M4).

    Returns:
        Tuple of (is_valid, error_message)
    """
    if invite.revoked_at is not None:
        return False, "This invite link was revoked by the group owner"
    if invite.is_expired():
        return False, "This invite link has expired"
    if invite.use_count >= invite.max_uses:
        return False, "This invite link has reached its usage limit"
    return True, ""


def accept_invite(
    session: Session,
    invite: GroupInvite,
    user_id: uuid.UUID,
) -> tuple[bool, str]:
    """
    Accept an invite and add user to the group.

    The invite row is re-read FOR UPDATE (WS4/M8 discipline) so concurrent
    accepts can't blow past max_uses; joining consumes one use, but an
    already-member no-op does not.

    Returns:
        Tuple of (success, message)
    """
    # Check if already a member (consumes no use)
    if is_group_member(session, group_id=invite.group_id, user_id=user_id):
        return True, "You are already a member of this group"

    # Lock the invite row and re-validate under the lock
    locked_invite = session.exec(
        select(GroupInvite).where(GroupInvite.id == invite.id).with_for_update()
    ).one()
    is_valid, error_msg = is_invite_valid(locked_invite)
    if not is_valid:
        return False, error_msg

    locked_invite.use_count += 1
    session.add(locked_invite)

    # Add as member
    member = GroupMember(
        group_id=invite.group_id,
        user_id=user_id,
        role=GROUP_ROLE_MEMBER,
    )
    session.add(member)
    session.flush()

    return True, "Successfully joined the group"


def revoke_invite(session: Session, invite: GroupInvite) -> GroupInvite:
    """Revoke an invite (WS8/S5-M4). Idempotent. Flushes; caller commits."""
    if invite.revoked_at is None:
        invite.revoked_at = utc_now()
        session.add(invite)
        session.flush()
    return invite


def is_group_owner(session: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if user is the owner of the group."""
    statement = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.role == GROUP_ROLE_OWNER,
    )
    return session.exec(statement).first() is not None


def get_group_invites(session: Session, group_id: uuid.UUID) -> list[GroupInvite]:
    """Get all active (non-expired, non-revoked) invites for a group."""
    statement = (
        select(GroupInvite)
        .where(
            GroupInvite.group_id == group_id,
            GroupInvite.expires_at > utc_now(),
            GroupInvite.revoked_at.is_(None),  # type: ignore[union-attr]
        )
        .order_by(GroupInvite.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_or_create_group_settings(
    session: Session, group_id: uuid.UUID
) -> GroupSettings:
    """
    Load a group's settings row, creating the defaults lazily (WS6).

    Flushes only — the router commits the request transaction (ARCH-001).
    """
    settings = session.exec(
        select(GroupSettings).where(GroupSettings.group_id == group_id)
    ).first()
    if not settings:
        settings = GroupSettings(group_id=group_id)
        session.add(settings)
        session.flush()
        session.refresh(settings)
    return settings


def get_group_members_with_user_data(
    session: Session,
    group_id: uuid.UUID,
) -> list[GroupMemberPublic]:
    """
    Get all members of a group with their user details.

    Joins GroupMember with User to get full_name and email.
    Orders by role (owner first), then by joined_at.

    Args:
        session: Database session
        group_id: UUID of the group

    Returns:
        List of GroupMemberPublic with user details
    """
    # Join GroupMember with User to get user details
    statement = (
        select(
            GroupMember.id,
            GroupMember.user_id,
            GroupMember.role,
            GroupMember.joined_at,
            User.full_name,
            User.email,
        )
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(
            # Owner first (descending sort: 'owner' > 'member' alphabetically)
            GroupMember.role.desc(),
            GroupMember.joined_at.asc(),
        )
    )

    results = session.exec(statement).all()

    return [
        GroupMemberPublic(
            id=row.id,
            user_id=row.user_id,
            role=row.role,
            joined_at=row.joined_at,
            full_name=row.full_name,
            email=row.email,
        )
        for row in results
    ]
