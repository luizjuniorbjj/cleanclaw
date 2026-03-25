"""
Xcleaners v3 — AI Scheduling Routes.

Endpoints for AI-powered schedule optimization, team suggestions,
duration predictions, and business insights.

All endpoints gated behind Intermediate+ plan via require_minimum_plan.

Endpoints:
  POST /api/v1/clean/{slug}/ai/optimize-schedule/{date}  — optimize schedule
  POST /api/v1/clean/{slug}/ai/suggest-team/{booking_id}  — suggest team
  POST /api/v1/clean/{slug}/ai/predict-duration            — predict duration
  GET  /api/v1/clean/{slug}/ai/insights                    — patterns & insights
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import get_db, Database
from app.modules.cleaning.middleware.plan_guard import require_minimum_plan
from app.modules.cleaning.middleware.role_guard import require_role

logger = logging.getLogger("xcleaners.ai_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}/ai",
    tags=["Xcleaners AI Scheduling"],
)


# ============================================
# REQUEST MODELS
# ============================================

class PredictDurationRequest(BaseModel):
    """Request body for duration prediction."""
    client_id: str = Field(..., description="UUID of the client.")
    service_type_id: Optional[str] = Field(
        None, description="UUID of the service type (optional, improves accuracy)."
    )


# ============================================
# POST /ai/optimize-schedule/{date}
# ============================================

@router.post("/optimize-schedule/{date}")
async def optimize_schedule(
    slug: str,
    date: str,
    user: dict = Depends(require_minimum_plan("intermediate")),
    db: Database = Depends(get_db),
):
    """
    AI analyzes the schedule for a specific date and suggests optimizations.

    Suggestions include:
    - Travel distance reduction (geographic clustering)
    - Workload rebalancing across teams
    - Team swap recommendations
    - Gap identification for additional jobs

    Requires: Intermediate or Maximum plan.
    Requires: Owner role.
    """
    # Verify owner role (require_minimum_plan already authenticated the user)
    business_id = user["business_id"]

    # Verify the user is an owner in this cleaning business
    role = await _get_user_cleaning_role(user, business_id, db)
    if role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the business owner can use AI scheduling features.",
        )

    # Validate date format
    _validate_date(date)

    from app.modules.cleaning.services.ai_scheduling import optimize_schedule as _optimize
    result = await _optimize(business_id, date, db)

    return result


# ============================================
# POST /ai/suggest-team/{booking_id}
# ============================================

@router.post("/suggest-team/{booking_id}")
async def suggest_team(
    slug: str,
    booking_id: str,
    user: dict = Depends(require_minimum_plan("intermediate")),
    db: Database = Depends(get_db),
):
    """
    AI suggests the best team to assign for a specific booking.

    Considers proximity, workload balance, client preference,
    and service continuity (same team as last time).

    Requires: Intermediate or Maximum plan.
    Requires: Owner role.
    """
    business_id = user["business_id"]

    role = await _get_user_cleaning_role(user, business_id, db)
    if role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the business owner can use AI scheduling features.",
        )

    from app.modules.cleaning.services.ai_scheduling import suggest_team_assignment
    result = await suggest_team_assignment(business_id, booking_id, db)

    return result


# ============================================
# POST /ai/predict-duration
# ============================================

@router.post("/predict-duration")
async def predict_duration(
    slug: str,
    body: PredictDurationRequest,
    user: dict = Depends(require_minimum_plan("intermediate")),
    db: Database = Depends(get_db),
):
    """
    Predict cleaning duration for a client based on history.

    Uses historical actual durations, weighted by recency,
    to predict how long the next cleaning will take.

    Requires: Intermediate or Maximum plan.
    Requires: Owner role.
    """
    business_id = user["business_id"]

    role = await _get_user_cleaning_role(user, business_id, db)
    if role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the business owner can use AI scheduling features.",
        )

    from app.modules.cleaning.services.ai_scheduling import predict_duration as _predict
    result = await _predict(business_id, body.client_id, body.service_type_id, db)

    return result


# ============================================
# GET /ai/insights
# ============================================

@router.get("/insights")
async def get_insights(
    slug: str,
    user: dict = Depends(require_minimum_plan("intermediate")),
    db: Database = Depends(get_db),
):
    """
    AI detects scheduling patterns and generates business insights.

    Analyzes: cancellation trends, peak days, underutilized teams,
    workload imbalances, and growth opportunities.

    Requires: Intermediate or Maximum plan.
    Requires: Owner role.
    """
    business_id = user["business_id"]

    role = await _get_user_cleaning_role(user, business_id, db)
    if role != "owner":
        raise HTTPException(
            status_code=403,
            detail="Only the business owner can use AI scheduling features.",
        )

    from app.modules.cleaning.services.ai_scheduling import detect_patterns
    result = await detect_patterns(business_id, db)

    return result


# ============================================
# HELPERS
# ============================================

async def _get_user_cleaning_role(user: dict, business_id: str, db: Database) -> Optional[str]:
    """Get the user's cleaning role in this business."""
    user_id = user.get("user_id") or user.get("sub")
    if not user_id:
        return None

    row = await db.pool.fetchrow(
        """
        SELECT role FROM cleaning_user_roles
        WHERE user_id = $1 AND business_id = $2 AND is_active = true
        """,
        user_id,
        business_id,
    )
    return row["role"] if row else None


def _validate_date(date_str: str):
    """Validate YYYY-MM-DD format."""
    try:
        from datetime import datetime
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.",
        )
