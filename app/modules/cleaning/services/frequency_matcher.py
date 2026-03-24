"""
CleanClaw v3 — Frequency Matcher (S2.4).

Determines which recurring client schedules fall on a given date.
Used by the daily schedule generator to collect jobs for a target date.

Supported frequencies: weekly, biweekly, monthly, sporadic.
"""

import logging
from datetime import date, timedelta
from typing import Optional

logger = logging.getLogger("cleanclaw.frequency_matcher")


def matches_date(schedule: dict, target_date: date) -> bool:
    """
    Check if a recurring schedule is due on target_date.

    Args:
        schedule: dict with keys: frequency, preferred_day_of_week,
                  custom_interval_days, created_at, next_occurrence
        target_date: the date to check

    Returns:
        True if the schedule is due on target_date
    """
    frequency = schedule.get("frequency", "")
    preferred_dow = schedule.get("preferred_day_of_week")

    # Convert target_date weekday: Python 0=Mon..6=Sun -> DB 0=Sun..6=Sat
    target_dow = (target_date.isoweekday() % 7)

    if frequency == "weekly":
        if preferred_dow is None:
            return False
        return target_dow == preferred_dow

    elif frequency == "biweekly":
        if preferred_dow is None:
            return False
        if target_dow != preferred_dow:
            return False
        # Use schedule creation date as epoch for bi-weekly counting
        created_at = schedule.get("created_at")
        if created_at is None:
            return False
        if isinstance(created_at, str):
            # Parse date from string (may be datetime or date)
            created_at = date.fromisoformat(str(created_at)[:10])
        elif hasattr(created_at, "date"):
            created_at = created_at.date()
        days_since = (target_date - created_at).days
        return days_since >= 0 and (days_since % 14) < 7

    elif frequency == "monthly":
        # preferred_day_of_week is repurposed as preferred day-of-month
        # for monthly schedules (per architecture spec)
        preferred_day = preferred_dow
        if preferred_day is None:
            return False
        # Handle short months: if preferred day > days in month, use last day
        import calendar
        max_day = calendar.monthrange(target_date.year, target_date.month)[1]
        effective_day = min(preferred_day, max_day) if preferred_day > 0 else max_day
        return target_date.day == effective_day

    elif frequency == "sporadic":
        # Sporadic schedules are only due on their explicit next_occurrence
        next_occ = schedule.get("next_occurrence")
        if next_occ is None:
            return False
        if isinstance(next_occ, str):
            next_occ = date.fromisoformat(next_occ[:10])
        elif hasattr(next_occ, "date"):
            next_occ = next_occ.date() if not isinstance(next_occ, date) else next_occ
        return target_date == next_occ

    return False


def compute_next_occurrence(
    schedule: dict,
    from_date: Optional[date] = None,
) -> Optional[date]:
    """
    Calculate the next occurrence date for a schedule after from_date.

    Args:
        schedule: dict with frequency, preferred_day_of_week,
                  custom_interval_days, created_at
        from_date: starting reference date (defaults to today)

    Returns:
        Next occurrence date, or None if cannot compute
    """
    if from_date is None:
        from_date = date.today()

    frequency = schedule.get("frequency", "")
    preferred_dow = schedule.get("preferred_day_of_week")

    if frequency == "weekly":
        if preferred_dow is None:
            return from_date + timedelta(days=7)
        # Find next occurrence of preferred day after from_date
        current_dow = from_date.isoweekday() % 7  # 0=Sun
        days_ahead = (preferred_dow - current_dow) % 7
        if days_ahead == 0:
            days_ahead = 7  # Next week if today is the day
        return from_date + timedelta(days=days_ahead)

    elif frequency == "biweekly":
        if preferred_dow is None:
            return from_date + timedelta(days=14)
        # Find next biweekly occurrence
        created_at = schedule.get("created_at")
        if isinstance(created_at, str):
            created_at = date.fromisoformat(str(created_at)[:10])
        elif hasattr(created_at, "date"):
            created_at = created_at.date()

        # Start from from_date + 1 and scan for next matching date
        candidate = from_date + timedelta(days=1)
        for _ in range(30):  # Max 30 days to find next biweekly
            candidate_dow = candidate.isoweekday() % 7
            if candidate_dow == preferred_dow:
                if created_at:
                    days_since = (candidate - created_at).days
                    if days_since >= 0 and (days_since % 14) < 7:
                        return candidate
                else:
                    return candidate
            candidate += timedelta(days=1)
        # Fallback
        return from_date + timedelta(days=14)

    elif frequency == "monthly":
        import calendar
        preferred_day = preferred_dow if preferred_dow else from_date.day
        # Next month
        year = from_date.year
        month = from_date.month + 1
        if month > 12:
            month = 1
            year += 1
        max_day = calendar.monthrange(year, month)[1]
        effective_day = min(preferred_day, max_day) if preferred_day > 0 else max_day
        next_date = date(year, month, effective_day)
        # If from_date is before the target day this month, use this month
        if from_date.day < preferred_day:
            max_day_this = calendar.monthrange(from_date.year, from_date.month)[1]
            day_this = min(preferred_day, max_day_this) if preferred_day > 0 else max_day_this
            candidate_this = date(from_date.year, from_date.month, day_this)
            if candidate_this > from_date:
                return candidate_this
        return next_date

    elif frequency == "sporadic":
        interval = schedule.get("custom_interval_days") or 30
        return from_date + timedelta(days=interval)

    return None
