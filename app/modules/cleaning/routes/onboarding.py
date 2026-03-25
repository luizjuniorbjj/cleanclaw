"""
Xcleaners v3 — Onboarding Routes.

5-step setup wizard for new cleaning businesses.

Endpoints:
  GET  /api/v1/clean/{slug}/onboarding/status     — current step & progress
  POST /api/v1/clean/{slug}/onboarding/step/{step} — save step data
  POST /api/v1/clean/{slug}/onboarding/complete    — finalize setup
  POST /api/v1/clean/{slug}/onboarding/skip        — skip to dashboard
  GET  /api/v1/clean/{slug}/onboarding/templates   — service templates for step 2
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.database import get_db, Database
from app.modules.cleaning.middleware.role_guard import require_role
from app.modules.cleaning.models.onboarding import (
    OnboardingCompleteResponse,
    OnboardingStatusResponse,
    OnboardingStepRequest,
)
from app.modules.cleaning.services.onboarding_service import (
    complete_onboarding,
    get_onboarding_status,
    save_step,
    skip_onboarding,
)
from app.modules.cleaning.services.template_copy_service import (
    get_service_templates,
)

logger = logging.getLogger("xcleaners.onboarding_routes")

router = APIRouter(
    prefix="/api/v1/clean/{slug}/onboarding",
    tags=["Xcleaners Onboarding"],
)


# ============================================
# GET /api/v1/clean/{slug}/onboarding/status
# ============================================

@router.get("/status", response_model=OnboardingStatusResponse)
async def onboarding_status(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Get current onboarding status: completed steps, current step, etc."""
    status = await get_onboarding_status(db, user["business_id"])
    return OnboardingStatusResponse(**status)


# ============================================
# POST /api/v1/clean/{slug}/onboarding/step/{step_number}
# ============================================

@router.post("/step/{step_number}")
async def save_onboarding_step(
    slug: str,
    step_number: int,
    body: OnboardingStepRequest,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """
    Save data for a specific onboarding step.

    Body: { step: 1-5, data: { ...step-specific fields } }
    """
    if step_number < 1 or step_number > 5:
        raise HTTPException(status_code=400, detail="Step must be between 1 and 5")

    if body.step != step_number:
        raise HTTPException(
            status_code=400,
            detail=f"URL step ({step_number}) doesn't match body step ({body.step})"
        )

    result = await save_step(
        db=db,
        business_id=user["business_id"],
        business_slug=slug,
        step=step_number,
        data=body.data,
        user_id=user["user_id"],
    )

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={"errors": result["errors"], "step": result["step"]},
        )

    return result


# ============================================
# POST /api/v1/clean/{slug}/onboarding/complete
# ============================================

@router.post("/complete", response_model=OnboardingCompleteResponse)
async def complete_onboarding_route(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """
    Finalize onboarding. Sets completed flag and activates business.

    Step 1 (Business Info) must be completed. Other steps are optional.
    """
    status = await get_onboarding_status(db, user["business_id"])

    # At minimum, step 1 must be completed
    if 1 not in status["completed_steps"]:
        raise HTTPException(
            status_code=400,
            detail="Step 1 (Business Info) must be completed before finalizing."
        )

    await complete_onboarding(db, user["business_id"])

    return OnboardingCompleteResponse(
        completed=True,
        business_slug=slug,
        message="Onboarding complete! Your business is ready.",
    )


# ============================================
# POST /api/v1/clean/{slug}/onboarding/skip
# ============================================

@router.post("/skip")
async def skip_onboarding_route(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Skip remaining onboarding steps. Can complete later from Settings."""
    result = await skip_onboarding(db, user["business_id"])
    return {"success": True, "skipped": True, "message": "You can complete setup later from Settings."}


# ============================================
# GET /api/v1/clean/{slug}/onboarding/templates
# ============================================

@router.get("/templates")
async def get_templates(
    slug: str,
    user: dict = Depends(require_role("owner")),
    db: Database = Depends(get_db),
):
    """Get available service templates for onboarding step 2."""
    templates = await get_service_templates(db)
    return {"templates": templates}
