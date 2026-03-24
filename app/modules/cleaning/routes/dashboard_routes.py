"""
CleanClaw v3 — Dashboard Routes.

Endpoints:
  GET /api/v1/clean/{slug}/dashboard           — summary KPIs
  GET /api/v1/clean/{slug}/dashboard/revenue   — revenue chart data
  GET /api/v1/clean/{slug}/dashboard/teams     — team performance
  GET /api/v1/clean/{slug}/dashboard/bookings  — booking stats
  GET /api/v1/clean/{slug}/dashboard/clients   — client stats
  POST /api/v1/clean/{slug}/dashboard/analytics — aggregate daily analytics

All endpoints require the 'owner' role.
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.services.dashboard_service import (
    get_dashboard_summary,
    get_revenue_chart,
    get_team_performance,
    get_booking_stats,
    get_client_stats,
    aggregate_daily_analytics,
)

logger = logging.getLogger("cleanclaw.dashboard_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}/dashboard",
    tags=["CleanClaw Dashboard"],
)


@router.get("")
async def dashboard_summary(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Return top-level KPIs for the owner dashboard."""
    return await get_dashboard_summary(db, user["business_id"])


@router.get("/revenue")
async def dashboard_revenue(
    slug: str,
    period: str = Query("month", description="week | month | quarter"),
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Return revenue chart data for the specified period."""
    if period not in ("week", "month", "quarter"):
        period = "month"
    return await get_revenue_chart(db, user["business_id"], period)


@router.get("/teams")
async def dashboard_teams(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Return performance stats per team."""
    return await get_team_performance(db, user["business_id"])


@router.get("/bookings")
async def dashboard_bookings(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Return booking completion/cancellation/no-show rates."""
    return await get_booking_stats(db, user["business_id"])


@router.get("/clients")
async def dashboard_clients(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Return client statistics."""
    return await get_client_stats(db, user["business_id"])


@router.post("/analytics")
async def dashboard_aggregate(
    slug: str,
    body: dict = None,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Aggregate daily analytics for a specific date (or today)."""
    from datetime import datetime

    target = None
    if body and body.get("date"):
        try:
            target = datetime.strptime(body["date"], "%Y-%m-%d").date()
        except ValueError:
            pass

    return await aggregate_daily_analytics(db, user["business_id"], target)
