"""
CleanClaw v3 — Shared Pydantic base models.
All cleaning models inherit from CleaningBase which carries business_id.
"""

from typing import Optional
from pydantic import BaseModel, Field


class CleaningBase(BaseModel):
    """Base model for all cleaning entities. Carries business_id for multi-tenant scoping."""
    business_id: str = Field(
        ...,
        description="UUID of the business this entity belongs to."
    )


class CleaningTimestamped(CleaningBase):
    """Base with created_at / updated_at for response models."""
    created_at: str
    updated_at: Optional[str] = None
