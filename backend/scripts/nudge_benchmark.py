"""
Nudge sweep benchmark (WS13) — measure the scheduler, don't guess at it.

The execution plan asks for a "load/scheduler sanity check … declare real
numbers, not aspirations". This is that check, kept as a runnable script
rather than a paragraph, so the numbers in the runbook can be re-measured
after any change instead of aging quietly into folklore.

What it measures is the thing that actually bounds the engine: one sweep
over N debt relationships. The sweep is triggered hourly by a GitHub Actions
cron (`.github/workflows/nudge-sweep.yml`), so the only question that
matters operationally is whether one sweep finishes comfortably inside an
hour — and, on Render's free tier, inside the request timeout of the HTTP
call that drives it.

Delivery is deliberately NOT exercised: every seeded user is created with
both channels switched OFF, so the sweep records SKIPPED and the timings
isolate the ENGINE's own cost — query, netting, suppressor checks, writes.
That switch-off is load-bearing rather than tidy: local compose runs
mailcatcher, so `emails_enabled` is TRUE here, and a first run of this
script spent most of its time in SMTP and reported it as engine cost. Real
delivery adds network time per recipient that no local benchmark can
honestly predict; the runbook says so instead of pretending otherwise.

Run it against the TEST database, never a real one:

    docker compose exec backend python scripts/nudge_benchmark.py --groups 50

Safety: refuses to run unless ENVIRONMENT=local, and always redirects to
`<POSTGRES_DB>_test` — the same guard the pytest suite uses. It writes a lot
of rows and must never be pointed at anything anyone cares about.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.core.config import settings

if settings.ENVIRONMENT != "local":
    sys.exit(
        f"Refusing to run: ENVIRONMENT is {settings.ENVIRONMENT!r}, not 'local'. "
        "This script writes thousands of rows."
    )
if not settings.POSTGRES_DB.endswith("_test"):
    settings.POSTGRES_DB = f"{settings.POSTGRES_DB}_test"

from sqlmodel import Session, select  # noqa: E402

from app.core.db import engine  # noqa: E402
from app.features.auth.models import User  # noqa: E402
from app.features.expenses.models import (  # noqa: E402
    Expense,
    ExpenseSplit,
    ExpenseStatus,
    SplitStatus,
)
from app.features.groups.models import (  # noqa: E402
    ExpenseGroup,
    GroupMember,
    GroupSettings,
)
from app.features.notifications import service as nudge_service  # noqa: E402
from app.features.notifications.models import (  # noqa: E402
    Notification,
    NotificationPreference,
    NudgeState,
)


def _seed(
    session: Session, *, groups: int, members_per_group: int, expenses_per_group: int
) -> int:
    """
    Build a synthetic but structurally REAL dataset: confirmed expenses with
    confirmed splits, backdated past the Level 1 threshold.

    Rows go in through the ORM rather than raw SQL so the benchmark measures
    the engine against the same shapes production produces — including the
    netting across both directions, which is where the sweep does its real
    work.
    """
    marker = f"bench-{uuid.uuid4().hex[:8]}"
    old = datetime.now(timezone.utc) - timedelta(
        hours=settings.NUDGE_LEVEL_1_AFTER_HOURS + 48
    )
    relationships = 0

    for g in range(groups):
        users: list[User] = []
        for m in range(members_per_group):
            user = User(
                email=f"{marker}-g{g}m{m}@bench.example.com",
                hashed_password="x",
                full_name=f"Bench {g}-{m}",
                is_active=True,
            )
            session.add(user)
            users.append(user)
        session.flush()

        # Both channels off: this benchmark measures the engine, not the
        # network. Without it, local mailcatcher turns every nudge into a
        # real SMTP round trip.
        for user in users:
            session.add(
                NotificationPreference(
                    user_id=user.id, push_enabled=False, email_enabled=False
                )
            )
        session.flush()

        group = ExpenseGroup(name=f"{marker} group {g}", created_by=users[0].id)
        session.add(group)
        session.flush()
        session.add(GroupSettings(group_id=group.id, currency="USD"))
        for user in users:
            session.add(GroupMember(group_id=group.id, user_id=user.id))
        session.flush()

        # Rotate the payer so every pair in the group ends up related, and
        # VARY the amount so the rotation does not cancel itself out. An
        # earlier version paid a flat 120.00 with an even rotation, which
        # meant everyone paid exactly as much as they owed: 49 relationships
        # discovered, one nudge sent, and a benchmark measuring an engine
        # with almost nothing to do. Unequal amounts are also what real
        # groups look like.
        for e in range(expenses_per_group):
            payer = users[e % len(users)]
            amount = Decimal("60.00") + Decimal(e) * Decimal("17.50")
            expense = Expense(
                group_id=group.id,
                payer_id=payer.id,
                created_by=payer.id,
                amount=amount,
                description=f"{marker} expense {e}",
                status=ExpenseStatus.CONFIRMED,
                confirmed_at=old,
            )
            session.add(expense)
            session.flush()
            share = (amount / len(users)).quantize(Decimal("0.01"))
            for user in users:
                if user.id == payer.id:
                    continue
                session.add(
                    ExpenseSplit(
                        expense_id=expense.id,
                        user_id=user.id,
                        amount_owed=share,
                        status=SplitStatus.CONFIRMED,
                    )
                )
        session.flush()
        relationships += members_per_group * (members_per_group - 1) // 2

    session.commit()
    return relationships


def _time(label: str, fn, repeats: int) -> float:
    """Run `fn` `repeats` times; report median and worst. Median, not mean —
    one cold cache should not become the headline number."""
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    median = statistics.median(samples)
    print(
        f"  {label:<34} median {median * 1000:8.1f} ms   "
        f"worst {max(samples) * 1000:8.1f} ms   (n={repeats})"
    )
    return median


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--groups", type=int, default=50)
    parser.add_argument("--members", type=int, default=5)
    parser.add_argument("--expenses", type=int, default=6)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Leave the seeded rows behind (default: clean up).",
    )
    args = parser.parse_args()

    print(
        f"\nSeeding {args.groups} groups x {args.members} members x "
        f"{args.expenses} expenses into {settings.POSTGRES_DB} ..."
    )
    with Session(engine) as session:
        expected = _seed(
            session,
            groups=args.groups,
            members_per_group=args.members,
            expenses_per_group=args.expenses,
        )
        print(f"Seeded. Pairs created by this run: {expected}\n")

        found = nudge_service.find_debt_relationships(session)
        print(
            f"Discovery found {len(found)} netted relationships DB-WIDE — this "
            "run's pairs plus whatever the test suite left behind. The sweep "
            "below runs over all of them, which is the production shape: one "
            "sweep, whole system, no per-group loop.\n"
        )

        print("Timings")
        _time(
            "find_debt_relationships (whole DB)",
            lambda: nudge_service.find_debt_relationships(session),
            args.repeats,
        )

        # Dry run: full traversal, suppressors and all, no writes and no
        # delivery. This is the engine's own cost.
        _time(
            "run_nudge_sweep (dry run)",
            lambda: nudge_service.run_nudge_sweep(session, dry_run=True),
            args.repeats,
        )

        # A real first sweep writes notification rows and cooldown stamps.
        # Timed ONCE and separately: every subsequent sweep is suppressed by
        # the cooldown it just set, so repeating it would measure the cheap
        # path and call it the expensive one.
        start = time.perf_counter()
        result = nudge_service.run_nudge_sweep(session)
        session.commit()
        first_sweep = time.perf_counter() - start
        print(
            f"  {'run_nudge_sweep (first, writes)':<34} "
            f"       {first_sweep * 1000:8.1f} ms                        (n=1)"
        )

        _time(
            "run_nudge_sweep (cooled down)",
            lambda: nudge_service.run_nudge_sweep(session),
            args.repeats,
        )

        print(
            f"\nFirst sweep: examined {result.relationships_examined}, "
            f"nudged {sum(result.nudges_by_level.values())} "
            f"({result.nudges_by_level}), "
            f"deliveries {result.deliveries}"
        )
        print(
            "NOTE: every seeded user has both channels switched OFF, so these "
            "numbers are the ENGINE's cost only — query, netting, suppressors "
            "and writes. Real sends add network time per recipient that no "
            "local run can predict; size the schedule from those separately."
        )

        if not args.keep:
            _cleanup(session)
            print("\nCleaned up seeded rows.")


def _cleanup(session: Session) -> None:
    """
    Remove everything the benchmark created.

    Ordered child-first because WS4 turned the user FK cascades into
    RESTRICTs (B-C4, soft deletion): deleting users first would simply
    fail.
    """
    bench_users = session.exec(
        select(User.id).where(User.email.like("bench-%@bench.example.com"))
    ).all()
    if not bench_users:
        return
    bench_groups = session.exec(
        select(ExpenseGroup.id).where(ExpenseGroup.name.like("bench-%"))
    ).all()

    for model, column in (
        (Notification, Notification.user_id),
        (NudgeState, NudgeState.user_id),
        (NotificationPreference, NotificationPreference.user_id),
    ):
        for row in session.exec(select(model).where(column.in_(bench_users))).all():
            session.delete(row)
    session.flush()

    expense_ids = session.exec(
        select(Expense.id).where(Expense.group_id.in_(bench_groups))
    ).all()
    for row in session.exec(
        select(ExpenseSplit).where(ExpenseSplit.expense_id.in_(expense_ids))
    ).all():
        session.delete(row)
    session.flush()
    for row in session.exec(
        select(Expense).where(Expense.id.in_(expense_ids))
    ).all():
        session.delete(row)
    session.flush()
    for model in (GroupMember, GroupSettings):
        for row in session.exec(
            select(model).where(model.group_id.in_(bench_groups))
        ).all():
            session.delete(row)
    session.flush()
    for row in session.exec(
        select(ExpenseGroup).where(ExpenseGroup.id.in_(bench_groups))
    ).all():
        session.delete(row)
    session.flush()
    for row in session.exec(select(User).where(User.id.in_(bench_users))).all():
        session.delete(row)
    session.commit()


if __name__ == "__main__":
    main()
