"""
Xcleaners v3 — Role Resolution Middleware.

Intercepts all requests to /api/v1/clean/{slug}/* and resolves the user's
cleaning role from the cleaning_user_roles table. Results are cached in Redis
with a 1-hour TTL.

Token enrichment flow (ADR-v3-2):
  1. User logs in via /auth/login or /auth/google/callback
  2. Standard JWT issued (user_id, email)
  3. On first cleaning API call, this middleware checks cleaning_user_roles
  4. If role exists, role + team_id cached in Redis
  5. Request state enriched with cleaning_role and cleaning_team_id

If no role found, request proceeds with cleaning_role = None (public endpoints
still work). Route-level guards (@require_role) enforce access.
"""

import json
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request

from app.auth import get_current_user
from app.database import get_db, Database

logger = logging.getLogger("xcleaners.auth_middleware")

# Redis cache TTL for role lookups
ROLE_CACHE_TTL = 3600  # 1 hour


def _get_redis():
    """Get Redis client, returns None if unavailable."""
    try:
        from app.redis_client import get_redis
        return get_redis()
    except ImportError:
        return None


async def _resolve_business_id(db: Database, slug: str) -> str:
    """Resolve business slug to business ID. Raises 404 if not found."""
    row = await db.pool.fetchrow(
        "SELECT id FROM businesses WHERE slug = $1 AND status != 'cancelled'",
        slug,
    )
    if not row:
        raise HTTPException(status_code=404, detail=f"Business '{slug}' not found")
    return str(row["id"])


async def resolve_cleaning_role(
    request: Request,
    user_id: str,
    business_id: str,
    db: Database,
) -> Optional[dict]:
    """
    Resolve user's cleaning role for a business.

    1. Check Redis cache first
    2. Fall back to DB query
    3. Cache result in Redis

    Returns dict with {role, team_id} or None if no role found.
    Sets request.state.cleaning_role and request.state.cleaning_team_id.
    """
    cache_key = f"clean:{business_id}:role:{user_id}"
    redis = _get_redis()

    # 1. Check Redis cache
    if redis:
        try:
            cached = await redis.get(cache_key)
            if cached:
                role_data = json.loads(cached)
                request.state.cleaning_role = role_data.get("role")
                request.state.cleaning_team_id = role_data.get("team_id")
                return role_data
        except Exception as e:
            logger.warning("[ROLE_CACHE] Redis read error: %s", e)

    # 2. Query DB
    row = await db.pool.fetchrow(
        """
        SELECT role, team_id
        FROM cleaning_user_roles
        WHERE user_id = $1
          AND business_id = $2
          AND is_active = true
        """,
        user_id,
        business_id,
    )

    if not row:
        request.state.cleaning_role = None
        request.state.cleaning_team_id = None
        return None

    role_data = {
        "role": row["role"],
        "team_id": str(row["team_id"]) if row["team_id"] else None,
    }

    # 3. Cache in Redis
    if redis:
        try:
            await redis.setex(cache_key, ROLE_CACHE_TTL, json.dumps(role_data))
        except Exception as e:
            logger.warning("[ROLE_CACHE] Redis write error: %s", e)

    request.state.cleaning_role = role_data["role"]
    request.state.cleaning_team_id = role_data["team_id"]
    return role_data


async def invalidate_role_cache(business_id: str, user_id: str):
    """Invalidate Redis cache when a role is created/updated/deleted."""
    redis = _get_redis()
    if redis:
        try:
            await redis.delete(f"clean:{business_id}:role:{user_id}")
        except Exception as e:
            logger.warning("[ROLE_CACHE] Redis delete error: %s", e)


async def get_cleaning_role(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> dict:
    """
    FastAPI dependency that resolves cleaning role from request context.

    Extracts slug from URL path params, resolves business_id, then resolves
    the user's cleaning role. Returns the current_user dict enriched with
    cleaning_role and cleaning_team_id.

    Usage:
        @router.get("/{slug}/some-endpoint")
        async def endpoint(user: dict = Depends(get_cleaning_role)):
            print(user["cleaning_role"])  # "owner" | "cleaner" | None
    """
    slug = request.path_params.get("slug")
    if not slug:
        raise HTTPException(
            status_code=400,
            detail="Business slug required in URL path.",
        )

    business_id = await _resolve_business_id(db, slug)

    role_data = await resolve_cleaning_role(
        request, current_user["user_id"], business_id, db
    )

    return {
        **current_user,
        "cleaning_role": role_data["role"] if role_data else None,
        "cleaning_team_id": role_data["team_id"] if role_data else None,
        "business_id": business_id,
        "business_slug": slug,
    }
