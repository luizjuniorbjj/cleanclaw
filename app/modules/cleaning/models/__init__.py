"""
Xcleaners v3 — Pydantic Models
All models for the cleaning business management module.
"""

from .base import CleaningBase
from .services import (
    CleaningServiceCreate,
    CleaningServiceUpdate,
    CleaningServiceResponse,
    CleaningServiceListResponse,
    ChecklistItemCreate,
    ChecklistItemResponse,
    ChecklistResponse,
)
from .teams import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamListResponse,
    TeamAssignmentCreate,
    TeamAssignmentUpdate,
    TeamAssignmentResponse,
    MemberCreate,
    MemberUpdate,
    TeamMemberResponse,
)
from .clients import (
    CleaningClientCreate,
    CleaningClientUpdate,
    CleaningClientResponse,
    CleaningClientListResponse,
    PropertyCreate,
    PropertyResponse,
    FinancialSummary,
)
from .bookings import (
    BookingCreate,
    BookingUpdate,
    BookingResponse,
    BookingListResponse,
)
from .schedules import (
    ClientScheduleCreate,
    ClientScheduleUpdate,
    ClientScheduleResponse,
    ClientScheduleListResponse,
    RecurringScheduleCreate,
    RecurringScheduleUpdate,
    RecurringScheduleResponse,
)
from .invoices import (
    InvoiceCreate,
    InvoiceUpdate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceItemCreate,
    InvoiceItemResponse,
)
from .auth import (
    CleaningUserRoleCreate,
    CleaningRoleInfo,
    InviteRequest,
    InviteResponse,
    AcceptInviteRequest,
    AcceptInviteResponse,
    MyRolesResponse,
)

__all__ = [
    # Base
    "CleaningBase",
    # Services
    "CleaningServiceCreate",
    "CleaningServiceUpdate",
    "CleaningServiceResponse",
    "CleaningServiceListResponse",
    "ChecklistItemCreate",
    "ChecklistItemResponse",
    "ChecklistResponse",
    # Teams
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "TeamListResponse",
    "TeamAssignmentCreate",
    "TeamAssignmentUpdate",
    "TeamAssignmentResponse",
    "MemberCreate",
    "MemberUpdate",
    "TeamMemberResponse",
    # Clients
    "CleaningClientCreate",
    "CleaningClientUpdate",
    "CleaningClientResponse",
    "CleaningClientListResponse",
    "PropertyCreate",
    "PropertyResponse",
    "FinancialSummary",
    # Bookings
    "BookingCreate",
    "BookingUpdate",
    "BookingResponse",
    "BookingListResponse",
    # Schedules
    "ClientScheduleCreate",
    "ClientScheduleUpdate",
    "ClientScheduleResponse",
    "ClientScheduleListResponse",
    "RecurringScheduleCreate",
    "RecurringScheduleUpdate",
    "RecurringScheduleResponse",
    # Invoices
    "InvoiceCreate",
    "InvoiceUpdate",
    "InvoiceResponse",
    "InvoiceListResponse",
    "InvoiceItemCreate",
    "InvoiceItemResponse",
    # Auth
    "CleaningUserRoleCreate",
    "CleaningRoleInfo",
    "InviteRequest",
    "InviteResponse",
    "AcceptInviteRequest",
    "AcceptInviteResponse",
    "MyRolesResponse",
]
