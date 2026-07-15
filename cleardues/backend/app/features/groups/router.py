# Groups feature router - API routes for group management
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.features.expenses.models import (
    AuditLogsPublic,
    ExpensePublic,
    ExpenseSplitPublic,
    GroupExpenseItem,
    GroupExpensesPublic,
    PairwiseBalancesPublic,
)
from app.features.groups import service
from app.features.auth.models import Message
from app.features.groups.models import (
    ExpenseGroup,
    ExpenseGroupCreate,
    ExpenseGroupDetail,
    ExpenseGroupPublic,
    ExpenseGroupWithMembers,
    GroupInvite,
    GroupInviteCreate,
    GroupInvitePublic,
    GroupInviteResponse,
    GroupInvitesPublic,
    GroupMembersListResponse,
    GroupSettingsPublic,
    GroupSettingsUpdate,
    InvitePreview,
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


# === Group Detail & Ledger Endpoints (WS5/B-H7) ===


def _get_group_for_member(
    session: SessionDep, group_id: uuid.UUID, current_user: CurrentUser
) -> ExpenseGroup:
    """Load a group and enforce membership (404 / 403)."""
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    if not service.is_group_member(
        session, group_id=group_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )
    return group


@router.get("/{group_id}", response_model=ExpenseGroupDetail)
def get_group_detail(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> ExpenseGroupDetail:
    """
    Get one group with member count and the current user's net balance.

    Only group members can view group details. This is the backing endpoint
    for the /groups/$groupId screen (deep-linkable group detail).
    """
    from app.features.expenses import service as expense_service

    group = _get_group_for_member(session, group_id, current_user)

    # Lazy confirmation-policy sweeps (WS6) so the balance reflects expired
    # objection/dispute windows
    swept = expense_service.auto_confirm_expired_expenses(
        session, group_id=group_id
    )
    swept += expense_service.auto_confirm_expired_settlement_claims(
        session, group_id=group_id
    )
    if swept:
        session.commit()

    return ExpenseGroupDetail(
        id=group.id,
        name=group.name,
        created_by=group.created_by,
        created_at=group.created_at,
        updated_at=group.updated_at,
        member_count=service.get_group_member_count(session, group_id),
        net_balance=expense_service.get_group_net_balance(
            session, group_id, current_user.id
        ),
    )


@router.get("/{group_id}/expenses", response_model=GroupExpensesPublic)
def list_group_expenses(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> GroupExpensesPublic:
    """
    List a group's expenses, newest first, each with the current user's own
    split attached (my_split is null when they are not part of the split).

    Only group members can view the ledger.
    """
    from app.features.expenses import service as expense_service

    _get_group_for_member(session, group_id, current_user)

    # Lazy confirmation-policy sweep (WS6): expenses past their objection
    # window confirm before the ledger is built
    if expense_service.auto_confirm_expired_expenses(session, group_id=group_id):
        session.commit()

    rows, count = expense_service.get_group_expenses(
        session, group_id, current_user.id, limit=limit, offset=offset
    )

    return GroupExpensesPublic(
        data=[
            GroupExpenseItem(
                expense=ExpensePublic.model_validate(expense),
                my_split=(
                    ExpenseSplitPublic.model_validate(split)
                    if split is not None
                    else None
                ),
            )
            for expense, split in rows
        ],
        count=count,
    )


# === WS6: Pairwise balances + group settings ===


@router.get("/{group_id}/pairwise-balances", response_model=PairwiseBalancesPublic)
def get_pairwise_balances(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> PairwiseBalancesPublic:
    """
    Who owes whom, exactly (WS6/S2-F9): per group member, what they owe the
    current user and what the current user owes them, with the net. The UI
    prerequisite for "Settle with X". Only group members can view.
    """
    from app.features.expenses import service as expense_service

    _get_group_for_member(session, group_id, current_user)

    # Lazy confirmation-policy sweeps (WS6) so balances reflect expired
    # objection/dispute windows
    swept = expense_service.auto_confirm_expired_expenses(
        session, group_id=group_id
    )
    swept += expense_service.auto_confirm_expired_settlement_claims(
        session, group_id=group_id
    )
    if swept:
        session.commit()

    items = expense_service.get_pairwise_balances(
        session, group_id, current_user.id
    )
    return PairwiseBalancesPublic(data=items, count=len(items))


@router.get("/{group_id}/settings", response_model=GroupSettingsPublic)
def get_group_settings(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupSettingsPublic:
    """
    Get a group's settings (WS6 — strict mode). Only group members can view.
    """
    _get_group_for_member(session, group_id, current_user)
    settings_row = service.get_or_create_group_settings(session, group_id)
    response = GroupSettingsPublic(
        group_id=settings_row.group_id,
        strict_mode=settings_row.strict_mode,
        ai_personality=settings_row.ai_personality,
    )
    session.commit()  # persists the lazily-created defaults row
    return response


@router.patch("/{group_id}/settings", response_model=GroupSettingsPublic)
def update_group_settings(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    settings_in: GroupSettingsUpdate,
) -> GroupSettingsPublic:
    """
    Update a group's settings. Owner only. Fields are optional — send only
    what changes.

    strict_mode (WS6) ON: every participant must explicitly confirm each
    expense. OFF (default): confirmation is opt-in — expenses auto-confirm
    after the objection window unless someone rejects first.

    ai_personality (WS7): commentary tone for AI expense parsing —
    professional | friendly | funny (capped at funny, UX-H5).
    """
    _get_group_for_member(session, group_id, current_user)

    if not service.is_group_owner(session, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can change group settings",
        )

    settings_row = service.get_or_create_group_settings(session, group_id)
    updates = settings_in.model_dump(exclude_unset=True, exclude_none=True)
    for field, value in updates.items():
        setattr(settings_row, field, value)
    session.add(settings_row)
    session.commit()
    session.refresh(settings_row)

    return GroupSettingsPublic(
        group_id=settings_row.group_id,
        strict_mode=settings_row.strict_mode,
        ai_personality=settings_row.ai_personality,
    )


# === Member Endpoints ===


@router.get("/{group_id}/members", response_model=GroupMembersListResponse)
def list_group_members(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupMembersListResponse:
    """
    List all members of a group with their details.

    Only group members can view the member list.
    Returns members ordered by role (owner first), then by join date.
    """
    # Verify group exists
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Verify user is a member
    if not service.is_group_member(session, group_id=group_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    members = service.get_group_members_with_user_data(session, group_id)

    return GroupMembersListResponse(
        members=members,
        count=len(members),
    )


# === Invite Endpoints ===
#
# WS8/S5-M4: accepting an invite is a POST (GET only previews — a
# state-changing GET let link prefetchers join groups), invites are capped
# per-use and revocable by the owner.


def _build_invite_public(invite: GroupInvite) -> GroupInvitePublic:
    return GroupInvitePublic(
        id=invite.id,
        group_id=invite.group_id,
        token=invite.token,
        expires_at=invite.expires_at,
        created_at=invite.created_at,
        max_uses=invite.max_uses,
        use_count=invite.use_count,
        revoked_at=invite.revoked_at,
        invite_url=f"{settings.FRONTEND_HOST}/invite/{invite.token}",
    )


def _get_group_for_owner(
    session: SessionDep, group_id: uuid.UUID, current_user: CurrentUser
) -> None:
    """Enforce group existence + ownership (404 / 403)."""
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )
    if not service.is_group_owner(session, group_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group owner can manage invite links",
        )


@router.post("/{group_id}/invites", response_model=GroupInviteResponse, status_code=201)
def create_invite(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    invite_in: GroupInviteCreate | None = None,
) -> GroupInviteResponse:
    """
    Generate an invite link for a group.

    Only the group owner can generate invites. Links expire after 30 days
    and allow max_uses joins (default 10).
    """
    _get_group_for_owner(session, group_id, current_user)

    max_uses = invite_in.max_uses if invite_in else 10
    invite = service.create_group_invite(
        session, group_id, current_user.id, max_uses=max_uses
    )
    session.commit()

    return GroupInviteResponse(
        invite=_build_invite_public(invite),
        message="Invite link created successfully",
    )


@router.get("/{group_id}/invites", response_model=GroupInvitesPublic)
def list_invites(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupInvitesPublic:
    """
    List a group's active invite links (owner only) — the revocation UI.
    """
    _get_group_for_owner(session, group_id, current_user)
    invites = service.get_group_invites(session, group_id)
    return GroupInvitesPublic(
        data=[_build_invite_public(i) for i in invites],
        count=len(invites),
    )


@router.delete("/{group_id}/invites/{invite_id}", response_model=Message)
def revoke_invite(
    group_id: uuid.UUID,
    invite_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Revoke an invite link (owner only, WS8/S5-M4). The link stops working
    immediately; existing members are unaffected.
    """
    _get_group_for_owner(session, group_id, current_user)

    invite = session.get(GroupInvite, invite_id)
    if not invite or invite.group_id != group_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invite not found",
        )

    service.revoke_invite(session, invite)
    session.commit()
    return Message(message="Invite link revoked. It can't be used to join anymore.")


def _get_valid_invite(session: SessionDep, token: str) -> GroupInvite:
    """Look up an invite token and 404/410 on invalid/expired/revoked."""
    invite = service.get_invite_by_token(session, token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invite link",
        )
    is_valid, error_msg = service.is_invite_valid(invite)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=error_msg,
        )
    return invite


@router.get("/invite/{token}", response_model=InvitePreview)
def preview_invite(
    token: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> InvitePreview:
    """
    Preview an invite WITHOUT joining: group name, member count, expiry.

    Read-only — the landing page renders this and joining happens via the
    explicit POST below. (WS10 extends this into the public preview page.)
    """
    invite = _get_valid_invite(session, token)

    group = service.get_group_by_id(session, invite.group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The group no longer exists",
        )

    return InvitePreview(
        group_id=group.id,
        group_name=group.name,
        member_count=service.get_group_member_count(session, group.id),
        expires_at=invite.expires_at,
        already_member=service.is_group_member(
            session, group_id=group.id, user_id=current_user.id
        ),
    )


@router.post("/invite/{token}/accept", response_model=GroupInviteResponse)
def accept_invite(
    token: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> GroupInviteResponse:
    """
    Accept a group invite using the invite token (explicit POST — WS8/S5-M4).

    The authenticated user will be added as a member of the group.
    """
    invite = _get_valid_invite(session, token)

    # Get group (verify it still exists)
    group = service.get_group_by_id(session, invite.group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The group no longer exists",
        )

    # Accept the invite (re-validates under a row lock; counts the use)
    success, message = service.accept_invite(session, invite, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=message)
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


# =============================================================================
# Story 4.4: Group Audit Log
# =============================================================================


@router.get("/{group_id}/audit-log", response_model=AuditLogsPublic)
def get_group_audit_log(
    group_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AuditLogsPublic:
    """
    Get audit logs for all expenses in a group.

    User must be a member of the group to view audit logs.
    Returns entries sorted by timestamp descending with pagination.
    """
    from app.features.expenses import service as expense_service

    # Verify group exists
    group = service.get_group_by_id(session, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    # Verify user is a member
    if not service.is_group_member(session, group_id=group_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    logs, count = expense_service.get_group_audit_logs(
        session, group_id, limit=limit, offset=offset
    )

    return AuditLogsPublic(
        data=logs,
        count=count,
    )
