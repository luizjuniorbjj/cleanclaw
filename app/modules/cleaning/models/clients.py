"""
Xcleaners v3 — CleaningClient Pydantic models.
Maps to: cleaning_clients table (migration 011).

Enhanced for S2.3: preferred_contact, tags, billing_address,
property details, access codes, pet info, cleaning preferences.
"""

from typing import Optional
from pydantic import BaseModel, Field


# ============================================
# PROPERTY (embedded in client — no separate table)
# ============================================

class PropertyCreate(BaseModel):
    """Property details embedded within a client record.
    Since the DB stores property data inline on cleaning_clients,
    this model extracts/organizes property fields for the API.
    """
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="US", max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = Field(
        None,
        pattern=r"^(house|apartment|condo|townhouse|office|retail|other)$"
    )
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=0)
    # Access info
    access_instructions: Optional[str] = None
    key_location: Optional[str] = Field(None, max_length=255)
    lockbox_code: Optional[str] = Field(None, max_length=50)
    alarm_code: Optional[str] = Field(None, max_length=50)
    gate_code: Optional[str] = Field(None, max_length=50)
    garage_code: Optional[str] = Field(None, max_length=50)
    parking_instructions: Optional[str] = Field(None, max_length=500)
    # Pet info
    has_pets: bool = False
    pet_details: Optional[str] = Field(None, max_length=255)
    pet_type: Optional[str] = Field(None, max_length=50)
    pet_name: Optional[str] = Field(None, max_length=100)
    pet_temperament: Optional[str] = Field(None, max_length=100)
    pet_location_during_cleaning: Optional[str] = Field(None, max_length=255)
    # Cleaning preferences
    products_to_use: Optional[str] = None
    products_to_avoid: Optional[str] = None
    rooms_to_skip: Optional[str] = None
    special_instructions: Optional[str] = None
    preferred_cleaning_order: Optional[str] = None


class PropertyResponse(BaseModel):
    """Property details in API response."""
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    access_instructions: Optional[str] = None
    key_location: Optional[str] = None
    lockbox_code: Optional[str] = None
    alarm_code: Optional[str] = None
    gate_code: Optional[str] = None
    garage_code: Optional[str] = None
    parking_instructions: Optional[str] = None
    has_pets: bool = False
    pet_details: Optional[str] = None
    pet_type: Optional[str] = None
    pet_name: Optional[str] = None
    pet_temperament: Optional[str] = None
    pet_location_during_cleaning: Optional[str] = None
    products_to_use: Optional[str] = None
    products_to_avoid: Optional[str] = None
    rooms_to_skip: Optional[str] = None
    special_instructions: Optional[str] = None
    preferred_cleaning_order: Optional[str] = None


# ============================================
# CREATE
# ============================================

class CleaningClientCreate(BaseModel):
    """Input model for creating a cleaning client.
    S2.3 enhanced: preferred_contact, tags, billing_address, property.
    """
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    phone_secondary: Optional[str] = Field(None, max_length=30)
    preferred_contact: Optional[str] = Field(
        None,
        pattern=r"^(phone|email|text|whatsapp)$"
    )
    # Billing address (may differ from property address)
    billing_address: Optional[str] = Field(None, max_length=500)
    # Tags for categorization
    tags: list[str] = Field(default_factory=list)
    internal_notes: Optional[str] = None
    # Property details (inline — DB stores on same row)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="US", max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = Field(
        None,
        pattern=r"^(house|apartment|condo|townhouse|office|retail|other)$"
    )
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=0)
    has_pets: bool = False
    pet_details: Optional[str] = Field(None, max_length=255)
    access_instructions: Optional[str] = None
    preferred_day: Optional[str] = Field(None, max_length=15)
    preferred_time_start: Optional[str] = None  # HH:MM format
    preferred_time_end: Optional[str] = None
    notes: Optional[str] = None
    source: str = Field(
        default="manual",
        pattern=r"^(manual|ai_chat|booking_page|referral|import|lead_conversion)$"
    )


# ============================================
# UPDATE
# ============================================

class CleaningClientUpdate(BaseModel):
    """Partial update model for a cleaning client."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=30)
    phone_secondary: Optional[str] = Field(None, max_length=30)
    preferred_contact: Optional[str] = Field(
        None,
        pattern=r"^(phone|email|text|whatsapp)$"
    )
    billing_address: Optional[str] = Field(None, max_length=500)
    tags: Optional[list[str]] = None
    internal_notes: Optional[str] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=50)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = Field(
        None,
        pattern=r"^(house|apartment|condo|townhouse|office|retail|other)$"
    )
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[float] = Field(None, ge=0)
    square_feet: Optional[int] = Field(None, ge=0)
    has_pets: Optional[bool] = None
    pet_details: Optional[str] = Field(None, max_length=255)
    access_instructions: Optional[str] = None
    preferred_day: Optional[str] = Field(None, max_length=15)
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(
        None,
        pattern=r"^(active|paused|former|inactive|blocked)$"
    )


# ============================================
# RESPONSE
# ============================================

class FinancialSummary(BaseModel):
    """Client financial summary for detail view."""
    total_spent: float = 0.0
    outstanding_balance: float = 0.0
    total_invoices: int = 0
    overdue_invoices: int = 0


class CleaningClientResponse(BaseModel):
    """API response model for a cleaning client."""
    id: str
    business_id: str
    user_id: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    phone_secondary: Optional[str] = None
    preferred_contact: Optional[str] = None
    billing_address: Optional[str] = None
    tags: list[str] = []
    internal_notes: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    has_pets: bool = False
    pet_details: Optional[str] = None
    access_instructions: Optional[str] = None
    preferred_day: Optional[str] = None
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    notes: Optional[str] = None
    source: str = "manual"
    status: str = "active"
    lifetime_value: float = 0.0
    total_bookings: int = 0
    last_service_date: Optional[str] = None
    active_schedules_count: int = 0
    financial_summary: Optional[FinancialSummary] = None
    created_at: str
    updated_at: str


class CleaningClientListResponse(BaseModel):
    """Paginated list of cleaning clients."""
    clients: list[CleaningClientResponse]
    total: int
    page: int = 1
    per_page: int = 25
