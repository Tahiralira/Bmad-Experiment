# Groups feature router - API routes for group management
from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.features.groups import service
from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupPublic,
    ExpenseGroupWithMembers,
)

router = APIRouter(prefix="/expense-groups", tags=["groups"])


@router.post("/", response_model=ExpenseGroupPublic, status_code=201)
def create_group(
    session: SessionDep,
    current_user: CurrentUser,
    group_in: ExpenseGroupCreate,
) -> ExpenseGroup:
    """
    Create a new expense group.

    The authenticated user becomes the owner of the group and is
    automatically added as a member.
    """
    group = service.create_expense_group(
        session=session,
        group_in=group_in,
        creator_id=current_user.id,
    )
    session.commit()
    return group


@router.get("/", response_model=list[ExpenseGroupWithMembers])
def list_user_groups(
    session: SessionDep,
    current_user: CurrentUser,
) -> list[ExpenseGroupWithMembers]:
    """
    List all expense groups the current user is a member of.

    Uses optimized single-query to fetch groups with member counts.
    """
    return service.get_user_groups_with_member_count(session, current_user.id)
