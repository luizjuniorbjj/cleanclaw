"""
CleanClaw v3 — Plan Routes.

Endpoints for plan information, usage limits, and plan upgrades.
These routes use the plan_guard middleware for plan resolution.

Endpoints:
  GET  /api/v1/clean/{slug}/plan          — current plan info + feature gates
  GET  /api/v1/clean/{slug}/plan/limits   — current usage vs plan limits
  POST /api/v1/clean/{slug}/plan/upgrade  — redirect to Stripe checkout
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.database import get_db, Database
from app.modules.cleaning.models.auth import PLAN_HIERARCHY, PLAN_LIMITS
from app.modules.cleaning.middleware.plan_guard import (
    get_business_plan,
    get_business_plan_by_slug,
)
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.routes.auth_middleware import get_cleaning_role

logger = logging.getLogger("cleanclaw.plan_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}/plan",
    tags=["CleanClaw Plan"],
)

# Feature gates per plan (what features are available)
PLAN_FEATURES = {
    "basic": [
        "teams",
        "clients",
        "schedule_manual",
        "bookings",
        "invoices_basic",
        "sms_notifications",
    ],
    "intermediate": [
        "teams",
        "clients",
        "schedule_manual",
        "schedule_ai",
        "bookings",
        "invoices_basic",
        "invoices_advanced",
        "sms_notifications",
        "homeowner_portal",
        "analytics_basic",
        "team_gps",
    ],
    "maximum": [
        "teams",
        "clients",
        "schedule_manual",
        "schedule_ai",
        "bookings",
        "invoices_basic",
        "invoices_advanced",
        "sms_notifications",
        "homeowner_portal",
        "analytics_basic",
        "analytics_advanced",
        "team_gps",
        "public_booking",
        "site_integration",
        "api_access",
        "white_label",
    ],
}


# ============================================
# GET /api/v1/clean/{slug}/plan
# ============================================

@router.get("")
async def get_plan_info(
    slug: str,
    user: dict = Depends(get_cleaning_role),
    db: Database = Depends(get_db),
):
    """
    Get current plan info including feature gates.
    Any authenticated user with a cleaning role can read plan info.
    """
    plan = await get_business_plan(user["business_id"], db)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["basic"])
    features = PLAN_FEATURES.get(plan, PLAN_FEATURES["basic"])

    return {
        "plan": plan,
        "limits": limits,
        "features": features,
        "hierarchy": PLAN_HIERARCHY,
        "can_upgrade": plan != "maximum",
    }


# ============================================
# GET /api/v1/clean/{slug}/plan/limits
# ============================================

@router.get("/limits")
async def get_plan_limits(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """
    Get current usage vs plan limits. Owner only.
    Shows how many teams, clients, and SMS have been used vs the limit.
    """
    business_id = user["business_id"]
    plan = await get_business_plan(business_id, db)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["basic"])

    # Count current usage
    team_count = await db.pool.fetchval(
        "SELECT COUNT(*) FROM cleaning_teams WHERE business_id = $1",
        business_id,
    )
    client_count = await db.pool.fetchval(
        "SELECT COUNT(*) FROM cleaning_client_schedules WHERE business_id = $1",
        business_id,
    )

    # SMS count for current month
    from datetime import datetime
    current_month = datetime.utcnow().strftime("%Y-%m")
    sms_key = f"clean:{business_id}:sms:count:{current_month}"
    sms_count = 0
    try:
        from app.redis_client import get_redis
        redis = get_redis()
        if redis:
            val = await redis.get(sms_key)
            sms_count = int(val) if val else 0
    except Exception:
        pass

    def _format_limit(limit_val):
        return "unlimited" if limit_val == -1 else limit_val

    return {
        "plan": plan,
        "usage": {
            "teams": {
                "current": team_count,
                "limit": _format_limit(limits["teams"]),
                "remaining": "unlimited" if limits["teams"] == -1 else max(0, limits["teams"] - team_count),
            },
            "clients": {
                "current": client_count,
                "limit": _format_limit(limits["clients"]),
                "remaining": "unlimited" if limits["clients"] == -1 else max(0, limits["clients"] - client_count),
            },
            "sms_monthly": {
                "current": sms_count,
                "limit": _format_limit(limits["sms_monthly"]),
                "remaining": "unlimited" if limits["sms_monthly"] == -1 else max(0, limits["sms_monthly"] - sms_count),
            },
        },
    }


# ============================================
# POST /api/v1/clean/{slug}/plan/upgrade
# ============================================

@router.post("/upgrade")
async def upgrade_plan(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """
    Initiate plan upgrade. Owner only.
    Returns a Stripe checkout URL for the upgrade.
    (Stub -- full Stripe integration in a later story.)
    """
    business_id = user["business_id"]
    plan = await get_business_plan(business_id, db)

    if plan == "maximum":
        raise HTTPException(
            status_code=400,
            detail="You are already on the maximum plan.",
        )

    # Determine next plan
    current_index = PLAN_HIERARCHY.index(plan) if plan in PLAN_HIERARCHY else 0
    next_plan = PLAN_HIERARCHY[current_index + 1]

    # TODO: Integrate with Stripe checkout (future story)
    # For now, return the upgrade target info
    return {
        "current_plan": plan,
        "upgrade_to": next_plan,
        "upgrade_limits": PLAN_LIMITS[next_plan],
        "upgrade_features": PLAN_FEATURES[next_plan],
        "message": "Stripe checkout integration coming in a future story.",
    }
