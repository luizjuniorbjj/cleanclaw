"""
Xcleaners v3 — AI Scheduling Tool Definitions.

Tool definitions for Claude tool_use integration.
These tools allow the AI scheduling assistant to query and manipulate
schedule data, team availability, client history, and distance calculations.

Each tool is defined as a dict matching Anthropic's tool schema format.
The execute_tool() function dispatches tool calls to the correct handler.
"""

import logging
from datetime import date, datetime
from typing import Optional

from app.database import Database
from app.modules.cleaning.services.team_assignment_scorer import haversine

logger = logging.getLogger("xcleaners.ai_tools")


# ============================================
# TOOL DEFINITIONS (Anthropic tool_use format)
# ============================================

AI_TOOLS = [
    {
        "name": "get_schedule_for_date",
        "description": (
            "Fetch the full daily schedule for a specific date. "
            "Returns all bookings grouped by team, including client name, "
            "address, service type, time slot, and status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format.",
                },
            },
            "required": ["date"],
        },
    },
    {
        "name": "get_team_availability",
        "description": (
            "Check team availability for a specific date. "
            "Returns each team's current job count, max capacity, "
            "active members, and available time slots."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format.",
                },
            },
            "required": ["date"],
        },
    },
    {
        "name": "get_client_history",
        "description": (
            "Get a client's booking history including past services, "
            "teams that served them, average duration, cancellation rate, "
            "and preferences."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {
                    "type": "string",
                    "description": "UUID of the client.",
                },
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "calculate_distance",
        "description": (
            "Calculate the driving distance in miles between two addresses "
            "using their latitude/longitude coordinates (haversine formula). "
            "Use this to evaluate travel time between jobs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "from_lat": {"type": "number", "description": "Latitude of origin."},
                "from_lon": {"type": "number", "description": "Longitude of origin."},
                "to_lat": {"type": "number", "description": "Latitude of destination."},
                "to_lon": {"type": "number", "description": "Longitude of destination."},
            },
            "required": ["from_lat", "from_lon", "to_lat", "to_lon"],
        },
    },
    {
        "name": "get_team_workload_summary",
        "description": (
            "Get a workload summary for all teams on a date range. "
            "Returns total jobs, total hours, and average jobs per day "
            "for each team. Useful for workload balancing analysis."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Start date in YYYY-MM-DD format.",
                },
                "end_date": {
                    "type": "string",
                    "description": "End date in YYYY-MM-DD format.",
                },
            },
            "required": ["start_date", "end_date"],
        },
    },
    {
        "name": "get_cancellation_patterns",
        "description": (
            "Analyze cancellation patterns for the business. "
            "Returns cancellation rate by day of week, by client, "
            "and trends over time."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days_back": {
                    "type": "integer",
                    "description": "Number of days to look back (default 30).",
                    "default": 30,
                },
            },
            "required": [],
        },
    },
]


# ============================================
# TOOL EXECUTORS
# ============================================

async def execute_tool(
    tool_name: str,
    tool_input: dict,
    business_id: str,
    db: Database,
) -> str:
    """
    Execute a tool call and return the result as a JSON string.

    Args:
        tool_name: Name of the tool to execute.
        tool_input: Input parameters for the tool.
        business_id: UUID of the business (scope).
        db: Database instance.

    Returns:
        JSON string with the tool result.
    """
    import json

    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = await handler(tool_input, business_id, db)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.error("[AI_TOOLS] Error executing %s: %s", tool_name, e)
        return json.dumps({"error": str(e)})


# ─── get_schedule_for_date ────────────────────

async def _get_schedule_for_date(
    params: dict, business_id: str, db: Database
) -> dict:
    target_date = params["date"]

    rows = await db.pool.fetch(
        """
        SELECT
            b.id AS booking_id,
            b.scheduled_date,
            b.start_time,
            b.end_time,
            b.status,
            b.estimated_duration_minutes,
            b.actual_duration_minutes,
            b.team_id,
            t.name AS team_name,
            cs.id AS client_id,
            cs.client_name,
            cs.address_line1,
            cs.city,
            cs.zip_code,
            cs.latitude,
            cs.longitude,
            st.name AS service_type_name,
            b.notes
        FROM cleaning_bookings b
        LEFT JOIN cleaning_teams t ON t.id = b.team_id
        LEFT JOIN cleaning_client_schedules cs ON cs.id = b.client_id
        LEFT JOIN cleaning_service_types st ON st.id = b.service_type_id
        WHERE b.business_id = $1
          AND b.scheduled_date = $2::date
          AND b.status NOT IN ('cancelled')
        ORDER BY t.name NULLS LAST, b.start_time NULLS LAST
        """,
        business_id,
        target_date,
    )

    # Group by team
    teams = {}
    unassigned = []
    for row in rows:
        booking = {
            "booking_id": str(row["booking_id"]),
            "client_name": row["client_name"],
            "address": f"{row['address_line1'] or ''}, {row['city'] or ''}".strip(", "),
            "zip_code": row["zip_code"],
            "latitude": float(row["latitude"]) if row["latitude"] else None,
            "longitude": float(row["longitude"]) if row["longitude"] else None,
            "service_type": row["service_type_name"],
            "start_time": str(row["start_time"]) if row["start_time"] else None,
            "end_time": str(row["end_time"]) if row["end_time"] else None,
            "estimated_minutes": row["estimated_duration_minutes"],
            "actual_minutes": row["actual_duration_minutes"],
            "status": row["status"],
            "notes": row["notes"],
        }
        if row["team_id"]:
            tid = str(row["team_id"])
            if tid not in teams:
                teams[tid] = {
                    "team_id": tid,
                    "team_name": row["team_name"],
                    "bookings": [],
                }
            teams[tid]["bookings"].append(booking)
        else:
            unassigned.append(booking)

    return {
        "date": target_date,
        "teams": list(teams.values()),
        "unassigned": unassigned,
        "total_bookings": len(rows),
    }


# ─── get_team_availability ────────────────────

async def _get_team_availability(
    params: dict, business_id: str, db: Database
) -> dict:
    target_date = params["date"]

    teams = await db.pool.fetch(
        """
        SELECT
            t.id,
            t.name,
            t.max_daily_jobs,
            t.status,
            (
                SELECT COUNT(*)
                FROM cleaning_bookings b
                WHERE b.team_id = t.id
                  AND b.scheduled_date = $2::date
                  AND b.status NOT IN ('cancelled')
            ) AS jobs_today,
            (
                SELECT COUNT(*)
                FROM cleaning_team_assignments ta
                WHERE ta.team_id = t.id
                  AND ta.status = 'active'
            ) AS active_members
        FROM cleaning_teams t
        WHERE t.business_id = $1
          AND t.status = 'active'
        ORDER BY t.name
        """,
        business_id,
        target_date,
    )

    result = []
    for team in teams:
        max_jobs = team["max_daily_jobs"] or 6
        jobs = team["jobs_today"]
        result.append({
            "team_id": str(team["id"]),
            "team_name": team["name"],
            "status": team["status"],
            "active_members": team["active_members"],
            "jobs_today": jobs,
            "max_daily_jobs": max_jobs,
            "available_slots": max(0, max_jobs - jobs),
            "utilization_percent": round((jobs / max_jobs) * 100, 1) if max_jobs > 0 else 0,
        })

    return {"date": target_date, "teams": result}


# ─── get_client_history ────────────────────

async def _get_client_history(
    params: dict, business_id: str, db: Database
) -> dict:
    client_id = params["client_id"]

    # Client info
    client = await db.pool.fetchrow(
        """
        SELECT client_name, address_line1, city, zip_code,
               frequency, preferred_team_id, special_instructions,
               latitude, longitude
        FROM cleaning_client_schedules
        WHERE id = $1 AND business_id = $2
        """,
        client_id,
        business_id,
    )

    if not client:
        return {"error": f"Client {client_id} not found."}

    # Booking history (last 20)
    bookings = await db.pool.fetch(
        """
        SELECT
            b.scheduled_date,
            b.status,
            b.estimated_duration_minutes,
            b.actual_duration_minutes,
            b.team_id,
            t.name AS team_name,
            st.name AS service_type_name
        FROM cleaning_bookings b
        LEFT JOIN cleaning_teams t ON t.id = b.team_id
        LEFT JOIN cleaning_service_types st ON st.id = b.service_type_id
        WHERE b.client_id = $1 AND b.business_id = $2
        ORDER BY b.scheduled_date DESC
        LIMIT 20
        """,
        client_id,
        business_id,
    )

    total = len(bookings)
    cancelled = sum(1 for b in bookings if b["status"] == "cancelled")
    completed = [b for b in bookings if b["actual_duration_minutes"]]
    avg_duration = (
        round(sum(b["actual_duration_minutes"] for b in completed) / len(completed), 0)
        if completed else None
    )

    return {
        "client_id": client_id,
        "client_name": client["client_name"],
        "address": f"{client['address_line1'] or ''}, {client['city'] or ''}".strip(", "),
        "frequency": client["frequency"],
        "preferred_team_id": str(client["preferred_team_id"]) if client["preferred_team_id"] else None,
        "special_instructions": client["special_instructions"],
        "total_bookings": total,
        "cancellation_rate": round(cancelled / total * 100, 1) if total > 0 else 0,
        "avg_actual_duration_minutes": avg_duration,
        "recent_bookings": [
            {
                "date": str(b["scheduled_date"]),
                "status": b["status"],
                "team_name": b["team_name"],
                "service_type": b["service_type_name"],
                "estimated_minutes": b["estimated_duration_minutes"],
                "actual_minutes": b["actual_duration_minutes"],
            }
            for b in bookings[:10]
        ],
    }


# ─── calculate_distance ────────────────────

async def _calculate_distance(
    params: dict, business_id: str, db: Database
) -> dict:
    distance = haversine(
        params["from_lat"],
        params["from_lon"],
        params["to_lat"],
        params["to_lon"],
    )
    # Estimate travel time: ~30 mph average in residential areas
    travel_minutes = round(distance / 30 * 60, 1)

    return {
        "distance_miles": round(distance, 2),
        "estimated_travel_minutes": travel_minutes,
    }


# ─── get_team_workload_summary ────────────────────

async def _get_team_workload_summary(
    params: dict, business_id: str, db: Database
) -> dict:
    start_date = params["start_date"]
    end_date = params["end_date"]

    rows = await db.pool.fetch(
        """
        SELECT
            t.id AS team_id,
            t.name AS team_name,
            COUNT(b.id) AS total_jobs,
            COALESCE(SUM(b.estimated_duration_minutes), 0) AS total_estimated_minutes,
            COALESCE(SUM(b.actual_duration_minutes), 0) AS total_actual_minutes,
            COUNT(DISTINCT b.scheduled_date) AS days_worked
        FROM cleaning_teams t
        LEFT JOIN cleaning_bookings b ON b.team_id = t.id
            AND b.scheduled_date BETWEEN $2::date AND $3::date
            AND b.status NOT IN ('cancelled')
        WHERE t.business_id = $1
          AND t.status = 'active'
        GROUP BY t.id, t.name
        ORDER BY t.name
        """,
        business_id,
        start_date,
        end_date,
    )

    result = []
    for row in rows:
        days = row["days_worked"] or 1
        result.append({
            "team_id": str(row["team_id"]),
            "team_name": row["team_name"],
            "total_jobs": row["total_jobs"],
            "total_estimated_hours": round(row["total_estimated_minutes"] / 60, 1),
            "total_actual_hours": round(row["total_actual_minutes"] / 60, 1),
            "days_worked": days,
            "avg_jobs_per_day": round(row["total_jobs"] / days, 1),
        })

    return {
        "start_date": start_date,
        "end_date": end_date,
        "teams": result,
    }


# ─── get_cancellation_patterns ────────────────────

async def _get_cancellation_patterns(
    params: dict, business_id: str, db: Database
) -> dict:
    days_back = params.get("days_back", 30)

    # Overall stats
    stats = await db.pool.fetchrow(
        """
        SELECT
            COUNT(*) AS total_bookings,
            COUNT(*) FILTER (WHERE status = 'cancelled') AS total_cancelled
        FROM cleaning_bookings
        WHERE business_id = $1
          AND scheduled_date >= CURRENT_DATE - $2::int
        """,
        business_id,
        days_back,
    )

    # By day of week
    by_dow = await db.pool.fetch(
        """
        SELECT
            EXTRACT(DOW FROM scheduled_date)::int AS day_of_week,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled
        FROM cleaning_bookings
        WHERE business_id = $1
          AND scheduled_date >= CURRENT_DATE - $2::int
        GROUP BY EXTRACT(DOW FROM scheduled_date)
        ORDER BY EXTRACT(DOW FROM scheduled_date)
        """,
        business_id,
        days_back,
    )

    dow_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    # Top cancelling clients
    top_cancellers = await db.pool.fetch(
        """
        SELECT
            cs.client_name,
            COUNT(*) FILTER (WHERE b.status = 'cancelled') AS cancellations,
            COUNT(*) AS total_bookings
        FROM cleaning_bookings b
        JOIN cleaning_client_schedules cs ON cs.id = b.client_id
        WHERE b.business_id = $1
          AND b.scheduled_date >= CURRENT_DATE - $2::int
        GROUP BY cs.client_name
        HAVING COUNT(*) FILTER (WHERE b.status = 'cancelled') > 0
        ORDER BY cancellations DESC
        LIMIT 5
        """,
        business_id,
        days_back,
    )

    total = stats["total_bookings"] or 0
    cancelled = stats["total_cancelled"] or 0

    return {
        "period_days": days_back,
        "total_bookings": total,
        "total_cancelled": cancelled,
        "cancellation_rate_percent": round(cancelled / total * 100, 1) if total > 0 else 0,
        "by_day_of_week": [
            {
                "day": dow_names[row["day_of_week"]],
                "total": row["total"],
                "cancelled": row["cancelled"],
                "rate_percent": round(row["cancelled"] / row["total"] * 100, 1) if row["total"] > 0 else 0,
            }
            for row in by_dow
        ],
        "top_cancelling_clients": [
            {
                "client_name": row["client_name"],
                "cancellations": row["cancellations"],
                "total_bookings": row["total_bookings"],
                "rate_percent": round(row["cancellations"] / row["total_bookings"] * 100, 1),
            }
            for row in top_cancellers
        ],
    }


# ============================================
# HANDLER REGISTRY
# ============================================

TOOL_HANDLERS = {
    "get_schedule_for_date": _get_schedule_for_date,
    "get_team_availability": _get_team_availability,
    "get_client_history": _get_client_history,
    "calculate_distance": _calculate_distance,
    "get_team_workload_summary": _get_team_workload_summary,
    "get_cancellation_patterns": _get_cancellation_patterns,
}
