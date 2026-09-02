# Expenses feature service - CRUD operations for expenses
#
# TRANSACTION DISCIPLINE (WS4/H5): service functions NEVER commit. They flush,
# so the operation and its audit entry live or die in ONE transaction, and the
# router (the request boundary) commits exactly once. See solution-patterns.yaml
# ARCH-001.
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, select

from app.features.expenses.models import (
    EXPENSE_AUTO_CONFIRM_DAYS,
    SETTLEMENT_AUTO_CONFIRM_HOURS,
    AuditActionType,
    AuditLog,
    AuditLogPublic,
    EqualSplitRequest,
    Expense,
    ExpenseCreate,
    ExpenseSplit,
    ExpenseSplitPublic,
    ExpenseStatus,
    ExpenseUpdate,
    PairwiseBalanceItem,
    PercentageSplitRequest,
    SettlementClaim,
    SettlementClaimPublic,
    SettlementClaimSplit,
    SettlementClaimStatus,
    SplitStatus,
    UnequalSplitRequest,
)
from app.features.auth.models import User
from app.features.groups.models import GroupMember, GroupSettings


# =============================================================================
# Story 4.4: Audit Logging - Service Layer
# =============================================================================


def record_audit(
    session: Session,
    *,
    expense_id: uuid.UUID,
    user_id: uuid.UUID,
    action_type: AuditActionType,
    before_data: dict | None = None,
    after_data: dict | None = None,
) -> None:
    """
    Create an immutable audit log entry.

    Joins the caller's transaction (no commit here): the audited operation and
    its audit entry are atomic — if either fails, both roll back. An operation
    without its audit row must never be persisted (PRD: complete audit trail).
    """
    changes = None
    if before_data is not None or after_data is not None:
        changes = {"before": before_data, "after": after_data}

    audit_entry = AuditLog(
        expense_id=expense_id,
        user_id=user_id,
        action_type=action_type,
        changes_json=changes,
    )
    session.add(audit_entry)


def filter_included_members(
    member_ids: List[uuid.UUID],
    excluded_user_ids: List[uuid.UUID] | None = None
) -> List[uuid.UUID]:
    """
    Filter out excluded members from the member list.

    Args:
        member_ids: All group member IDs
        excluded_user_ids: Members to exclude

    Returns:
        List of included member IDs

    Raises:
        ValueError: If fewer than 2 members remain after exclusion
    """
    excluded_set = set(excluded_user_ids) if excluded_user_ids else set()
    included_members = [m for m in member_ids if m not in excluded_set]

    if len(included_members) < 2:
        raise ValueError(
            "At least 2 members must be included in the split. "
            f"Currently have {len(included_members)} member(s)."
        )

    return included_members


def create_expense(
    session: Session, expense_in: ExpenseCreate, current_user_id: uuid.UUID
) -> Expense:
    """
    Create a new expense in a group.

    Args:
        session: Database session
        expense_in: Expense creation data
        current_user_id: ID of the user creating the expense

    Returns:
        Created Expense object

    Note:
        - payer_id defaults to current_user_id if not provided
        - status is always DRAFT for new expenses
        - Caller must verify user is member of group first
        - Flushes only; the router commits the request transaction
    """
    expense = Expense(
        group_id=expense_in.group_id,
        amount=expense_in.amount,
        description=expense_in.description,
        payer_id=expense_in.payer_id or current_user_id,
        created_by=current_user_id,
        status=ExpenseStatus.DRAFT,
    )
    session.add(expense)
    session.flush()
    session.refresh(expense)

    # Audit entry is atomic with the creation (same transaction)
    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id,
        action_type=AuditActionType.CREATED,
        after_data={"amount": str(expense.amount), "description": expense.description},
    )
    session.flush()

    return expense


# Fields whose change alters what members consented to owe: the amount, and
# who the money is owed to. Changing either re-opens consent (WS4/H2).
_CONSENT_FIELDS = ("amount", "payer_id")


def update_expense(
    session: Session, expense: Expense, update_data: ExpenseUpdate, current_user_id: uuid.UUID | None = None
) -> Expense:
    """
    Update expense fields. Only updates provided (non-None) fields.

    Consent contract (WS4/H2): if amount or payer changes while splits exist,
    the splits are deleted and the expense reverts to DRAFT — members must
    re-confirm what they actually owe. Splits can never drift out of sync with
    the expense amount, and nobody stays "confirmed" on numbers they never saw.

    Args:
        session: Database session
        expense: Existing Expense object to update
        update_data: ExpenseUpdate with optional fields

    Returns:
        Updated Expense object (possibly reverted to DRAFT)
    """
    update_dict = update_data.model_dump(exclude_unset=True)

    original_status = expense.status

    # Capture BEFORE state for changed fields only
    before_data = {}
    for field in update_dict:
        before_data[field] = str(getattr(expense, field))

    consent_changed = any(
        field in _CONSENT_FIELDS and getattr(expense, field) != value
        for field, value in update_dict.items()
    )

    for field, value in update_dict.items():
        setattr(expense, field, value)
    session.add(expense)

    reverted = False
    if consent_changed:
        deleted = session.exec(
            delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id)
        )
        if deleted.rowcount > 0:
            expense.status = ExpenseStatus.DRAFT
            reverted = True

    session.flush()
    session.refresh(expense)

    # Capture AFTER state for changed fields only
    after_data = {}
    for field in update_dict:
        after_data[field] = str(getattr(expense, field))
    if reverted:
        before_data["status"] = original_status.value
        after_data["status"] = ExpenseStatus.DRAFT.value
        after_data["splits"] = "removed — consent re-opened"

    # Audit entry is atomic with the edit (same transaction)
    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id or expense.created_by,
        action_type=AuditActionType.EDITED,
        before_data=before_data,
        after_data=after_data,
    )
    session.flush()

    return expense


def calculate_equal_split(
    total_amount: Decimal,
    member_ids: list[uuid.UUID],
    excluded_user_ids: list[uuid.UUID] | None = None,
    payer_id: uuid.UUID | None = None,
) -> list[dict]:
    """
    Calculate equal split amounts among group members.

    Args:
        total_amount: Total expense amount
        member_ids: All group member IDs
        excluded_user_ids: Members to exclude from split (optional)
        payer_id: The expense creator (absorbs rounding difference)

    Returns:
        List of {user_id, amount_owed} for included members

    Raises:
        ValueError: If fewer than 2 members are included in the split

    Examples:
        >>> calculate_equal_split(Decimal("100.00"), [id1, id2, id3, id4])
        [{'user_id': id1, 'amount_owed': Decimal('25.00')}, ...]

        >>> calculate_equal_split(Decimal("100.00"), [id1, id2, id3])
        [{'user_id': id1, 'amount_owed': Decimal('33.34')}, ...]  # payer absorbs 0.01
    """
    # Filter out excluded members and validate minimum
    included_members = filter_included_members(member_ids, excluded_user_ids)

    # Calculate equal amount
    amount_per_person = total_amount / Decimal(len(included_members))

    # Round to 2 decimal places using half-up rounding
    amount_rounded = amount_per_person.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Calculate total after rounding
    rounded_total = amount_rounded * Decimal(len(included_members))

    # Handle penny mismatch: payer absorbs difference
    difference = total_amount - rounded_total
    splits = []

    for user_id in included_members:
        amount = amount_rounded
        # Payer absorbs rounding difference
        if payer_id and user_id == payer_id:
            amount += difference
        splits.append({
            "user_id": user_id,
            "amount_owed": amount
        })

    return splits


def calculate_unequal_split(
    total_amount: Decimal,
    splits: list[dict],
    member_ids: list[uuid.UUID] | None = None,
    excluded_user_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Validate and prepare unequal split amounts.

    Args:
        total_amount: Total expense amount
        splits: List of {user_id, amount} specified by user
        member_ids: All group member IDs (for validation)
        excluded_user_ids: Members to exclude from split (optional)

    Returns:
        List of {user_id, amount_owed} validated

    Raises:
        ValueError: If amounts don't sum to total or fewer than 2 members after exclusion

    Examples:
        >>> calculate_unequal_split(
        ...     Decimal("100.00"),
        ...     [{"user_id": id1, "amount": 50.00}, {"user_id": id2, "amount": 50.00}]
        ... )
        [{'user_id': id1, 'amount_owed': Decimal('50.00')}, ...]
    """
    excluded_set = set(excluded_user_ids) if excluded_user_ids else set()

    # Filter out excluded members from splits
    included_splits = [
        s for s in splits
        if uuid.UUID(str(s["user_id"])) not in excluded_set
    ]

    # Validate minimum members
    if len(included_splits) < 2:
        raise ValueError(
            f"At least 2 members must be included in the split. "
            f"Currently have {len(included_splits)} member(s)."
        )

    # Sum all provided amounts
    provided_total = sum(Decimal(str(s["amount"])) for s in included_splits)

    # Validate sum matches total (within 0.01 tolerance for floating point)
    if abs(provided_total - total_amount) > Decimal("0.01"):
        raise ValueError(
            f"Split amounts ({provided_total}) must equal "
            f"total expense amount ({total_amount})"
        )

    # Return validated splits with safe UUID conversion
    validated_splits = []
    for split_item in included_splits:
        # Safe UUID conversion - handle both string and UUID objects
        user_id_val = split_item["user_id"]
        if isinstance(user_id_val, uuid.UUID):
            user_id = user_id_val
        else:
            user_id = uuid.UUID(str(user_id_val))

        validated_splits.append({
            "user_id": user_id,
            "amount_owed": Decimal(str(split_item["amount"]))
        })

    return validated_splits


def calculate_percentage_split(
    total_amount: Decimal,
    splits: list[dict],
    member_ids: list[uuid.UUID] | None = None,
    excluded_user_ids: list[uuid.UUID] | None = None,
) -> list[dict]:
    """
    Validate percentages and calculate split amounts.

    Args:
        total_amount: Total expense amount
        splits: List of {user_id, percentage} specified by user
        member_ids: All group member IDs (for validation)
        excluded_user_ids: Members to exclude from split (optional)

    Returns:
        List of {user_id, amount_owed} calculated

    Raises:
        ValueError: If percentages don't sum to 100 or fewer than 2 members after exclusion

    Examples:
        >>> calculate_percentage_split(
        ...     Decimal("100.00"),
        ...     [{"user_id": id1, "percentage": 60.0}, {"user_id": id2, "percentage": 40.0}]
        ... )
        [{'user_id': id1, 'amount_owed': Decimal('60.00')}, ...]
    """
    excluded_set = set(excluded_user_ids) if excluded_user_ids else set()

    # Filter out excluded members from splits
    included_splits = [
        s for s in splits
        if uuid.UUID(str(s["user_id"])) not in excluded_set
    ]

    # Validate minimum members
    if len(included_splits) < 2:
        raise ValueError(
            f"At least 2 members must be included in the split. "
            f"Currently have {len(included_splits)} member(s)."
        )

    # Sum all provided percentages
    total_percentage = sum(Decimal(str(s["percentage"])) for s in included_splits)

    # Validate sum equals 100 (within 0.01 tolerance)
    if abs(total_percentage - Decimal("100")) > Decimal("0.01"):
        raise ValueError(
            f"Split percentages ({total_percentage}%) must equal 100%"
        )

    # Calculate amounts and handle rounding
    calculated_splits = []
    remaining_amount = total_amount

    for i, split_item in enumerate(included_splits):
        # Safe UUID conversion - handle both string and UUID objects
        user_id_val = split_item["user_id"]
        if isinstance(user_id_val, uuid.UUID):
            user_id = user_id_val
        else:
            user_id = uuid.UUID(str(user_id_val))

        percentage = Decimal(str(split_item["percentage"]))

        # Calculate amount for this member
        if i == len(included_splits) - 1:
            # Last member gets remainder (to avoid rounding errors)
            amount_owed = remaining_amount
        else:
            amount_owed = (total_amount * percentage / Decimal("100")).quantize(Decimal("0.01"))
            remaining_amount -= amount_owed

        calculated_splits.append({
            "user_id": user_id,
            "amount_owed": amount_owed
        })

    return calculated_splits


def apply_split(
    session: Session,
    expense: Expense,
    req: EqualSplitRequest | UnequalSplitRequest | PercentageSplitRequest,
    current_user_id: uuid.UUID,
) -> list[dict]:
    """
    Validate, calculate, and persist a split configuration (WS5/B-H6).

    One home for the member validation that used to be copy-pasted three
    times in the router. Existing splits are replaced; a DRAFT expense
    transitions to PENDING_CONFIRMATION; the audit entry joins the same
    transaction (ARCH-001 — caller commits).

    Raises:
        ValueError: any domain validation failure (router translates to 400)

    Returns:
        List of {user_id, amount_owed} for the created splits
    """
    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == expense.group_id)
    ).all()
    member_ids = [m.user_id for m in members]
    member_id_set = set(member_ids)

    for excluded_id in req.excluded_user_ids:
        if excluded_id not in member_id_set:
            raise ValueError(
                f"Excluded user {excluded_id} is not a member of this group"
            )

    if isinstance(req, EqualSplitRequest):
        splits_data = calculate_equal_split(
            total_amount=expense.amount,
            member_ids=member_ids,
            excluded_user_ids=req.excluded_user_ids,
            payer_id=expense.payer_id,
        )
    else:
        for item in req.splits:
            if item.user_id not in member_id_set:
                raise ValueError(
                    f"User {item.user_id} is not a member of this group"
                )
        raw_splits = [item.model_dump() for item in req.splits]
        if isinstance(req, UnequalSplitRequest):
            splits_data = calculate_unequal_split(
                total_amount=expense.amount,
                splits=raw_splits,
                member_ids=member_ids,
                excluded_user_ids=req.excluded_user_ids,
            )
        else:
            splits_data = calculate_percentage_split(
                total_amount=expense.amount,
                splits=raw_splits,
                member_ids=member_ids,
                excluded_user_ids=req.excluded_user_ids,
            )

    # A member must not appear twice: an unequal/percentage body could repeat
    # a user_id, and two rows for one (expense, user) would trip
    # uq_expense_user_split as a raw 500 at flush. Reject it as a clean domain
    # error (router → 400) before we insert anything (audit finding F10).
    seen_user_ids: set[uuid.UUID] = set()
    for split in splits_data:
        if split["user_id"] in seen_user_ids:
            raise ValueError("Each member can appear only once in a split")
        seen_user_ids.add(split["user_id"])

    # Replace any existing splits with the new configuration
    session.exec(delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense.id))
    for split in splits_data:
        session.add(
            ExpenseSplit(
                expense_id=expense.id,
                user_id=split["user_id"],
                amount_owed=split["amount_owed"],
            )
        )

    # Assigning splits moves a DRAFT expense into the confirmation flow
    if expense.status == ExpenseStatus.DRAFT:
        expense.status = ExpenseStatus.PENDING_CONFIRMATION
        session.add(expense)

    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id,
        action_type=AuditActionType.SPLIT_UPDATED,
        after_data={"type": req.type, "members": len(splits_data)},
    )
    session.flush()

    # Tell each non-payer participant they have a share to confirm (audit
    # finding F8 — before this, participants only found out by opening
    # /pending). Imported inside the function: notifications.service imports
    # this module's models, so a module-level import would close the cycle.
    # SAVEPOINT-guarded and never raises — a push failure can't fail a split.
    from app.features.groups.service import get_group_currency
    from app.features.notifications.service import notify_split_assigned

    notify_split_assigned(
        session,
        expense_id=expense.id,
        group_id=expense.group_id,
        payer_id=expense.payer_id,
        currency=get_group_currency(session, expense.group_id),
    )

    return splits_data


# =============================================================================
# Story 4.2: Expense Confirmation Workflow - Service Layer
# =============================================================================


# =============================================================================
# Story 4.3: Expense Finalization - Service Layer
# =============================================================================


def check_all_splits_confirmed(session: Session, expense_id: uuid.UUID) -> bool:
    """
    Check if all splits for an expense are confirmed.

    Args:
        session: Database session
        expense_id: Expense ID

    Returns:
        True if all splits have status CONFIRMED, False otherwise
    """
    splits = session.exec(
        select(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
    ).all()

    if not splits:
        return False

    return all(split.status == SplitStatus.CONFIRMED for split in splits)


def finalize_expense(
    session: Session, expense_id: uuid.UUID, *, auto: bool = False
) -> Expense | None:
    """
    Finalize an expense when all splits are confirmed.

    Sets expense status to CONFIRMED and records confirmed_at timestamp.
    Publishes Redis event and creates notification records.

    Args:
        session: Database session
        expense_id: Expense ID
        auto: True when the confirmation came from the non-strict-mode
            timeout sweep (WS6) rather than every member confirming

    Returns:
        Finalized Expense with status CONFIRMED, or None if not all splits confirmed
    """
    expense = session.get(Expense, expense_id)
    if not expense:
        return None

    # Check all splits are confirmed
    if not check_all_splits_confirmed(session, expense_id):
        return None

    # Finalize the expense
    expense.status = ExpenseStatus.CONFIRMED
    expense.confirmed_at = datetime.now(timezone.utc)

    session.add(expense)
    session.flush()
    session.refresh(expense)

    after_data: dict = {"status": "confirmed"}
    if auto:
        after_data["auto_confirmed"] = (
            f"no objection within {EXPENSE_AUTO_CONFIRM_DAYS} days"
        )

    # Audit entry is atomic with the finalization (same transaction)
    record_audit(
        session,
        expense_id=expense_id,
        user_id=expense.created_by,
        action_type=AuditActionType.CONFIRMED,
        after_data=after_data,
    )
    session.flush()

    return expense


def confirm_expense_split(
    session: Session, expense_id: uuid.UUID, user_id: uuid.UUID
) -> ExpenseSplit | None:
    """
    Confirm a user's expense split.

    Locks the expense row (WS4/M8) so concurrent confirms serialize: exactly
    one of two racing last-member confirms triggers finalization, and a
    concurrent reject (which reverts to DRAFT and deletes splits) cannot
    interleave — if it wins, the split lookup below comes up empty.

    Args:
        session: Database session
        expense_id: Expense ID
        user_id: User ID

    Returns:
        Updated ExpenseSplit with status confirmed
    """
    expense = session.exec(
        select(Expense).where(Expense.id == expense_id).with_for_update()
    ).first()
    if not expense:
        return None

    # Find and update the split
    split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense_id)
        .where(ExpenseSplit.user_id == user_id)
    ).first()

    if not split:
        return None

    # Update split status
    split.status = SplitStatus.CONFIRMED
    split.confirmed_at = datetime.now(timezone.utc)

    session.add(split)
    session.flush()
    session.refresh(split)

    # Audit entry is atomic with the confirmation (same transaction)
    record_audit(
        session,
        expense_id=expense_id,
        user_id=user_id,
        action_type=AuditActionType.CONFIRMED,
    )
    session.flush()

    # After confirming, check if any splits remain pending — if not, finalize
    pending_count = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense_id)
        .where(ExpenseSplit.status != SplitStatus.CONFIRMED)
    ).first()

    if pending_count is None:
        finalize_expense(session, expense_id)

    return split


def reject_expense_split(
    session: Session, expense_id: uuid.UUID, user_id: uuid.UUID
) -> dict | None:
    """
    Reject a user's expense split: the expense reverts to DRAFT.

    Product decision (WS4/H3): rejection does NOT redistribute the rejected
    amount over the remaining members — that silently rewrote amounts other
    members had already confirmed, destroyed unequal/percentage splits, and
    could strand the expense in PENDING_CONFIRMATION forever. Instead, ALL
    splits are deleted and the expense returns to DRAFT so the creator
    re-splits and every member re-confirms. The audit trail records who
    rejected. (Creator notification delivery arrives with the WS12 nudge
    infrastructure; until then the status change and audit entry are the
    signal.)

    Args:
        session: Database session
        expense_id: Expense ID
        user_id: User ID

    Returns:
        Dictionary with message and remaining split count (always 0 —
        kept for response-shape compatibility)
    """
    # Lock the expense row: serializes against concurrent confirms/rejects
    expense = session.exec(
        select(Expense).where(Expense.id == expense_id).with_for_update()
    ).first()
    if not expense:
        return None

    # The rejecting user must actually hold a split in this expense
    split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense_id)
        .where(ExpenseSplit.user_id == user_id)
    ).first()

    if not split:
        return None

    # Re-open consent: drop every split and return the expense to DRAFT
    session.exec(
        delete(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
    )
    original_status = expense.status
    expense.status = ExpenseStatus.DRAFT
    session.add(expense)

    # Audit entry is atomic with the revert (same transaction)
    record_audit(
        session,
        expense_id=expense_id,
        user_id=user_id,
        action_type=AuditActionType.REJECTED,
        before_data={"status": original_status.value},
        after_data={"status": ExpenseStatus.DRAFT.value,
                    "splits": "removed — consent re-opened"},
    )
    session.flush()

    return {
        "message": "Expense rejected — it's back with the creator to re-split",
        "remaining_splits": 0,
    }


def get_pending_confirmations_for_user(
    session: Session, user_id: uuid.UUID
) -> list[dict]:
    """
    Get all expenses pending confirmation for a user.

    Single JOIN query (WS5/B-M6) — the previous per-split session.get was an
    N+1; the settlement worklists already used this pattern.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        List of dictionaries with expense and split details
    """
    rows = session.exec(
        select(ExpenseSplit, Expense)
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(ExpenseSplit.user_id == user_id)
        .where(ExpenseSplit.status == SplitStatus.PENDING)
        .where(Expense.status == ExpenseStatus.PENDING_CONFIRMATION)
    ).all()

    return [{"expense": expense, "split": split} for split, expense in rows]


# =============================================================================
# WS5 (B-H7): Ledger read endpoints - Service Layer
# =============================================================================


def get_group_expenses(
    session: Session,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[tuple[Expense, ExpenseSplit | None]], int]:
    """
    Get a group's expense ledger, newest first, with the requesting user's
    own split attached to each expense (LEFT JOIN — None when the user is
    not part of that split).

    Returns:
        Tuple of (list of (expense, my_split | None), total_count)
    """
    count = session.exec(
        select(sa.func.count())
        .select_from(Expense)
        .where(Expense.group_id == group_id)
    ).one()

    rows = session.exec(
        select(Expense, ExpenseSplit)
        .join(
            ExpenseSplit,
            sa.and_(
                ExpenseSplit.expense_id == Expense.id,
                ExpenseSplit.user_id == user_id,
            ),
            isouter=True,
        )
        .where(Expense.group_id == group_id)
        .order_by(Expense.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return list(rows), count


def get_expense_splits(
    session: Session, expense_id: uuid.UUID
) -> list[ExpenseSplitPublic]:
    """
    Get all splits for an expense with user names populated (who owes what).
    """
    rows = session.exec(
        select(ExpenseSplit, User)
        .join(User, ExpenseSplit.user_id == User.id)
        .where(ExpenseSplit.expense_id == expense_id)
        .order_by(ExpenseSplit.created_at.asc())
    ).all()

    return [
        ExpenseSplitPublic(
            id=split.id,
            expense_id=split.expense_id,
            user_id=split.user_id,
            amount_owed=split.amount_owed,
            status=split.status,
            confirmed_at=split.confirmed_at,
            created_at=split.created_at,
            user_name=user.full_name or user.email,
        )
        for split, user in rows
    ]


def get_group_net_balance(
    session: Session, group_id: uuid.UUID, user_id: uuid.UUID
) -> Decimal:
    """
    The user's net balance in one group — same semantics as the dashboard
    (confirmed splits on confirmed expenses; positive = owed to the user).
    Decimal end-to-end (WS4/M1).
    """
    from sqlalchemy import case, literal

    row = session.exec(
        select(
            sa.func.sum(
                case(
                    (ExpenseSplit.user_id == user_id, -ExpenseSplit.amount_owed),
                    else_=literal(0),
                )
            ).label("user_owes"),
            sa.func.sum(
                case(
                    (Expense.payer_id == user_id, ExpenseSplit.amount_owed),
                    else_=literal(0),
                )
            ).label("owed_to_user"),
        )
        .select_from(Expense)
        .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
        .where(
            Expense.status == ExpenseStatus.CONFIRMED,
            ExpenseSplit.status == SplitStatus.CONFIRMED,
            Expense.group_id == group_id,
        )
    ).one()

    zero = Decimal("0.00")
    return ((row.owed_to_user or zero) + (row.user_owes or zero)).quantize(
        Decimal("0.01")
    )


# =============================================================================
# Story 4.4: Audit Log Retrieval
# =============================================================================


def _build_audit_log_public(logs: list[AuditLog], session: Session) -> list[AuditLogPublic]:
    """
    Build AuditLogPublic schemas with user names populated.

    Batch-loads user names to avoid N+1 queries.
    """
    if not logs:
        return []

    user_ids = {log.user_id for log in logs}
    users = session.exec(
        select(User).where(User.id.in_(user_ids))
    ).all()
    user_map = {u.id: u.full_name or u.email for u in users}

    return [
        AuditLogPublic(
            id=log.id,
            expense_id=log.expense_id,
            user_id=log.user_id,
            action_type=log.action_type,
            changes_json=log.changes_json,
            created_at=log.created_at,
            user_name=user_map.get(log.user_id),
        )
        for log in logs
    ]


def get_expense_audit_logs(
    session: Session, expense_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> tuple[list[AuditLogPublic], int]:
    """
    Get audit logs for a specific expense.

    Args:
        session: Database session
        expense_id: Expense ID
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        Tuple of (audit_log_public_entries, total_count)
    """
    # Count total
    count_statement = (
        select(sa.func.count())
        .select_from(AuditLog)
        .where(AuditLog.expense_id == expense_id)
    )
    count = session.exec(count_statement).one()

    if count == 0:
        return [], 0

    # Get paginated results
    statement = (
        select(AuditLog)
        .where(AuditLog.expense_id == expense_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = session.exec(statement).all()
    enriched = _build_audit_log_public(logs, session)

    return enriched, count


def get_group_audit_logs(
    session: Session, group_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> tuple[list[AuditLogPublic], int]:
    """
    Get audit logs for all expenses in a group.

    Args:
        session: Database session
        group_id: Group ID
        limit: Maximum number of entries to return
        offset: Number of entries to skip

    Returns:
        Tuple of (audit_log_public_entries, total_count)
    """
    # Use JOIN instead of subquery for better performance
    count_statement = (
        select(sa.func.count())
        .select_from(AuditLog)
        .join(Expense, AuditLog.expense_id == Expense.id)
        .where(Expense.group_id == group_id)
    )
    count = session.exec(count_statement).one()

    if count == 0:
        return [], 0

    # Get paginated results
    statement = (
        select(AuditLog)
        .join(Expense, AuditLog.expense_id == Expense.id)
        .where(Expense.group_id == group_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = session.exec(statement).all()
    enriched = _build_audit_log_public(logs, session)

    return enriched, count


# =============================================================================
# Story 5.1: Settlement Claim - Service Layer
# =============================================================================


def _claim_auto_confirm_at(claim: SettlementClaim) -> datetime | None:
    """When this pending claim auto-confirms; None once processed (WS6)."""
    if claim.status != SettlementClaimStatus.PENDING:
        return None
    claimed = claim.claimed_at
    if claimed.tzinfo is None:
        claimed = claimed.replace(tzinfo=timezone.utc)
    return claimed + timedelta(hours=SETTLEMENT_AUTO_CONFIRM_HOURS)


def _is_claim_expired(claim: SettlementClaim) -> bool:
    """True when the owner's 72h dispute window has closed (WS6)."""
    deadline = _claim_auto_confirm_at(claim)
    return deadline is not None and datetime.now(timezone.utc) >= deadline


def _build_claim_public(
    claim: SettlementClaim, session: Session
) -> SettlementClaimPublic:
    """
    Build a SettlementClaimPublic schema with user_name populated.

    Shared helper to avoid duplicating field mapping across service functions.
    For aggregate claims (WS6), also resolves the counterparty name and the
    covered split/expense counts.
    """
    user = session.get(User, claim.claimant_user_id)
    user_name = user.full_name or user.email if user else None

    counterparty_name = None
    covered_split_count = 1
    covered_expense_count = 1
    if claim.expense_split_id is None:
        counterparty = session.get(User, claim.counterparty_user_id)
        counterparty_name = (
            counterparty.full_name or counterparty.email if counterparty else None
        )
        counts = session.exec(
            select(
                sa.func.count(),
                sa.func.count(sa.distinct(ExpenseSplit.expense_id)),
            )
            .select_from(SettlementClaimSplit)
            .join(
                ExpenseSplit,
                SettlementClaimSplit.expense_split_id == ExpenseSplit.id,
            )
            .where(SettlementClaimSplit.claim_id == claim.id)
        ).one()
        covered_split_count, covered_expense_count = counts

    return SettlementClaimPublic(
        id=claim.id,
        expense_split_id=claim.expense_split_id,
        claimant_user_id=claim.claimant_user_id,
        amount=claim.amount,
        status=claim.status,
        claimed_at=claim.claimed_at,
        confirmed_at=claim.confirmed_at,
        rejected_at=claim.rejected_at,
        created_at=claim.created_at,
        user_name=user_name,
        group_id=claim.group_id,
        counterparty_user_id=claim.counterparty_user_id,
        counterparty_name=counterparty_name,
        covered_split_count=covered_split_count,
        covered_expense_count=covered_expense_count,
        auto_confirm_at=_claim_auto_confirm_at(claim),
    )


def settle_expense_split(
    session: Session, expense_id: uuid.UUID, current_user_id: uuid.UUID
) -> SettlementClaimPublic:
    """
    Create a settlement claim for the current user's split in an expense.

    Creates: SettlementClaim record + AuditLog entry.
    Caller (router) is responsible for validation (404, 400, 403, 409).

    Concurrency (WS4/M8): the split row is locked FOR UPDATE, so a
    double-submit serializes and the loser sees the existing claim. If an
    insert still races past (e.g. a lock-free code path elsewhere), the
    unique index on expense_split_id raises IntegrityError at flush, which is
    translated to the same CONFLICT signal instead of leaking a 500.

    Args:
        session: Database session
        expense_id: Expense ID
        current_user_id: User ID of the claimant

    Returns:
        SettlementClaimPublic with populated user_name
    """
    # Find and lock user's split in this expense
    split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense_id)
        .where(ExpenseSplit.user_id == current_user_id)
        .with_for_update()
    ).first()

    if not split:
        return None  # Signal to router that user is not involved

    # Check for existing claim on this split
    existing_claim = session.exec(
        select(SettlementClaim).where(
            SettlementClaim.expense_split_id == split.id
        )
    ).first()

    if existing_claim:
        return "CONFLICT"  # Signal to router for 409

    # WS6: a pending aggregate settle-up may already cover this split
    covered = session.exec(
        select(SettlementClaimSplit.id)
        .join(
            SettlementClaim,
            SettlementClaimSplit.claim_id == SettlementClaim.id,
        )
        .where(
            SettlementClaimSplit.expense_split_id == split.id,
            SettlementClaim.status == SettlementClaimStatus.PENDING,
        )
    ).first()
    if covered:
        return "CONFLICT"  # Signal to router for 409

    # Create SettlementClaim with status PENDING
    claim = SettlementClaim(
        expense_split_id=split.id,
        claimant_user_id=current_user_id,
        amount=split.amount_owed,
        status=SettlementClaimStatus.PENDING,
        claimed_at=datetime.now(timezone.utc),
    )
    session.add(claim)
    try:
        session.flush()
    except IntegrityError:
        # Unique index on expense_split_id: someone else's claim won the race
        session.rollback()
        return "CONFLICT"
    session.refresh(claim)

    # Audit entry is atomic with the claim (same transaction)
    record_audit(
        session,
        expense_id=expense_id,
        user_id=current_user_id,
        action_type=AuditActionType.SETTLED,
        after_data={
            "amount": str(split.amount_owed),
            "status": "pending",
        },
    )
    session.flush()

    return _build_claim_public(claim, session)


def check_all_splits_settled(session: Session, expense_id: uuid.UUID) -> bool:
    """
    Check if all splits for an expense are settled.

    Args:
        session: Database session
        expense_id: Expense ID

    Returns:
        True if all splits have status SETTLED, False otherwise
    """
    splits = session.exec(
        select(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
    ).all()

    if not splits:
        return False

    return all(split.status == SplitStatus.SETTLED for split in splits)


def _settle_expense_after_covered_splits(
    session: Session, expense: Expense
) -> None:
    """Settle the payer's own split and flip the expense to SETTLED once
    every split is. Shared tail of both confirmation shapes.

    (The payer has no debt to settle — they're the one receiving payment, so
    their own split resolves alongside the confirmed one.)
    """
    payer_split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense.id)
        .where(ExpenseSplit.user_id == expense.payer_id)
    ).first()
    if payer_split and payer_split.status != SplitStatus.SETTLED:
        payer_split.status = SplitStatus.SETTLED
        session.add(payer_split)

    # The split status changes must be flushed so the check sees them
    session.flush()
    if check_all_splits_settled(session, expense.id):
        expense.status = ExpenseStatus.SETTLED
        session.add(expense)


def _confirm_per_expense_claim(
    session: Session,
    claim: SettlementClaim,
    split: ExpenseSplit,
    expense: Expense,
    actor_user_id: uuid.UUID,
    *,
    auto: bool = False,
) -> None:
    """Core of a per-expense confirmation. Caller holds the claim → split →
    expense locks and has validated auth + PENDING status."""
    claim.status = SettlementClaimStatus.CONFIRMED
    claim.confirmed_at = datetime.now(timezone.utc)
    split.status = SplitStatus.SETTLED
    session.add(claim)
    session.add(split)

    after_data: dict = {"status": "confirmed"}
    if auto:
        after_data["auto_confirmed"] = (
            f"owner silent for {SETTLEMENT_AUTO_CONFIRM_HOURS}h"
        )
    record_audit(
        session,
        expense_id=expense.id,
        user_id=actor_user_id,
        action_type=AuditActionType.SETTLED,
        before_data={"status": "pending", "amount": str(claim.amount)},
        after_data=after_data,
    )

    _settle_expense_after_covered_splits(session, expense)
    session.flush()

    _announce_if_debt_cleared(
        session,
        group_id=expense.group_id,
        debtor_id=split.user_id,
        creditor_id=expense.payer_id,
        amount=claim.amount,
    )


def _get_aggregate_covered_rows(
    session: Session, claim_id: uuid.UUID, *, lock: bool = False
) -> list[tuple[ExpenseSplit, Expense]]:
    """The (split, expense) rows an aggregate claim covers, split-id ordered
    (deterministic lock order — WS4/M8 discipline)."""
    stmt = (
        select(ExpenseSplit, Expense)
        .join(
            SettlementClaimSplit,
            SettlementClaimSplit.expense_split_id == ExpenseSplit.id,
        )
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(SettlementClaimSplit.claim_id == claim_id)
        .order_by(ExpenseSplit.id)
    )
    if lock:
        stmt = stmt.with_for_update(of=ExpenseSplit)
    return list(session.exec(stmt).all())


def _confirm_aggregate_claim(
    session: Session,
    claim: SettlementClaim,
    actor_user_id: uuid.UUID,
    *,
    auto: bool = False,
) -> None:
    """Core of an aggregate settle-up confirmation (WS6): every covered split
    settles atomically, each covered expense gets its audit entry (one
    fan-out), and expenses flip to SETTLED where complete. Caller holds the
    claim lock and has validated auth + PENDING status."""
    claim.status = SettlementClaimStatus.CONFIRMED
    claim.confirmed_at = datetime.now(timezone.utc)
    session.add(claim)

    covered = _get_aggregate_covered_rows(session, claim.id, lock=True)

    # Lock the distinct expenses in id order (serializes the all-settled
    # check against concurrent per-expense confirmations on shared expenses)
    expense_ids = sorted({expense.id for _, expense in covered})
    if expense_ids:
        session.exec(
            select(Expense)
            .where(Expense.id.in_(expense_ids))
            .order_by(Expense.id)
            .with_for_update()
        ).all()

    by_expense: dict[uuid.UUID, list[ExpenseSplit]] = {}
    expense_map: dict[uuid.UUID, Expense] = {}
    for split, expense in covered:
        by_expense.setdefault(expense.id, []).append(split)
        expense_map[expense.id] = expense

    after_data: dict = {
        "status": "confirmed",
        "settle_up": True,
        "net_amount": str(claim.amount),
    }
    if auto:
        after_data["auto_confirmed"] = (
            f"owner silent for {SETTLEMENT_AUTO_CONFIRM_HOURS}h"
        )

    for expense_id in expense_ids:
        expense = expense_map[expense_id]
        for split in by_expense[expense_id]:
            split.status = SplitStatus.SETTLED
            session.add(split)
        record_audit(
            session,
            expense_id=expense_id,
            user_id=actor_user_id,
            action_type=AuditActionType.SETTLED,
            before_data={"status": "pending"},
            after_data=after_data,
        )
        _settle_expense_after_covered_splits(session, expense)

    session.flush()

    if claim.group_id and claim.counterparty_user_id:
        _announce_if_debt_cleared(
            session,
            group_id=claim.group_id,
            debtor_id=claim.claimant_user_id,
            creditor_id=claim.counterparty_user_id,
            amount=claim.amount,
        )


def _announce_if_debt_cleared(
    session: Session,
    *,
    group_id: uuid.UUID,
    debtor_id: uuid.UUID,
    creditor_id: uuid.UUID,
    amount: Decimal,
) -> None:
    """
    Tell the creditor their dues cleared, if the nudge engine had been doing
    the asking on their behalf (WS13 — 02 §7, wow moment #2).

    Placed on the two `_confirm_*_claim` helpers rather than on
    `confirm_settlement_claim`, so it covers AUTO-confirmation as well as the
    manual kind. That is not an edge case worth skipping — a claim that
    auto-confirms is one whose creditor never even had to respond, which is
    the purest form of the sentence this notification gets to say.

    Cost on the request path is bounded: a cleared debt happens once per
    relationship, delivery is capped at PUSH_TIMEOUT_INLINE_SECONDS per
    endpoint, and `notify_debt_cleared` runs in a SAVEPOINT and never raises
    — a broken push service cannot fail somebody's settlement.

    Imported inside the function: `notifications.service` imports this
    module's models, so a module-level import here would close the cycle.
    """
    from app.features.groups.service import get_group_currency
    from app.features.notifications.service import notify_debt_cleared

    currency = get_group_currency(session, group_id)
    notify_debt_cleared(
        session,
        group_id=group_id,
        debtor_id=debtor_id,
        creditor_id=creditor_id,
        amount=amount,
        currency=currency,
    )


def confirm_settlement_claim(
    session: Session, claim_id: uuid.UUID, current_user_id: uuid.UUID
) -> SettlementClaimPublic | str | None:
    """
    Owner confirms a settlement claim (per-expense or aggregate — WS6).

    Validates: claim exists, user is the claim's owner (expense payer for
    per-expense claims, counterparty for aggregate ones), claim is pending.
    Updates: claim → CONFIRMED, covered split(s) → SETTLED; expenses whose
    splits are all settled → SETTLED.

    Concurrency (WS4/M8): locks claim → split(s) → expense(s), always in
    that order (shared with reject, so no deadlock). The claim lock
    serializes a confirm/reject race on the same claim; the expense lock
    serializes the "all splits settled?" check so exactly one of two
    concurrent confirmations flips the expense to SETTLED.

    Returns:
        SettlementClaimPublic on success,
        None if claim not found,
        "FORBIDDEN" if not the claim's owner,
        "CONFLICT" if claim already processed
    """
    # 1. Load and lock claim
    claim = session.exec(
        select(SettlementClaim)
        .where(SettlementClaim.id == claim_id)
        .with_for_update()
    ).first()
    if not claim:
        return None  # Router: 404

    # 2. Aggregate settle-up claims (WS6)
    if claim.expense_split_id is None:
        if current_user_id != claim.counterparty_user_id:
            return "FORBIDDEN"  # Router: 403
        if claim.status != SettlementClaimStatus.PENDING:
            return "CONFLICT"  # Router: 409
        _confirm_aggregate_claim(session, claim, current_user_id)
        session.refresh(claim)
        return _build_claim_public(claim, session)

    # 3. Per-expense claims: load and lock associated split → expense
    split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.id == claim.expense_split_id)
        .with_for_update()
    ).first()
    if not split:
        return None  # Router: 404

    expense = session.exec(
        select(Expense).where(Expense.id == split.expense_id).with_for_update()
    ).first()
    if not expense:
        return None  # Router: 404

    # 4. Verify current_user is expense owner (payer)
    if current_user_id != expense.payer_id:
        return "FORBIDDEN"  # Router: 403

    # 5. Verify claim is still PENDING
    if claim.status != SettlementClaimStatus.PENDING:
        return "CONFLICT"  # Router: 409

    _confirm_per_expense_claim(session, claim, split, expense, current_user_id)
    session.refresh(claim)

    return _build_claim_public(claim, session)


def reject_settlement_claim(
    session: Session, claim_id: uuid.UUID, current_user_id: uuid.UUID
) -> SettlementClaimPublic | str | None:
    """
    Owner rejects a settlement claim (per-expense or aggregate — WS6).

    Same auth/status guards as confirm.
    Updates (WS4/H4): claim.status → REJECTED and rejected_at → now, so the
    response tells the truth instead of echoing a stale "pending" object.
    Deletes: the claim record (allows claimant to re-claim — the audit log
    preserves the rejection history).

    Dispute window (WS6): once the claim's 72h auto-confirm deadline has
    passed it is no longer rejectable — the claim is confirmed on the spot
    (the lazy sweep just hadn't run yet) and "EXPIRED" is returned.

    Args:
        session: Database session
        claim_id: Settlement claim ID
        current_user_id: User ID of the claim's owner (expense payer for
            per-expense claims, counterparty for aggregate ones)

    Returns:
        SettlementClaimPublic with status "rejected" and rejected_at set,
        None if claim not found,
        "FORBIDDEN" if not the claim's owner,
        "CONFLICT" if claim already processed,
        "EXPIRED" if the dispute window closed (claim is now confirmed)
    """
    # 1. Load and lock claim (serializes a confirm/reject race — WS4/M8)
    claim = session.exec(
        select(SettlementClaim)
        .where(SettlementClaim.id == claim_id)
        .with_for_update()
    ).first()
    if not claim:
        return None  # Router: 404

    is_aggregate = claim.expense_split_id is None

    # 2. Resolve the claim's owner; per-expense claims also need their
    #    split → expense for the rejection audit entry
    split: ExpenseSplit | None = None
    expense: Expense | None = None
    if is_aggregate:
        owner_id = claim.counterparty_user_id
    else:
        split = session.get(ExpenseSplit, claim.expense_split_id)
        if not split:
            return None  # Router: 404
        expense = session.get(Expense, split.expense_id)
        if not expense:
            return None  # Router: 404
        owner_id = expense.payer_id

    # 3. Verify current_user owns the claim
    if current_user_id != owner_id:
        return "FORBIDDEN"  # Router: 403

    # 4. Verify claim is still PENDING
    if claim.status != SettlementClaimStatus.PENDING:
        return "CONFLICT"  # Router: 409

    # 5. Dispute window closed → the claim auto-confirms instead (WS6)
    if _is_claim_expired(claim):
        if is_aggregate:
            _confirm_aggregate_claim(session, claim, owner_id, auto=True)
        else:
            _confirm_per_expense_claim(
                session, claim, split, expense, owner_id, auto=True
            )
        return "EXPIRED"  # Router: 409 with the dispute-window detail

    # 6. Record the rejection on the claim, THEN build the response from the
    #    truthful state (WS4/H4)
    claim.status = SettlementClaimStatus.REJECTED
    claim.rejected_at = datetime.now(timezone.utc)
    response = _build_claim_public(claim, session)

    # 7. Record audit (REJECTED, before/after) — atomic with the rejection.
    #    Aggregate claims fan out one entry per covered expense.
    if is_aggregate:
        covered = _get_aggregate_covered_rows(session, claim.id)
        for expense_id in {exp.id for _, exp in covered}:
            record_audit(
                session,
                expense_id=expense_id,
                user_id=current_user_id,
                action_type=AuditActionType.REJECTED,
                before_data={"status": "pending"},
                after_data={"status": "rejected", "settle_up": True},
            )
        # Link rows go with the claim (DB cascade would too; explicit keeps
        # the ORM's view consistent)
        session.exec(
            delete(SettlementClaimSplit).where(
                SettlementClaimSplit.claim_id == claim.id
            )
        )
    else:
        record_audit(
            session,
            expense_id=expense.id,
            user_id=current_user_id,
            action_type=AuditActionType.REJECTED,
            before_data={"status": "pending"},
            after_data={"status": "rejected"},
        )

    # 8. Delete the claim so the user can re-claim
    session.delete(claim)

    # 9. Flush + return (router commits the request transaction)
    session.flush()

    return response


def get_claims_awaiting_owner_confirmation(
    session: Session, user_id: uuid.UUID, group_id: uuid.UUID | None = None
) -> list[dict]:
    """
    Get all pending settlement claims for expenses owned by the given user.

    Uses JOIN query to avoid N+1 database calls.

    Args:
        session: Database session
        user_id: User ID (expense owner/payer)
        group_id: Optional group scope (WS5/S4-M6 — a group screen must not
            show other groups' claims)

    Returns:
        List of dictionaries with expense, split, and claim details
    """
    # Single JOIN query to fetch claims + splits + expenses
    statement = (
        select(SettlementClaim, ExpenseSplit, Expense)
        .join(ExpenseSplit, SettlementClaim.expense_split_id == ExpenseSplit.id)
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(Expense.payer_id == user_id)
        .where(SettlementClaim.status == SettlementClaimStatus.PENDING)
    )
    if group_id is not None:
        statement = statement.where(Expense.group_id == group_id)
    rows = session.exec(statement).all()

    # Batch-fetch all claimant users to avoid N+1 per-row lookups
    claimant_ids = {claim.claimant_user_id for claim, _, _ in rows}
    users_map: dict[uuid.UUID, User | None] = {}
    if claimant_ids:
        users = session.exec(
            select(User).where(User.id.in_(claimant_ids))
        ).all()
        users_map = {u.id: u for u in users}

    result = []
    for claim, split, expense in rows:
        # Build claim public inline (avoids per-row session.get in _build_claim_public)
        user = users_map.get(claim.claimant_user_id)
        user_name = user.full_name or user.email if user else None
        claim_public = SettlementClaimPublic(
            id=claim.id,
            expense_split_id=claim.expense_split_id,
            claimant_user_id=claim.claimant_user_id,
            amount=claim.amount,
            status=claim.status,
            claimed_at=claim.claimed_at,
            confirmed_at=claim.confirmed_at,
            rejected_at=claim.rejected_at,
            created_at=claim.created_at,
            user_name=user_name,
        )
        result.append({
            "expense": expense,
            "split": split,
            "claim": claim_public,
        })

    return result


def get_pending_settlements_for_user(
    session: Session, user_id: uuid.UUID
) -> list[dict]:
    """
    Get all pending settlement claims for a user.

    Uses JOIN query to avoid N+1 database calls.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        List of dictionaries with expense, split, and claim details
    """
    # Single JOIN query to fetch claims + splits + expenses
    rows = session.exec(
        select(SettlementClaim, ExpenseSplit, Expense)
        .join(ExpenseSplit, SettlementClaim.expense_split_id == ExpenseSplit.id)
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(SettlementClaim.claimant_user_id == user_id)
        .where(SettlementClaim.status == SettlementClaimStatus.PENDING)
    ).all()

    result = []
    for claim, split, expense in rows:
        result.append({
            "expense": expense,
            "split": split,
            "claim": _build_claim_public(claim, session),
        })

    return result


# =============================================================================
# WS6: Aggregate settle-up + pairwise balances + confirmation policy
# =============================================================================


def get_pairwise_balances(
    session: Session, group_id: uuid.UUID, user_id: uuid.UUID
) -> list[PairwiseBalanceItem]:
    """
    'Who owes whom exactly' for one group member (S2-F9): per counterparty,
    what they owe the caller and what the caller owes them, across confirmed
    splits on confirmed expenses (same semantics as the net balance —
    settled splits drop out; splits with in-flight claims still count until
    the claim is confirmed).
    """
    from sqlalchemy import case, literal

    counterparty_id = case(
        (Expense.payer_id == user_id, ExpenseSplit.user_id),
        else_=Expense.payer_id,
    ).label("counterparty_id")

    rows = session.exec(
        select(
            counterparty_id,
            sa.func.sum(
                case(
                    (Expense.payer_id == user_id, ExpenseSplit.amount_owed),
                    else_=literal(0),
                )
            ).label("they_owe_you"),
            sa.func.sum(
                case(
                    (ExpenseSplit.user_id == user_id, ExpenseSplit.amount_owed),
                    else_=literal(0),
                )
            ).label("you_owe_them"),
        )
        .select_from(Expense)
        .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
        .where(
            Expense.group_id == group_id,
            Expense.status == ExpenseStatus.CONFIRMED,
            ExpenseSplit.status == SplitStatus.CONFIRMED,
            sa.or_(
                sa.and_(
                    Expense.payer_id == user_id,
                    ExpenseSplit.user_id != user_id,
                ),
                sa.and_(
                    ExpenseSplit.user_id == user_id,
                    Expense.payer_id != user_id,
                ),
            ),
        )
        .group_by("counterparty_id")
    ).all()

    ids = [row.counterparty_id for row in rows]
    user_map: dict[uuid.UUID, User] = {}
    if ids:
        users = session.exec(select(User).where(User.id.in_(ids))).all()
        user_map = {u.id: u for u in users}

    zero = Decimal("0.00")
    items = []
    for row in rows:
        they_owe_you = (row.they_owe_you or zero).quantize(Decimal("0.01"))
        you_owe_them = (row.you_owe_them or zero).quantize(Decimal("0.01"))
        user = user_map.get(row.counterparty_id)
        items.append(
            PairwiseBalanceItem(
                user_id=row.counterparty_id,
                user_name=(user.full_name or user.email) if user else None,
                they_owe_you=they_owe_you,
                you_owe_them=you_owe_them,
                net=they_owe_you - you_owe_them,
            )
        )

    items.sort(key=lambda i: (i.user_name or ""))
    return items


def _get_pair_coverable_splits(
    session: Session,
    *,
    group_id: uuid.UUID,
    user_a: uuid.UUID,
    user_b: uuid.UUID,
    lock: bool = False,
) -> list[tuple[ExpenseSplit, Expense]]:
    """
    The splits an aggregate settle-up between a pair would cover: confirmed
    splits on confirmed expenses in the group, in EITHER direction (A owes B
    or B owes A), that aren't already claimed — per-expense or by another
    pending aggregate claim.

    Ordered by split id so concurrent settle-ups acquire row locks in the
    same order (WS4/M8 discipline).
    """
    pending_per_expense = (
        select(SettlementClaim.expense_split_id)
        .where(
            SettlementClaim.status == SettlementClaimStatus.PENDING,
            SettlementClaim.expense_split_id.is_not(None),
        )
    )
    pending_aggregate = (
        select(SettlementClaimSplit.expense_split_id)
        .join(
            SettlementClaim,
            SettlementClaimSplit.claim_id == SettlementClaim.id,
        )
        .where(SettlementClaim.status == SettlementClaimStatus.PENDING)
    )

    stmt = (
        select(ExpenseSplit, Expense)
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(
            Expense.group_id == group_id,
            Expense.status == ExpenseStatus.CONFIRMED,
            ExpenseSplit.status == SplitStatus.CONFIRMED,
            sa.or_(
                sa.and_(
                    Expense.payer_id == user_a, ExpenseSplit.user_id == user_b
                ),
                sa.and_(
                    Expense.payer_id == user_b, ExpenseSplit.user_id == user_a
                ),
            ),
            ExpenseSplit.id.not_in(pending_per_expense),
            ExpenseSplit.id.not_in(pending_aggregate),
        )
        .order_by(ExpenseSplit.id)
    )
    if lock:
        stmt = stmt.with_for_update(of=ExpenseSplit)
    return list(session.exec(stmt).all())


def create_aggregate_settlement(
    session: Session,
    *,
    group_id: uuid.UUID,
    claimant_id: uuid.UUID,
    counterparty_id: uuid.UUID,
) -> SettlementClaimPublic | str:
    """
    "Settle with X" (WS6/S2 §4): net every confirmed, unclaimed split between
    the pair in this group into ONE claim awaiting ONE confirmation. The net
    can be 0.00 when the pair is exactly even (the claim still clears both
    directions). Covered splits settle atomically when the counterparty
    confirms; the per-expense path remains for partial payments.

    Returns:
        SettlementClaimPublic on success,
        "NOTHING" when there is nothing to settle between the pair,
        "WRONG_DIRECTION" when the counterparty owes the claimant overall,
        "CONFLICT" when a racing claim covered one of the splits first
    """
    covered = _get_pair_coverable_splits(
        session,
        group_id=group_id,
        user_a=claimant_id,
        user_b=counterparty_id,
        lock=True,
    )
    if not covered:
        return "NOTHING"

    zero = Decimal("0.00")
    claimant_owes = sum(
        (split.amount_owed for split, _ in covered
         if split.user_id == claimant_id),
        zero,
    )
    counterparty_owes = sum(
        (split.amount_owed for split, _ in covered
         if split.user_id == counterparty_id),
        zero,
    )
    net = (claimant_owes - counterparty_owes).quantize(Decimal("0.01"))
    if net < zero:
        return "WRONG_DIRECTION"

    claim = SettlementClaim(
        expense_split_id=None,
        claimant_user_id=claimant_id,
        group_id=group_id,
        counterparty_user_id=counterparty_id,
        amount=net,
        status=SettlementClaimStatus.PENDING,
        claimed_at=datetime.now(timezone.utc),
    )
    session.add(claim)
    session.flush()

    for split, _ in covered:
        session.add(
            SettlementClaimSplit(
                claim_id=claim.id,
                expense_split_id=split.id,
                amount=split.amount_owed,
            )
        )
    try:
        session.flush()
    except IntegrityError:
        # Unique coverage guard: a racing claim covered one of these splits
        session.rollback()
        return "CONFLICT"

    # Audit fan-out: one entry per covered expense, atomic with the claim
    for expense_id in {expense.id for _, expense in covered}:
        record_audit(
            session,
            expense_id=expense_id,
            user_id=claimant_id,
            action_type=AuditActionType.SETTLED,
            after_data={
                "status": "pending",
                "settle_up": True,
                "net_amount": str(net),
            },
        )
    session.flush()
    session.refresh(claim)

    return _build_claim_public(claim, session)


def get_aggregate_claims(
    session: Session, user_id: uuid.UUID, group_id: uuid.UUID | None = None
) -> list[SettlementClaimPublic]:
    """Pending aggregate settle-up claims involving the user (either side),
    optionally scoped to one group."""
    stmt = (
        select(SettlementClaim)
        .where(
            SettlementClaim.expense_split_id.is_(None),
            SettlementClaim.status == SettlementClaimStatus.PENDING,
            sa.or_(
                SettlementClaim.claimant_user_id == user_id,
                SettlementClaim.counterparty_user_id == user_id,
            ),
        )
        .order_by(SettlementClaim.claimed_at.asc())
    )
    if group_id is not None:
        stmt = stmt.where(SettlementClaim.group_id == group_id)
    claims = session.exec(stmt).all()
    return [_build_claim_public(claim, session) for claim in claims]


def auto_confirm_expired_settlement_claims(
    session: Session,
    *,
    group_id: uuid.UUID | None = None,
    involving_user_id: uuid.UUID | None = None,
) -> int:
    """
    Lazy sweep (WS6): confirm pending settlement claims whose 72h dispute
    window has closed. Runs on the read/write paths that surface claims
    until WS12's scheduler owns it. Filters keep the sweep scoped to what
    the caller is about to see.

    Returns the number of claims confirmed (caller commits when > 0).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(
        hours=SETTLEMENT_AUTO_CONFIRM_HOURS
    )

    per_expense_stmt = (
        select(SettlementClaim.id)
        .join(ExpenseSplit, SettlementClaim.expense_split_id == ExpenseSplit.id)
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(
            SettlementClaim.status == SettlementClaimStatus.PENDING,
            SettlementClaim.claimed_at <= cutoff,
        )
    )
    aggregate_stmt = select(SettlementClaim.id).where(
        SettlementClaim.expense_split_id.is_(None),
        SettlementClaim.status == SettlementClaimStatus.PENDING,
        SettlementClaim.claimed_at <= cutoff,
    )
    if group_id is not None:
        per_expense_stmt = per_expense_stmt.where(Expense.group_id == group_id)
        aggregate_stmt = aggregate_stmt.where(
            SettlementClaim.group_id == group_id
        )
    if involving_user_id is not None:
        per_expense_stmt = per_expense_stmt.where(
            sa.or_(
                SettlementClaim.claimant_user_id == involving_user_id,
                Expense.payer_id == involving_user_id,
            )
        )
        aggregate_stmt = aggregate_stmt.where(
            sa.or_(
                SettlementClaim.claimant_user_id == involving_user_id,
                SettlementClaim.counterparty_user_id == involving_user_id,
            )
        )

    claim_ids = list(session.exec(per_expense_stmt).all()) + list(
        session.exec(aggregate_stmt).all()
    )

    confirmed = 0
    for claim_id in claim_ids:
        # Re-load under lock: a concurrent request may have processed it
        claim = session.exec(
            select(SettlementClaim)
            .where(SettlementClaim.id == claim_id)
            .with_for_update()
        ).first()
        if (
            not claim
            or claim.status != SettlementClaimStatus.PENDING
            or not _is_claim_expired(claim)
        ):
            continue

        if claim.expense_split_id is None:
            _confirm_aggregate_claim(
                session, claim, claim.counterparty_user_id, auto=True
            )
            confirmed += 1
            continue

        split = session.exec(
            select(ExpenseSplit)
            .where(ExpenseSplit.id == claim.expense_split_id)
            .with_for_update()
        ).first()
        if not split:
            continue
        expense = session.exec(
            select(Expense)
            .where(Expense.id == split.expense_id)
            .with_for_update()
        ).first()
        if not expense:
            continue
        _confirm_per_expense_claim(
            session, claim, split, expense, expense.payer_id, auto=True
        )
        confirmed += 1

    return confirmed


def auto_confirm_expired_expenses(
    session: Session,
    *,
    group_id: uuid.UUID | None = None,
    participant_user_id: uuid.UUID | None = None,
) -> int:
    """
    Lazy sweep (WS6 strict mode): in NON-strict groups (the default),
    expenses still awaiting confirmation auto-confirm once their splits are
    EXPENSE_AUTO_CONFIRM_DAYS old — silence is consent; members keep the
    whole window to confirm early or reject. Strict-mode groups are
    untouched (the original Epic 4 workflow). Re-splitting recreates the
    splits, which restarts the window.

    Returns the number of expenses confirmed (caller commits when > 0).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=EXPENSE_AUTO_CONFIRM_DAYS
    )

    stmt = (
        select(Expense.id)
        .join(
            GroupSettings,
            GroupSettings.group_id == Expense.group_id,
            isouter=True,
        )
        .join(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
        .where(
            Expense.status == ExpenseStatus.PENDING_CONFIRMATION,
            sa.or_(
                GroupSettings.strict_mode.is_(None),
                GroupSettings.strict_mode == False,  # noqa: E712
            ),
        )
        .group_by(Expense.id)
        .having(sa.func.max(ExpenseSplit.created_at) <= cutoff)
    )
    if group_id is not None:
        stmt = stmt.where(Expense.group_id == group_id)
    if participant_user_id is not None:
        # Alias: ExpenseSplit is already in the outer FROM, so a bare EXISTS
        # subquery would auto-correlate itself away
        participant_split = sa.orm.aliased(ExpenseSplit)
        participant = select(participant_split.id).where(
            participant_split.expense_id == Expense.id,
            participant_split.user_id == participant_user_id,
        )
        stmt = stmt.where(participant.exists())

    expense_ids = session.exec(stmt).all()

    confirmed = 0
    now = datetime.now(timezone.utc)
    for expense_id in expense_ids:
        # Lock the expense row: serializes against concurrent confirm/reject
        expense = session.exec(
            select(Expense).where(Expense.id == expense_id).with_for_update()
        ).first()
        if not expense or expense.status != ExpenseStatus.PENDING_CONFIRMATION:
            continue

        splits = session.exec(
            select(ExpenseSplit).where(
                ExpenseSplit.expense_id == expense_id,
                ExpenseSplit.status == SplitStatus.PENDING,
            )
        ).all()
        for split in splits:
            split.status = SplitStatus.CONFIRMED
            split.confirmed_at = now
            session.add(split)
        session.flush()

        if finalize_expense(session, expense_id, auto=True):
            confirmed += 1

    return confirmed
