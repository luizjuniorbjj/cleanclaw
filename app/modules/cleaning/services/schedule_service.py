"""
Xcleaners v3 — Client Schedule Service (S2.3).

CRUD for cleaning_client_schedules (recurring service agreements).
Handles next_occurrence computation, pause/resume, and
listing schedules due on a specific date (for the schedule engine).
"""

import logging
from datetime import date, timedelta
from typing import Optional

from app.database import Database
from app.modules.cleaning.services._type_helpers import to_date, to_time

logger = logging.getLogger("xcleaners.schedule_service")


# ============================================
# NEXT OCCURRENCE COMPUTATION
# ============================================

def compute_next_occurrence(
    frequency: str,
    preferred_day_of_week: Optional[int],
    custom_interval_days: Optional[int] = None,
    from_date: Optional[date] = None,
) -> Optional[date]:
    """
    Compute the next occurrence date based on frequency.

    Args:
        frequency: weekly, biweekly, monthly, sporadic
        preferred_day_of_week: 0=Sunday, 6=Saturday
        custom_interval_days: days between services (sporadic only)
        from_date: starting reference date (defaults to today)

    Returns:
        Next occurrence date
    """
    if from_date is None:
        from_date = date.today()

    if frequency == "weekly":
        if preferred_day_of_week is not None:
            # Find next occurrence of preferred day
            current_dow = from_date.isoweekday() % 7  # Convert to 0=Sun
            target_dow = preferred_day_of_week
            days_ahead = (target_dow - current_dow) % 7
            if days_ahead == 0:
                days_ahead = 7  # Next week if today is the day
            return from_date + timedelta(days=days_ahead)
        return from_date + timedelta(days=7)

    elif frequency == "biweekly":
        if preferred_day_of_week is not None:
            current_dow = from_date.isoweekday() % 7
            target_dow = preferred_day_of_week
            days_ahead = (target_dow - current_dow) % 7
            if days_ahead == 0:
                days_ahead = 14
            elif days_ahead < 7:
                days_ahead += 7  # Ensure at least 2 weeks out
            return from_date + timedelta(days=days_ahead)
        return from_date + timedelta(days=14)

    elif frequency == "monthly":
        # Same day next month
        year = from_date.year
        month = from_date.month + 1
        if month > 12:
            month = 1
            year += 1
        day = min(from_date.day, 28)  # Safe for all months
        if preferred_day_of_week is not None:
            # Find the first occurrence of preferred day in next month
            first_of_month = date(year, month, 1)
            current_dow = first_of_month.isoweekday() % 7
            days_ahead = (preferred_day_of_week - current_dow) % 7
            return first_of_month + timedelta(days=days_ahead)
        return date(year, month, day)

    elif frequency == "sporadic":
        interval = custom_interval_days or 30
        return from_date + timedelta(days=interval)

    return None


# ============================================
# SCHEDULE CRUD
# ============================================

async def create_schedule(
    db: Database,
    business_id: str,
    client_id: str,
    data: dict,
) -> dict:
    """Create a recurring client schedule."""
    # Validate client exists and belongs to business
    client = await db.pool.fetchrow(
        "SELECT id, status FROM cleaning_clients WHERE id = $1 AND business_id = $2",
        client_id, business_id,
    )
    if not client:
        return {"error": "Client not found", "status_code": 404}
    if client["status"] == "blocked":
        return {"error": "Cannot create schedule for blocked client", "status_code": 400}

    # Validate service exists
    service = await db.pool.fetchrow(
        "SELECT id, estimated_duration_minutes FROM cleaning_services WHERE id = $1 AND business_id = $2 AND is_active = true",
        data["service_id"], business_id,
    )
    if not service:
        return {"error": "Service not found or inactive", "status_code": 404}

    # Validate preferred_team_id if provided
    if data.get("preferred_team_id"):
        team = await db.pool.fetchrow(
            "SELECT id FROM cleaning_teams WHERE id = $1 AND business_id = $2 AND is_active = true",
            data["preferred_team_id"], business_id,
        )
        if not team:
            return {"error": "Team not found or inactive", "status_code": 404}

    # Validate frequency requirements
    frequency = data["frequency"]
    if frequency in ("weekly", "biweekly") and data.get("preferred_day_of_week") is None:
        return {"error": "preferred_day_of_week is required for weekly/biweekly frequency", "status_code": 400}

    # Compute next_occurrence if not provided
    next_occ = data.get("next_occurrence")
    if not next_occ:
        computed = compute_next_occurrence(
            frequency=frequency,
            preferred_day_of_week=data.get("preferred_day_of_week"),
            custom_interval_days=data.get("custom_interval_days"),
        )
        next_occ = str(computed) if computed else None

    # Default duration from service if not specified
    est_duration = data.get("estimated_duration_minutes") or service["estimated_duration_minutes"]

    # Convert string times/dates to proper Python types for asyncpg
    from datetime import time as dt_time, date as dt_date
    time_start = None
    if data.get("preferred_time_start"):
        h, m = data["preferred_time_start"].split(":")
        time_start = dt_time(int(h), int(m))
    time_end = None
    if data.get("preferred_time_end"):
        h, m = data["preferred_time_end"].split(":")
        time_end = dt_time(int(h), int(m))
    next_occ_date = None
    if next_occ:
        if isinstance(next_occ, str):
            next_occ_date = dt_date.fromisoformat(next_occ)
        else:
            next_occ_date = next_occ

    row = await db.pool.fetchrow(
        """INSERT INTO cleaning_client_schedules
           (business_id, client_id, service_id, frequency, custom_interval_days,
            preferred_day_of_week, preferred_time_start, preferred_time_end,
            preferred_team_id, agreed_price, estimated_duration_minutes,
            min_team_size, next_occurrence, notes, status)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
           RETURNING *""",
        business_id,
        client_id,
        data["service_id"],
        frequency,
        data.get("custom_interval_days"),
        data.get("preferred_day_of_week"),
        time_start,
        time_end,
        data.get("preferred_team_id"),
        data.get("agreed_price"),
        est_duration,
        data.get("min_team_size", 1),
        next_occ_date,
        data.get("notes"),
        data.get("status", "active"),
    )

    return _schedule_to_dict(row)


async def get_schedule(
    db: Database,
    business_id: str,
    schedule_id: str,
) -> Optional[dict]:
    """Get a single schedule by ID."""
    row = await db.pool.fetchrow(
        "SELECT * FROM cleaning_client_schedules WHERE id = $1 AND business_id = $2",
        schedule_id, business_id,
    )
    return _schedule_to_dict(row) if row else None


async def update_schedule(
    db: Database,
    business_id: str,
    schedule_id: str,
    data: dict,
) -> Optional[dict]:
    """Update schedule fields. Recomputes next_occurrence if frequency changes."""
    valid_columns = {
        "frequency", "custom_interval_days", "preferred_day_of_week",
        "preferred_time_start", "preferred_time_end", "preferred_team_id",
        "agreed_price", "estimated_duration_minutes", "min_team_size",
        "next_occurrence", "notes", "status",
    }

    update_data = {k: v for k, v in data.items() if k in valid_columns and v is not None}

    if not update_data:
        return await get_schedule(db, business_id, schedule_id)

    # If frequency changed, recompute next_occurrence
    if "frequency" in update_data and "next_occurrence" not in update_data:
        new_next = compute_next_occurrence(
            frequency=update_data["frequency"],
            preferred_day_of_week=update_data.get("preferred_day_of_week")
                or data.get("preferred_day_of_week"),
            custom_interval_days=update_data.get("custom_interval_days"),
        )
        if new_next:
            update_data["next_occurrence"] = str(new_next)

    # Build SET clause with type casts for time/date columns
    set_parts = []
    values = []
    idx = 1
    for col, val in update_data.items():
        if col in ("preferred_time_start", "preferred_time_end"):
            set_parts.append(f"{col} = ${idx}")
            val = to_time(val)
        elif col == "next_occurrence":
            set_parts.append(f"{col} = ${idx}")
            val = to_date(val)
        else:
            set_parts.append(f"{col} = ${idx}")
        values.append(val)
        idx += 1

    values.extend([schedule_id, business_id])
    row = await db.pool.fetchrow(
        f"""UPDATE cleaning_client_schedules
            SET {', '.join(set_parts)}, updated_at = NOW()
            WHERE id = ${idx} AND business_id = ${idx + 1}
            RETURNING *""",
        *values,
    )

    return _schedule_to_dict(row) if row else None


async def pause_schedule(
    db: Database,
    business_id: str,
    schedule_id: str,
) -> Optional[dict]:
    """Pause an active schedule."""
    row = await db.pool.fetchrow(
        """UPDATE cleaning_client_schedules
           SET status = 'paused', updated_at = NOW()
           WHERE id = $1 AND business_id = $2 AND status = 'active'
           RETURNING *""",
        schedule_id, business_id,
    )
    return _schedule_to_dict(row) if row else None


async def resume_schedule(
    db: Database,
    business_id: str,
    schedule_id: str,
) -> Optional[dict]:
    """Resume a paused schedule, recomputing next_occurrence."""
    current = await db.pool.fetchrow(
        "SELECT * FROM cleaning_client_schedules WHERE id = $1 AND business_id = $2 AND status = 'paused'",
        schedule_id, business_id,
    )
    if not current:
        return None

    # Recompute next_occurrence from today
    new_next = compute_next_occurrence(
        frequency=current["frequency"],
        preferred_day_of_week=current["preferred_day_of_week"],
        custom_interval_days=current["custom_interval_days"],
    )

    row = await db.pool.fetchrow(
        """UPDATE cleaning_client_schedules
           SET status = 'active', next_occurrence = $3, updated_at = NOW()
           WHERE id = $1 AND business_id = $2
           RETURNING *""",
        schedule_id, business_id, to_date(new_next) if new_next else None,
    )
    return _schedule_to_dict(row) if row else None


async def cancel_schedule(
    db: Database,
    business_id: str,
    schedule_id: str,
) -> bool:
    """Cancel (soft delete) a schedule."""
    result = await db.pool.execute(
        """UPDATE cleaning_client_schedules
           SET status = 'cancelled', updated_at = NOW()
           WHERE id = $1 AND business_id = $2 AND status IN ('active', 'paused')""",
        schedule_id, business_id,
    )
    return result != "UPDATE 0"


async def list_client_schedules(
    db: Database,
    business_id: str,
    client_id: str,
    include_cancelled: bool = False,
) -> dict:
    """List all schedules for a client."""
    conditions = ["business_id = $1", "client_id = $2"]
    params = [business_id, client_id]

    if not include_cancelled:
        conditions.append("status != 'cancelled'")

    where = " AND ".join(conditions)
    rows = await db.pool.fetch(
        f"SELECT * FROM cleaning_client_schedules WHERE {where} ORDER BY created_at DESC",
        *params,
    )

    total = len(rows)
    schedules = [_schedule_to_dict(r) for r in rows]

    return {"schedules": schedules, "total": total}


async def list_schedules_due_on(
    db: Database,
    business_id: str,
    target_date: date,
) -> list[dict]:
    """
    List all active schedules due on a specific date.
    Used by the schedule engine to generate daily bookings.
    """
    rows = await db.pool.fetch(
        """SELECT cs.*, c.first_name, c.last_name, c.address_line1, c.city
           FROM cleaning_client_schedules cs
           JOIN cleaning_clients c ON c.id = cs.client_id
           WHERE cs.business_id = $1
             AND cs.next_occurrence <= $2
             AND cs.status = 'active'
           ORDER BY cs.preferred_time_start ASC NULLS LAST""",
        business_id, target_date,
    )
    return [_schedule_to_dict(r) for r in rows]


# ============================================
# HELPERS
# ============================================

def _schedule_to_dict(row) -> dict:
    """Convert schedule row to serializable dict."""
    if not row:
        return {}

    d = dict(row)

    # UUID to str
    for key in ["id", "business_id", "client_id", "service_id", "preferred_team_id"]:
        if d.get(key) is not None:
            d[key] = str(d[key])

    # Dates/times to str
    for key in ["created_at", "updated_at"]:
        if d.get(key) is not None:
            d[key] = str(d[key])

    if d.get("next_occurrence") is not None:
        d["next_occurrence"] = str(d["next_occurrence"])

    for key in ["preferred_time_start", "preferred_time_end"]:
        if d.get(key) is not None:
            d["preferred_time_end" if key == "preferred_time_end" else key] = str(d[key])

    # Numeric
    if d.get("agreed_price") is not None:
        d["agreed_price"] = float(d["agreed_price"])

    return d
