"""
CleanClaw v3 — Team Management Service.

CRUD operations for cleaning_teams, cleaning_team_members (members),
cleaning_team_assignments (member-to-team mapping), and team invitations.

Tables: cleaning_teams, cleaning_team_members, cleaning_team_assignments,
        cleaning_team_availability, cleaning_user_roles
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from app.database import Database
from app.modules.cleaning.middleware.plan_guard import check_limit

logger = logging.getLogger("cleanclaw.team_service")


# ============================================
# TEAM CRUD
# ============================================


async def list_teams(
    db: Database,
    business_id: str,
    include_inactive: bool = False,
) -> dict:
    """List all teams for a business with member counts and today's stats."""
    where = "WHERE t.business_id = $1"
    if not include_inactive:
        where += " AND t.is_active = true"

    rows = await db.pool.fetch(
        f"""
        SELECT
            t.id, t.business_id, t.name, t.color, t.team_lead_id,
            t.max_daily_jobs, t.service_area_ids, t.is_active,
            t.created_at, t.updated_at,
            COALESCE(mc.member_count, 0) AS member_count,
            COALESCE(jc.jobs_today, 0) AS jobs_today,
            tl.first_name AS lead_first_name,
            tl.last_name AS lead_last_name
        FROM cleaning_teams t
        LEFT JOIN (
            SELECT team_id, COUNT(*) AS member_count
            FROM cleaning_team_assignments
            WHERE is_active = true
            GROUP BY team_id
        ) mc ON mc.team_id = t.id
        LEFT JOIN (
            SELECT team_id, COUNT(*) AS jobs_today
            FROM cleaning_bookings
            WHERE scheduled_date = CURRENT_DATE
              AND status NOT IN ('cancelled', 'no_show')
              AND team_id IS NOT NULL
            GROUP BY team_id
        ) jc ON jc.team_id = t.id
        LEFT JOIN cleaning_team_members tl ON tl.id = t.team_lead_id
        {where}
        ORDER BY t.name
        """,
        business_id,
    )

    teams = []
    for row in rows:
        team = _row_to_team(row)
        team["member_count"] = row["member_count"]
        team["jobs_today"] = row["jobs_today"]
        team["team_lead_name"] = (
            f"{row['lead_first_name'] or ''} {row['lead_last_name'] or ''}".strip()
            if row["lead_first_name"]
            else None
        )
        teams.append(team)

    return {"teams": teams, "total": len(teams)}


async def get_team(
    db: Database,
    business_id: str,
    team_id: str,
) -> Optional[dict]:
    """Get team details with members and stats."""
    row = await db.pool.fetchrow(
        """
        SELECT id, business_id, name, color, team_lead_id,
               max_daily_jobs, service_area_ids, is_active,
               created_at, updated_at
        FROM cleaning_teams
        WHERE id = $1 AND business_id = $2
        """,
        team_id,
        business_id,
    )

    if not row:
        return None

    team = _row_to_team(row)

    # Get members
    members = await db.pool.fetch(
        """
        SELECT
            m.id, m.first_name, m.last_name, m.email, m.phone,
            m.role, m.employment_type, m.hourly_rate, m.color,
            m.photo_url, m.certifications, m.status,
            m.invitation_status, m.created_at, m.updated_at,
            a.role_in_team, a.effective_from
        FROM cleaning_team_assignments a
        JOIN cleaning_team_members m ON m.id = a.member_id
        WHERE a.team_id = $1 AND a.is_active = true
        ORDER BY a.role_in_team = 'lead' DESC, m.first_name
        """,
        team_id,
    )

    team["members"] = []
    for m in members:
        team["members"].append({
            "id": str(m["id"]),
            "first_name": m["first_name"],
            "last_name": m["last_name"],
            "email": m["email"],
            "phone": m["phone"],
            "role": m["role"],
            "employment_type": m["employment_type"],
            "hourly_rate": float(m["hourly_rate"]) if m["hourly_rate"] else None,
            "color": m["color"],
            "photo_url": m["photo_url"],
            "certifications": m["certifications"] or [],
            "status": m["status"],
            "invitation_status": m["invitation_status"] or "none",
            "role_in_team": m["role_in_team"],
            "effective_from": m["effective_from"].isoformat() if m["effective_from"] else None,
            "created_at": m["created_at"].isoformat() if m["created_at"] else "",
            "updated_at": m["updated_at"].isoformat() if m["updated_at"] else "",
        })

    # Get stats: jobs this week, hours this week
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    stats = await db.pool.fetchrow(
        """
        SELECT
            COUNT(*) AS jobs_this_week,
            COALESCE(SUM(estimated_duration_minutes), 0) AS minutes_this_week,
            COUNT(*) FILTER (WHERE scheduled_date = $4) AS jobs_today
        FROM cleaning_bookings
        WHERE team_id = $1
          AND business_id = $2
          AND scheduled_date BETWEEN $3 AND $5
          AND status NOT IN ('cancelled', 'no_show')
        """,
        team_id,
        business_id,
        week_start,
        today,
        week_end,
    )

    team["stats"] = {
        "jobs_this_week": stats["jobs_this_week"] if stats else 0,
        "hours_this_week": round((stats["minutes_this_week"] or 0) / 60, 1) if stats else 0,
        "jobs_today": stats["jobs_today"] if stats else 0,
    }

    return team


async def create_team(
    db: Database,
    business_id: str,
    data: dict,
) -> dict:
    """Create a new cleaning team."""
    # Plan limit check
    current_count = await db.pool.fetchval(
        "SELECT COUNT(*) FROM cleaning_teams WHERE business_id = $1 AND is_active = true",
        business_id,
    )
    await check_limit(business_id, "teams", current_count, db)

    # Check unique name
    exists = await db.pool.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM cleaning_teams
            WHERE business_id = $1 AND name = $2
        )
        """,
        business_id,
        data["name"].strip(),
    )
    if exists:
        return {"error": True, "status": 409, "message": f"A team named '{data['name']}' already exists."}

    service_area_ids = data.get("service_area_ids", [])

    row = await db.pool.fetchrow(
        """
        INSERT INTO cleaning_teams
            (business_id, name, color, team_lead_id, max_daily_jobs,
             service_area_ids, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id, business_id, name, color, team_lead_id,
                  max_daily_jobs, service_area_ids, is_active,
                  created_at, updated_at
        """,
        business_id,
        data["name"].strip(),
        data.get("color", "#3B82F6"),
        data.get("team_lead_id"),
        data.get("max_daily_jobs", 6),
        service_area_ids,
        data.get("is_active", True),
    )

    logger.info("[TEAM] Created team '%s' for business %s", data["name"], business_id)
    return _row_to_team(row)


async def update_team(
    db: Database,
    business_id: str,
    team_id: str,
    data: dict,
) -> Optional[dict]:
    """Update a team. Returns None if not found."""
    existing = await db.pool.fetchrow(
        "SELECT id FROM cleaning_teams WHERE id = $1 AND business_id = $2",
        team_id,
        business_id,
    )
    if not existing:
        return None

    # Check unique name if changing name
    if data.get("name"):
        name_exists = await db.pool.fetchval(
            """
            SELECT EXISTS(
                SELECT 1 FROM cleaning_teams
                WHERE business_id = $1 AND name = $2 AND id != $3
            )
            """,
            business_id,
            data["name"].strip(),
            team_id,
        )
        if name_exists:
            return {"error": True, "status": 409, "message": f"A team named '{data['name']}' already exists."}

    updates = []
    params = [team_id, business_id]
    idx = 3

    for field in ["name", "color", "team_lead_id", "max_daily_jobs", "is_active"]:
        if field in data and data[field] is not None:
            val = data[field]
            if field == "name":
                val = val.strip()
            updates.append(f"{field} = ${idx}")
            params.append(val)
            idx += 1

    if "service_area_ids" in data and data["service_area_ids"] is not None:
        updates.append(f"service_area_ids = ${idx}")
        params.append(data["service_area_ids"])
        idx += 1

    if not updates:
        return await get_team(db, business_id, team_id)

    query = f"""
        UPDATE cleaning_teams
        SET {', '.join(updates)}
        WHERE id = $1 AND business_id = $2
        RETURNING id, business_id, name, color, team_lead_id,
                  max_daily_jobs, service_area_ids, is_active,
                  created_at, updated_at
    """
    row = await db.pool.fetchrow(query, *params)

    if not row:
        return None

    logger.info("[TEAM] Updated team %s for business %s", team_id, business_id)
    return _row_to_team(row)


async def delete_team(
    db: Database,
    business_id: str,
    team_id: str,
) -> dict:
    """
    Deactivate a team. Returns 409 if team has future assigned bookings.
    """
    # Check for future bookings
    future_count = await db.pool.fetchval(
        """
        SELECT COUNT(*) FROM cleaning_bookings
        WHERE team_id = $1
          AND business_id = $2
          AND scheduled_date >= CURRENT_DATE
          AND status NOT IN ('cancelled', 'no_show')
        """,
        team_id,
        business_id,
    )

    if future_count and future_count > 0:
        return {
            "deleted": False,
            "conflict": True,
            "future_bookings": future_count,
            "message": f"Reassign {future_count} future job(s) before deactivating this team.",
        }

    result = await db.pool.execute(
        """
        UPDATE cleaning_teams
        SET is_active = false
        WHERE id = $1 AND business_id = $2
        """,
        team_id,
        business_id,
    )

    if "UPDATE 0" in result:
        return {"deleted": False, "not_found": True}

    # Deactivate all assignments for this team
    await db.pool.execute(
        """
        UPDATE cleaning_team_assignments
        SET is_active = false, effective_until = CURRENT_DATE
        WHERE team_id = $1 AND is_active = true
        """,
        team_id,
    )

    logger.info("[TEAM] Deactivated team %s for business %s", team_id, business_id)
    return {"deleted": True}


# ============================================
# MEMBER CRUD
# ============================================


async def list_members(
    db: Database,
    business_id: str,
    include_inactive: bool = False,
) -> dict:
    """List all team members for a business."""
    where = "WHERE m.business_id = $1"
    if not include_inactive:
        where += " AND m.status = 'active'"

    rows = await db.pool.fetch(
        f"""
        SELECT
            m.id, m.business_id, m.user_id, m.first_name, m.last_name,
            m.email, m.phone, m.role, m.employment_type, m.hourly_rate,
            m.color, m.photo_url, m.certifications, m.max_daily_hours,
            m.can_drive, m.home_zip, m.notes, m.status, m.hire_date,
            m.termination_date, m.invitation_email, m.invitation_status,
            m.invited_at, m.created_at, m.updated_at,
            a.team_id, t.name AS team_name, a.role_in_team
        FROM cleaning_team_members m
        LEFT JOIN cleaning_team_assignments a
            ON a.member_id = m.id AND a.is_active = true
        LEFT JOIN cleaning_teams t
            ON t.id = a.team_id
        {where}
        ORDER BY m.first_name, m.last_name
        """,
        business_id,
    )

    members = []
    for row in rows:
        member = _row_to_member(row)
        member["team_id"] = str(row["team_id"]) if row["team_id"] else None
        member["team_name"] = row["team_name"]
        member["role_in_team"] = row["role_in_team"]
        members.append(member)

    return {"members": members, "total": len(members)}


async def get_member(
    db: Database,
    business_id: str,
    member_id: str,
) -> Optional[dict]:
    """Get a single member with stats."""
    row = await db.pool.fetchrow(
        """
        SELECT
            m.id, m.business_id, m.user_id, m.first_name, m.last_name,
            m.email, m.phone, m.role, m.employment_type, m.hourly_rate,
            m.color, m.photo_url, m.certifications, m.max_daily_hours,
            m.can_drive, m.home_zip, m.notes, m.status, m.hire_date,
            m.termination_date, m.invitation_email, m.invitation_status,
            m.invited_at, m.created_at, m.updated_at
        FROM cleaning_team_members m
        WHERE m.id = $1 AND m.business_id = $2
        """,
        member_id,
        business_id,
    )

    if not row:
        return None

    member = _row_to_member(row)

    # Get team assignments
    assignments = await db.pool.fetch(
        """
        SELECT a.team_id, t.name AS team_name, a.role_in_team, a.effective_from
        FROM cleaning_team_assignments a
        JOIN cleaning_teams t ON t.id = a.team_id
        WHERE a.member_id = $1 AND a.is_active = true
        """,
        member_id,
    )

    member["team_assignments"] = [
        {
            "team_id": str(a["team_id"]),
            "team_name": a["team_name"],
            "role_in_team": a["role_in_team"],
            "effective_from": a["effective_from"].isoformat() if a["effective_from"] else None,
        }
        for a in assignments
    ]

    # Get availability
    avail = await db.pool.fetch(
        """
        SELECT day_of_week, start_time, end_time, is_available
        FROM cleaning_team_availability
        WHERE team_member_id = $1 AND business_id = $2
          AND (effective_until IS NULL OR effective_until >= CURRENT_DATE)
        ORDER BY day_of_week, start_time
        """,
        member_id,
        business_id,
    )

    member["availability"] = [
        {
            "day_of_week": a["day_of_week"],
            "start_time": a["start_time"].isoformat() if a["start_time"] else None,
            "end_time": a["end_time"].isoformat() if a["end_time"] else None,
            "is_available": a["is_available"],
        }
        for a in avail
    ]

    # Get stats
    today = date.today()
    month_start = today.replace(day=1)

    stats = await db.pool.fetchrow(
        """
        SELECT
            COUNT(*) FILTER (WHERE b.status = 'completed') AS jobs_completed,
            COALESCE(SUM(b.estimated_duration_minutes) FILTER (
                WHERE b.scheduled_date >= $3
            ), 0) AS minutes_this_month
        FROM cleaning_bookings b
        JOIN cleaning_team_assignments ta ON ta.team_id = b.team_id AND ta.is_active = true
        WHERE ta.member_id = $1
          AND b.business_id = $2
          AND b.status NOT IN ('cancelled', 'no_show')
        """,
        member_id,
        business_id,
        month_start,
    )

    member["stats"] = {
        "jobs_completed": stats["jobs_completed"] if stats else 0,
        "hours_this_month": round((stats["minutes_this_month"] or 0) / 60, 1) if stats else 0,
    }

    return member


async def create_member(
    db: Database,
    business_id: str,
    data: dict,
) -> dict:
    """Create a new team member."""
    # Plan limit check on cleaners
    current_count = await db.pool.fetchval(
        "SELECT COUNT(*) FROM cleaning_team_members WHERE business_id = $1 AND status = 'active'",
        business_id,
    )

    # Use 'clients' limit as proxy for cleaners (or we add a cleaners limit)
    # For now, story says: Basic max 3, Intermediate max 15, Maximum max 50
    # These limits are not in PLAN_LIMITS yet, so we do a manual check
    from app.modules.cleaning.middleware.plan_guard import get_business_plan
    plan = await get_business_plan(business_id, db)
    member_limits = {"basic": 3, "intermediate": 15, "maximum": 50}
    limit = member_limits.get(plan, 3)
    if current_count >= limit:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=403,
            detail=f"Cleaner limit reached ({current_count}/{limit}). Upgrade your plan to add more.",
        )

    row = await db.pool.fetchrow(
        """
        INSERT INTO cleaning_team_members
            (business_id, first_name, last_name, email, phone,
             role, employment_type, hourly_rate, status, hire_date)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active', CURRENT_DATE)
        RETURNING id, business_id, user_id, first_name, last_name,
                  email, phone, role, employment_type, hourly_rate,
                  color, photo_url, certifications, max_daily_hours,
                  can_drive, home_zip, notes, status, hire_date,
                  termination_date, invitation_email, invitation_status,
                  invited_at, created_at, updated_at
        """,
        business_id,
        data["first_name"].strip(),
        data.get("last_name", "").strip() or None,
        data.get("email"),
        data.get("phone"),
        data.get("role", "cleaner"),
        data.get("employment_type", "employee"),
        data.get("hourly_rate"),
    )

    logger.info("[TEAM] Created member '%s' for business %s", data["first_name"], business_id)
    return _row_to_member(row)


async def update_member(
    db: Database,
    business_id: str,
    member_id: str,
    data: dict,
) -> Optional[dict]:
    """Update a team member."""
    existing = await db.pool.fetchrow(
        "SELECT id FROM cleaning_team_members WHERE id = $1 AND business_id = $2",
        member_id,
        business_id,
    )
    if not existing:
        return None

    updates = []
    params = [member_id, business_id]
    idx = 3

    for field in [
        "first_name", "last_name", "email", "phone", "role",
        "employment_type", "hourly_rate", "color", "photo_url",
        "max_daily_hours", "can_drive", "home_zip", "notes", "status",
    ]:
        if field in data and data[field] is not None:
            val = data[field]
            if isinstance(val, str):
                val = val.strip()
            updates.append(f"{field} = ${idx}")
            params.append(val)
            idx += 1

    if "certifications" in data and data["certifications"] is not None:
        updates.append(f"certifications = ${idx}")
        params.append(data["certifications"])
        idx += 1

    if not updates:
        return await get_member(db, business_id, member_id)

    query = f"""
        UPDATE cleaning_team_members
        SET {', '.join(updates)}
        WHERE id = $1 AND business_id = $2
        RETURNING id, business_id, user_id, first_name, last_name,
                  email, phone, role, employment_type, hourly_rate,
                  color, photo_url, certifications, max_daily_hours,
                  can_drive, home_zip, notes, status, hire_date,
                  termination_date, invitation_email, invitation_status,
                  invited_at, created_at, updated_at
    """
    row = await db.pool.fetchrow(query, *params)
    if not row:
        return None

    logger.info("[TEAM] Updated member %s for business %s", member_id, business_id)
    return _row_to_member(row)


async def delete_member(
    db: Database,
    business_id: str,
    member_id: str,
) -> dict:
    """Deactivate a member (status=terminated), preserves history."""
    result = await db.pool.execute(
        """
        UPDATE cleaning_team_members
        SET status = 'terminated', termination_date = CURRENT_DATE
        WHERE id = $1 AND business_id = $2
        """,
        member_id,
        business_id,
    )

    if "UPDATE 0" in result:
        return {"deleted": False, "not_found": True}

    # Deactivate all team assignments
    await db.pool.execute(
        """
        UPDATE cleaning_team_assignments
        SET is_active = false, effective_until = CURRENT_DATE
        WHERE member_id = $1 AND is_active = true
        """,
        member_id,
    )

    logger.info("[TEAM] Terminated member %s for business %s", member_id, business_id)
    return {"deleted": True}


# ============================================
# TEAM ASSIGNMENTS
# ============================================


async def assign_member_to_team(
    db: Database,
    business_id: str,
    team_id: str,
    member_id: str,
    role_in_team: str = "member",
) -> dict:
    """Assign a member to a team."""
    # Verify team exists
    team = await db.pool.fetchrow(
        "SELECT id, business_id FROM cleaning_teams WHERE id = $1 AND business_id = $2",
        team_id,
        business_id,
    )
    if not team:
        return {"error": True, "status": 404, "message": "Team not found."}

    # Verify member exists
    member = await db.pool.fetchrow(
        "SELECT id, business_id FROM cleaning_team_members WHERE id = $1 AND business_id = $2",
        member_id,
        business_id,
    )
    if not member:
        return {"error": True, "status": 404, "message": "Member not found."}

    # Check if already assigned to this team
    existing = await db.pool.fetchval(
        """
        SELECT EXISTS(
            SELECT 1 FROM cleaning_team_assignments
            WHERE team_id = $1 AND member_id = $2 AND is_active = true
        )
        """,
        team_id,
        member_id,
    )
    if existing:
        return {"error": True, "status": 409, "message": "Member is already assigned to this team."}

    # Create assignment
    row = await db.pool.fetchrow(
        """
        INSERT INTO cleaning_team_assignments
            (team_id, member_id, role_in_team, effective_from, is_active)
        VALUES ($1, $2, $3, CURRENT_DATE, true)
        RETURNING id, team_id, member_id, role_in_team, effective_from,
                  effective_until, is_active, created_at
        """,
        team_id,
        member_id,
        role_in_team,
    )

    # If role is lead, update team_lead_id
    if role_in_team == "lead":
        await db.pool.execute(
            "UPDATE cleaning_teams SET team_lead_id = $1 WHERE id = $2",
            member_id,
            team_id,
        )

    logger.info("[TEAM] Assigned member %s to team %s as %s", member_id, team_id, role_in_team)

    return {
        "id": str(row["id"]),
        "team_id": str(row["team_id"]),
        "member_id": str(row["member_id"]),
        "role_in_team": row["role_in_team"],
        "effective_from": row["effective_from"].isoformat() if row["effective_from"] else None,
        "effective_until": None,
        "is_active": row["is_active"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
    }


async def remove_member_from_team(
    db: Database,
    business_id: str,
    team_id: str,
    member_id: str,
) -> dict:
    """Remove a member from a team (sets effective_until = today)."""
    # Verify team belongs to business
    team = await db.pool.fetchrow(
        "SELECT id, team_lead_id FROM cleaning_teams WHERE id = $1 AND business_id = $2",
        team_id,
        business_id,
    )
    if not team:
        return {"error": True, "status": 404, "message": "Team not found."}

    result = await db.pool.execute(
        """
        UPDATE cleaning_team_assignments
        SET is_active = false, effective_until = CURRENT_DATE
        WHERE team_id = $1 AND member_id = $2 AND is_active = true
        """,
        team_id,
        member_id,
    )

    if "UPDATE 0" in result:
        return {"error": True, "status": 404, "message": "Member is not assigned to this team."}

    # If this was the team lead, clear team_lead_id
    if team["team_lead_id"] and str(team["team_lead_id"]) == member_id:
        await db.pool.execute(
            "UPDATE cleaning_teams SET team_lead_id = NULL WHERE id = $1",
            team_id,
        )

    logger.info("[TEAM] Removed member %s from team %s", member_id, team_id)
    return {"removed": True}


async def set_team_lead(
    db: Database,
    business_id: str,
    team_id: str,
    member_id: str,
) -> dict:
    """Set a member as team lead."""
    # Verify team
    team = await db.pool.fetchrow(
        "SELECT id FROM cleaning_teams WHERE id = $1 AND business_id = $2",
        team_id,
        business_id,
    )
    if not team:
        return {"error": True, "status": 404, "message": "Team not found."}

    # Verify member is assigned to the team
    assignment = await db.pool.fetchrow(
        """
        SELECT id FROM cleaning_team_assignments
        WHERE team_id = $1 AND member_id = $2 AND is_active = true
        """,
        team_id,
        member_id,
    )
    if not assignment:
        return {"error": True, "status": 404, "message": "Member is not assigned to this team."}

    # Demote previous lead
    await db.pool.execute(
        """
        UPDATE cleaning_team_assignments
        SET role_in_team = 'member'
        WHERE team_id = $1 AND role_in_team = 'lead' AND is_active = true
        """,
        team_id,
    )

    # Promote new lead
    await db.pool.execute(
        """
        UPDATE cleaning_team_assignments
        SET role_in_team = 'lead'
        WHERE team_id = $1 AND member_id = $2 AND is_active = true
        """,
        team_id,
        member_id,
    )

    # Update team_lead_id on the team
    await db.pool.execute(
        "UPDATE cleaning_teams SET team_lead_id = $1 WHERE id = $2",
        member_id,
        team_id,
    )

    logger.info("[TEAM] Set member %s as lead of team %s", member_id, team_id)
    return {"team_lead_id": member_id, "success": True}


# ============================================
# AVAILABILITY
# ============================================


async def set_member_availability(
    db: Database,
    business_id: str,
    member_id: str,
    rules: list[dict],
) -> dict:
    """Set weekly default availability for a member. Replaces existing rules."""
    # Verify member exists
    exists = await db.pool.fetchval(
        "SELECT EXISTS(SELECT 1 FROM cleaning_team_members WHERE id = $1 AND business_id = $2)",
        member_id,
        business_id,
    )
    if not exists:
        return {"error": True, "status": 404, "message": "Member not found."}

    # Deactivate old availability (set effective_until)
    await db.pool.execute(
        """
        UPDATE cleaning_team_availability
        SET effective_until = CURRENT_DATE
        WHERE team_member_id = $1 AND business_id = $2
          AND (effective_until IS NULL OR effective_until > CURRENT_DATE)
        """,
        member_id,
        business_id,
    )

    # Insert new rules
    for rule in rules:
        await db.pool.execute(
            """
            INSERT INTO cleaning_team_availability
                (business_id, team_member_id, day_of_week, start_time, end_time,
                 is_available, effective_from)
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_DATE)
            """,
            business_id,
            member_id,
            rule["day_of_week"],
            rule["start_time"],
            rule["end_time"],
            rule.get("is_available", True),
        )

    logger.info("[TEAM] Set availability for member %s (%d rules)", member_id, len(rules))
    return {"success": True, "rules_count": len(rules)}


async def add_availability_exception(
    db: Database,
    business_id: str,
    member_id: str,
    data: dict,
) -> dict:
    """Add an availability exception (PTO, sick day, etc.)."""
    exists = await db.pool.fetchval(
        "SELECT EXISTS(SELECT 1 FROM cleaning_team_members WHERE id = $1 AND business_id = $2)",
        member_id,
        business_id,
    )
    if not exists:
        return {"error": True, "status": 404, "message": "Member not found."}

    exception_date = data["date"]
    if isinstance(exception_date, str):
        exception_date = date.fromisoformat(exception_date)

    day_of_week = exception_date.weekday()
    # Python weekday: 0=Mon, 6=Sun. DB: 0=Sun, 6=Sat. Convert.
    day_of_week = (day_of_week + 1) % 7

    if data.get("is_full_day", True):
        start_time = "00:00"
        end_time = "23:59"
    else:
        start_time = data.get("start_time", "00:00")
        end_time = data.get("end_time", "23:59")

    await db.pool.execute(
        """
        INSERT INTO cleaning_team_availability
            (business_id, team_member_id, day_of_week, start_time, end_time,
             is_available, effective_from, effective_until)
        VALUES ($1, $2, $3, $4, $5, false, $6, $6)
        """,
        business_id,
        member_id,
        day_of_week,
        start_time,
        end_time,
        exception_date,
    )

    logger.info(
        "[TEAM] Added exception for member %s on %s (reason: %s)",
        member_id, exception_date, data.get("reason", "unspecified"),
    )
    return {"success": True, "date": exception_date.isoformat(), "reason": data.get("reason")}


# ============================================
# INVITE CLEANER
# ============================================


async def invite_cleaner(
    db: Database,
    business_id: str,
    business_slug: str,
    data: dict,
    owner_user_id: str,
) -> dict:
    """
    Invite a cleaner by email. Creates team member placeholder + user role entry.
    Reuses invitation flow from S1.3 auth_routes.
    """
    import jwt as pyjwt
    from app.config import SECRET_KEY, APP_URL

    email = data["email"].strip().lower()
    team_id = data.get("team_id")
    role_in_team = data.get("role_in_team", "member")

    # Check if member with this email already exists
    existing = await db.pool.fetchval(
        "SELECT id FROM cleaning_team_members WHERE business_id = $1 AND email = $2",
        business_id,
        email,
    )
    if existing:
        return {"error": True, "status": 409, "message": f"A member with email {email} already exists."}

    now = datetime.utcnow()

    # Create team member placeholder
    member_id = await db.pool.fetchval(
        """
        INSERT INTO cleaning_team_members
            (business_id, first_name, email, role, employment_type,
             status, invitation_email, invitation_status, invited_at)
        VALUES ($1, $2, $3, 'cleaner', 'employee', 'invited',
                $3, 'pending', $4)
        RETURNING id
        """,
        business_id,
        email.split("@")[0],
        email,
        now,
    )

    # If team_id provided, create team assignment
    if team_id:
        await db.pool.execute(
            """
            INSERT INTO cleaning_team_assignments
                (team_id, member_id, role_in_team, effective_from, is_active)
            VALUES ($1, $2, $3, CURRENT_DATE, true)
            """,
            team_id,
            member_id,
            role_in_team,
        )

    # Check if user exists on platform
    user_row = await db.pool.fetchrow(
        "SELECT id FROM users WHERE email = $1",
        email,
    )

    # Create cleaning_user_roles entry
    role_type = "team_lead" if role_in_team == "lead" else "cleaner"
    role_id = await db.pool.fetchval(
        """
        INSERT INTO cleaning_user_roles
            (user_id, business_id, role, team_id, invited_by, invited_at, is_active)
        VALUES ($1, $2, $3, $4, $5, $6, false)
        RETURNING id
        """,
        str(user_row["id"]) if user_row else None,
        business_id,
        role_type,
        team_id,
        owner_user_id,
        now,
    )

    # Generate invite token
    expires_at = now + timedelta(days=7)
    invite_payload = {
        "sub": str(role_id),
        "type": "cleaning_invite",
        "email": email,
        "role": role_type,
        "business_id": business_id,
        "business_slug": business_slug,
        "team_id": team_id,
        "iat": now,
        "exp": expires_at,
    }
    invite_token = pyjwt.encode(invite_payload, SECRET_KEY, algorithm="HS256")
    invite_link = f"{APP_URL}/cleaning/invite?token={invite_token}"

    logger.info("[TEAM] Invited %s to business %s", email, business_slug)

    return {
        "invite_id": str(role_id),
        "member_id": str(member_id),
        "email": email,
        "role": role_type,
        "invite_link": invite_link,
        "expires_at": expires_at.isoformat(),
    }


# ============================================
# HELPERS
# ============================================


def _row_to_team(row) -> dict:
    """Convert a DB row to a team response dict."""
    return {
        "id": str(row["id"]),
        "business_id": str(row["business_id"]),
        "name": row["name"],
        "color": row["color"],
        "team_lead_id": str(row["team_lead_id"]) if row["team_lead_id"] else None,
        "max_daily_jobs": row["max_daily_jobs"],
        "service_area_ids": [str(x) for x in row["service_area_ids"]] if row["service_area_ids"] else [],
        "is_active": row["is_active"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else "",
    }


def _row_to_member(row) -> dict:
    """Convert a DB row to a member response dict."""
    return {
        "id": str(row["id"]),
        "business_id": str(row["business_id"]),
        "user_id": str(row["user_id"]) if row["user_id"] else None,
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
        "phone": row["phone"],
        "role": row["role"],
        "employment_type": row["employment_type"],
        "hourly_rate": float(row["hourly_rate"]) if row["hourly_rate"] else None,
        "color": row["color"],
        "photo_url": row["photo_url"],
        "certifications": row["certifications"] or [],
        "max_daily_hours": float(row["max_daily_hours"]) if row["max_daily_hours"] else 8.0,
        "can_drive": row["can_drive"],
        "home_zip": row["home_zip"],
        "notes": row["notes"],
        "status": row["status"],
        "hire_date": row["hire_date"].isoformat() if row["hire_date"] else None,
        "termination_date": row["termination_date"].isoformat() if row["termination_date"] else None,
        "invitation_email": row["invitation_email"],
        "invitation_status": row["invitation_status"] or "none",
        "invited_at": row["invited_at"].isoformat() if row["invited_at"] else None,
        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else "",
    }
