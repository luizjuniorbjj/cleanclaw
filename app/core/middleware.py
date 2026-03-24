"""
ClaWtoBusiness — Business Resolver Middleware
Resolves the current business from URL path, header, or user default.
"""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Header, Request

from app.database import get_db, Database
from app.auth import get_current_user

logger = logging.getLogger("clawin.middleware")


async def resolve_business(
    request: Request,
    x_business_slug: Optional[str] = Header(None),
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> dict:
    """
    Resolve the current business context. Priority:
    1. URL path parameter {slug} (e.g. /api/b/{slug}/...)
    2. X-Business-Slug header
    3. User's default_business_id

    Returns the full business dict with access verified.
    Raises 404 if business not found, 403 if no access.
    """
    slug = None

    # 1. URL path parameter
    slug = request.path_params.get("slug")

    # 2. Header fallback
    if not slug and x_business_slug:
        slug = x_business_slug

    # 3. User default fallback
    if not slug:
        default_id = await db.pool.fetchval(
            "SELECT default_business_id FROM users WHERE id = $1",
            current_user["user_id"],
        )
        if default_id:
            row = await db.pool.fetchrow(
                "SELECT * FROM businesses WHERE id = $1 AND status != 'cancelled'",
                str(default_id),
            )
            if row:
                business = dict(row)
                await _verify_access(db, str(business["id"]), current_user["user_id"])
                return business

        raise HTTPException(
            status_code=400,
            detail="No business context. Provide slug in URL or X-Business-Slug header.",
        )

    # Lookup by slug
    row = await db.pool.fetchrow(
        "SELECT * FROM businesses WHERE slug = $1 AND status != 'cancelled'",
        slug,
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Business '{slug}' not found")

    business = dict(row)
    await _verify_access(db, str(business["id"]), current_user["user_id"])
    return business


async def _verify_access(db: Database, business_id: str, user_id: str):
    """Check that user has access to this business."""
    role = await db.pool.fetchval(
        "SELECT role FROM business_members WHERE business_id = $1 AND user_id = $2",
        business_id, user_id,
    )
    if not role:
        raise HTTPException(status_code=403, detail="No access to this business")
