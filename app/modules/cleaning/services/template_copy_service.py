"""
Xcleaners v3 — Template Copy Service.

Copies cleaning_service_templates and cleaning_checklist_templates
into business-scoped tables during onboarding.
"""

import logging
import re
from typing import Optional

from app.database import Database

logger = logging.getLogger("xcleaners.template_copy_service")


async def get_service_templates(db: Database) -> list[dict]:
    """
    Fetch all available service templates.

    Returns list of dicts with template data for the onboarding UI.
    """
    rows = await db.pool.fetch(
        """
        SELECT
            name, slug, description, category,
            suggested_base_price, price_unit,
            estimated_duration_minutes, min_team_size,
            icon, sort_order
        FROM cleaning_service_templates
        ORDER BY sort_order
        """
    )
    return [dict(row) for row in rows]


async def copy_service_templates(
    db: Database,
    business_id: str,
    selected_slugs: list[str],
    customizations: Optional[dict] = None,
) -> list[str]:
    """
    Copy selected service templates into cleaning_services for a business.

    Args:
        db: Database connection
        business_id: Target business UUID
        selected_slugs: List of template slugs to copy
        customizations: Optional dict of {slug: {field: value}} overrides

    Returns:
        List of created cleaning_services IDs
    """
    if not selected_slugs:
        return []

    customizations = customizations or {}

    # Fetch selected templates
    templates = await db.pool.fetch(
        """
        SELECT
            name, slug, description, category,
            suggested_base_price, price_unit,
            estimated_duration_minutes, min_team_size,
            icon, sort_order
        FROM cleaning_service_templates
        WHERE slug = ANY($1)
        ORDER BY sort_order
        """,
        selected_slugs,
    )

    created_ids = []

    for tmpl in templates:
        slug = tmpl["slug"]
        custom = customizations.get(slug, {})

        # Apply customizations (override template defaults)
        name = custom.get("name", tmpl["name"])
        description = custom.get("description", tmpl["description"])
        category = custom.get("category", tmpl["category"])
        base_price = custom.get("base_price", tmpl["suggested_base_price"])
        price_unit = custom.get("price_unit", tmpl["price_unit"])
        duration = custom.get("estimated_duration_minutes", tmpl["estimated_duration_minutes"])

        # Check for existing service with same slug in this business
        existing = await db.pool.fetchval(
            "SELECT id FROM cleaning_services WHERE business_id = $1 AND slug = $2",
            business_id,
            slug,
        )
        if existing:
            logger.info("[TEMPLATE] Service %s already exists for business %s, skipping", slug, business_id)
            created_ids.append(str(existing))
            continue

        service_id = await db.pool.fetchval(
            """
            INSERT INTO cleaning_services
                (business_id, name, slug, description, category,
                 base_price, price_unit, estimated_duration_minutes,
                 min_team_size, icon, sort_order, is_active)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true)
            RETURNING id
            """,
            business_id,
            name,
            slug,
            description,
            category,
            base_price,
            price_unit,
            duration,
            tmpl["min_team_size"],
            tmpl["icon"],
            tmpl["sort_order"],
        )

        created_ids.append(str(service_id))

        logger.info(
            "[TEMPLATE] Copied service template '%s' -> cleaning_services id=%s for business %s",
            slug,
            service_id,
            business_id,
        )

    return created_ids


async def copy_checklist_templates(
    db: Database,
    business_id: str,
    service_id: str,
    service_slug: str,
) -> Optional[str]:
    """
    Copy checklist template items for a service into the business.

    Creates a cleaning_checklists record and copies all matching
    cleaning_checklist_templates items into cleaning_checklist_items.

    Returns:
        Checklist ID if created, None if no templates found
    """
    # Fetch matching checklist template items
    items = await db.pool.fetch(
        """
        SELECT room, task_description, is_required, sort_order
        FROM cleaning_checklist_templates
        WHERE service_slug = $1
        ORDER BY sort_order
        """,
        service_slug,
    )

    if not items:
        return None

    # Create the checklist
    checklist_id = await db.pool.fetchval(
        """
        INSERT INTO cleaning_checklists
            (business_id, service_id, name, description, is_default)
        VALUES ($1, $2, $3, $4, true)
        RETURNING id
        """,
        business_id,
        service_id,
        f"{service_slug} Checklist",
        f"Default checklist for {service_slug}",
    )

    # Copy all items
    for item in items:
        await db.pool.execute(
            """
            INSERT INTO cleaning_checklist_items
                (checklist_id, business_id, room, task_description, is_required, sort_order)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            checklist_id,
            business_id,
            item["room"],
            item["task_description"],
            item["is_required"],
            item["sort_order"],
        )

    logger.info(
        "[TEMPLATE] Copied %d checklist items for service '%s' in business %s",
        len(items),
        service_slug,
        business_id,
    )

    return str(checklist_id)


def slugify(name: str) -> str:
    """Convert a service name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s-]+", "-", slug)
    return slug.strip("-")
