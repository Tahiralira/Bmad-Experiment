"""Tests for equal split calculation service (Story 3.5)"""
from decimal import Decimal
import uuid

import pytest
from sqlmodel import Session

from app.features.expenses.service import calculate_equal_split
from app.features.expenses.models import Expense, ExpenseSplit
from app.features.groups.models import GroupMember


class TestCalculateEqualSplit:
    """Test suite for calculate_equal_split function"""

    def test_equal_split_exact_division(self):
        """Test equal split when amount divides evenly"""
        member_ids = [
            uuid.uuid4(),
            uuid.uuid4(),
            uuid.uuid4(),
            uuid.uuid4(),
        ]

        splits = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=member_ids,
            excluded_user_ids=[],
            payer_id=member_ids[0],
        )

        assert len(splits) == 4
        assert all(s["amount_owed"] == Decimal("25.00") for s in splits)

    def test_equal_split_with_rounding(self):
        """Test equal split with rounding mismatch (100 / 3 = 33.33 each, payer absorbs 0.01)"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        splits = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=[user1, user2, user3],
            excluded_user_ids=[],
            payer_id=user1,
        )

        assert len(splits) == 3
        # Payer absorbs the penny difference
        assert splits[0]["amount_owed"] == Decimal("33.34")  # Payer
        assert splits[1]["amount_owed"] == Decimal("33.33")
        assert splits[2]["amount_owed"] == Decimal("33.33")

        # Verify total sums correctly
        total = sum(s["amount_owed"] for s in splits)
        assert total == Decimal("100.00")

    def test_equal_split_with_excluded_members(self):
        """Test equal split with member exclusions"""
        member_ids = [
            uuid.uuid4(),  # user1
            uuid.uuid4(),  # user2
            uuid.uuid4(),  # user3 (excluded)
            uuid.uuid4(),  # user4
        ]

        splits = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=member_ids,
            excluded_user_ids=[member_ids[2]],
            payer_id=member_ids[0],
        )

        # Only 3 members included (user3 excluded)
        assert len(splits) == 3
        # 100 / 3 = 33.33 each
        assert all(s["amount_owed"] == Decimal("33.33") or s["amount_owed"] == Decimal("33.34") for s in splits)
        assert member_ids[2] not in [s["user_id"] for s in splits]

    def test_equal_split_minimum_members_required(self):
        """Test that at least 2 members are required"""
        single_user = uuid.uuid4()

        with pytest.raises(ValueError, match="At least 2 members required"):
            calculate_equal_split(
                total_amount=Decimal("100.00"),
                member_ids=[single_user],
                excluded_user_ids=[],
                payer_id=single_user,
            )

    def test_equal_split_all_but_one_excluded(self):
        """Test split when all but one member excluded (should still require 2)"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        # Exclude user3, leaving 2 members - this should work
        splits = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=[user1, user2, user3],
            excluded_user_ids=[user3],
            payer_id=user1,
        )

        assert len(splits) == 2
        assert all(s["amount_owed"] == Decimal("50.00") for s in splits)

    def test_equal_split_complex_rounding(self):
        """Test rounding with complex amounts"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()

        splits = calculate_equal_split(
            total_amount=Decimal("99.99"),
            member_ids=[user1, user2],
            excluded_user_ids=[],
            payer_id=user1,
        )

        # 99.99 / 2 = 49.995 -> rounds to 50.00 each
        # Total after rounding = 100.00
        # Difference = -0.01, payer absorbs it
        assert splits[0]["amount_owed"] == Decimal("49.99")  # Payer with -0.01 adjustment
        assert splits[1]["amount_owed"] == Decimal("50.00")

        # Verify total
        total = sum(s["amount_owed"] for s in splits)
        assert total == Decimal("99.99")

    def test_equal_split_large_amount(self):
        """Test split with large amount"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        splits = calculate_equal_split(
            total_amount=Decimal("999999.99"),
            member_ids=[user1, user2, user3],
            excluded_user_ids=[],
            payer_id=user1,
        )

        # 999999.99 / 3 = 333333.33 each, payer absorbs 0.01
        assert len(splits) == 3
        total = sum(s["amount_owed"] for s in splits)
        assert total == Decimal("999999.99")


class TestExpenseSplitAPI:
    """Test suite for expense split API endpoint"""

    def test_create_equal_split_for_expense(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Test creating equal split via API"""
        # First create a group with members
        group_data = {"name": "Split Test Group"}
        group_response = client.post(
            f"{settings.API_V1_STR}/expense-groups/",
            headers=normal_user_token_headers,
            json=group_data,
        )
        assert group_response.status_code == 201
        group = group_response.json()

        # Create an expense
        expense_data = {
            "group_id": group["id"],
            "amount": "150.00",
            "description": "Test expense for split",
        }
        expense_response = client.post(
            f"{settings.API_V1_STR}/expenses/",
            headers=normal_user_token_headers,
            json=expense_data,
        )
        assert expense_response.status_code == 200
        expense = expense_response.json()

        # Create equal split
        split_data = {
            "type": "equal",
            "excluded_user_ids": [],
        }
        split_response = client.put(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
            headers=normal_user_token_headers,
            json=split_data,
        )
        assert split_response.status_code == 200
        split_result = split_response.json()

        assert split_result["split_type"] == "equal"
        assert len(split_result["splits"]) == 1  # Only creator in group
        assert split_result["splits"][0]["amount_owed"] == "150.00"

    def test_split_nonexistent_expense_returns_404(
        self, client: TestClient, normal_user_token_headers: dict[str, str]
    ) -> None:
        """Test splitting non-existent expense returns 404"""
        fake_expense_id = uuid.uuid4()
        split_data = {"type": "equal", "excluded_user_ids": []}

        response = client.put(
            f"{settings.API_V1_STR}/expenses/{fake_expense_id}/split",
            headers=normal_user_token_headers,
            json=split_data,
        )
        assert response.status_code == 404

    def test_split_unimplemented_type_returns_400(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Test that unimplemented split types return 400"""
        # Create a group and expense first
        group_data = {"name": "Split Type Test Group"}
        group_response = client.post(
            f"{settings.API_V1_STR}/expense-groups/",
            headers=normal_user_token_headers,
            json=group_data,
        )
        group = group_response.json()

        expense_data = {
            "group_id": group["id"],
            "amount": "100.00",
            "description": "Test",
        }
        expense_response = client.post(
            f"{settings.API_V1_STR}/expenses/",
            headers=normal_user_token_headers,
            json=expense_data,
        )
        expense = expense_response.json()

        # Try unimplemented split type
        split_data = {"type": "percentage", "excluded_user_ids": []}
        split_response = client.put(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
            headers=normal_user_token_headers,
            json=split_data,
        )
        assert split_response.status_code == 400
        assert "not yet implemented" in split_response.json()["detail"]
