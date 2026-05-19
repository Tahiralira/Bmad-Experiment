# Expenses feature service - CRUD operations for expenses
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import sqlalchemy as sa
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
    SplitStatus,
)
from app.features.auth.models import User
from app.features.groups.models import GroupMember


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

    Non-blocking: logs errors but does not fail the parent operation.
    Does NOT commit — lets the parent operation's commit handle it for atomicity.
    """
    import logging

    try:
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
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(
            "Failed to record audit log: expense_id=%s action=%s error=%s",
            expense_id, action_type.value, e,
            exc_info=True,
        )


def is_user_group_member(
    session: Session, user_id: uuid.UUID, group_id: uuid.UUID
) -> bool:
    """Check if user is a member of the specified group."""
    statement = select(GroupMember).where(
        GroupMember.user_id == user_id, GroupMember.group_id == group_id
    )
    return session.exec(statement).first() is not None


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
    session.commit()
    session.refresh(expense)

    # Audit log for expense creation
    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id,
        action_type=AuditActionType.CREATED,
        after_data={"amount": str(expense.amount), "description": expense.description},
    )
    session.commit()

    return expense


def update_expense(
    session: Session, expense: Expense, update_data: ExpenseUpdate, current_user_id: uuid.UUID | None = None
) -> Expense:
    """
    Update expense fields. Only updates provided (non-None) fields.

    Args:
        session: Database session
        expense: Existing Expense object to update
        update_data: ExpenseUpdate with optional fields

    Returns:
        Updated Expense object
    """
    update_dict = update_data.model_dump(exclude_unset=True)

    # Capture BEFORE state for changed fields only
    before_data = {}
    for field in update_dict:
        before_data[field] = str(getattr(expense, field))

    for field, value in update_dict.items():
        setattr(expense, field, value)
    session.add(expense)
    session.commit()
    session.refresh(expense)

    # Capture AFTER state for changed fields only
    after_data = {}
    for field in update_dict:
        after_data[field] = str(getattr(expense, field))

    # Audit log for expense edit
    record_audit(
        session,
        expense_id=expense.id,
        user_id=current_user_id or expense.created_by,
        action_type=AuditActionType.EDITED,
        before_data=before_data,
        after_data=after_data,
    )
    session.commit()

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
    session.commit()
    session.refresh(expense)

    # Publish Redis event for notifications
    publish_expense_confirmed_event(expense)

    # Create notification records for group members
    notify_group_of_finalized_expense(session, expense)

    # Audit log for expense finalization
    record_audit(
        session,
        expense_id=expense_id,
        user_id=expense.created_by,
        action_type=AuditActionType.CONFIRMED,
        after_data={"status": "confirmed"},
    )
    session.commit()

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

    Args:
        session: Database session
        expense_id: Expense ID
        user_id: User ID

    Returns:
        Updated ExpenseSplit with status confirmed
    """
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
    session.commit()
    session.refresh(split)

    # Audit log for split confirmation
    record_audit(
        session,
        expense_id=expense_id,
        user_id=user_id,
        action_type=AuditActionType.CONFIRMED,
    )
    session.commit()

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
    Reject a user's expense split and recalculate remaining splits.

    Args:
        session: Database session
        expense_id: Expense ID
        user_id: User ID

    Returns:
        Dictionary with message and remaining split count
    """
    # Find and delete the split
    split = session.exec(
        select(ExpenseSplit)
        .where(ExpenseSplit.expense_id == expense_id)
        .where(ExpenseSplit.user_id == user_id)
    ).first()

    if not split:
        return None

    # Delete the split
    session.delete(split)

    # Get remaining splits before commit
    remaining_statement = select(ExpenseSplit).where(
        ExpenseSplit.expense_id == expense_id
    )
    remaining_splits = session.exec(remaining_statement).all()

    # Recalculate remaining splits if any remain
    if remaining_splits:
        # Get expense to redistribute amount
        expense = session.get(Expense, expense_id)
        if expense:
            # Redistribute amount equally among remaining members
            per_person = expense.amount / len(remaining_splits)
            for s in remaining_splits:
                s.amount_owed = per_person
                session.add(s)

    session.commit()

    # Audit log for split rejection
    record_audit(
        session,
        expense_id=expense_id,
        user_id=user_id,
        action_type=AuditActionType.REJECTED,
    )
    session.commit()

    return {
        "message": "Expense rejected",
        "remaining_splits": len(remaining_splits) if remaining_splits else 0,
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
