"""
CleanClaw v3 — Service Catalog Service.

CRUD operations for cleaning_services (service types a business offers).
Also manages checklists per service.

Tables: cleaning_services, cleaning_checklists, cleaning_checklist_items
"""

import logging
import re
from typing import Optional

from app.database import Database

logger = logging.getLogger("cleanclaw.catalog_service")


def slugify(name: str) -> str:
    """Convert a service name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")


async def _ensure_unique_slug(
    db: Database, business_id: str, base_slug: str, exclude_id: Optional[str] = None
) -> str:
    """
    Generate a unique slug for a service within a business.
    Appends -2, -3, etc. if the slug already exists.
    """
    slug = base_slug
    suffix = 1

    while True:
        if exclude_id:
            exists = await db.pool.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM cleaning_services
                    WHERE business_id = $1 AND slug = $2 AND id != $3
                )
                """,
                business_id,
                slug,
                exclude_id,
            )
        else:
            exists = await db.pool.fetchval(
                """
                SELECT EXISTS(
                    SELECT 1 FROM cleaning_services
                    WHERE business_id = $1 AND slug = $2
                )
                """,
                business_id,
                slug,
            )

        if not exists:
            return slug

        suffix += 1
        slug = f"{base_slug}-{suffix}"


# ============================================
# SERVICE CRUD
# ============================================


async def list_services(
    db: Database,
    business_id: str,
    include_inactive: bool = False,
) -> dict:
    """List all services for a business."""
    if include_inactive:
        rows = await db.pool.fetch(
            """
            SELECT id, business_id, name, slug, description, category,
                   base_price, price_unit, estimated_duration_minutes,
                   min_team_size, is_active, sort_order, icon,
                   created_at, updated_at
            FROM cleaning_services
            WHERE business_id = $1
            ORDER BY sort_order, name
            """,
            business_id,
        )
    else:
        rows = await db.pool.fetch(
            """
            SELECT id, business_id, name, slug, description, category,
                   base_price, price_unit, estimated_duration_minutes,
                   min_team_size, is_active, sort_order, icon,
                   created_at, updated_at
            FROM cleaning_services
            WHERE business_id = $1 AND is_active = true
            ORDER BY sort_order, name
            """,
            business_id,
        )

    services = []
    for row in rows:
        services.append(_row_to_service(row))

    return {"services": services, "total": len(services)}


async def get_service(
    db: Database,
    business_id: str,
    service_id: str,
) -> Optional[dict]:
    """Get a single service by ID."""
    row = await db.pool.fetchrow(
        """
        SELECT id, business_id, name, slug, description, category,
               base_price, price_unit, estimated_duration_minutes,
               min_team_size, is_active, sort_order, icon,
               created_at, updated_at
        FROM cleaning_services
        WHERE id = $1 AND business_id = $2
        """,
        service_id,
        business_id,
    )

    if not row:
        return None

    return _row_to_service(row)


async def create_service(
    db: Database,
    business_id: str,
    data: dict,
) -> dict:
    """Create a new cleaning service."""
    name = data["name"].strip()

    # Auto-generate slug from name
    base_slug = slugify(name)
    if not base_slug:
        base_slug = "service"

    slug = await _ensure_unique_slug(db, business_id, base_slug)

    row = await db.pool.fetchrow(
        """
        INSERT INTO cleaning_services
            (business_id, name, slug, description, category,
             base_price, price_unit, estimated_duration_minutes,
             min_team_size, is_active, sort_order, icon)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id, business_id, name, slug, description, category,
                  base_price, price_unit, estimated_duration_minutes,
                  min_team_size, is_active, sort_order, icon,
                  created_at, updated_at
        """,
        business_id,
        name,
        slug,
        data.get("description"),
        data.get("category", "residential"),
        data.get("base_price"),
        data.get("price_unit", "flat"),
        data.get("estimated_duration_minutes"),
        data.get("min_team_size", 1),
        data.get("is_active", True),
        data.get("sort_order", 0),
        data.get("icon"),
    )

    logger.info("[CATALOG] Created service '%s' (slug=%s) for business %s", name, slug, business_id)
    return _row_to_service(row)


async def update_service(
    db: Database,
    business_id: str,
    service_id: str,
    data: dict,
) -> Optional[dict]:
    """Update a cleaning service. Returns None if not found."""
    # Verify service exists
    existing = await db.pool.fetchrow(
        "SELECT id, slug FROM cleaning_services WHERE id = $1 AND business_id = $2",
        service_id,
        business_id,
    )
    if not existing:
        return None

    # Build dynamic UPDATE
    updates = []
    params = [service_id, business_id]
    idx = 3

    for field in [
        "name", "description", "category", "base_price", "price_unit",
        "estimated_duration_minutes", "min_team_size", "is_active",
        "sort_order", "icon",
    ]:
        if field in data and data[field] is not None:
            updates.append(f"{field} = ${idx}")
            params.append(data[field])
            idx += 1

    # If name changed, regenerate slug
    if "name" in data and data["name"] is not None:
        new_slug = slugify(data["name"].strip())
        new_slug = await _ensure_unique_slug(db, business_id, new_slug, exclude_id=service_id)
        updates.append(f"slug = ${idx}")
        params.append(new_slug)
        idx += 1

    if not updates:
        # Nothing to update, return current state
        return await get_service(db, business_id, service_id)

    query = f"""
        UPDATE cleaning_services
        SET {', '.join(updates)}
        WHERE id = $1 AND business_id = $2
        RETURNING id, business_id, name, slug, description, category,
                  base_price, price_unit, estimated_duration_minutes,
                  min_team_size, is_active, sort_order, icon,
                  created_at, updated_at
    """
    row = await db.pool.fetchrow(query, *params)

    if not row:
        return None

    logger.info("[CATALOG] Updated service %s for business %s", service_id, business_id)
    return _row_to_service(row)


async def delete_service(
    db: Database,
    business_id: str,
    service_id: str,
) -> dict:
    """
    Soft-delete a service (set is_active=false).
    Returns 409 info if service has future bookings.
    Returns {"deleted": True} on success, or {"conflict": True, "future_bookings": N} on conflict.
    """
    # Check for future bookings
    from datetime import date

    future_count = await db.pool.fetchval(
        """
        SELECT COUNT(*) FROM cleaning_bookings
        WHERE service_id = $1
          AND business_id = $2
          AND scheduled_date >= $3
          AND status NOT IN ('cancelled', 'no_show')
        """,
        service_id,
        business_id,
        date.today(),
    )

    if future_count and future_count > 0:
        return {
            "deleted": False,
            "conflict": True,
            "future_bookings": future_count,
            "message": f"Cannot deactivate: {future_count} future booking(s) use this service. Reassign or cancel them first.",
        }

    # Soft delete
    result = await db.pool.execute(
        """
        UPDATE cleaning_services
        SET is_active = false
        WHERE id = $1 AND business_id = $2
        """,
        service_id,
        business_id,
    )

    if "UPDATE 0" in result:
        return {"deleted": False, "not_found": True}

    logger.info("[CATALOG] Soft-deleted service %s for business %s", service_id, business_id)
    return {"deleted": True}


# ============================================
# CHECKLIST CRUD
# ============================================


async def get_checklists(
    db: Database,
    business_id: str,
    service_id: str,
) -> dict:
    """Get checklist items for a service."""
    # Find the default checklist for this service
    checklist = await db.pool.fetchrow(
        """
        SELECT id, name, description, is_default
        FROM cleaning_checklists
        WHERE service_id = $1 AND business_id = $2
        ORDER BY is_default DESC
        LIMIT 1
        """,
        service_id,
        business_id,
    )

    if not checklist:
        return {"checklist_id": None, "items": [], "total": 0}

    checklist_id = str(checklist["id"])

    items = await db.pool.fetch(
        """
        SELECT id, room, task_description, is_required, sort_order, estimated_minutes
        FROM cleaning_checklist_items
        WHERE checklist_id = $1 AND business_id = $2
        ORDER BY sort_order
        """,
        checklist["id"],
        business_id,
    )

    item_list = []
    for item in items:
        item_list.append({
            "id": str(item["id"]),
            "room": item["room"],
            "task_description": item["task_description"],
            "is_required": item["is_required"],
            "sort_order": item["sort_order"],
            "estimated_minutes": item["estimated_minutes"],
        })

    return {
        "checklist_id": checklist_id,
        "name": checklist["name"],
        "description": checklist["description"],
        "is_default": checklist["is_default"],
        "items": item_list,
        "total": len(item_list),
    }


async def save_checklist(
    db: Database,
    business_id: str,
    service_id: str,
    items: list[dict],
) -> dict:
    """
    Create or replace checklist for a service.
    Deletes existing items and inserts new ones.
    """
    # Get or create checklist
    checklist = await db.pool.fetchrow(
        """
        SELECT id FROM cleaning_checklists
        WHERE service_id = $1 AND business_id = $2
        ORDER BY is_default DESC
        LIMIT 1
        """,
        service_id,
        business_id,
    )

    if checklist:
        checklist_id = checklist["id"]
        # Delete existing items
        await db.pool.execute(
            "DELETE FROM cleaning_checklist_items WHERE checklist_id = $1",
            checklist_id,
        )
    else:
        # Get service name for checklist name
        service_name = await db.pool.fetchval(
            "SELECT name FROM cleaning_services WHERE id = $1 AND business_id = $2",
            service_id,
            business_id,
        )

        checklist_id = await db.pool.fetchval(
            """
            INSERT INTO cleaning_checklists
                (business_id, service_id, name, description, is_default)
            VALUES ($1, $2, $3, $4, true)
            RETURNING id
            """,
            business_id,
            service_id,
            f"{service_name or 'Service'} Checklist",
            f"Default checklist",
        )

    # Insert new items
    for i, item in enumerate(items):
        await db.pool.execute(
            """
            INSERT INTO cleaning_checklist_items
                (checklist_id, business_id, room, task_description,
                 is_required, sort_order, estimated_minutes)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            checklist_id,
            business_id,
            item.get("room"),
            item["name"],
            item.get("is_required", True),
            item.get("sort_order", i),
            item.get("estimated_minutes"),
        )

    logger.info(
        "[CATALOG] Saved %d checklist items for service %s in business %s",
        len(items), service_id, business_id,
    )

    return await get_checklists(db, business_id, service_id)


# ============================================
# HELPERS
# ============================================


def _row_to_service(row) -> dict:
    """Convert a DB row to a service response dict."""
    return {
        "id": str(row["id"]),
        "business_id": str(row["business_id"]),
        "name": row["name"],
        "slug": row["slug"],
        "description": row["description"],
        "category": row["category"],
        "base_price": float(row["base_price"]) if row["base_price"] is not None else None,
        "price_unit": row["price_unit"],
        "estimated_duration_minutes": row["estimated_duration_minutes"],
        "min_team_size": row["min_team_size"],
        "is_active": row["is_active"],
        "sort_order": row["sort_order"],
        "icon": row["icon"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else "",
    }
