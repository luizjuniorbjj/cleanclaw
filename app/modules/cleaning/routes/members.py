"""
CleanClaw v3 — Team Member Routes.

CRUD endpoints for cleaning team members (individual cleaners).
Separated from teams.py for clarity as per S2.2 story.

Endpoints:
  GET    /api/v1/clean/{slug}/members                        — list all members
  POST   /api/v1/clean/{slug}/members                        — create member
  GET    /api/v1/clean/{slug}/members/{id}                   — get member detail
  PATCH  /api/v1/clean/{slug}/members/{id}                   — update member
  DELETE /api/v1/clean/{slug}/members/{id}                   — deactivate (terminate)
  PATCH  /api/v1/clean/{slug}/members/{id}/availability      — set availability
  POST   /api/v1/clean/{slug}/members/{id}/exception         — add exception
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.services.team_service import (
    add_availability_exception,
    create_member,
    delete_member,
    get_member,
    list_members,
    set_member_availability,
    update_member,
)

logger = logging.getLogger("cleanclaw.member_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}/members",
    tags=["CleanClaw Members"],
)


# ============================================
# Pydantic models for member-specific requests
# ============================================

class MemberCreate(BaseModel):
    """Create a new team member."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = Field(default="cleaner", pattern=r"^(cleaner|lead_cleaner|supervisor|manager)$")
    employment_type: str = Field(default="employee", pattern=r"^(employee|contractor|part_time)$")
    hourly_rate: Optional[float] = Field(None, ge=0)
    skills: list[str] = Field(default_factory=list)


class MemberUpdate(BaseModel):
    """Partial update for a team member."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(None, pattern=r"^(cleaner|lead_cleaner|supervisor|manager)$")
    employment_type: Optional[str] = Field(None, pattern=r"^(employee|contractor|part_time)$")
    hourly_rate: Optional[float] = Field(None, ge=0)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    max_daily_hours: Optional[float] = Field(None, ge=1, le=24)
    can_drive: Optional[bool] = None
    home_zip: Optional[str] = None
    notes: Optional[str] = None
    certifications: Optional[list[str]] = None
    status: Optional[str] = Field(None, pattern=r"^(active|inactive|on_leave|terminated)$")


class AvailabilityRule(BaseModel):
    """Weekly availability rule."""
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., description="HH:MM format")
    end_time: str = Field(..., description="HH:MM format")
    is_available: bool = True


class AvailabilityException(BaseModel):
    """One-off availability exception (PTO, sick day)."""
    date: str = Field(..., description="ISO date: YYYY-MM-DD")
    reason: Optional[str] = Field(None, description="pto, sick, personal, other")
    is_full_day: bool = True
    start_time: Optional[str] = None
    end_time: Optional[str] = None


# ============================================
# GET /api/v1/clean/{slug}/members
# ============================================

@router.get("")
async def list_members_route(
    slug: str,
    include_inactive: bool = Query(False),
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """List all team members for this business."""
    result = await list_members(db, user["business_id"], include_inactive)
    return result


# ============================================
# POST /api/v1/clean/{slug}/members
# ============================================

@router.post("", status_code=201)
async def create_member_route(
    slug: str,
    body: MemberCreate,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Create a new team member."""
    data = body.model_dump()
    # Map skills to certifications (DB column name)
    if data.get("skills"):
        data["certifications"] = data.pop("skills")

    result = await create_member(db, user["business_id"], data)
    return result


# ============================================
# GET /api/v1/clean/{slug}/members/{member_id}
# ============================================

@router.get("/{member_id}")
async def get_member_route(
    slug: str,
    member_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Get member profile with stats and availability."""
    result = await get_member(db, user["business_id"], member_id)
    if not result:
        raise HTTPException(status_code=404, detail="Member not found.")
    return result


# ============================================
# PATCH /api/v1/clean/{slug}/members/{member_id}
# ============================================

@router.patch("/{member_id}")
async def update_member_route(
    slug: str,
    member_id: str,
    body: MemberUpdate,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Update a member's profile."""
    data = body.model_dump(exclude_unset=True)
    result = await update_member(db, user["business_id"], member_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Member not found.")
    return result


# ============================================
# DELETE /api/v1/clean/{slug}/members/{member_id}
# ============================================

@router.delete("/{member_id}")
async def delete_member_route(
    slug: str,
    member_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Deactivate a member (status=terminated). Preserves history."""
    result = await delete_member(db, user["business_id"], member_id)

    if result.get("not_found"):
        raise HTTPException(status_code=404, detail="Member not found.")

    return {"success": True, "message": "Member terminated."}


# ============================================
# PATCH /api/v1/clean/{slug}/members/{member_id}/availability
# ============================================

@router.patch("/{member_id}/availability")
async def set_availability_route(
    slug: str,
    member_id: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Set weekly default availability for a member. Replaces existing rules."""
    rules = body.get("rules", [])
    if not rules:
        raise HTTPException(status_code=400, detail="At least one availability rule is required.")

    # Validate each rule
    for i, rule in enumerate(rules):
        if "day_of_week" not in rule:
            raise HTTPException(status_code=400, detail=f"Rule {i+1}: day_of_week is required (0-6).")
        if "start_time" not in rule or "end_time" not in rule:
            raise HTTPException(status_code=400, detail=f"Rule {i+1}: start_time and end_time are required.")

    result = await set_member_availability(db, user["business_id"], member_id, rules)

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result


# ============================================
# POST /api/v1/clean/{slug}/members/{member_id}/exception
# ============================================

@router.post("/{member_id}/exception")
async def add_exception_route(
    slug: str,
    member_id: str,
    body: AvailabilityException,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Add an availability exception (PTO, sick day, personal)."""
    result = await add_availability_exception(
        db, user["business_id"], member_id, body.model_dump()
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result
