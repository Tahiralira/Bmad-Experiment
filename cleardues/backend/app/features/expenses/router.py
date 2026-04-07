# Expenses feature router - API routes for expense management
import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Body
from sqlmodel import Session, select

from app.api.deps import CurrentUser, SessionDep
from app.features.expenses import service as expense_service
from app.features.expenses.models import (
    Expense,
    ExpenseCreate,
    ExpensePublic,
    ExpenseSplit,
    ExpenseSplitResponse,
    ExpenseStatus,
    ExpenseUpdate,
)
from app.features.groups.models import ExpenseGroup, GroupMember

router = APIRouter(prefix="/expenses", tags=["expenses"])


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
    if not expense_service.is_user_group_member(
        session, current_user.id, expense_in.group_id
    ):
        raise HTTPException(
            status_code=403,
            detail="You must be a member of the group to create expenses",
        )

    # If payer_id provided, verify payer is also a group member
    if expense_in.payer_id and expense_in.payer_id != current_user.id:
        if not expense_service.is_user_group_member(
            session, expense_in.payer_id, expense_in.group_id
        ):
            raise HTTPException(
                status_code=400, detail="Payer must be a member of the group"
            )

    expense = expense_service.create_expense(session, expense_in, current_user.id)
    return ExpensePublic.model_validate(expense)


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
    """
    expense = session.get(Expense, expense_id)
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
        if not expense_service.is_user_group_member(
            session, expense_in.payer_id, expense.group_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Payer must be a member of the group",
            )

    expense = expense_service.update_expense(session, expense, expense_in)
    return ExpensePublic.model_validate(expense)


@router.put("/{expense_id}/split", response_model=ExpenseSplitResponse)
def update_expense_split(
    *,
    session: Session,
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
    # Get expense
    expense = session.get(Expense, expense_id)
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
    session.query(ExpenseSplit).filter(
        ExpenseSplit.expense_id == expense_id
    ).delete()

    # Create new splits
    for split in splits_data:
        expense_split = ExpenseSplit(
            expense_id=expense_id,
            user_id=split["user_id"],
            amount_owed=split["amount_owed"],
        )
        session.add(expense_split)

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
