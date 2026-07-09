# Expenses feature router - API routes for expense management
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Body
from sqlmodel import delete, select

from app.api.deps import CurrentUser, SessionDep
from app.features.expenses import service as expense_service
from app.features.expenses.models import (
    AuditActionType,
    AuditLogPublic,
    AuditLogsPublic,
    Expense,
    ExpenseCreate,
    ExpensePublic,
    ExpenseSplit,
    ExpenseSplitPublic,
    ExpenseSplitResponse,
    ExpenseStatus,
    ExpenseUpdate,
    ExpenseConfirmRequest,
    ExpenseRejectRequest,
    ExpenseRejectResponse,
    PendingConfirmationPublic,
    SettlementClaimPublic,
    PendingSettlementPublic,
)
from app.features.expenses.service import (
    confirm_settlement_claim,
    reject_settlement_claim,
    get_claims_awaiting_owner_confirmation,
)
from app.features.groups.models import ExpenseGroup, GroupMember
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
    split_data: dict = Body(...),
    current_user: CurrentUser,
) -> ExpenseSplitResponse:
    """
    Update expense split configuration.

    Supports equal split (Story 3.5), unequal split (Story 3.6), and percentage split (Story 3.7).
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

    # Get split type
    split_type = split_data.get("type")

    # Handle equal split
    if split_type == "equal":
        # Get group members
        statement = select(GroupMember).where(GroupMember.group_id == expense.group_id)
        members = session.exec(statement).all()
        member_ids = [m.user_id for m in members]

        # Calculate split
        try:
            splits_data = expense_service.calculate_equal_split(
                total_amount=expense.amount,
                member_ids=member_ids,
                excluded_user_ids=split_data.get("excluded_user_ids", []),
                payer_id=expense.payer_id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Handle unequal split
    elif split_type == "unequal":
        # Get excluded user IDs
        excluded_user_ids = split_data.get("excluded_user_ids", [])

        # Validate excluded members are group members
        if excluded_user_ids:
            statement = select(GroupMember).where(GroupMember.group_id == expense.group_id)
            group_members = session.exec(statement).all()
            group_member_user_ids = {m.user_id for m in group_members}

            for excluded_id in excluded_user_ids:
                excluded_uuid = uuid.UUID(str(excluded_id))
                if excluded_uuid not in group_member_user_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Excluded user {excluded_id} is not a member of this group",
                    )

        # Validate splits provided
        splits_data_raw = split_data.get("splits", [])
        if not splits_data_raw:
            raise HTTPException(
                status_code=400,
                detail="Unequal split requires 'splits' array with user_id and amount",
            )

        # Validate each split item has required fields and valid amounts
        for idx, split_item in enumerate(splits_data_raw):
            if "user_id" not in split_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Split item at index {idx} missing 'user_id'",
                )
            if "amount" not in split_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Split item at index {idx} missing 'amount'",
                )
            # Validate amount is positive
            try:
                amount = Decimal(str(split_item["amount"]))
                if amount <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Split amount must be greater than 0 (got {amount} at index {idx})",
                    )
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid amount at index {idx}: {str(e)}",
                )

        # Get group members for validation and calculation
        statement = select(GroupMember).where(GroupMember.group_id == expense.group_id)
        group_members = session.exec(statement).all()
        member_ids = [m.user_id for m in group_members]

        # Validate all users in splits are group members
        group_member_user_ids = {m.user_id for m in group_members}

        for idx, split_item in enumerate(splits_data_raw):
            user_id = uuid.UUID(str(split_item["user_id"]))
            if user_id not in group_member_user_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"User at index {idx} is not a member of this group",
                )

        # Calculate and validate unequal split
        try:
            splits_data = expense_service.calculate_unequal_split(
                total_amount=expense.amount,
                splits=splits_data_raw,
                member_ids=member_ids,
                excluded_user_ids=excluded_user_ids,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Handle percentage split (Story 3.7)
    elif split_type == "percentage":
        # Get excluded user IDs
        excluded_user_ids = split_data.get("excluded_user_ids", [])

        # Validate excluded members are group members
        if excluded_user_ids:
            statement = select(GroupMember).where(GroupMember.group_id == expense.group_id)
            group_members = session.exec(statement).all()
            group_member_user_ids = {m.user_id for m in group_members}

            for excluded_id in excluded_user_ids:
                excluded_uuid = uuid.UUID(str(excluded_id))
                if excluded_uuid not in group_member_user_ids:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Excluded user {excluded_id} is not a member of this group",
                    )

        # Validate splits provided
        splits_data_raw = split_data.get("splits", [])
        if not splits_data_raw:
            raise HTTPException(
                status_code=400,
                detail="Percentage split requires 'splits' array with user_id and percentage",
            )

        # Validate each split item has required fields and valid percentages
        for idx, split_item in enumerate(splits_data_raw):
            if "user_id" not in split_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Split item at index {idx} missing 'user_id'",
                )
            if "percentage" not in split_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Split item at index {idx} missing 'percentage'",
                )
            # Validate percentage is in valid range [0, 100]
            try:
                percentage = Decimal(str(split_item["percentage"]))
                if percentage < 0 or percentage > 100:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Percentage must be between 0 and 100 (got {percentage} at index {idx})",
                    )
            except (ValueError, TypeError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid percentage at index {idx}: {str(e)}",
                )

        # Get group members for validation and calculation
        statement = select(GroupMember).where(GroupMember.group_id == expense.group_id)
        group_members = session.exec(statement).all()
        member_ids = [m.user_id for m in group_members]

        # Validate all users in splits are group members
        group_member_user_ids = {m.user_id for m in group_members}

        for idx, split_item in enumerate(splits_data_raw):
            user_id = uuid.UUID(str(split_item["user_id"]))
            if user_id not in group_member_user_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"User at index {idx} is not a member of this group",
                )

        # Calculate and validate percentage split
        try:
            splits_data = expense_service.calculate_percentage_split(
                total_amount=expense.amount,
                splits=splits_data_raw,
                member_ids=member_ids,
                excluded_user_ids=excluded_user_ids,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Unimplemented split types
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Split type '{split_type}' not yet implemented. Use 'equal', 'unequal', or 'percentage'.",
        )

    # Delete existing splits for this expense
    session.exec(
        delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
    )

    # Create new splits
    for split in splits_data:
        expense_split = ExpenseSplit(
            expense_id=expense_id,
            user_id=split["user_id"],
            amount_owed=split["amount_owed"],
        )
        session.add(expense_split)

    # Transition expense to PENDING_CONFIRMATION when splits are assigned
    if expense.status == ExpenseStatus.DRAFT:
        expense.status = ExpenseStatus.PENDING_CONFIRMATION
        session.add(expense)

    # Audit entry joins the same transaction: splits, status transition, and
    # audit land atomically (WS4/H5)
    expense_service.record_audit(
        session,
        expense_id=expense_id,
        user_id=current_user.id,
        action_type=AuditActionType.SPLIT_UPDATED,
        after_data={"type": split_type, "members": len(splits_data)},
    )
    session.commit()

    # Get excluded_user_ids from request for all split types
    excluded_user_ids = split_data.get("excluded_user_ids", [])

    return ExpenseSplitResponse(
        expense_id=expense_id,
        split_type=split_type,
        splits=[{
            "user_id": s["user_id"],
            "amount_owed": s["amount_owed"],
        } for s in splits_data],
        excluded_user_ids=excluded_user_ids,
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
) -> list[PendingSettlementPublic]:
    """
    Get all pending settlement claims for expenses owned by the current user.

    Returns claims where the current user is the expense owner (payer)
    and the claim status is still 'pending'.
    """
    pending_data = get_claims_awaiting_owner_confirmation(
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


# =============================================================================
# Story 4.4: Audit Log Retrieval
# =============================================================================


@router.get("/{expense_id}/audit-log", response_model=AuditLogsPublic)
def get_expense_audit_log(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    expense_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
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


def _handle_settlement_result(result):
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
                     409 (claim already processed)
    """
    result = _handle_settlement_result(
        reject_settlement_claim(session, claim_id, current_user.id)
    )
    session.commit()
    return result
