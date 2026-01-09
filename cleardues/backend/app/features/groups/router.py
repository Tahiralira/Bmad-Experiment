# Groups feature router - API routes for group management
import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.features.groups import service
from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupPublic,
    ExpenseGroupWithMembers,
    GroupInvitePublic,
    GroupInviteResponse,
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


# === Invite Endpoints ===


@router.post("/{group_id}/invites", response_model=GroupInviteResponse, status_code=201)
def create_invite(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupInviteResponse:
    """
    Generate an invite link for a group.

    Only the group owner can generate invites.
    """
    # Verify group exists
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Verify user is owner
    if not service.is_group_owner(session, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can generate invite links",
        )

    invite = service.create_group_invite(session, group_id, current_user.id)
    session.commit()

    # Build invite URL
    invite_url = f"{settings.FRONTEND_HOST}/invite/{invite.token}"

    return GroupInviteResponse(
        invite=GroupInvitePublic(
            id=invite.id,
            group_id=invite.group_id,
            token=invite.token,
            expires_at=invite.expires_at,
            created_at=invite.created_at,
            invite_url=invite_url,
        ),
        message="Invite link created successfully",
    )


@router.get("/invite/{token}", response_model=GroupInviteResponse)
def accept_invite(
    token: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupInviteResponse:
    """
    Accept a group invite using the invite token.

    The authenticated user will be added as a member of the group.
    """
    # Look up invite
    invite = service.get_invite_by_token(session, token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite link",
        )

    # Check if valid
    is_valid, error_msg = service.is_invite_valid(invite)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=error_msg,
        )

    # Get group (verify it still exists)
    group = service.get_group_by_id(session, invite.group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The group no longer exists",
        )

    # Accept the invite
    success, message = service.accept_invite(session, invite, current_user.id)
    session.commit()

    return GroupInviteResponse(
        group=ExpenseGroupPublic(
            id=group.id,
            name=group.name,
            created_by=group.created_by,
            created_at=group.created_at,
            updated_at=group.updated_at,
        ),
        message=message,
    )
