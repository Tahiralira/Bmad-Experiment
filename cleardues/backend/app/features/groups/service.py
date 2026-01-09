# Groups feature service - CRUD operations for groups
import uuid

from sqlalchemy import func
from sqlmodel import Session, select

from app.features.auth.models import utc_now
from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupWithMembers,
    GroupInvite,
    GroupMember,
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
    session.flush()  # Flush member to DB within transaction
    session.refresh(group)
    # Note: Caller is responsible for commit (handled by FastAPI session dependency)

    return group


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
    session: Session, group_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    """Check if user is a member of the group."""
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
) -> GroupInvite:
    """
    Create a new invite token for a group.

    Args:
        session: Database session
        group_id: UUID of the group to create invite for
        creator_id: UUID of the user creating the invite (must be owner)

    Returns:
        Created GroupInvite with token
    """
    invite = GroupInvite(
        group_id=group_id,
        token=GroupInvite.generate_token(),
        expires_at=GroupInvite.default_expiration(),
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
    Check if an invite is valid.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if invite.is_expired():
        return False, "This invite link has expired"
    return True, ""


def accept_invite(
    session: Session,
    invite: GroupInvite,
    user_id: uuid.UUID,
) -> tuple[bool, str]:
    """
    Accept an invite and add user to the group.

    Args:
        session: Database session
        invite: The invite to accept
        user_id: UUID of the user accepting the invite

    Returns:
        Tuple of (success, message)
    """
    # Check if already a member
    if is_group_member(session, invite.group_id, user_id):
        return True, "You are already a member of this group"

    # Add as member
    member = GroupMember(
        group_id=invite.group_id,
        user_id=user_id,
        role=GROUP_ROLE_MEMBER,
    )
    session.add(member)
    session.flush()

    return True, "Successfully joined the group"


def is_group_owner(session: Session, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    """Check if user is the owner of the group."""
    statement = select(GroupMember).where(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
        GroupMember.role == GROUP_ROLE_OWNER,
    )
    return session.exec(statement).first() is not None


def get_group_invites(session: Session, group_id: uuid.UUID) -> list[GroupInvite]:
    """Get all active (non-expired) invites for a group."""
    statement = (
        select(GroupInvite)
        .where(
            GroupInvite.group_id == group_id,
            GroupInvite.expires_at > utc_now(),
        )
        .order_by(GroupInvite.created_at.desc())
    )
    return list(session.exec(statement).all())
