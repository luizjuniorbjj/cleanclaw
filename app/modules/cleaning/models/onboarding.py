"""
CleanClaw v3 — Onboarding Wizard Pydantic models.
Models for the 5-step onboarding wizard.
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


# ============================================
# STEP 1: BUSINESS INFO
# ============================================

class OnboardingStep1(BaseModel):
    """Step 1: Business information."""
    business_name: str = Field(..., min_length=1, max_length=255)
    phone: str = Field(..., min_length=5, max_length=30)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    timezone: str = Field(default="America/New_York", max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = None


# ============================================
# STEP 2: SERVICES
# ============================================

class ServiceSelection(BaseModel):
    """A single service selection from templates or custom."""
    template_slug: Optional[str] = None  # if from template
    name: str = Field(..., min_length=1, max_length=150)
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
    is_selected: bool = True


class OnboardingStep2(BaseModel):
    """Step 2: Service selection and customization."""
    services: list[ServiceSelection] = Field(..., min_length=1)


# ============================================
# STEP 3: SERVICE AREA
# ============================================

class AreaEntry(BaseModel):
    """A single service area entry."""
    name: str = Field(..., min_length=1, max_length=150)
    zip_codes: list[str] = Field(default_factory=list)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    radius_miles: Optional[float] = Field(None, ge=0)
    travel_fee: Optional[float] = Field(None, ge=0)


class OnboardingStep3(BaseModel):
    """Step 3: Service area definition."""
    serve_all_areas: bool = False
    areas: list[AreaEntry] = Field(default_factory=list)


# ============================================
# STEP 4: PRICING
# ============================================

class PricingAdjustment(BaseModel):
    """Price adjustment for a service selected in step 2."""
    service_slug: str
    base_price: Optional[float] = Field(None, ge=0)
    price_unit: Optional[str] = Field(
        None,
        pattern=r"^(flat|hourly|per_sqft|per_room)$"
    )


class PricingExtra(BaseModel):
    """Extra pricing rule (pet surcharge, weekend premium, etc.)."""
    name: str = Field(..., min_length=1, max_length=150)
    rule_type: str = Field(
        default="surcharge",
        pattern=r"^(surcharge|multiplier|discount_percent|discount_fixed|minimum|package)$"
    )
    value: float = Field(..., description="Amount or percentage depending on rule_type")
    description: Optional[str] = None


class OnboardingStep4(BaseModel):
    """Step 4: Pricing configuration."""
    use_defaults: bool = False
    adjustments: list[PricingAdjustment] = Field(default_factory=list)
    extras: list[PricingExtra] = Field(default_factory=list)


# ============================================
# STEP 5: TEAM
# ============================================

class OnboardingStep5(BaseModel):
    """Step 5: Team creation and member invitations."""
    team_name: Optional[str] = Field(None, min_length=1, max_length=100)
    team_color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")
    invite_emails: list[str] = Field(
        default_factory=list,
        description="Email addresses to invite as cleaners"
    )


# ============================================
# STEP WRAPPER (POST body)
# ============================================

class OnboardingStepRequest(BaseModel):
    """Generic wrapper for saving a step."""
    step: int = Field(..., ge=1, le=5)
    data: dict = Field(..., description="Step-specific data (validated by service)")


# ============================================
# STATUS RESPONSE
# ============================================

class OnboardingStatusResponse(BaseModel):
    """Onboarding progress status."""
    completed_steps: list[int] = Field(default_factory=list)
    current_step: int = 1
    completed: bool = False
    skipped: bool = False
    business_name: Optional[str] = None


class OnboardingCompleteResponse(BaseModel):
    """Response after completing onboarding."""
    completed: bool = True
    business_slug: str
    message: str = "Onboarding complete! Your business is ready."
