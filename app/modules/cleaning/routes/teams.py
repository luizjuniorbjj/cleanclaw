"""
CleanClaw v3 — Team Management Routes.

CRUD endpoints for teams, team members, assignments, and invitations.
All endpoints require owner role.

Endpoints:
  GET    /api/v1/clean/{slug}/teams                          — list teams
  POST   /api/v1/clean/{slug}/teams                          — create team
  GET    /api/v1/clean/{slug}/teams/{id}                     — get team detail
  PATCH  /api/v1/clean/{slug}/teams/{id}                     — update team
  DELETE /api/v1/clean/{slug}/teams/{id}                     — deactivate team
  POST   /api/v1/clean/{slug}/teams/{id}/members             — assign member to team
  DELETE /api/v1/clean/{slug}/teams/{id}/members/{member_id} — remove member
  POST   /api/v1/clean/{slug}/teams/{id}/lead/{member_id}    — set team lead
  POST   /api/v1/clean/{slug}/team/invite                    — invite cleaner by email
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.models.teams import (
    TeamCreate,
    TeamUpdate,
    TeamAssignmentCreate,
)
from app.modules.cleaning.services.team_service import (
    assign_member_to_team,
    create_team,
    delete_team,
    get_team,
    invite_cleaner,
    list_teams,
    remove_member_from_team,
    set_team_lead,
    update_team,
)

logger = logging.getLogger("cleanclaw.team_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}",
    tags=["CleanClaw Teams"],
)


# ============================================
# GET /api/v1/clean/{slug}/teams
# ============================================

@router.get("/teams")
async def list_teams_route(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """List all teams with member count and today's stats."""
    result = await list_teams(db, user["business_id"])
    return result


# ============================================
# POST /api/v1/clean/{slug}/teams
# ============================================

@router.post("/teams", status_code=201)
async def create_team_route(
    slug: str,
    body: TeamCreate,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Create a new cleaning team."""
    result = await create_team(db, user["business_id"], body.model_dump())

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result


# ============================================
# GET /api/v1/clean/{slug}/teams/{team_id}
# ============================================

@router.get("/teams/{team_id}")
async def get_team_route(
    slug: str,
    team_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Get team details with members and stats."""
    result = await get_team(db, user["business_id"], team_id)
    if not result:
        raise HTTPException(status_code=404, detail="Team not found.")
    return result


# ============================================
# PATCH /api/v1/clean/{slug}/teams/{team_id}
# ============================================

@router.patch("/teams/{team_id}")
async def update_team_route(
    slug: str,
    team_id: str,
    body: TeamUpdate,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Update a team."""
    data = body.model_dump(exclude_unset=True)
    result = await update_team(db, user["business_id"], team_id, data)

    if not result:
        raise HTTPException(status_code=404, detail="Team not found.")

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result


# ============================================
# DELETE /api/v1/clean/{slug}/teams/{team_id}
# ============================================

@router.delete("/teams/{team_id}")
async def delete_team_route(
    slug: str,
    team_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Deactivate a team. Returns 409 if team has future bookings."""
    result = await delete_team(db, user["business_id"], team_id)

    if result.get("not_found"):
        raise HTTPException(status_code=404, detail="Team not found.")

    if result.get("conflict"):
        raise HTTPException(status_code=409, detail=result["message"])

    return {"success": True, "message": "Team deactivated."}


# ============================================
# POST /api/v1/clean/{slug}/teams/{team_id}/members
# ============================================

@router.post("/teams/{team_id}/members", status_code=201)
async def assign_member_route(
    slug: str,
    team_id: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Assign a member to a team."""
    member_id = body.get("member_id")
    if not member_id:
        raise HTTPException(status_code=400, detail="member_id is required.")

    role_in_team = body.get("role_in_team", "member")
    if role_in_team not in ("lead", "member", "trainee"):
        raise HTTPException(status_code=400, detail="role_in_team must be 'lead', 'member', or 'trainee'.")

    result = await assign_member_to_team(
        db, user["business_id"], team_id, member_id, role_in_team
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result


# ============================================
# DELETE /api/v1/clean/{slug}/teams/{team_id}/members/{member_id}
# ============================================

@router.delete("/teams/{team_id}/members/{member_id}")
async def remove_member_route(
    slug: str,
    team_id: str,
    member_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Remove a member from a team."""
    result = await remove_member_from_team(db, user["business_id"], team_id, member_id)

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return {"success": True, "message": "Member removed from team."}


# ============================================
# POST /api/v1/clean/{slug}/teams/{team_id}/lead/{member_id}
# ============================================

@router.post("/teams/{team_id}/lead/{member_id}")
async def set_team_lead_route(
    slug: str,
    team_id: str,
    member_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Set a member as team lead."""
    result = await set_team_lead(db, user["business_id"], team_id, member_id)

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result


# ============================================
# POST /api/v1/clean/{slug}/team/invite
# ============================================

@router.post("/team/invite", status_code=201)
async def invite_cleaner_route(
    slug: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Invite a cleaner by email. Creates placeholder member and sends invite link."""
    email = body.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email is required.")

    result = await invite_cleaner(
        db,
        user["business_id"],
        slug,
        body,
        user["user_id"],
    )

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(status_code=result["status"], detail=result["message"])

    return result
