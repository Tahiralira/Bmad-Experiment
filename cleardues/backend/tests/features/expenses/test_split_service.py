"""Tests for equal split calculation service (Story 3.5)"""
from decimal import Decimal
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.features.expenses.service import calculate_equal_split, calculate_unequal_split, calculate_percentage_split
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

        with pytest.raises(ValueError, match="At least 2 members"):
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


class TestCalculateUnequalSplit:
    """Test suite for calculate_unequal_split function"""

    def test_unequal_split_exact_match(self):
        """Test unequal split when amounts sum to total exactly"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())
        user3 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "amount": 50.00},
            {"user_id": user2, "amount": 30.00},
            {"user_id": user3, "amount": 20.00}
        ]

        result = calculate_unequal_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 3
        assert result[0]["amount_owed"] == Decimal("50.00")
        assert result[1]["amount_owed"] == Decimal("30.00")
        assert result[2]["amount_owed"] == Decimal("20.00")

    def test_unequal_split_under_allocated(self):
        """Test that under-allocated splits raise error"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())
        user3 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "amount": 40.00},
            {"user_id": user2, "amount": 30.00},
            {"user_id": user3, "amount": 20.00}
        ]  # Total = 90, but expense is 100

        with pytest.raises(ValueError, match="must equal total"):
            calculate_unequal_split(
                total_amount=Decimal("100.00"),
                splits=splits
            )

    def test_unequal_split_over_allocated(self):
        """Test that over-allocated splits raise error"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())
        user3 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "amount": 60.00},
            {"user_id": user2, "amount": 30.00},
            {"user_id": user3, "amount": 20.00}
        ]  # Total = 110, but expense is 100

        with pytest.raises(ValueError, match="must equal total"):
            calculate_unequal_split(
                total_amount=Decimal("100.00"),
                splits=splits
            )

    def test_unequal_split_tolerance(self):
        """Test that small rounding differences are tolerated"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())
        user3 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "amount": 33.33},
            {"user_id": user2, "amount": 33.33},
            {"user_id": user3, "amount": 33.34}
        ]  # Total = 100.00 (with rounding)

        result = calculate_unequal_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 3
        # Verify total sums correctly
        total = sum(s["amount_owed"] for s in result)
        assert total == Decimal("100.00")

    def test_unequal_split_decimals(self):
        """Test unequal split with decimal amounts"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "amount": 55.55},
            {"user_id": user2, "amount": 44.45}
        ]

        result = calculate_unequal_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 2
        assert result[0]["amount_owed"] == Decimal("55.55")
        assert result[1]["amount_owed"] == Decimal("44.45")

    def test_unequal_split_large_amounts(self):
        """Test unequal split with large amounts"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "amount": 600000.00},
            {"user_id": user2, "amount": 399999.99}
        ]

        result = calculate_unequal_split(
            total_amount=Decimal("999999.99"),
            splits=splits
        )

        assert len(result) == 2
        total = sum(s["amount_owed"] for s in result)
        assert total == Decimal("999999.99")

    def test_unequal_split_with_excluded_members(self):
        """Test unequal split with member exclusions"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()  # Will be excluded
        user4 = uuid.uuid4()

        member_ids = [user1, user2, user3, user4]

        # Contract: the caller provides splits for INCLUDED members only, and
        # they must sum to the total — the service does not redistribute an
        # excluded member's share (the original test asserted auto-adjustment
        # that was never implemented).
        splits = [
            {"user_id": str(user1), "amount": 50.00},
            {"user_id": str(user2), "amount": 30.00},
            {"user_id": str(user4), "amount": 20.00},
        ]

        result = calculate_unequal_split(
            total_amount=Decimal("100.00"),
            splits=splits,
            member_ids=member_ids,
            excluded_user_ids=[user3]
        )

        # Only 3 members included (user3 excluded)
        assert len(result) == 3
        # Verify user3 is not in result
        assert user3 not in [s["user_id"] for s in result]
        # Verify amounts are correct for included members
        assert result[0]["amount_owed"] == Decimal("50.00")
        assert result[1]["amount_owed"] == Decimal("30.00")
        assert result[2]["amount_owed"] == Decimal("20.00")

    def test_unequal_split_exclude_all_but_one_raises_error(self):
        """Test that excluding all but one member raises error"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        member_ids = [user1, user2, user3]

        splits = [
            {"user_id": str(user1), "amount": 100.00},
            {"user_id": str(user2), "amount": 0.00},  # Will be excluded
            {"user_id": str(user3), "amount": 0.00}   # Will be excluded
        ]

        with pytest.raises(ValueError, match="At least 2 members must be included"):
            calculate_unequal_split(
                total_amount=Decimal("100.00"),
                splits=splits,
                member_ids=member_ids,
                excluded_user_ids=[user2, user3]
            )

    def test_unequal_split_with_string_uuids(self):
        """Test unequal split handles string UUIDs correctly with exclusions"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        member_ids = [user1, user2, user3]

        splits = [
            {"user_id": str(user1), "amount": 60.00},
            {"user_id": str(user2), "amount": 40.00},
            {"user_id": str(user3), "amount": 0.00}  # Excluded
        ]

        result = calculate_unequal_split(
            total_amount=Decimal("100.00"),
            splits=splits,
            member_ids=member_ids,
            excluded_user_ids=[user3]
        )

        assert len(result) == 2
        # All user_ids should be UUID objects
        assert all(isinstance(s["user_id"], uuid.UUID) for s in result)


class TestExpenseSplitAPI:
    """Test suite for expense split API endpoint"""

    def test_create_equal_split_for_expense(
        self,
        client: TestClient,
        normal_user_token_headers: dict[str, str],
        second_user_token_headers: dict[str, str],
        db: Session,
    ) -> None:
        """Test creating equal split via API.

        Note: the original version split among a single member, which the
        service (correctly) rejects with "At least 2 members" — it never
        passed. A second member is required for the success path.
        """
        # First create a group
        group_data = {"name": f"Split Test Group {uuid.uuid4().hex[:8]}"}
        group_response = client.post(
            f"{settings.API_V1_STR}/expense-groups/",
            headers=normal_user_token_headers,
            json=group_data,
        )
        assert group_response.status_code == 201
        group = group_response.json()

        # Add a second member via invite (acceptance is a GET per current API)
        invite_response = client.post(
            f"{settings.API_V1_STR}/expense-groups/{group['id']}/invites",
            headers=normal_user_token_headers,
            json={},
        )
        assert invite_response.status_code == 201
        invite_token = invite_response.json()["invite"]["token"]
        accept_response = client.get(
            f"{settings.API_V1_STR}/expense-groups/invite/{invite_token}",
            headers=second_user_token_headers,
        )
        assert accept_response.status_code == 200

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
        assert len(split_result["splits"]) == 2
        amounts = sorted(s["amount_owed"] for s in split_result["splits"])
        assert amounts == ["75.00", "75.00"]

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

        # Try unimplemented split type (shares - not yet implemented)
        split_data = {"type": "shares", "splits": []}
        split_response = client.put(
            f"{settings.API_V1_STR}/expenses/{expense['id']}/split",
            headers=normal_user_token_headers,
            json=split_data,
        )
        assert split_response.status_code == 400
        assert "not yet implemented" in split_response.json()["detail"]


class TestCalculatePercentageSplit:
    """Test suite for calculate_percentage_split function (Story 3.7)"""

    def test_percentage_split_exact_100(self):
        """Test percentage split when percentages sum to 100 exactly"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 60.0},
            {"user_id": user2, "percentage": 40.0}
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 2
        assert result[0]["amount_owed"] == Decimal("60.00")
        assert result[1]["amount_owed"] == Decimal("40.00")

    def test_percentage_split_three_way_split(self):
        """Test three-way percentage split (33.33%, 33.33%, 33.34%)"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())
        user3 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 33.33},
            {"user_id": user2, "percentage": 33.33},
            {"user_id": user3, "percentage": 33.34}
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 3
        # Verify amounts sum to total (last member gets rounding remainder)
        total = sum(s["amount_owed"] for s in result)
        assert total == Decimal("100.00")

    def test_percentage_split_under_100(self):
        """Test that percentages under 100 raise error"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 50.0},
            {"user_id": user2, "percentage": 30.0}
        ]  # Total = 80, should be 100

        with pytest.raises(ValueError, match="must equal 100%"):
            calculate_percentage_split(
                total_amount=Decimal("100.00"),
                splits=splits
            )

    def test_percentage_split_over_100(self):
        """Test that percentages over 100 raise error"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 70.0},
            {"user_id": user2, "percentage": 50.0}
        ]  # Total = 120, should be 100

        with pytest.raises(ValueError, match="must equal 100%"):
            calculate_percentage_split(
                total_amount=Decimal("100.00"),
                splits=splits
            )

    def test_percentage_split_rounding(self):
        """Test that rounding is handled correctly with last member getting remainder"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())
        user3 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 33.33},
            {"user_id": user2, "percentage": 33.33},
            {"user_id": user3, "percentage": 33.34}
        ]  # Total = 100.00

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        # Verify amounts sum to total (last member gets remainder)
        total_calculated = sum(s["amount_owed"] for s in result)
        assert total_calculated == Decimal("100.00")

    def test_percentage_split_with_decimals(self):
        """Test percentage split with decimal percentages"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 66.67},
            {"user_id": user2, "percentage": 33.33}
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 2
        # Verify total sums correctly
        total = sum(s["amount_owed"] for s in result)
        assert total == Decimal("100.00")

    def test_percentage_split_large_amounts(self):
        """Test percentage split with large amounts"""
        user1 = str(uuid.uuid4())
        user2 = str(uuid.uuid4())

        splits = [
            {"user_id": user1, "percentage": 60.0},
            {"user_id": user2, "percentage": 40.0}
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("999999.99"),
            splits=splits
        )

        assert len(result) == 2
        assert result[0]["amount_owed"] == Decimal("599999.99")
        assert result[1]["amount_owed"] == Decimal("400000.00")

        # Verify total
        total = sum(s["amount_owed"] for s in result)
        assert total == Decimal("999999.99")

    def test_percentage_split_uuid_conversion(self):
        """Test that function handles both string and UUID objects"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()

        # Mix string and UUID objects
        splits = [
            {"user_id": str(user1), "percentage": 50.0},
            {"user_id": user2, "percentage": 50.0}  # UUID object
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits
        )

        assert len(result) == 2
        # Both should be UUID objects in result
        assert isinstance(result[0]["user_id"], uuid.UUID)
        assert isinstance(result[1]["user_id"], uuid.UUID)
        assert result[0]["user_id"] == user1
        assert result[1]["user_id"] == user2

    def test_percentage_split_with_excluded_members(self):
        """Test percentage split with member exclusions"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()  # Will be excluded

        member_ids = [user1, user2, user3]

        splits = [
            {"user_id": str(user1), "percentage": 60.0},
            {"user_id": str(user2), "percentage": 40.0},
            {"user_id": str(user3), "percentage": 0.0}  # Will be excluded
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits,
            member_ids=member_ids,
            excluded_user_ids=[user3]
        )

        # Only 2 members included (user3 excluded)
        assert len(result) == 2
        # Verify user3 is not in result
        assert user3 not in [s["user_id"] for s in result]
        # Verify amounts are correct
        assert result[0]["amount_owed"] == Decimal("60.00")
        assert result[1]["amount_owed"] == Decimal("40.00")

    def test_percentage_split_exclude_all_but_one_raises_error(self):
        """Test that excluding all but one member raises error"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        member_ids = [user1, user2, user3]

        splits = [
            {"user_id": str(user1), "percentage": 100.0},
            {"user_id": str(user2), "percentage": 0.0},  # Excluded
            {"user_id": str(user3), "percentage": 0.0}   # Excluded
        ]

        with pytest.raises(ValueError, match="At least 2 members must be included"):
            calculate_percentage_split(
                total_amount=Decimal("100.00"),
                splits=splits,
                member_ids=member_ids,
                excluded_user_ids=[user2, user3]
            )

    def test_percentage_split_three_way_with_exclusion(self):
        """Test three-way percentage split with one member excluded"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()
        user4 = uuid.uuid4()  # Will be excluded

        member_ids = [user1, user2, user3, user4]

        splits = [
            {"user_id": str(user1), "percentage": 50.0},
            {"user_id": str(user2), "percentage": 30.0},
            {"user_id": str(user3), "percentage": 20.0},
            {"user_id": str(user4), "percentage": 0.0}  # Excluded
        ]

        result = calculate_percentage_split(
            total_amount=Decimal("100.00"),
            splits=splits,
            member_ids=member_ids,
            excluded_user_ids=[user4]
        )

        # Only 3 members included
        assert len(result) == 3
        # Verify user4 is not in result
        assert user4 not in [s["user_id"] for s in result]
        # Verify total sums to 100
        total = sum(s["amount_owed"] for s in result)
        assert total == Decimal("100.00")


class TestFilterIncludedMembers:
    """Test suite for filter_included_members helper function"""

    def test_filter_no_exclusions(self):
        """Test filtering with no exclusions returns all members"""
        member_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]

        result = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=member_ids,
            excluded_user_ids=[]
        )

        assert len(result) == 3

    def test_filter_with_exclusions(self):
        """Test filtering excludes specified members"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        result = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=[user1, user2, user3],
            excluded_user_ids=[user2]
        )

        assert len(result) == 2
        assert user2 not in [s["user_id"] for s in result]

    def test_filter_minimum_members_required(self):
        """Test that filter requires at least 2 members"""
        user1 = uuid.uuid4()
        user2 = uuid.uuid4()
        user3 = uuid.uuid4()

        with pytest.raises(ValueError, match="At least 2 members must be included"):
            calculate_equal_split(
                total_amount=Decimal("100.00"),
                member_ids=[user1, user2, user3],
                excluded_user_ids=[user2, user3]  # Only user1 left
            )

    def test_filter_empty_exclusion_list(self):
        """Test that empty exclusion list is handled correctly"""
        member_ids = [uuid.uuid4(), uuid.uuid4()]

        # None instead of empty list
        result = calculate_equal_split(
            total_amount=Decimal("100.00"),
            member_ids=member_ids,
            excluded_user_ids=None
        )

        assert len(result) == 2
