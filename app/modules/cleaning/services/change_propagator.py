"""
Xcleaners v3 — Change Propagator (S2.6).

Publishes real-time schedule events via Redis PubSub.
Events fan-out to both team-specific and business-level channels
so owners see all events and team members see only their team's events.

Channel naming (ADR-v3-4):
  - clean:{business_id}:sse:schedule        — owner listens here
  - clean:{business_id}:sse:team:{team_id}  — team members listen here

Event types:
  - schedule.generated  — daily schedule created for a team
  - schedule.changed    — booking added/removed/updated on a team's day
  - booking.confirmed   — booking was confirmed
  - booking.cancelled   — booking was cancelled
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger("xcleaners.change_propagator")


def _get_redis():
    """Get Redis client, returns None if unavailable."""
    try:
        from app.redis_client import get_redis
        return get_redis()
    except ImportError:
        return None


def _build_event(event_type: str, data: dict) -> str:
    """Build a JSON event payload with timestamp."""
    payload = {
        "event": event_type,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return json.dumps(payload)


async def _publish(business_id: str, team_id: Optional[str], event_type: str, data: dict):
    """
    Publish an event to Redis PubSub channels.

    Always publishes to the business-level channel (owner).
    If team_id is provided, also publishes to the team-specific channel.
    """
    redis = _get_redis()
    if not redis:
        logger.warning("[PROPAGATOR] Redis unavailable — event not published: %s", event_type)
        return

    message = _build_event(event_type, data)

    try:
        # Business-level channel (owner sees ALL events)
        biz_channel = f"clean:{business_id}:sse:schedule"
        await redis.publish(biz_channel, message)
        logger.debug("[PROPAGATOR] Published %s to %s", event_type, biz_channel)

        # Team-specific channel
        if team_id:
            team_channel = f"clean:{business_id}:sse:team:{team_id}"
            await redis.publish(team_channel, message)
            logger.debug("[PROPAGATOR] Published %s to %s", event_type, team_channel)

    except Exception as e:
        logger.error("[PROPAGATOR] Redis publish error: %s", e)


# ============================================
# PUBLIC API — called by schedule_service, bookings routes, etc.
# ============================================

async def on_schedule_generated(
    business_id: str,
    date_str: str,
    teams: list[dict],
):
    """
    Called after the schedule engine generates a daily schedule.

    Args:
        business_id: The business UUID
        date_str: ISO date string (YYYY-MM-DD)
        teams: List of team dicts with {team_id, team_name, job_count}
    """
    for team_info in teams:
        data = {
            "action": "generated",
            "team_id": team_info.get("team_id"),
            "team_name": team_info.get("team_name", ""),
            "scheduled_date": date_str,
            "job_count": team_info.get("job_count", 0),
        }
        await _publish(business_id, team_info.get("team_id"), "schedule.generated", data)

    logger.info(
        "[PROPAGATOR] schedule.generated for %s on %s (%d teams)",
        business_id, date_str, len(teams),
    )


async def on_booking_created(
    business_id: str,
    booking: dict,
):
    """Called when a new booking is created or assigned to a team."""
    data = {
        "action": "added",
        "booking_id": booking.get("id"),
        "team_id": booking.get("team_id"),
        "scheduled_date": booking.get("scheduled_date"),
        "scheduled_start": booking.get("scheduled_start"),
        "scheduled_end": booking.get("scheduled_end"),
        "client_name": booking.get("client_name", ""),
        "service_name": booking.get("service_name", ""),
        "status": booking.get("status", "scheduled"),
    }
    await _publish(business_id, booking.get("team_id"), "schedule.changed", data)
    logger.info("[PROPAGATOR] schedule.changed (added) booking=%s", booking.get("id"))


async def on_booking_updated(
    business_id: str,
    booking: dict,
    old_team_id: Optional[str] = None,
):
    """
    Called when a booking is updated (time change, team reassignment, etc.).
    If team changed, publishes to both old and new team channels.
    """
    data = {
        "action": "updated",
        "booking_id": booking.get("id"),
        "team_id": booking.get("team_id"),
        "scheduled_date": booking.get("scheduled_date"),
        "scheduled_start": booking.get("scheduled_start"),
        "scheduled_end": booking.get("scheduled_end"),
        "client_name": booking.get("client_name", ""),
        "service_name": booking.get("service_name", ""),
        "status": booking.get("status"),
    }

    # Publish to current team
    await _publish(business_id, booking.get("team_id"), "schedule.changed", data)

    # If team changed, also notify old team that job was removed
    if old_team_id and old_team_id != booking.get("team_id"):
        removed_data = {
            "action": "removed",
            "booking_id": booking.get("id"),
            "team_id": old_team_id,
            "scheduled_date": booking.get("scheduled_date"),
        }
        await _publish(business_id, old_team_id, "schedule.changed", removed_data)

    logger.info("[PROPAGATOR] schedule.changed (updated) booking=%s", booking.get("id"))


async def on_booking_cancelled(
    business_id: str,
    booking: dict,
):
    """Called when a booking is cancelled."""
    data = {
        "action": "cancelled",
        "booking_id": booking.get("id"),
        "team_id": booking.get("team_id"),
        "scheduled_date": booking.get("scheduled_date"),
        "client_name": booking.get("client_name", ""),
        "status": "cancelled",
    }
    await _publish(business_id, booking.get("team_id"), "booking.cancelled", data)
    logger.info("[PROPAGATOR] booking.cancelled booking=%s", booking.get("id"))


async def on_booking_confirmed(
    business_id: str,
    booking: dict,
):
    """Called when a booking is confirmed."""
    data = {
        "action": "confirmed",
        "booking_id": booking.get("id"),
        "team_id": booking.get("team_id"),
        "scheduled_date": booking.get("scheduled_date"),
        "scheduled_start": booking.get("scheduled_start"),
        "client_name": booking.get("client_name", ""),
        "status": "confirmed",
    }
    await _publish(business_id, booking.get("team_id"), "booking.confirmed", data)
    logger.info("[PROPAGATOR] booking.confirmed booking=%s", booking.get("id"))


async def on_booking_rescheduled(
    business_id: str,
    booking: dict,
    old_date: str,
    old_team_id: Optional[str] = None,
):
    """Called when a booking is rescheduled to a different date/time."""
    data = {
        "action": "updated",
        "booking_id": booking.get("id"),
        "team_id": booking.get("team_id"),
        "scheduled_date": booking.get("scheduled_date"),
        "scheduled_start": booking.get("scheduled_start"),
        "scheduled_end": booking.get("scheduled_end"),
        "client_name": booking.get("client_name", ""),
        "service_name": booking.get("service_name", ""),
        "status": booking.get("status"),
        "old_date": old_date,
    }
    await _publish(business_id, booking.get("team_id"), "schedule.changed", data)

    # If team changed, notify old team
    effective_old_team = old_team_id or booking.get("team_id")
    if effective_old_team and effective_old_team != booking.get("team_id"):
        removed_data = {
            "action": "removed",
            "booking_id": booking.get("id"),
            "team_id": effective_old_team,
            "scheduled_date": old_date,
        }
        await _publish(business_id, effective_old_team, "schedule.changed", removed_data)

    logger.info("[PROPAGATOR] schedule.changed (rescheduled) booking=%s", booking.get("id"))
