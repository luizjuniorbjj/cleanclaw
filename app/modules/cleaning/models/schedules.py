"""
CleanClaw v3 — Schedule Pydantic models.
Maps to: cleaning_client_schedules (migration 012, new v3 table)
         cleaning_recurring_schedules (migration 011, legacy table)
         Schedule engine output models (S2.4)
"""

from typing import Optional, Any
from datetime import date
from pydantic import BaseModel, Field


# ============================================
# CLIENT SCHEDULE (v3 — migration 012)
# ============================================

class ClientScheduleCreate(BaseModel):
    """Input model for creating a recurring client schedule (v3)."""
    client_id: str
    service_id: str
    frequency: str = Field(
        ...,
        pattern=r"^(weekly|biweekly|monthly|sporadic)$"
    )
    custom_interval_days: Optional[int] = Field(
        None, ge=1,
        description="Only used when frequency='sporadic'. Days between services."
    )
    preferred_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    preferred_time_start: Optional[str] = None  # HH:MM
    preferred_time_end: Optional[str] = None  # HH:MM
    preferred_team_id: Optional[str] = None
    agreed_price: Optional[float] = Field(None, ge=0)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    min_team_size: int = Field(default=1, ge=1)
    next_occurrence: Optional[str] = None  # YYYY-MM-DD
    notes: Optional[str] = None
    status: str = Field(
        default="active",
        pattern=r"^(active|paused|cancelled)$"
    )


class ClientScheduleUpdate(BaseModel):
    """Partial update model for a client schedule (v3)."""
    frequency: Optional[str] = Field(
        None,
        pattern=r"^(weekly|biweekly|monthly|sporadic)$"
    )
    custom_interval_days: Optional[int] = Field(None, ge=1)
    preferred_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    preferred_team_id: Optional[str] = None
    agreed_price: Optional[float] = Field(None, ge=0)
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    min_team_size: Optional[int] = Field(None, ge=1)
    next_occurrence: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = Field(
        None,
        pattern=r"^(active|paused|cancelled)$"
    )


class ClientScheduleResponse(BaseModel):
    """API response model for a client schedule (v3)."""
    id: str
    business_id: str
    client_id: str
    service_id: str
    frequency: str
    custom_interval_days: Optional[int] = None
    preferred_day_of_week: Optional[int] = None
    preferred_time_start: Optional[str] = None
    preferred_time_end: Optional[str] = None
    preferred_team_id: Optional[str] = None
    agreed_price: Optional[float] = None
    estimated_duration_minutes: Optional[int] = None
    min_team_size: int = 1
    next_occurrence: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: str
    updated_at: str


class ClientScheduleListResponse(BaseModel):
    """Paginated list of client schedules."""
    schedules: list[ClientScheduleResponse]
    total: int


# ============================================
# RECURRING SCHEDULE (legacy — migration 011)
# ============================================

class RecurringScheduleCreate(BaseModel):
    """Input model for creating a recurring schedule (legacy, migration 011).
    Kept for backward compatibility with existing data.
    """
    client_id: str
    service_id: str
    frequency: str = Field(
        ...,
        pattern=r"^(weekly|biweekly|monthly|custom)$"
    )
    custom_interval_days: Optional[int] = Field(None, ge=1)
    preferred_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    preferred_time: Optional[str] = None  # HH:MM
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    assigned_team: list[str] = Field(
        default_factory=list,
        description="Array of team_member_id UUIDs (stored as JSONB)."
    )
    notes: Optional[str] = None
    agreed_price: Optional[float] = Field(None, ge=0)
    start_date: str  # YYYY-MM-DD (required)
    end_date: Optional[str] = None  # YYYY-MM-DD
    next_occurrence: Optional[str] = None  # YYYY-MM-DD


class RecurringScheduleUpdate(BaseModel):
    """Partial update model for a recurring schedule (legacy)."""
    frequency: Optional[str] = Field(
        None,
        pattern=r"^(weekly|biweekly|monthly|custom)$"
    )
    custom_interval_days: Optional[int] = Field(None, ge=1)
    preferred_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    preferred_time: Optional[str] = None
    estimated_duration_minutes: Optional[int] = Field(None, ge=1)
    assigned_team: Optional[list[str]] = None
    notes: Optional[str] = None
    agreed_price: Optional[float] = Field(None, ge=0)
    end_date: Optional[str] = None
    next_occurrence: Optional[str] = None
    status: Optional[str] = Field(
        None,
        pattern=r"^(active|paused|cancelled|completed)$"
    )
    pause_reason: Optional[str] = None


class RecurringScheduleResponse(BaseModel):
    """API response model for a recurring schedule (legacy)."""
    id: str
    business_id: str
    client_id: str
    service_id: str
    frequency: str
    custom_interval_days: Optional[int] = None
    preferred_day_of_week: Optional[int] = None
    preferred_time: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    assigned_team: list[Any] = []
    notes: Optional[str] = None
    agreed_price: Optional[float] = None
    start_date: str
    end_date: Optional[str] = None
    next_occurrence: Optional[str] = None
    status: str
    pause_reason: Optional[str] = None
    created_at: str
    updated_at: str


# ============================================
# SCHEDULE ENGINE MODELS (S2.4)
# ============================================

class TimeSlot(BaseModel):
    """A time window for a scheduled job."""
    start: str  # HH:MM
    end: str  # HH:MM
    duration_minutes: int


class ScoreBreakdown(BaseModel):
    """Breakdown of team assignment scoring factors."""
    area_match: float = 0.0
    workload_balance: float = 0.0
    client_preference: float = 0.0
    proximity: float = 0.0
    continuity: float = 0.0


class ScheduleEntry(BaseModel):
    """A single entry in the generated daily schedule."""
    booking_id: str
    team_id: str
    team_name: str
    team_color: Optional[str] = None
    client_id: str
    client_name: str = ""
    service_name: Optional[str] = None
    source: str  # recurring or manual
    time_slot: TimeSlot
    score: Optional[float] = None
    score_breakdown: Optional[ScoreBreakdown] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None


class ScheduleConflict(BaseModel):
    """A detected scheduling conflict."""
    type: str  # time_overlap, max_jobs_exceeded, insufficient_team_members, travel_buffer_violation
    team_id: Optional[str] = None
    job_a_id: Optional[str] = None
    job_b_id: Optional[str] = None
    detail: str
    resolution_suggestions: list[str] = []


class UnassignedJob(BaseModel):
    """A job that could not be assigned to any team."""
    client_id: str
    client_name: str = ""
    service_name: Optional[str] = None
    source: str
    reason: str
    schedule_id: Optional[str] = None
    booking_id: Optional[str] = None
    preferred_time_start: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None


class ScheduleSummary(BaseModel):
    """Summary statistics for a generated schedule."""
    date: str
    total_jobs: int
    assigned_count: int
    unassigned_count: int
    conflict_count: int


class GeneratedScheduleResponse(BaseModel):
    """Full response from the schedule generation endpoint."""
    assigned: list[ScheduleEntry] = []
    conflicts: list[ScheduleConflict] = []
    unassigned: list[UnassignedJob] = []
    summary: ScheduleSummary


class DailyScheduleResponse(BaseModel):
    """Response for the daily schedule view (grouped by team)."""
    date: str
    teams: list[dict] = []
    unassigned: list[dict] = []
    total_bookings: int = 0


class AssignJobRequest(BaseModel):
    """Request to assign a job to a team."""
    booking_id: str
    team_id: str


class MoveJobRequest(BaseModel):
    """Request to move a job between teams."""
    booking_id: str
    from_team_id: str
    to_team_id: str
