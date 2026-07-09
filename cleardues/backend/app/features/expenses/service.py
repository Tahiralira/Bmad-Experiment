# Expenses feature service - CRUD operations for expenses
#
# TRANSACTION DISCIPLINE (WS4/H5): service functions NEVER commit. They flush,
# so the operation and its audit entry live or die in ONE transaction, and the
# router (the request boundary) commits exactly once. See solution-patterns.yaml
# ARCH-001.
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, delete, select

from app.features.expenses.models import (
    AuditActionType,
    AuditLog,
    AuditLogPublic,
    Expense,
    ExpenseCreate,
    ExpenseSplit,
    ExpenseStatus,
    ExpenseUpdate,
    SettlementClaim,
    SettlementClaimPublic,
    SettlementClaimStatus,
    SplitStatus,
)
from app.features.auth.models import User


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
            f"Split amounts (Rs {provided_total}) must equal "
            f"total expense amount (Rs {total_amount})"
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


def finalize_expense(session: Session, expense_id: uuid.UUID) -> Expense | None:
    """
    Finalize an expense when all splits are confirmed.

    Sets expense status to CONFIRMED and records confirmed_at timestamp.
    Publishes Redis event and creates notification records.

    Args:
        session: Database session
        expense_id: Expense ID

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

    # Publish Redis event for notifications
    publish_expense_confirmed_event(expense)

    # Create notification records for group members
    notify_group_of_finalized_expense(session, expense)

    # Audit entry is atomic with the finalization (same transaction)
    record_audit(
        session,
        expense_id=expense_id,
        user_id=expense.created_by,
        action_type=AuditActionType.CONFIRMED,
        after_data={"status": "confirmed"},
    )
    session.flush()

    return expense


def publish_expense_confirmed_event(expense: Expense) -> None:
    """
    Publish expense confirmed event to Redis Pub/Sub.

    Uses a module-level Redis client for connection reuse.

    Args:
        expense: The finalized expense
    """
    import json
    import logging

    try:
        import redis
        from app.core.config import settings

        # Module-level singleton to avoid creating connections per call
        if not hasattr(publish_expense_confirmed_event, "_redis_client"):
            publish_expense_confirmed_event._redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True,
            )

        redis_client = publish_expense_confirmed_event._redis_client
        event_data = {
            "event_type": "billing.expense.confirmed",
            "expense_id": str(expense.id),
            "group_id": str(expense.group_id),
            "amount": float(expense.amount),
            "confirmed_at": expense.confirmed_at.isoformat() if expense.confirmed_at else None,
        }
        redis_client.publish("billing.expense.confirmed", json.dumps(event_data))
    except Exception as e:
        # Non-blocking: log but don't fail the finalization if Redis is unavailable
        logging.getLogger(__name__).warning(
            f"Failed to publish expense confirmed event: {e}"
        )


def notify_group_of_finalized_expense(session: Session, expense: Expense) -> None:
    """
    Create notification records for all group members about finalized expense.

    Note: Actual notification delivery is handled by Epic 6 (Background Jobs).
    This function prepares the notification data.

    Args:
        session: Database session
        expense: The finalized expense
    """
    # Get all group members - using existing service function
    from app.features.groups.models import GroupMember

    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == expense.group_id)
    ).all()

    # Placeholder for notification creation
    # Full implementation in Epic 6 when notification model is created
    _ = members  # Will be used in Epic 6


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

    Args:
        session: Database session
        user_id: User ID

    Returns:
        List of dictionaries with expense and split details
    """
    # Find all pending splits for user
    splits = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.user_id == user_id)
        .where(ExpenseSplit.status == SplitStatus.PENDING)
    ).all()

    result = []
    for split in splits:
        expense = session.get(Expense, split.expense_id)
        if expense and expense.status == ExpenseStatus.PENDING_CONFIRMATION:
            result.append({
                "expense": expense,
                "split": split,
            })

    return result


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


def _build_claim_public(
    claim: SettlementClaim, session: Session
) -> SettlementClaimPublic:
    """
    Build a SettlementClaimPublic schema with user_name populated.

    Shared helper to avoid duplicating field mapping across service functions.
    """
    user = session.get(User, claim.claimant_user_id)
    user_name = user.full_name or user.email if user else None

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


def confirm_settlement_claim(
    session: Session, claim_id: uuid.UUID, current_user_id: uuid.UUID
) -> SettlementClaimPublic | str | None:
    """
    Owner confirms a settlement claim.

    Validates: claim exists, user is expense owner, claim is pending.
    Updates: claim.status → CONFIRMED, split.status → SETTLED.
    Checks: if all splits settled → expense.status → SETTLED.

    Concurrency (WS4/M8): locks claim → split → expense (always in that
    order, shared with reject, so no deadlock). The claim lock serializes a
    confirm/reject race on the same claim; the expense lock serializes the
    "all splits settled?" check so exactly one of two concurrent
    confirmations flips the expense to SETTLED.

    Args:
        session: Database session
        claim_id: Settlement claim ID
        current_user_id: User ID of the expense owner (payer)

    Returns:
        SettlementClaimPublic on success,
        None if claim not found,
        "FORBIDDEN" if not the expense owner,
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

    # 2. Load and lock associated split → expense
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

    # 3. Verify current_user is expense owner (payer)
    if current_user_id != expense.payer_id:
        return "FORBIDDEN"  # Router: 403

    # 4. Verify claim is still PENDING
    if claim.status != SettlementClaimStatus.PENDING:
        return "CONFLICT"  # Router: 409

    # 5. Update claim: status → CONFIRMED, confirmed_at → now
    claim.status = SettlementClaimStatus.CONFIRMED
    claim.confirmed_at = datetime.now(timezone.utc)

    # 6. Update split: status → SETTLED
    split.status = SplitStatus.SETTLED

    # 6b. Also settle the payer's own split (payer has no debt to settle —
    #     they're the one receiving payment, so their split is resolved too)
    payer_split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense.id)
        .where(ExpenseSplit.user_id == expense.payer_id)
    ).first()
    if payer_split and payer_split.status != SplitStatus.SETTLED:
        payer_split.status = SplitStatus.SETTLED
        session.add(payer_split)

    session.add(claim)
    session.add(split)

    # 7. Record audit (SETTLED, before/after) — atomic with the confirmation
    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id,
        action_type=AuditActionType.SETTLED,
        before_data={"status": "pending", "amount": str(claim.amount)},
        after_data={"status": "confirmed"},
    )

    # 8. Check if ALL expense splits are now SETTLED → expense.status = SETTLED
    # (the split status changes above must be flushed so the check sees them)
    session.flush()
    if check_all_splits_settled(session, expense.id):
        expense.status = ExpenseStatus.SETTLED
        session.add(expense)

    # 9. Flush + return (router commits the request transaction)
    session.flush()
    session.refresh(claim)

    return _build_claim_public(claim, session)


def reject_settlement_claim(
    session: Session, claim_id: uuid.UUID, current_user_id: uuid.UUID
) -> SettlementClaimPublic | str | None:
    """
    Owner rejects a settlement claim.

    Same auth/status guards as confirm.
    Updates (WS4/H4): claim.status → REJECTED and rejected_at → now, so the
    response tells the truth instead of echoing a stale "pending" object.
    Deletes: the claim record (allows claimant to re-claim — the audit log
    preserves the rejection history).

    Args:
        session: Database session
        claim_id: Settlement claim ID
        current_user_id: User ID of the expense owner (payer)

    Returns:
        SettlementClaimPublic with status "rejected" and rejected_at set,
        None if claim not found,
        "FORBIDDEN" if not the expense owner,
        "CONFLICT" if claim already processed
    """
    # 1. Load and lock claim (serializes a confirm/reject race — WS4/M8)
    claim = session.exec(
        select(SettlementClaim)
        .where(SettlementClaim.id == claim_id)
        .with_for_update()
    ).first()
    if not claim:
        return None  # Router: 404

    # 2. Load associated split → expense
    split = session.get(ExpenseSplit, claim.expense_split_id)
    if not split:
        return None  # Router: 404

    expense = session.get(Expense, split.expense_id)
    if not expense:
        return None  # Router: 404

    # 3. Verify current_user is expense owner (payer)
    if current_user_id != expense.payer_id:
        return "FORBIDDEN"  # Router: 403

    # 4. Verify claim is still PENDING
    if claim.status != SettlementClaimStatus.PENDING:
        return "CONFLICT"  # Router: 409

    # 5. Record the rejection on the claim, THEN build the response from the
    #    truthful state (WS4/H4)
    claim.status = SettlementClaimStatus.REJECTED
    claim.rejected_at = datetime.now(timezone.utc)
    response = _build_claim_public(claim, session)

    # 6. Record audit (REJECTED, before/after) — atomic with the rejection
    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id,
        action_type=AuditActionType.REJECTED,
        before_data={"status": "pending"},
        after_data={"status": "rejected"},
    )

    # 7. Delete the claim so the user can re-claim
    session.delete(claim)

    # 8. Flush + return (router commits the request transaction)
    session.flush()

    return response


def get_claims_awaiting_owner_confirmation(
    session: Session, user_id: uuid.UUID
) -> list[dict]:
    """
    Get all pending settlement claims for expenses owned by the given user.

    Uses JOIN query to avoid N+1 database calls.

    Args:
        session: Database session
        user_id: User ID (expense owner/payer)

    Returns:
        List of dictionaries with expense, split, and claim details
    """
    # Single JOIN query to fetch claims + splits + expenses
    rows = session.exec(
        select(SettlementClaim, ExpenseSplit, Expense)
        .join(ExpenseSplit, SettlementClaim.expense_split_id == ExpenseSplit.id)
        .join(Expense, ExpenseSplit.expense_id == Expense.id)
        .where(Expense.payer_id == user_id)
        .where(SettlementClaim.status == SettlementClaimStatus.PENDING)
    ).all()

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
