"""
Xcleaners v3 — Team & TeamAssignment Pydantic models.
Maps to: cleaning_teams (migration 012), cleaning_team_assignments (012),
         cleaning_team_members (011 + 012 ALTER).
"""

from typing import Optional
from datetime import date
from pydantic import BaseModel, Field


# ============================================
# TEAM — CREATE
# ============================================

class TeamCreate(BaseModel):
    """Input model for creating a cleaning team."""
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")
    team_lead_id: Optional[str] = Field(
        None,
        description="UUID of a cleaning_team_member to designate as team lead."
    )
    max_daily_jobs: int = Field(default=6, ge=1, le=50)
    service_area_ids: list[str] = Field(
        default_factory=list,
        description="Array of cleaning_areas.id UUIDs."
    )
    is_active: bool = True


# ============================================
# TEAM — UPDATE
# ============================================

class TeamUpdate(BaseModel):
    """Partial update model for a cleaning team."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    team_lead_id: Optional[str] = None
    max_daily_jobs: Optional[int] = Field(None, ge=1, le=50)
    service_area_ids: Optional[list[str]] = None
    is_active: Optional[bool] = None


# ============================================
# TEAM — RESPONSE
# ============================================

class TeamResponse(BaseModel):
    """API response model for a cleaning team."""
    id: str
    business_id: str
    name: str
    color: str
    team_lead_id: Optional[str] = None
    max_daily_jobs: int
    service_area_ids: list[str] = []
    is_active: bool
    created_at: str
    updated_at: str


class TeamListResponse(BaseModel):
    """Paginated list of teams."""
    teams: list[TeamResponse]
    total: int


# ============================================
# TEAM ASSIGNMENT — CREATE
# ============================================

class TeamAssignmentCreate(BaseModel):
    """Assign a team member to a team."""
    team_id: str
    member_id: str
    role_in_team: str = Field(
        default="member",
        pattern=r"^(lead|member|trainee)$"
    )
    effective_from: Optional[date] = None  # defaults to today in DB
    effective_until: Optional[date] = None


# ============================================
# TEAM ASSIGNMENT — UPDATE
# ============================================

class TeamAssignmentUpdate(BaseModel):
    """Partial update model for a team assignment."""
    role_in_team: Optional[str] = Field(
        None,
        pattern=r"^(lead|member|trainee)$"
    )
    effective_until: Optional[date] = None
    is_active: Optional[bool] = None


# ============================================
# TEAM ASSIGNMENT — RESPONSE
# ============================================

class TeamAssignmentResponse(BaseModel):
    """API response model for a team assignment."""
    id: str
    team_id: str
    member_id: str
    role_in_team: str
    effective_from: str
    effective_until: Optional[str] = None
    is_active: bool
    created_at: str


# ============================================
# TEAM MEMBER — RESPONSE (from 011 + 012 ALTER)
# ============================================

# ============================================
# TEAM MEMBER — CREATE
# ============================================

class MemberCreate(BaseModel):
    """Input model for creating a team member."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str = Field(
        default="cleaner",
        pattern=r"^(cleaner|lead_cleaner|supervisor|manager)$"
    )
    employment_type: str = Field(
        default="employee",
        pattern=r"^(employee|contractor|part_time)$"
    )
    hourly_rate: Optional[float] = Field(None, ge=0)
    skills: list[str] = Field(
        default_factory=list,
        description="Skill tags: deep_cleaning, move_in_out, post_construction, eco_products, pet_friendly, carpet, windows"
    )


# ============================================
# TEAM MEMBER — UPDATE
# ============================================

class MemberUpdate(BaseModel):
    """Partial update model for a team member."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(
        None,
        pattern=r"^(cleaner|lead_cleaner|supervisor|manager)$"
    )
    employment_type: Optional[str] = Field(
        None,
        pattern=r"^(employee|contractor|part_time)$"
    )
    hourly_rate: Optional[float] = Field(None, ge=0)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    max_daily_hours: Optional[float] = Field(None, ge=1, le=24)
    can_drive: Optional[bool] = None
    home_zip: Optional[str] = None
    notes: Optional[str] = None
    certifications: Optional[list[str]] = None
    status: Optional[str] = Field(
        None,
        pattern=r"^(active|inactive|on_leave|terminated)$"
    )


# ============================================
# TEAM MEMBER — RESPONSE (from 011 + 012 ALTER)
# ============================================

class TeamMemberResponse(BaseModel):
    """API response model for a cleaning team member.
    Combines original 011 columns with 012 invitation fields.
    """
    id: str
    business_id: str
    user_id: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str  # cleaner, lead_cleaner, supervisor, manager
    employment_type: str
    hourly_rate: Optional[float] = None
    color: Optional[str] = None
    photo_url: Optional[str] = None
    certifications: list[str] = []
    max_daily_hours: float = 8.0
    can_drive: bool = True
    home_zip: Optional[str] = None
    notes: Optional[str] = None
    status: str
    hire_date: Optional[str] = None
    termination_date: Optional[str] = None
    # v3 fields (012)
    invitation_email: Optional[str] = None
    invitation_status: str = "none"  # none, pending, accepted, expired
    invited_at: Optional[str] = None
    created_at: str
    updated_at: str
