"""
Xcleaners v3 — Notification Routes (Sprint 4).

Endpoints:
  POST /api/v1/clean/{slug}/notifications/send         — manual notification
  GET  /api/v1/clean/{slug}/notifications               — notification history
  GET  /api/v1/clean/{slug}/notifications/stats         — delivery stats by channel
  POST /api/v1/clean/{slug}/notifications/test-sms      — test SMS delivery
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.services.notification_service import (
    send_notification,
    get_notifications,
    get_notification_stats,
)

logger = logging.getLogger("xcleaners.notification_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}",
    tags=["Xcleaners Notifications"],
)


# ============================================
# REQUEST MODELS
# ============================================

class SendNotificationRequest(BaseModel):
    target_type: str = Field(..., pattern=r"^(client|cleaner|owner)$")
    target_id: str
    template_key: str
    data: dict = Field(default_factory=dict)
    channel_priority: Optional[list] = None


class TestSMSRequest(BaseModel):
    phone: str = Field(..., min_length=10)
    message: str = Field(default="Xcleaners test SMS. If you received this, SMS is working!")


# ============================================
# SEND NOTIFICATION (manual)
# ============================================

@router.post("/notifications/send")
async def send_notification_route(
    slug: str,
    body: SendNotificationRequest,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Send a manual notification to a client, cleaner, or owner."""
    result = await send_notification(
        db=db,
        business_id=user["business_id"],
        target_type=body.target_type,
        target_id=body.target_id,
        template_key=body.template_key,
        data=body.data,
        channel_priority=body.channel_priority,
    )
    return result


# ============================================
# NOTIFICATION HISTORY
# ============================================

@router.get("/notifications")
async def list_notifications(
    slug: str,
    channel: Optional[str] = Query(None, description="Filter by channel: sms, whatsapp, email, push"),
    status: Optional[str] = Query(None, description="Filter by status: pending, sent, delivered, failed"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """List sent notification history with filters."""
    return await get_notifications(
        db, user["business_id"],
        channel=channel, status=status,
        page=page, page_size=page_size,
    )


# ============================================
# DELIVERY STATS
# ============================================

@router.get("/notifications/stats")
async def notification_stats(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Delivery stats by channel including SMS quota."""
    return await get_notification_stats(db, user["business_id"])


# ============================================
# TEST SMS
# ============================================

@router.post("/notifications/test-sms")
async def test_sms(
    slug: str,
    body: TestSMSRequest,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Test SMS delivery to a phone number."""
    from app.modules.cleaning.services.sms_service import send_sms

    result = await send_sms(
        db, user["business_id"], body.phone, body.message,
        target_type="owner", target_id=user.get("user_id"),
        template_key="test",
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "SMS send failed"),
        )
    return result
