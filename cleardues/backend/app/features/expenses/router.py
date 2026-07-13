# Expenses feature router - API routes for expense management
import uuid

from fastapi import APIRouter, Body, HTTPException, Query
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.features.expenses import service as expense_service
from app.features.expenses.models import (
    AggregateSettleUpRequest,
    AuditLogsPublic,
    Expense,
    ExpenseCreate,
    ExpensePublic,
    ExpenseSplitPublic,
    ExpenseSplitResponse,
    ExpenseSplitsPublic,
    ExpenseStatus,
    ExpenseUpdate,
    ExpenseRejectRequest,
    ExpenseRejectResponse,
    PendingConfirmationPublic,
    SettlementClaimPublic,
    SettlementClaimsPublic,
    PendingSettlementPublic,
    SplitRequest,
)
from app.features.expenses.service import (
    confirm_settlement_claim,
    reject_settlement_claim,
    get_claims_awaiting_owner_confirmation,
)
from app.features.groups.models import ExpenseGroup
from app.features.groups.service import is_group_member

router = APIRouter(prefix="/expenses", tags=["expenses"])

# TRANSACTION DISCIPLINE (WS4/H5): the service layer only flushes; every
# mutating endpoint here commits exactly once, after all writes (including
# audit entries) have joined the same transaction. See solution-patterns.yaml
# ARCH-001.


@router.post("/", response_model=ExpensePublic)
def create_expense(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_in: ExpenseCreate,
) -> ExpensePublic:
    """
    Create a new expense in a group.

    The current user must be a member of the group.
    If payer_id is not provided, defaults to the current user.
    New expenses start with status 'draft'.
    """
    # Verify group exists
    group = session.get(ExpenseGroup, expense_in.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify user is member of group
    if not is_group_member(
        session, group_id=expense_in.group_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to create expenses",
        )

    # If payer_id provided, verify payer is also a group member
    if expense_in.payer_id and expense_in.payer_id != current_user.id:
        if not is_group_member(
            session, group_id=expense_in.group_id, user_id=expense_in.payer_id
        ):
            raise HTTPException(
                status_code=400, detail="Payer must be a member of the group"
            )

    expense = expense_service.create_expense(session, expense_in, current_user.id)
    response = ExpensePublic.model_validate(expense)
    session.commit()
    return response


@router.patch("/{expense_id}", response_model=ExpensePublic)
def edit_expense(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
    expense_in: ExpenseUpdate,
) -> ExpensePublic:
    """
    Edit expense details. Only the creator can edit.
    Only DRAFT and PENDING_CONFIRMATION expenses can be edited.

    Changing the amount or the payer while splits exist re-opens consent:
    the splits are removed and the expense reverts to DRAFT for re-splitting.
    """
    expense = session.exec(
        select(Expense).where(Expense.id == expense_id).with_for_update()
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Authorization: Only creator can edit
    if expense.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the expense creator can edit this expense",
        )

    # Status guard: Confirmed/settled expenses are immutable
    if expense.status in (ExpenseStatus.CONFIRMED, ExpenseStatus.SETTLED):
        raise HTTPException(
            status_code=403,
            detail="Cannot edit a confirmed or settled expense",
        )

    # If payer_id changed, verify new payer is group member
    if expense_in.payer_id is not None and expense_in.payer_id != expense.payer_id:
        if not is_group_member(
            session, group_id=expense.group_id, user_id=expense_in.payer_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Payer must be a member of the group",
            )

    expense = expense_service.update_expense(session, expense, expense_in, current_user.id)
    response = ExpensePublic.model_validate(expense)
    session.commit()
    return response


@router.put("/{expense_id}/split", response_model=ExpenseSplitResponse)
def update_expense_split(
    *,
    session: SessionDep,
    expense_id: uuid.UUID,
    split_data: SplitRequest = Body(...),
    current_user: CurrentUser,
) -> ExpenseSplitResponse:
    """
    Update expense split configuration.

    The body is a discriminated union on `type`: equal (Story 3.5), unequal
    (Story 3.6), or percentage (Story 3.7) — malformed bodies (bad UUIDs,
    missing fields, out-of-range values, unknown types) are rejected with 422
    by schema validation (WS5/B-H6). Domain failures (non-members, sums that
    don't match the total) return 400.

    Only the expense creator can modify the split.
    Confirmed/settled expenses cannot have splits modified.
    """
    # Get and lock expense (serializes against concurrent confirm/reject,
    # which also lock this row — WS4/M8)
    expense = session.exec(
        select(Expense).where(Expense.id == expense_id).with_for_update()
    ).first()
    if not expense:
        raise HTTPException(
            status_code=404, detail="Expense not found"
        )

    # Status guard: Cannot modify splits on confirmed/settled expenses (Story 4.1)
    if expense.status in (ExpenseStatus.CONFIRMED, ExpenseStatus.SETTLED):
        raise HTTPException(
            status_code=403,
            detail="Cannot modify splits on a confirmed or settled expense",
        )

    # Verify user is expense creator
    if expense.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only expense creator can modify split",
        )

    # Validation + calculation + persistence live in ONE service function
    # (was ~220 lines copy-pasted three times here); audit entry joins the
    # same transaction (WS4/H5)
    try:
        splits_data = expense_service.apply_split(
            session, expense, split_data, current_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    session.commit()

    return ExpenseSplitResponse(
        expense_id=expense_id,
        split_type=split_data.type,
        splits=[{
            "user_id": s["user_id"],
            "amount_owed": s["amount_owed"],
        } for s in splits_data],
        excluded_user_ids=split_data.excluded_user_ids,
    )


# =============================================================================
# Story 4.2: Expense Confirmation Workflow
# =============================================================================


@router.post("/{expense_id}/confirm", response_model=ExpenseSplitPublic)
def confirm_expense_split_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
) -> ExpenseSplitPublic:
    """
    Confirm an expense split.

    User must have a split in this expense to confirm.
    Only pending_confirmation expenses can be confirmed.

    Returns the updated split with status 'confirmed'.
    """
    # Get expense
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Status guard: Only pending_confirmation expenses can be confirmed
    if expense.status != ExpenseStatus.PENDING_CONFIRMATION:
        raise HTTPException(
            status_code=403,
            detail="Cannot confirm a finalized expense"
        )

    # Use service layer for business logic
    split = expense_service.confirm_expense_split(session, expense_id, current_user.id)

    if not split:
        raise HTTPException(
            status_code=403,
            detail="You are not involved in this expense"
        )

    response = ExpenseSplitPublic.model_validate(split)
    session.commit()
    return response


@router.post("/{expense_id}/reject", response_model=ExpenseRejectResponse)
def reject_expense_split_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
    reject_data: ExpenseRejectRequest | None = None,
) -> ExpenseRejectResponse:
    """
    Reject an expense split.

    User must have a split in this expense to reject.
    Only pending_confirmation expenses can be rejected.
    Rejecting re-opens consent: all splits are removed and the expense
    reverts to DRAFT so the creator can re-split (WS4/H3 — no silent
    redistribution).

    Returns success message; remaining_splits is always 0.
    """
    # Get expense
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Status guard
    if expense.status != ExpenseStatus.PENDING_CONFIRMATION:
        raise HTTPException(
            status_code=403,
            detail="Cannot reject a finalized expense"
        )

    # Use service layer for business logic
    result = expense_service.reject_expense_split(session, expense_id, current_user.id)

    if not result:
        raise HTTPException(
            status_code=403,
            detail="You are not involved in this expense"
        )

    session.commit()
    return ExpenseRejectResponse(
        message=result["message"],
        remaining_splits=result["remaining_splits"]
    )


@router.get("/pending-confirmations", response_model=list[PendingConfirmationPublic])
def get_pending_confirmations(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[PendingConfirmationPublic]:
    """
    Get all expenses pending confirmation for the current user.

    Returns expenses where user has a split with status 'pending'
    and expense status is 'pending_confirmation'.
    """
    # Lazy confirmation-policy sweep (WS6): in non-strict groups, expenses
    # past their objection window auto-confirm before the list is built
    if expense_service.auto_confirm_expired_expenses(
        session, participant_user_id=current_user.id
    ):
        session.commit()

    # Use service layer for data retrieval
    pending_data = expense_service.get_pending_confirmations_for_user(
        session, current_user.id
    )

    result = []
    for item in pending_data:
        result.append(PendingConfirmationPublic(
            expense=ExpensePublic.model_validate(item["expense"]),
            split=ExpenseSplitPublic.model_validate(item["split"])
        ))

    return result


@router.get("/pending-settlements", response_model=list[PendingSettlementPublic])
def get_pending_settlements(
    *,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[PendingSettlementPublic]:
    """
    Get all expenses with pending settlement claims for the current user.

    Returns expenses where the user has submitted a settlement claim
    that is still awaiting owner confirmation (status: pending).
    """
    # Lazy dispute-window sweep (WS6): expired claims confirm before listing
    if expense_service.auto_confirm_expired_settlement_claims(
        session, involving_user_id=current_user.id
    ):
        session.commit()

    pending_data = expense_service.get_pending_settlements_for_user(
        session, current_user.id
    )

    result = []
    for item in pending_data:
        result.append(PendingSettlementPublic(
            expense=ExpensePublic.model_validate(item["expense"]),
            split=ExpenseSplitPublic.model_validate(item["split"]),
            claim=item["claim"],
        ))

    return result


@router.get("/settlement-claims/pending-for-owner", response_model=list[PendingSettlementPublic])
def get_pending_claims_for_owner(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID | None = None,
) -> list[PendingSettlementPublic]:
    """
    Get all pending settlement claims for expenses owned by the current user.

    Returns claims where the current user is the expense owner (payer)
    and the claim status is still 'pending'. Pass ?group_id= to scope the
    list to one group (WS5/S4-M6 — group screens must not show other
    groups' claims).
    """
    # Lazy dispute-window sweep (WS6): expired claims confirm before listing
    if expense_service.auto_confirm_expired_settlement_claims(
        session, involving_user_id=current_user.id, group_id=group_id
    ):
        session.commit()

    pending_data = get_claims_awaiting_owner_confirmation(
        session, current_user.id, group_id=group_id
    )

    result = []
    for item in pending_data:
        result.append(PendingSettlementPublic(
            expense=ExpensePublic.model_validate(item["expense"]),
            split=ExpenseSplitPublic.model_validate(item["split"]),
            claim=item["claim"],
        ))

    return result


# =============================================================================
# Story 4.4: Audit Log Retrieval
# =============================================================================


@router.get("/{expense_id}/audit-log", response_model=AuditLogsPublic)
def get_expense_audit_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> AuditLogsPublic:
    """
    Get audit logs for a specific expense.

    User must be a member of the expense's group to view audit logs.
    Returns entries sorted by timestamp descending with pagination.
    """
    # Get expense
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Verify user is member of the expense's group
    if not is_group_member(
        session, group_id=expense.group_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to view audit logs",
        )

    logs, count = expense_service.get_expense_audit_logs(
        session, expense_id, limit=limit, offset=offset
    )

    return AuditLogsPublic(
        data=logs,
        count=count,
    )


# =============================================================================
# Story 5.1: Settlement Claims
# =============================================================================


@router.post("/{expense_id}/settle", response_model=SettlementClaimPublic, status_code=201)
def settle_expense_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
) -> SettlementClaimPublic:
    """
    Mark an expense split as settled (claim payment).

    Creates a settlement claim for the current user's split in the expense.
    The claim starts with status 'pending' and awaits owner confirmation (Story 5.2).

    Returns 201 Created with the settlement claim details.
    Error responses: 400 (expense not confirmed), 403 (not involved),
                     404 (expense not found), 409 (already claimed)
    """
    # Get expense (404 if not found)
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Status guard: Only confirmed expenses can be settled
    if expense.status != ExpenseStatus.CONFIRMED:
        raise HTTPException(
            status_code=400,
            detail="Expense must be confirmed before settling",
        )

    # Use service layer for business logic
    result = expense_service.settle_expense_split(
        session, expense_id, current_user.id
    )

    if result == "CONFLICT":
        raise HTTPException(
            status_code=409,
            detail="Settlement already claimed for this expense",
        )

    if not result:
        raise HTTPException(
            status_code=403,
            detail="You are not involved in this expense",
        )

    session.commit()
    return result


# =============================================================================
# Story 5.2: Owner Confirms Settlement
# =============================================================================


def _handle_settlement_result(result, session=None):
    """Translate service sentinel values to HTTPException for settlement endpoints."""
    if result is None:
        raise HTTPException(status_code=404, detail="Settlement claim not found")
    if result == "FORBIDDEN":
        raise HTTPException(
            status_code=403,
            detail="Only the expense owner can manage settlements",
        )
    if result == "CONFLICT":
        raise HTTPException(
            status_code=409,
            detail="Settlement claim has already been processed",
        )
    if result == "EXPIRED":
        # WS6: the dispute window closed — the service confirmed the claim
        # in this transaction; persist that before signalling the caller
        if session is not None:
            session.commit()
        raise HTTPException(
            status_code=409,
            detail=(
                "The dispute window has closed — this claim was "
                "auto-confirmed after 72 hours"
            ),
        )
    return result


@router.post("/settlement-claims/{claim_id}/confirm", response_model=SettlementClaimPublic)
def confirm_settlement_claim_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
) -> SettlementClaimPublic:
    """
    Confirm a settlement claim.

    Only the expense owner (payer) can confirm settlement claims.
    On confirmation: claim status → confirmed, split status → settled.
    If all splits in the expense are settled, expense status → settled.

    Error responses: 403 (not expense owner), 404 (claim not found),
                     409 (claim already processed)
    """
    result = _handle_settlement_result(
        confirm_settlement_claim(session, claim_id, current_user.id)
    )
    session.commit()
    return result


@router.post("/settlement-claims/{claim_id}/reject", response_model=SettlementClaimPublic)
def reject_settlement_claim_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    claim_id: uuid.UUID,
) -> SettlementClaimPublic:
    """
    Reject a settlement claim.

    Only the expense owner (payer) can reject settlement claims.
    On rejection: returns the claim with status "rejected" and rejected_at
    set; the claim record is then deleted (allows claimant to re-claim).
    Audit log preserves the rejection history.

    Error responses: 403 (not expense owner), 404 (claim not found),
                     409 (claim already processed, or the 72h dispute
                     window closed — the claim auto-confirms instead)
    """
    result = _handle_settlement_result(
        reject_settlement_claim(session, claim_id, current_user.id),
        session=session,
    )
    session.commit()
    return result


# =============================================================================
# WS6: Aggregate settle-up ("Settle with X")
# =============================================================================


@router.post(
    "/settlement-claims/aggregate",
    response_model=SettlementClaimPublic,
    status_code=201,
)
def create_aggregate_settlement_endpoint(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    body: AggregateSettleUpRequest,
) -> SettlementClaimPublic:
    """
    Settle with one group member in a single move (WS6/S2 §4).

    Nets every confirmed, unclaimed expense split between the caller and the
    counterparty in the group into ONE claim ("I paid them the net amount"),
    awaiting the counterparty's single confirmation. Confirming settles all
    covered splits atomically. The per-expense settle path remains available
    for partial payments.

    Error responses: 400 (nothing to settle / wrong direction / bad
    counterparty), 403 (not a member), 404 (group not found), 409 (a racing
    settlement covered these expenses first)
    """
    group = session.get(ExpenseGroup, body.group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    if not is_group_member(
        session, group_id=body.group_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to settle up",
        )

    if body.counterparty_user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="You cannot settle up with yourself"
        )

    if not is_group_member(
        session, group_id=body.group_id, user_id=body.counterparty_user_id
    ):
        raise HTTPException(
            status_code=400,
            detail="That person is not a member of this group",
        )

    # Sweep first so expired claims/expenses resolve before netting — all in
    # this request's single transaction (ARCH-001)
    expense_service.auto_confirm_expired_expenses(
        session, group_id=body.group_id
    )
    expense_service.auto_confirm_expired_settlement_claims(
        session, group_id=body.group_id
    )

    result = expense_service.create_aggregate_settlement(
        session,
        group_id=body.group_id,
        claimant_id=current_user.id,
        counterparty_id=body.counterparty_user_id,
    )

    if result == "NOTHING":
        raise HTTPException(
            status_code=400,
            detail="You're all settled with this member — nothing to net",
        )
    if result == "WRONG_DIRECTION":
        raise HTTPException(
            status_code=400,
            detail=(
                "They owe you overall — settlement flows the other way, "
                "so they should settle up with you"
            ),
        )
    if result == "CONFLICT":
        raise HTTPException(
            status_code=409,
            detail="A settlement is already in flight for these expenses",
        )

    session.commit()
    return result


@router.get(
    "/settlement-claims/aggregate", response_model=SettlementClaimsPublic
)
def list_aggregate_settlement_claims(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    group_id: uuid.UUID | None = None,
) -> SettlementClaimsPublic:
    """
    Pending aggregate settle-up claims involving the current user — as
    claimant (waiting on the counterparty) or as counterparty (awaiting
    the user's review). Pass ?group_id= to scope to one group.
    """
    # Lazy dispute-window sweep (WS6): expired claims confirm before listing
    if expense_service.auto_confirm_expired_settlement_claims(
        session, involving_user_id=current_user.id, group_id=group_id
    ):
        session.commit()

    claims = expense_service.get_aggregate_claims(
        session, current_user.id, group_id=group_id
    )
    return SettlementClaimsPublic(data=claims, count=len(claims))


# =============================================================================
# WS5 (B-H7): Ledger read endpoints
#
# NOTE: these are declared LAST on purpose. Starlette matches routes in
# declaration order, so GET /{expense_id} must come after the static GET
# routes (/pending-confirmations, /pending-settlements,
# /settlement-claims/...) or it would capture them and 422 on the UUID parse.
# =============================================================================


def _get_expense_for_member(
    session: SessionDep, expense_id: uuid.UUID, current_user: CurrentUser
) -> Expense:
    """Load an expense and enforce group membership (404 / 403)."""
    expense = session.get(Expense, expense_id)
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if not is_group_member(
        session, group_id=expense.group_id, user_id=current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to view this expense",
        )
    return expense


@router.get("/{expense_id}", response_model=ExpensePublic)
def get_expense(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
) -> ExpensePublic:
    """
    Get a single expense. User must be a member of the expense's group.
    """
    expense = _get_expense_for_member(session, expense_id, current_user)
    return ExpensePublic.model_validate(expense)


@router.get("/{expense_id}/splits", response_model=ExpenseSplitsPublic)
def get_expense_splits(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
) -> ExpenseSplitsPublic:
    """
    Get who owes what on an expense, with member names.
    User must be a member of the expense's group.
    """
    _get_expense_for_member(session, expense_id, current_user)
    splits = expense_service.get_expense_splits(session, expense_id)
    return ExpenseSplitsPublic(data=splits, count=len(splits))
