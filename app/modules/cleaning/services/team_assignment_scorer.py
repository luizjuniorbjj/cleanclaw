"""
CleanClaw v3 — Team Assignment Scorer (S2.4).

Scores every team for every job using the 5-factor weighted formula
from Architecture v3 Section 7.3.

Factors (total = 1.0):
  - area_match:       0.35  — team's service area includes client zip
  - workload_balance: 0.25  — inverse of team's current daily load
  - client_preference:0.20  — client's preferred_team_id matches
  - proximity:        0.10  — haversine distance to nearest assigned job
  - continuity:       0.10  — same team served this client last time
"""

import logging
from math import radians, sin, cos, sqrt, atan2
from typing import Optional

from app.database import Database

logger = logging.getLogger("cleanclaw.team_scorer")

# Maximum distance in miles for proximity scoring
MAX_PROXIMITY_MILES = 30.0


# ============================================
# HAVERSINE DISTANCE
# ============================================

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in miles using Haversine formula.

    Returns:
        Distance in miles
    """
    R = 3959  # Earth radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))


# ============================================
# INDIVIDUAL SCORING FACTORS
# ============================================

def compute_area_match(team: dict, job: dict) -> float:
    """
    Score area match: 1.0 if client zip in team's service area,
    0.5 if nearby, 0.0 if outside.

    For MVP, we do a simple zip code containment check against
    the team's service_area_zips. If no zip data, return 0.5 (neutral).
    """
    client_zip = job.get("zip_code") or ""
    team_zips = team.get("service_area_zips") or []

    if not client_zip or not team_zips:
        return 0.5  # Neutral when no area data

    if client_zip in team_zips:
        return 1.0

    # Check if zip is "nearby" (same 3-digit prefix)
    prefix = client_zip[:3]
    for tz in team_zips:
        if tz[:3] == prefix:
            return 0.5

    return 0.0


def compute_workload_balance(team: dict, existing_job_count: int) -> float:
    """
    Score workload balance: 1.0 - (jobs_today / max_daily_jobs).
    Team with 0/6 jobs = 1.0, team with 5/6 = 0.17.
    """
    max_jobs = team.get("max_daily_jobs", 6)
    if max_jobs <= 0:
        return 0.0
    score = 1.0 - (existing_job_count / max_jobs)
    return max(0.0, score)


def compute_client_preference(team_id: str, preferred_team_id: Optional[str]) -> float:
    """
    Score client preference: 1.0 if preferred_team_id matches, 0.0 otherwise.
    """
    if not preferred_team_id:
        return 0.0
    return 1.0 if team_id == preferred_team_id else 0.0


def compute_proximity(
    team_assignments: list[dict],
    job_lat: Optional[float],
    job_lon: Optional[float],
) -> float:
    """
    Score proximity: based on haversine distance to nearest assigned job.
    Score = max(0, 1.0 - distance / 30 miles).
    Returns 0.5 (neutral) if team has no prior assignments or no coords.
    """
    if job_lat is None or job_lon is None:
        return 0.5  # No coordinates available

    if not team_assignments:
        return 0.5  # No prior assignments today

    min_distance = float("inf")
    for assignment in team_assignments:
        a_lat = assignment.get("latitude")
        a_lon = assignment.get("longitude")
        if a_lat is not None and a_lon is not None:
            dist = haversine(job_lat, job_lon, a_lat, a_lon)
            min_distance = min(min_distance, dist)

    if min_distance == float("inf"):
        return 0.5  # No assignments with coordinates

    return max(0.0, 1.0 - min_distance / MAX_PROXIMITY_MILES)


def compute_continuity(team_id: str, last_team_id: Optional[str]) -> float:
    """
    Score continuity: 1.0 if same team served this client last time.
    """
    if not last_team_id:
        return 0.0
    return 1.0 if team_id == last_team_id else 0.0


# ============================================
# COMPOSITE SCORER
# ============================================

def score_team_for_job(
    team: dict,
    job: dict,
    existing_assignments: list[dict],
    existing_job_count: int,
    last_team_id: Optional[str] = None,
) -> dict:
    """
    Compute weighted score for assigning a team to a job.

    Args:
        team: dict with id, max_daily_jobs, service_area_zips
        job: dict with zip_code, latitude, longitude, preferred_team_id
        existing_assignments: list of already-assigned jobs for this team today
                             (each with latitude, longitude)
        existing_job_count: number of jobs already assigned to this team today
        last_team_id: team_id that served this client last time (for continuity)

    Returns:
        dict with total_score, breakdown of individual factor scores
    """
    team_id = team["id"]

    area = compute_area_match(team, job)
    workload = compute_workload_balance(team, existing_job_count)
    preference = compute_client_preference(team_id, job.get("preferred_team_id"))
    proximity = compute_proximity(
        existing_assignments,
        job.get("latitude"),
        job.get("longitude"),
    )
    continuity = compute_continuity(team_id, last_team_id)

    total = (
        area * 0.35
        + workload * 0.25
        + preference * 0.20
        + proximity * 0.10
        + continuity * 0.10
    )

    return {
        "team_id": team_id,
        "total_score": round(total, 4),
        "breakdown": {
            "area_match": round(area, 4),
            "workload_balance": round(workload, 4),
            "client_preference": round(preference, 4),
            "proximity": round(proximity, 4),
            "continuity": round(continuity, 4),
        },
    }


async def get_last_team_for_client(
    db: Database,
    business_id: str,
    client_id: str,
) -> Optional[str]:
    """
    Find the team_id that last served this client (most recent completed booking).
    """
    row = await db.pool.fetchrow(
        """
        SELECT team_id FROM cleaning_bookings
        WHERE business_id = $1
          AND client_id = $2
          AND team_id IS NOT NULL
          AND status IN ('completed', 'in_progress', 'confirmed', 'scheduled')
        ORDER BY scheduled_date DESC, created_at DESC
        LIMIT 1
        """,
        business_id,
        client_id,
    )
    return str(row["team_id"]) if row and row["team_id"] else None
