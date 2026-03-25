"""
Xcleaners v3 — Settings Routes.

Endpoints:
  GET  /api/v1/clean/{slug}/settings                   — get all settings
  PUT  /api/v1/clean/{slug}/settings                   — update settings
  GET  /api/v1/clean/{slug}/settings/areas              — list service areas
  POST /api/v1/clean/{slug}/settings/areas              — add service area
  PUT  /api/v1/clean/{slug}/settings/areas/{area_id}    — update area
  DELETE /api/v1/clean/{slug}/settings/areas/{area_id}  — delete area
  GET  /api/v1/clean/{slug}/settings/pricing            — list pricing rules
  POST /api/v1/clean/{slug}/settings/pricing            — add pricing rule
  PUT  /api/v1/clean/{slug}/settings/pricing/{rule_id}  — update rule
  DELETE /api/v1/clean/{slug}/settings/pricing/{rule_id} — delete rule

All endpoints require the 'owner' role.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.services.settings_service import (
    get_business_settings,
    update_business_settings,
    list_service_areas,
    create_service_area,
    update_service_area,
    delete_service_area,
    list_pricing_rules,
    create_pricing_rule,
    update_pricing_rule,
    delete_pricing_rule,
)

logger = logging.getLogger("xcleaners.settings_routes")


# ============================================
# REQUEST MODELS
# ============================================

class BusinessSettingsUpdate(BaseModel):
    """
    Validated body for PUT /settings.

    Fields mirror what update_business_settings accepts:
      - business_table_keys: name, timezone  (written to businesses table)
      - contact_keys: phone, email, address, city, state, zip_code
                      (written to cleaning_settings.business_info)
      - everything else goes into cleaning_settings as-is (JSONB merge)
    """
    # Business table fields
    name: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)

    # Contact info (stored in cleaning_settings.business_info)
    phone: Optional[str] = Field(None, max_length=30)
    email: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)

    # Operational settings (merged into cleaning_settings JSONB)
    business_hours: Optional[Dict[str, Any]] = None
    cancellation_policy: Optional[Dict[str, Any]] = None
    travel_buffer_minutes: Optional[int] = Field(None, ge=0, le=240)
    auto_generate_schedule: Optional[bool] = None
    auto_generate_time: Optional[str] = Field(None, max_length=5)
    default_service_duration: Optional[int] = Field(None, ge=15, le=480)
    notification_preferences: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"  # Forward unknown keys to the JSONB merge (open-ended settings)


router = APIRouter(
    prefix="/api/v1/clean/{slug}/settings",
    tags=["Xcleaners Settings"],
)


# ============================================
# SETTINGS
# ============================================

@router.get("")
async def get_settings(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Get all business settings."""
    result = await get_business_settings(db, user["business_id"])
    if not result:
        raise HTTPException(status_code=404, detail="Business not found")
    return result


@router.put("")
async def put_settings(
    slug: str,
    body: BusinessSettingsUpdate,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Update business settings (partial merge)."""
    return await update_business_settings(
        db, user["business_id"], body.model_dump(exclude_none=True)
    )


# ============================================
# SERVICE AREAS
# ============================================

@router.get("/areas")
async def get_areas(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """List all service areas."""
    return await list_service_areas(db, user["business_id"])


@router.post("/areas")
async def add_area(
    slug: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Add a new service area."""
    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Area name is required")
    return await create_service_area(db, user["business_id"], body)


@router.put("/areas/{area_id}")
async def put_area(
    slug: str,
    area_id: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Update a service area."""
    result = await update_service_area(db, user["business_id"], area_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Area not found or no changes")
    return result


@router.delete("/areas/{area_id}")
async def del_area(
    slug: str,
    area_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Delete a service area."""
    deleted = await delete_service_area(db, user["business_id"], area_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Area not found")
    return {"message": "Area deleted", "id": area_id}


# ============================================
# PRICING RULES
# ============================================

@router.get("/pricing")
async def get_pricing(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """List all pricing rules."""
    return await list_pricing_rules(db, user["business_id"])


@router.post("/pricing")
async def add_pricing(
    slug: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Add a new pricing rule."""
    if not body.get("name"):
        raise HTTPException(status_code=400, detail="Rule name is required")
    if not body.get("rule_type"):
        raise HTTPException(status_code=400, detail="Rule type is required")
    valid_types = {"base_price", "addon", "multiplier", "surcharge", "discount", "minimum"}
    if body["rule_type"] not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid rule_type. Must be one of: {', '.join(sorted(valid_types))}",
        )
    return await create_pricing_rule(db, user["business_id"], body)


@router.put("/pricing/{rule_id}")
async def put_pricing(
    slug: str,
    rule_id: str,
    body: dict,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Update a pricing rule."""
    result = await update_pricing_rule(db, user["business_id"], rule_id, body)
    if not result:
        raise HTTPException(status_code=404, detail="Rule not found or no changes")
    return result


@router.delete("/pricing/{rule_id}")
async def del_pricing(
    slug: str,
    rule_id: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Delete a pricing rule."""
    deleted = await delete_pricing_rule(db, user["business_id"], rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"message": "Rule deleted", "id": rule_id}
