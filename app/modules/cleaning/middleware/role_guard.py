"""
CleanClaw v3 — Role Guard Middleware.

Provides FastAPI dependencies that enforce cleaning role requirements
on route handlers. Uses the cleaning_role set by auth_middleware.

Usage as FastAPI dependency:
    @router.get("/{slug}/teams")
    async def list_teams(user: dict = Depends(require_role("owner", "team_lead"))):
        ...

The dependency calls get_cleaning_role internally, so routes don't need
to explicitly depend on get_cleaning_role when using require_role.
"""

import logging
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, Request

logger = logging.getLogger("cleanclaw.role_guard")


def _get_cleaning_role_dep():
    """Lazy import to avoid circular dependency with routes/__init__.py."""
    from app.modules.cleaning.routes.auth_middleware import get_cleaning_role
    return get_cleaning_role


def require_role(*allowed_roles: str) -> Callable:
    """
    FastAPI dependency factory that enforces cleaning role requirements.

    Returns a dependency function that:
    1. Resolves the user's cleaning role via get_cleaning_role
    2. Checks if the role is in allowed_roles
    3. Returns 403 if not authorized
    4. Returns the enriched user dict if authorized

    Args:
        *allowed_roles: One or more role strings (OR logic).
                        Valid roles: owner, homeowner, team_lead, cleaner

    Example:
        require_role("owner")  # only owners
        require_role("owner", "team_lead")  # owners OR team leads
        require_role("team_lead", "cleaner")  # team members
    """
    async def _guard(user: dict = Depends(_get_cleaning_role_dep())) -> dict:
        current_role = user.get("cleaning_role")
        if current_role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Access denied. Required role: {', '.join(allowed_roles)}. "
                    f"Your role: {current_role or 'none'}"
                ),
            )
        return user

    return _guard


def require_owner() -> Callable:
    """Shortcut: require owner role."""
    return require_role("owner")


def require_cleaner() -> Callable:
    """Shortcut: require any team member role (team_lead or cleaner)."""
    return require_role("team_lead", "cleaner")


def require_homeowner() -> Callable:
    """Shortcut: require homeowner role."""
    return require_role("homeowner")


def require_any_role() -> Callable:
    """Require that the user has ANY cleaning role (not None)."""
    async def _guard(user: dict = Depends(_get_cleaning_role_dep())) -> dict:
        current_role = user.get("cleaning_role")
        if current_role is None:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You have no role in this cleaning business.",
            )
        return user

    return _guard
