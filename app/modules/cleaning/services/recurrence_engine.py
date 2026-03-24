"""
CleanClaw v3 — Recurrence Engine (S2.4).

Updates next_occurrence for recurring schedules after they are matched
by the schedule engine. Ensures that each schedule's next_occurrence
always points to the next valid date.
"""

import logging
from datetime import date
from typing import Optional

from app.database import Database
from app.modules.cleaning.services.frequency_matcher import compute_next_occurrence
from app.modules.cleaning.services._type_helpers import to_date

logger = logging.getLogger("cleanclaw.recurrence_engine")


async def advance_next_occurrence(
    db: Database,
    schedule_id: str,
    business_id: str,
    matched_date: date,
) -> Optional[date]:
    """
    After a schedule is matched for matched_date, compute and store
    the next occurrence.

    Args:
        db: Database instance
        schedule_id: cleaning_client_schedules.id
        business_id: business_id for safety
        matched_date: the date that was matched (used as from_date)

    Returns:
        The new next_occurrence date, or None
    """
    row = await db.pool.fetchrow(
        """
        SELECT frequency, preferred_day_of_week, custom_interval_days, created_at
        FROM cleaning_client_schedules
        WHERE id = $1 AND business_id = $2
        """,
        schedule_id,
        business_id,
    )

    if not row:
        logger.warning("[RECURRENCE] Schedule %s not found", schedule_id)
        return None

    schedule = dict(row)
    # Convert created_at for compute_next_occurrence
    if schedule.get("created_at") and hasattr(schedule["created_at"], "date"):
        schedule["created_at"] = schedule["created_at"].date()

    next_date = compute_next_occurrence(schedule, from_date=matched_date)

    if next_date:
        await db.pool.execute(
            """
            UPDATE cleaning_client_schedules
            SET next_occurrence = $3, updated_at = NOW()
            WHERE id = $1 AND business_id = $2
            """,
            schedule_id,
            business_id,
            to_date(next_date),
        )
        logger.info(
            "[RECURRENCE] Schedule %s: next_occurrence updated %s -> %s",
            schedule_id[:8], matched_date, next_date,
        )

    return next_date


async def bulk_advance(
    db: Database,
    business_id: str,
    matched_schedules: list[dict],
    matched_date: date,
) -> dict:
    """
    Advance next_occurrence for multiple schedules at once.

    Args:
        db: Database instance
        business_id: business_id
        matched_schedules: list of schedule dicts (each must have 'id')
        matched_date: the date that was matched

    Returns:
        dict with updated count and any errors
    """
    updated = 0
    errors = []

    for schedule in matched_schedules:
        schedule_id = schedule.get("id") or schedule.get("schedule_id")
        if not schedule_id:
            continue

        try:
            next_date = await advance_next_occurrence(
                db, str(schedule_id), business_id, matched_date,
            )
            if next_date:
                updated += 1
        except Exception as e:
            logger.error("[RECURRENCE] Error advancing schedule %s: %s", schedule_id, e)
            errors.append({"schedule_id": str(schedule_id), "error": str(e)})

    return {"updated": updated, "errors": errors}
