"""
Xcleaners v3 — Conflict Resolver (S2.4).

Detects scheduling conflicts within a team's daily assignments:
  - Time slot overlaps
  - Exceeding max_jobs_per_day
  - Insufficient team members for min_team_size
  - Travel buffer violations

Returns conflicts with suggested resolutions.
"""

import logging
from datetime import time, timedelta, datetime
from typing import Optional

logger = logging.getLogger("xcleaners.conflict_resolver")


# ============================================
# CONFLICT TYPES
# ============================================

CONFLICT_TIME_OVERLAP = "time_overlap"
CONFLICT_MAX_JOBS = "max_jobs_exceeded"
CONFLICT_MIN_TEAM_SIZE = "insufficient_team_members"
CONFLICT_TRAVEL_BUFFER = "travel_buffer_violation"


# ============================================
# TIME PARSING HELPERS
# ============================================

def _parse_time(t) -> Optional[time]:
    """Parse a time value from various formats."""
    if t is None:
        return None
    if isinstance(t, time):
        return t
    if isinstance(t, str):
        parts = t.split(":")
        if len(parts) >= 2:
            return time(int(parts[0]), int(parts[1]))
    return None


def _time_to_minutes(t: time) -> int:
    """Convert time to minutes since midnight."""
    return t.hour * 60 + t.minute


def _minutes_to_time_str(minutes: int) -> str:
    """Convert minutes since midnight to HH:MM string."""
    h = min(23, minutes // 60)
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


# ============================================
# CONFLICT DETECTION
# ============================================

def detect_time_overlaps(assignments: list[dict]) -> list[dict]:
    """
    Detect overlapping time slots within a list of assignments for the same team.

    Each assignment must have: id, scheduled_start, scheduled_end or estimated_duration_minutes.

    Returns:
        List of conflict dicts
    """
    conflicts = []

    # Build time slots
    slots = []
    for a in assignments:
        start = _parse_time(a.get("scheduled_start"))
        if start is None:
            continue

        end = _parse_time(a.get("scheduled_end"))
        if end is None:
            duration = a.get("estimated_duration_minutes", 120)
            start_min = _time_to_minutes(start)
            end_min = start_min + duration
            end = time(min(23, end_min // 60), end_min % 60)

        slots.append({
            "id": a.get("id", a.get("booking_id", "")),
            "client_id": a.get("client_id", ""),
            "start": start,
            "end": end,
        })

    # Sort by start time
    slots.sort(key=lambda s: _time_to_minutes(s["start"]))

    # Check consecutive pairs for overlap
    for i in range(len(slots) - 1):
        current = slots[i]
        next_slot = slots[i + 1]
        if _time_to_minutes(current["end"]) > _time_to_minutes(next_slot["start"]):
            overlap_minutes = (
                _time_to_minutes(current["end"]) - _time_to_minutes(next_slot["start"])
            )
            conflicts.append({
                "type": CONFLICT_TIME_OVERLAP,
                "job_a_id": str(current["id"]),
                "job_b_id": str(next_slot["id"]),
                "overlap_minutes": overlap_minutes,
                "detail": (
                    f"Job {str(current['id'])[:8]} ends at {current['end'].strftime('%H:%M')} "
                    f"but job {str(next_slot['id'])[:8]} starts at {next_slot['start'].strftime('%H:%M')} "
                    f"({overlap_minutes}min overlap)"
                ),
                "resolution_suggestions": [
                    f"Move job {str(next_slot['id'])[:8]} to start at {current['end'].strftime('%H:%M')} or later",
                    f"Reassign one of the jobs to a different team",
                ],
            })

    return conflicts


def detect_max_jobs_exceeded(
    team: dict,
    job_count: int,
) -> Optional[dict]:
    """
    Check if team has been assigned more jobs than max_daily_jobs.

    Returns:
        Conflict dict or None
    """
    max_jobs = team.get("max_daily_jobs", 6)
    if job_count > max_jobs:
        return {
            "type": CONFLICT_MAX_JOBS,
            "team_id": str(team["id"]),
            "assigned_count": job_count,
            "max_allowed": max_jobs,
            "detail": (
                f"Team '{team.get('name', 'Unknown')}' has {job_count} jobs "
                f"but max is {max_jobs}"
            ),
            "resolution_suggestions": [
                f"Reassign {job_count - max_jobs} job(s) to other teams",
                f"Increase team's max_daily_jobs if capacity allows",
            ],
        }
    return None


def detect_insufficient_team_size(
    team: dict,
    available_members: int,
    job: dict,
) -> Optional[dict]:
    """
    Check if team has enough available members for the job's min_team_size.

    Returns:
        Conflict dict or None
    """
    min_size = job.get("min_team_size", 1)
    if available_members < min_size:
        return {
            "type": CONFLICT_MIN_TEAM_SIZE,
            "team_id": str(team["id"]),
            "job_id": str(job.get("id", job.get("schedule_id", ""))),
            "available_members": available_members,
            "required_members": min_size,
            "detail": (
                f"Team '{team.get('name', 'Unknown')}' has {available_members} "
                f"available members but job requires {min_size}"
            ),
            "resolution_suggestions": [
                f"Add members to the team for this date",
                f"Reassign job to a team with {min_size}+ members",
                f"Adjust job's minimum team size requirement",
            ],
        }
    return None


def detect_travel_buffer_violations(
    assignments: list[dict],
    travel_buffer_same_zip: int = 15,
    travel_buffer_diff_zip: int = 30,
) -> list[dict]:
    """
    Check consecutive jobs for travel buffer violations.

    Args:
        assignments: sorted list of assignments for one team
        travel_buffer_same_zip: minutes buffer for same zip code (default 15)
        travel_buffer_diff_zip: minutes buffer for different zip codes (default 30)

    Returns:
        List of conflict dicts
    """
    conflicts = []

    # Sort by start time
    sorted_assignments = sorted(
        assignments,
        key=lambda a: _time_to_minutes(_parse_time(a.get("scheduled_start")) or time(0, 0)),
    )

    for i in range(len(sorted_assignments) - 1):
        current = sorted_assignments[i]
        next_job = sorted_assignments[i + 1]

        current_end = _parse_time(current.get("scheduled_end"))
        if current_end is None:
            start = _parse_time(current.get("scheduled_start"))
            if start is None:
                continue
            duration = current.get("estimated_duration_minutes", 120)
            end_min = _time_to_minutes(start) + duration
            current_end = time(min(23, end_min // 60), end_min % 60)

        next_start = _parse_time(next_job.get("scheduled_start"))
        if next_start is None:
            continue

        # Determine required buffer
        current_zip = current.get("zip_code", "")
        next_zip = next_job.get("zip_code", "")
        same_zip = current_zip and next_zip and current_zip == next_zip
        required_buffer = travel_buffer_same_zip if same_zip else travel_buffer_diff_zip

        # Check gap
        gap_minutes = _time_to_minutes(next_start) - _time_to_minutes(current_end)

        if gap_minutes < required_buffer:
            shortfall = required_buffer - gap_minutes
            suggested_start = _time_to_minutes(current_end) + required_buffer
            conflicts.append({
                "type": CONFLICT_TRAVEL_BUFFER,
                "job_a_id": str(current.get("id", current.get("booking_id", ""))),
                "job_b_id": str(next_job.get("id", next_job.get("booking_id", ""))),
                "gap_minutes": gap_minutes,
                "required_buffer": required_buffer,
                "same_zip": same_zip,
                "detail": (
                    f"Only {gap_minutes}min gap between jobs "
                    f"({'same' if same_zip else 'different'} zip) — "
                    f"need {required_buffer}min buffer"
                ),
                "resolution_suggestions": [
                    f"Move next job to start at {_minutes_to_time_str(suggested_start)}",
                    f"Swap job order if it reduces travel",
                    f"Reassign one job to a different team",
                ],
            })

    return conflicts


# ============================================
# FULL CONFLICT SCAN
# ============================================

def detect_all_conflicts(
    team: dict,
    assignments: list[dict],
    available_members: int,
    travel_buffer_same_zip: int = 15,
    travel_buffer_diff_zip: int = 30,
) -> list[dict]:
    """
    Run all conflict detectors for a team's daily assignments.

    Args:
        team: team dict with id, name, max_daily_jobs
        assignments: list of assignments for this team on this date
        available_members: count of team members available on this date
        travel_buffer_same_zip: minutes buffer for same zip
        travel_buffer_diff_zip: minutes buffer for different zips

    Returns:
        List of all detected conflicts
    """
    conflicts = []

    # 1. Max jobs exceeded
    max_conflict = detect_max_jobs_exceeded(team, len(assignments))
    if max_conflict:
        max_conflict["team_id"] = str(team["id"])
        conflicts.append(max_conflict)

    # 2. Time overlaps
    overlaps = detect_time_overlaps(assignments)
    for c in overlaps:
        c["team_id"] = str(team["id"])
    conflicts.extend(overlaps)

    # 3. Insufficient team size (per job)
    for assignment in assignments:
        size_conflict = detect_insufficient_team_size(team, available_members, assignment)
        if size_conflict:
            conflicts.append(size_conflict)

    # 4. Travel buffer violations
    travel = detect_travel_buffer_violations(
        assignments,
        travel_buffer_same_zip,
        travel_buffer_diff_zip,
    )
    for c in travel:
        c["team_id"] = str(team["id"])
    conflicts.extend(travel)

    return conflicts
