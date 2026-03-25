"""
Xcleaners v3 — Booking Pydantic models.
Maps to: cleaning_bookings table (migration 011 + 012 ALTER adds team_id).
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


# ============================================
# CREATE
# ============================================

class BookingCreate(BaseModel):
    """Input model for creating a booking."""
    client_id: str
    service_id: str
    recurring_schedule_id: Optional[str] = None
    # Scheduling
    scheduled_date: str  # YYYY-MM-DD
    scheduled_start: str  # HH:MM
    scheduled_end: Optional[str] = None  # HH:MM
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    # Location (optional override — defaults to client address)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_instructions: Optional[str] = None
    # Assignment
    assigned_team: list[str] = Field(
        default_factory=list,
        description="Array of team_member_id UUIDs (JSONB in DB)."
    )
    lead_cleaner_id: Optional[str] = None
    team_id: Optional[str] = Field(
        None,
        description="v3: Primary team assignment (cleaning_teams.id)."
    )
    # Pricing
    quoted_price: Optional[float] = Field(None, ge=0)
    discount_amount: float = Field(default=0.0, ge=0)
    discount_reason: Optional[str] = Field(None, max_length=255)
    # Extras
    special_instructions: Optional[str] = None
    extras: list[dict] = Field(
        default_factory=list,
        description="Add-on services: [{service_id, name, price}]."
    )
    source: str = Field(
        default="manual",
        pattern=r"^(manual|ai_chat|booking_page|recurring|phone|referral)$"
    )


# ============================================
# UPDATE
# ============================================

class BookingUpdate(BaseModel):
    """Partial update model for a booking."""
    scheduled_date: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_instructions: Optional[str] = None
    assigned_team: Optional[list[str]] = None
    lead_cleaner_id: Optional[str] = None
    team_id: Optional[str] = None
    quoted_price: Optional[float] = Field(None, ge=0)
    final_price: Optional[float] = Field(None, ge=0)
    discount_amount: Optional[float] = Field(None, ge=0)
    discount_reason: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(
        None,
        pattern=r"^(draft|scheduled|confirmed|in_progress|completed|cancelled|no_show|rescheduled)$"
    )
    cancellation_reason: Optional[str] = None
    cancelled_by: Optional[str] = Field(
        None,
        pattern=r"^(client|business|system)$"
    )
    special_instructions: Optional[str] = None
    extras: Optional[list[dict]] = None
    confirmation_sent: Optional[bool] = None
    reminder_sent: Optional[bool] = None


# ============================================
# RESPONSE
# ============================================

class BookingResponse(BaseModel):
    """API response model for a booking."""
    id: str
    business_id: str
    client_id: str
    service_id: str
    recurring_schedule_id: Optional[str] = None
    # Scheduling
    scheduled_date: str
    scheduled_start: str
    scheduled_end: Optional[str] = None
    actual_start: Optional[str] = None
    actual_end: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    # Location
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    access_instructions: Optional[str] = None
    # Assignment
    assigned_team: list[Any] = []
    lead_cleaner_id: Optional[str] = None
    team_id: Optional[str] = None  # v3
    # Pricing
    quoted_price: Optional[float] = None
    final_price: Optional[float] = None
    discount_amount: float = 0.0
    discount_reason: Optional[str] = None
    # Status
    status: str
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancelled_by: Optional[str] = None
    # Extras
    special_instructions: Optional[str] = None
    extras: list[Any] = []
    source: str
    confirmation_sent: bool = False
    reminder_sent: bool = False
    created_at: str
    updated_at: str


class BookingListResponse(BaseModel):
    """Paginated list of bookings."""
    bookings: list[BookingResponse]
    total: int
