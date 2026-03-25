"""
Xcleaners v3 — CleaningService Pydantic models.
Maps to: cleaning_services table (migration 011).
"""

from typing import Optional
from pydantic import BaseModel, Field


# ============================================
# CREATE
# ============================================

class CleaningServiceCreate(BaseModel):
    """Input model for creating a cleaning service."""
    name: str = Field(..., min_length=1, max_length=150)
    slug: Optional[str] = Field(None, max_length=100, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    description: Optional[str] = None
    category: str = Field(
        default="residential",
        pattern=r"^(residential|commercial|specialized|addon)$"
    )
    base_price: Optional[float] = Field(None, ge=0)
    price_unit: str = Field(
        default="flat",
        pattern=r"^(flat|hourly|per_sqft|per_room)$"
    )
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    min_team_size: int = Field(default=1, ge=1)
    is_active: bool = True
    sort_order: int = Field(default=0, ge=0)
    icon: Optional[str] = Field(None, max_length=50)


# ============================================
# UPDATE
# ============================================

class CleaningServiceUpdate(BaseModel):
    """Partial update model for a cleaning service."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    description: Optional[str] = None
    category: Optional[str] = Field(
        None,
        pattern=r"^(residential|commercial|specialized|addon)$"
    )
    base_price: Optional[float] = Field(None, ge=0)
    price_unit: Optional[str] = Field(
        None,
        pattern=r"^(flat|hourly|per_sqft|per_room)$"
    )
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    min_team_size: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0)
    icon: Optional[str] = Field(None, max_length=50)


# ============================================
# RESPONSE
# ============================================

class CleaningServiceResponse(BaseModel):
    """API response model for a cleaning service."""
    id: str
    business_id: str
    name: str
    slug: str
    description: Optional[str] = None
    category: str
    base_price: Optional[float] = None
    price_unit: str
    estimated_duration_minutes: Optional[int] = None
    min_team_size: int
    is_active: bool
    sort_order: int
    icon: Optional[str] = None
    created_at: str
    updated_at: str


class CleaningServiceListResponse(BaseModel):
    """Paginated list of cleaning services."""
    services: list[CleaningServiceResponse]
    total: int


# ============================================
# CHECKLIST
# ============================================

class ChecklistItemCreate(BaseModel):
    """Input model for a checklist item."""
    name: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    room: Optional[str] = Field(None, max_length=100)
    is_required: bool = True
    sort_order: int = Field(default=0, ge=0)
    estimated_minutes: Optional[int] = Field(None, ge=1)


class ChecklistItemResponse(BaseModel):
    """Response model for a checklist item."""
    id: str
    room: Optional[str] = None
    task_description: str
    is_required: bool
    sort_order: int
    estimated_minutes: Optional[int] = None


class ChecklistResponse(BaseModel):
    """Response model for a service checklist."""
    checklist_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    items: list[ChecklistItemResponse] = []
    total: int = 0
