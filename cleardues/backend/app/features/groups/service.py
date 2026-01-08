# Groups feature service - CRUD operations for groups
import uuid

from sqlalchemy import func
from sqlmodel import Session, select

from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupWithMembers,
    GroupMember,
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
