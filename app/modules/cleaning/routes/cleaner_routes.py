"""
Xcleaners v3 — Cleaner Routes (Sprint 3).

Endpoints for the cleaner/team-member experience:
  GET  /api/v1/clean/{slug}/my-jobs/today             — today's jobs
  GET  /api/v1/clean/{slug}/my-jobs/{booking_id}       — job detail
  POST /api/v1/clean/{slug}/my-jobs/{booking_id}/checkin   — check-in with GPS
  POST /api/v1/clean/{slug}/my-jobs/{booking_id}/checkout  — check-out
  POST /api/v1/clean/{slug}/my-jobs/{booking_id}/checklist/{item_id}/complete — complete checklist item
  POST /api/v1/clean/{slug}/my-jobs/{booking_id}/note  — add note/photo
  POST /api/v1/clean/{slug}/my-jobs/{booking_id}/issue — report issue
  GET  /api/v1/clean/{slug}/my-schedule                — week schedule
  GET  /api/v1/clean/{slug}/my-earnings                — earnings summary

All protected by require_role("cleaner", "team_lead").
"""

import logging
from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.services.cleaner_service import (
    get_today_jobs,
    get_job_detail,
    check_in,
    check_out,
    complete_checklist_item,
    add_job_note,
    report_issue,
    get_my_schedule,
    get_my_earnings,
)

logger = logging.getLogger("xcleaners.cleaner_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}",
    tags=["Xcleaners Cleaner"],
)


# ============================================
# REQUEST MODELS
# ============================================

class CheckInRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None


class CheckOutRequest(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    notes: Optional[str] = None


class JobNoteRequest(BaseModel):
    note: Optional[str] = None
    photo_url: Optional[str] = Field(None, max_length=2048, pattern=r'^https?://')


class ReportIssueRequest(BaseModel):
    issue_type: str = Field(
        ...,
        description="Type: locked_out, pet_problem, damage_found, supplies_needed, client_not_home, other"
    )
    description: str = Field(..., min_length=1, max_length=2000)


# ============================================
# HELPER: resolve team member
# ============================================

async def _resolve_team_member(user: dict, db: Database) -> str:
    """Get the cleaning_team_members.id for the current user."""
    member = await db.pool.fetchrow(
        """SELECT id FROM cleaning_team_members
           WHERE user_id = $1 AND business_id = $2 AND status = 'active'
           LIMIT 1""",
        user["user_id"], user["business_id"],
    )
    if not member:
        raise HTTPException(
            status_code=403,
            detail="Your team member profile was not found. Contact your employer.",
        )
    return str(member["id"])


# ============================================
# GET /my-jobs/today
# ============================================

@router.get("/my-jobs/today")
async def today_jobs_route(
    slug: str,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Get today's jobs for the cleaner's team."""
    team_id = user.get("cleaning_team_id")
    if not team_id:
        raise HTTPException(status_code=403, detail="You are not assigned to a team.")

    team_member_id = await _resolve_team_member(user, db)
    result = await get_today_jobs(db, user["business_id"], team_member_id, team_id)
    return result


# ============================================
# GET /my-jobs/{booking_id}
# ============================================

@router.get("/my-jobs/{booking_id}")
async def job_detail_route(
    slug: str,
    booking_id: str,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Get full job detail with client info, checklist, notes."""
    team_id = user.get("cleaning_team_id")
    if not team_id:
        raise HTTPException(status_code=403, detail="You are not assigned to a team.")

    team_member_id = await _resolve_team_member(user, db)
    result = await get_job_detail(db, user["business_id"], booking_id, team_member_id, team_id)

    if not result:
        raise HTTPException(status_code=404, detail="Job not found or not assigned to your team.")

    return result


# ============================================
# POST /my-jobs/{booking_id}/checkin
# ============================================

@router.post("/my-jobs/{booking_id}/checkin")
async def checkin_route(
    slug: str,
    booking_id: str,
    body: CheckInRequest,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """GPS-verified check-in to a job."""
    team_id = user.get("cleaning_team_id")
    if not team_id:
        raise HTTPException(status_code=403, detail="You are not assigned to a team.")

    team_member_id = await _resolve_team_member(user, db)
    result = await check_in(
        db, user["business_id"], booking_id, team_member_id, team_id,
        lat=body.lat, lng=body.lng,
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    return result


# ============================================
# POST /my-jobs/{booking_id}/checkout
# ============================================

@router.post("/my-jobs/{booking_id}/checkout")
async def checkout_route(
    slug: str,
    booking_id: str,
    body: CheckOutRequest,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Check-out from a job."""
    team_id = user.get("cleaning_team_id")
    if not team_id:
        raise HTTPException(status_code=403, detail="You are not assigned to a team.")

    team_member_id = await _resolve_team_member(user, db)
    result = await check_out(
        db, user["business_id"], booking_id, team_member_id, team_id,
        lat=body.lat, lng=body.lng, notes=body.notes,
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    return result


# ============================================
# POST /my-jobs/{booking_id}/checklist/{item_id}/complete
# ============================================

@router.post("/my-jobs/{booking_id}/checklist/{item_id}/complete")
async def complete_checklist_route(
    slug: str,
    booking_id: str,
    item_id: str,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Mark a checklist item as completed."""
    team_member_id = await _resolve_team_member(user, db)
    result = await complete_checklist_item(
        db, user["business_id"], booking_id, item_id, team_member_id,
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    return result


# ============================================
# POST /my-jobs/{booking_id}/note
# ============================================

@router.post("/my-jobs/{booking_id}/note")
async def add_note_route(
    slug: str,
    booking_id: str,
    body: JobNoteRequest,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Add a note or photo to a job."""
    team_member_id = await _resolve_team_member(user, db)
    result = await add_job_note(
        db, user["business_id"], booking_id, team_member_id,
        note=body.note, photo_url=body.photo_url,
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    return result


# ============================================
# POST /my-jobs/{booking_id}/issue
# ============================================

@router.post("/my-jobs/{booking_id}/issue")
async def report_issue_route(
    slug: str,
    booking_id: str,
    body: ReportIssueRequest,
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Report an issue during a job."""
    team_member_id = await _resolve_team_member(user, db)
    result = await report_issue(
        db, user["business_id"], booking_id, team_member_id,
        issue_type=body.issue_type, description=body.description,
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status_code"], detail=result["message"])

    return result


# ============================================
# GET /my-schedule
# ============================================

@router.get("/my-schedule")
async def my_schedule_route(
    slug: str,
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Get the team's weekly schedule."""
    team_id = user.get("cleaning_team_id")
    if not team_id:
        raise HTTPException(status_code=403, detail="You are not assigned to a team.")

    today = date.today()
    if start:
        try:
            start_date = date.fromisoformat(start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start date format.")
    else:
        start_date = today - timedelta(days=today.weekday())

    if end:
        try:
            end_date = date.fromisoformat(end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end date format.")
    else:
        end_date = start_date + timedelta(days=6)

    result = await get_my_schedule(db, user["business_id"], team_id, start_date, end_date)
    return result


# ============================================
# GET /my-earnings
# ============================================

@router.get("/my-earnings")
async def my_earnings_route(
    slug: str,
    period: str = Query("week", description="Period: week, month, year"),
    user: dict = Depends(require_role("cleaner", "team_lead")),
    db: Database = Depends(get_db),
):
    """Get earnings summary."""
    team_id = user.get("cleaning_team_id")
    if not team_id:
        raise HTTPException(status_code=403, detail="You are not assigned to a team.")

    team_member_id = await _resolve_team_member(user, db)

    if period not in ("week", "month", "year"):
        raise HTTPException(status_code=400, detail="Period must be 'week', 'month', or 'year'.")

    result = await get_my_earnings(db, user["business_id"], team_member_id, team_id, period)
    return result
