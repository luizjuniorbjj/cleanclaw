"""
Xcleaners v3 — Onboarding Service.

Orchestrates the 5-step onboarding wizard for new cleaning businesses.

Steps:
  1. Business Info  — name, phone, address, timezone, logo
  2. Services       — select/customize from templates
  3. Service Area   — zip codes, cities, travel fees
  4. Pricing        — adjust prices, add extras (pet surcharge, etc.)
  5. Team           — create first team, invite cleaners by email

Onboarding state is tracked via a JSONB column on the businesses table
(cleaning_onboarding_state). If the column doesn't exist yet, we
gracefully fall back to tracking in-memory.
"""

import json
import logging
import re
from datetime import datetime
from typing import Optional

from app.database import Database
from app.modules.cleaning.services.template_copy_service import (
    copy_checklist_templates,
    copy_service_templates,
    get_service_templates,
    slugify,
)
from app.modules.cleaning.services.setup_validator import validate_step

logger = logging.getLogger("xcleaners.onboarding_service")

# State keys in cleaning_onboarding_state JSONB
STATE_KEY = "cleaning_onboarding_state"

# Total steps
TOTAL_STEPS = 5


async def _get_state(db: Database, business_id: str) -> dict:
    """Get onboarding state from businesses table."""
    row = await db.pool.fetchrow(
        """
        SELECT
            name,
            COALESCE(
                (SELECT value FROM business_metadata WHERE business_id = $1 AND key = $2),
                '{}'
            ) AS state
        FROM businesses
        WHERE id = $1
        """,
        business_id,
        STATE_KEY,
    )

    if not row:
        return {"completed_steps": [], "completed": False, "skipped": False}

    try:
        state = json.loads(row["state"]) if isinstance(row["state"], str) else {}
    except (json.JSONDecodeError, TypeError):
        state = {}

    return {
        "completed_steps": state.get("completed_steps", []),
        "completed": state.get("completed", False),
        "skipped": state.get("skipped", False),
        "business_name": row["name"],
    }


async def _save_state(db: Database, business_id: str, state: dict) -> None:
    """Save onboarding state to business_metadata table."""
    state_json = json.dumps(state)

    # Upsert into business_metadata
    await db.pool.execute(
        """
        INSERT INTO business_metadata (business_id, key, value)
        VALUES ($1, $2, $3)
        ON CONFLICT (business_id, key) DO UPDATE SET value = $3
        """,
        business_id,
        STATE_KEY,
        state_json,
    )


async def _ensure_metadata_table(db: Database) -> None:
    """Create business_metadata table if it doesn't exist."""
    await db.pool.execute(
        """
        CREATE TABLE IF NOT EXISTS business_metadata (
            business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
            key VARCHAR(100) NOT NULL,
            value TEXT,
            PRIMARY KEY (business_id, key)
        )
        """
    )


async def get_onboarding_status(db: Database, business_id: str) -> dict:
    """
    Get current onboarding status.

    Returns:
        {completed_steps: [1,2], current_step: 3, completed: false, business_name: "..."}
    """
    await _ensure_metadata_table(db)
    state = await _get_state(db, business_id)

    completed_steps = sorted(state.get("completed_steps", []))
    completed = state.get("completed", False)
    skipped = state.get("skipped", False)

    # Determine current step
    if completed or skipped:
        current_step = TOTAL_STEPS
    elif completed_steps:
        current_step = max(completed_steps) + 1
        if current_step > TOTAL_STEPS:
            current_step = TOTAL_STEPS
    else:
        current_step = 1

    return {
        "completed_steps": completed_steps,
        "current_step": current_step,
        "completed": completed,
        "skipped": skipped,
        "business_name": state.get("business_name"),
    }


async def save_step(
    db: Database,
    business_id: str,
    business_slug: str,
    step: int,
    data: dict,
    user_id: str,
) -> dict:
    """
    Save data for a specific onboarding step.

    Validates the data, persists it to the appropriate tables,
    and updates onboarding state.

    Returns:
        {success: true, step: N, errors: []} or {success: false, errors: [...]}
    """
    await _ensure_metadata_table(db)

    # Validate step data
    is_valid, errors = validate_step(step, data)
    if not is_valid:
        return {"success": False, "step": step, "errors": errors}

    # Execute step-specific logic
    try:
        if step == 1:
            await _save_step1(db, business_id, data)
        elif step == 2:
            await _save_step2(db, business_id, data)
        elif step == 3:
            await _save_step3(db, business_id, data)
        elif step == 4:
            await _save_step4(db, business_id, data)
        elif step == 5:
            await _save_step5(db, business_id, business_slug, data, user_id)
        else:
            return {"success": False, "step": step, "errors": [f"Invalid step: {step}"]}
    except Exception as e:
        logger.error("[ONBOARDING] Error saving step %d for business %s: %s", step, business_id, e)
        return {"success": False, "step": step, "errors": [str(e)]}

    # Update onboarding state
    state = await _get_state(db, business_id)
    completed_steps = state.get("completed_steps", [])
    if step not in completed_steps:
        completed_steps.append(step)
        completed_steps.sort()

    state["completed_steps"] = completed_steps
    await _save_state(db, business_id, state)

    logger.info("[ONBOARDING] Step %d saved for business %s", step, business_id)

    return {"success": True, "step": step, "errors": []}


async def complete_onboarding(db: Database, business_id: str) -> dict:
    """
    Mark onboarding as complete.

    Sets the completed flag and updates the business status to active.
    """
    await _ensure_metadata_table(db)

    state = await _get_state(db, business_id)
    state["completed"] = True
    state["completed_at"] = datetime.utcnow().isoformat()
    await _save_state(db, business_id, state)

    # Update business status to active (in case it was 'setup')
    await db.pool.execute(
        "UPDATE businesses SET status = 'active', updated_at = NOW() WHERE id = $1",
        business_id,
    )

    logger.info("[ONBOARDING] Completed for business %s", business_id)

    return {"completed": True}


async def skip_onboarding(db: Database, business_id: str) -> dict:
    """
    Skip remaining onboarding steps. Owner can complete later from settings.
    """
    await _ensure_metadata_table(db)

    state = await _get_state(db, business_id)
    state["skipped"] = True
    state["skipped_at"] = datetime.utcnow().isoformat()
    await _save_state(db, business_id, state)

    # Update business status to active
    await db.pool.execute(
        "UPDATE businesses SET status = 'active', updated_at = NOW() WHERE id = $1",
        business_id,
    )

    logger.info("[ONBOARDING] Skipped for business %s", business_id)

    return {"skipped": True}


# ============================================
# Step-specific save logic
# ============================================


async def _save_step1(db: Database, business_id: str, data: dict) -> None:
    """Save Step 1: Business Info to businesses table."""
    await db.pool.execute(
        """
        UPDATE businesses
        SET name = $2,
            timezone = $3,
            logo_url = $4,
            updated_at = NOW()
        WHERE id = $1
        """,
        business_id,
        data["business_name"].strip(),
        data.get("timezone", "America/New_York"),
        data.get("logo_url"),
    )

    # Save address/phone as business_metadata entries
    address_data = {
        "phone": data.get("phone", ""),
        "address_line1": data.get("address_line1", ""),
        "address_line2": data.get("address_line2", ""),
        "city": data.get("city", ""),
        "state": data.get("state", ""),
        "zip_code": data.get("zip_code", ""),
        "contact_email": data.get("contact_email", ""),
    }

    await db.pool.execute(
        """
        INSERT INTO business_metadata (business_id, key, value)
        VALUES ($1, 'cleaning_business_info', $2)
        ON CONFLICT (business_id, key) DO UPDATE SET value = $2
        """,
        business_id,
        json.dumps(address_data),
    )


async def _save_step2(db: Database, business_id: str, data: dict) -> None:
    """Save Step 2: Copy selected service templates and create custom services."""
    services = data.get("services", [])
    selected = [s for s in services if s.get("is_selected", True)]

    # Separate template-based vs custom services
    template_slugs = []
    customizations = {}
    custom_services = []

    for svc in selected:
        slug = svc.get("template_slug")
        if slug:
            template_slugs.append(slug)
            # Collect any customizations
            custom = {}
            if svc.get("name"):
                custom["name"] = svc["name"]
            if svc.get("base_price") is not None:
                custom["base_price"] = svc["base_price"]
            if svc.get("price_unit"):
                custom["price_unit"] = svc["price_unit"]
            if svc.get("estimated_duration_minutes"):
                custom["estimated_duration_minutes"] = svc["estimated_duration_minutes"]
            if svc.get("description"):
                custom["description"] = svc["description"]
            if custom:
                customizations[slug] = custom
        else:
            custom_services.append(svc)

    # Copy templates
    service_ids = await copy_service_templates(
        db, business_id, template_slugs, customizations
    )

    # Copy checklists for each template-based service
    for slug in template_slugs:
        # Find the service_id for this slug
        sid = await db.pool.fetchval(
            "SELECT id FROM cleaning_services WHERE business_id = $1 AND slug = $2",
            business_id,
            slug,
        )
        if sid:
            await copy_checklist_templates(db, business_id, str(sid), slug)

    # Create custom services
    for svc in custom_services:
        svc_slug = slugify(svc["name"])
        # Ensure unique slug
        existing = await db.pool.fetchval(
            "SELECT COUNT(*) FROM cleaning_services WHERE business_id = $1 AND slug = $2",
            business_id,
            svc_slug,
        )
        if existing:
            svc_slug = f"{svc_slug}-{existing + 1}"

        await db.pool.execute(
            """
            INSERT INTO cleaning_services
                (business_id, name, slug, description, category,
                 base_price, price_unit, estimated_duration_minutes,
                 min_team_size, is_active, sort_order)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 1, true, 99)
            """,
            business_id,
            svc["name"],
            svc_slug,
            svc.get("description"),
            svc.get("category", "residential"),
            svc.get("base_price"),
            svc.get("price_unit", "flat"),
            svc.get("estimated_duration_minutes"),
        )


async def _save_step3(db: Database, business_id: str, data: dict) -> None:
    """Save Step 3: Service areas."""
    serve_all = data.get("serve_all_areas", False)
    areas = data.get("areas", [])

    if serve_all:
        # Create a single catch-all area
        existing = await db.pool.fetchval(
            "SELECT id FROM cleaning_areas WHERE business_id = $1 AND name = 'All Areas'",
            business_id,
        )
        if not existing:
            await db.pool.execute(
                """
                INSERT INTO cleaning_areas (business_id, name, is_active)
                VALUES ($1, 'All Areas', true)
                """,
                business_id,
            )
    else:
        for area in areas:
            zip_codes = area.get("zip_codes", [])
            existing = await db.pool.fetchval(
                "SELECT id FROM cleaning_areas WHERE business_id = $1 AND name = $2",
                business_id,
                area["name"],
            )
            if existing:
                await db.pool.execute(
                    """
                    UPDATE cleaning_areas
                    SET zip_codes = $2, city = $3, state = $4,
                        radius_miles = $5, travel_fee = $6, updated_at = NOW()
                    WHERE id = $1
                    """,
                    existing,
                    zip_codes,
                    area.get("city"),
                    area.get("state"),
                    area.get("radius_miles"),
                    area.get("travel_fee"),
                )
            else:
                await db.pool.execute(
                    """
                    INSERT INTO cleaning_areas
                        (business_id, name, zip_codes, city, state,
                         radius_miles, travel_fee, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, true)
                    """,
                    business_id,
                    area["name"],
                    zip_codes,
                    area.get("city"),
                    area.get("state"),
                    area.get("radius_miles"),
                    area.get("travel_fee"),
                )


async def _save_step4(db: Database, business_id: str, data: dict) -> None:
    """Save Step 4: Pricing adjustments and extras."""
    # Apply price adjustments to existing services
    adjustments = data.get("adjustments", [])
    for adj in adjustments:
        slug = adj.get("service_slug")
        if not slug:
            continue

        updates = []
        params = [business_id, slug]
        idx = 3

        if adj.get("base_price") is not None:
            updates.append(f"base_price = ${idx}")
            params.append(adj["base_price"])
            idx += 1
        if adj.get("price_unit"):
            updates.append(f"price_unit = ${idx}")
            params.append(adj["price_unit"])
            idx += 1

        if updates:
            updates.append("updated_at = NOW()")
            query = f"""
                UPDATE cleaning_services
                SET {', '.join(updates)}
                WHERE business_id = $1 AND slug = $2
            """
            await db.pool.execute(query, *params)

    # Create pricing rule extras
    extras = data.get("extras", [])
    for extra in extras:
        existing = await db.pool.fetchval(
            "SELECT id FROM cleaning_pricing_rules WHERE business_id = $1 AND name = $2",
            business_id,
            extra["name"],
        )
        if existing:
            continue

        await db.pool.execute(
            """
            INSERT INTO cleaning_pricing_rules
                (business_id, name, rule_type, value, description,
                 applies_to, is_active, priority)
            VALUES ($1, $2, $3, $4, $5, 'all_services', true, 10)
            """,
            business_id,
            extra["name"],
            extra.get("rule_type", "surcharge"),
            extra["value"],
            extra.get("description"),
        )


async def _save_step5(
    db: Database,
    business_id: str,
    business_slug: str,
    data: dict,
    user_id: str,
) -> None:
    """Save Step 5: Create team and send invitations."""
    team_name = data.get("team_name", "").strip()
    team_color = data.get("team_color", "#3B82F6")
    invite_emails = data.get("invite_emails", [])

    # Create team if name provided
    team_id = None
    if team_name:
        existing = await db.pool.fetchval(
            "SELECT id FROM cleaning_teams WHERE business_id = $1 AND name = $2",
            business_id,
            team_name,
        )
        if existing:
            team_id = existing
        else:
            team_id = await db.pool.fetchval(
                """
                INSERT INTO cleaning_teams (business_id, name, color, is_active)
                VALUES ($1, $2, $3, true)
                RETURNING id
                """,
                business_id,
                team_name,
                team_color,
            )
            logger.info("[ONBOARDING] Created team '%s' for business %s", team_name, business_id)

    # Create invitations for each email
    now = datetime.utcnow()
    for email in invite_emails:
        email = email.strip()
        if not email:
            continue

        # Check if invitation already exists
        existing = await db.pool.fetchval(
            """
            SELECT id FROM cleaning_team_members
            WHERE business_id = $1 AND email = $2
            """,
            business_id,
            email,
        )
        if existing:
            continue

        # Create a team member placeholder with invitation status
        await db.pool.execute(
            """
            INSERT INTO cleaning_team_members
                (business_id, first_name, email, role, employment_type,
                 status, invitation_email, invitation_status, invited_at)
            VALUES ($1, $2, $3, 'cleaner', 'employee', 'invited',
                    $3, 'pending', $4)
            """,
            business_id,
            email.split("@")[0],  # Use email prefix as placeholder name
            email,
            now,
        )

        logger.info("[ONBOARDING] Created invite for %s in business %s", email, business_id)

    # If we have both a team and invited members, create user role entries too
    if team_id and invite_emails:
        for email in invite_emails:
            email = email.strip()
            if not email:
                continue

            # Check for existing user
            user_row = await db.pool.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                email,
            )

            # Create cleaning_user_roles entry (pending)
            existing_role = await db.pool.fetchval(
                """
                SELECT id FROM cleaning_user_roles
                WHERE business_id = $1 AND role = 'cleaner'
                  AND id IN (
                      SELECT cur.id FROM cleaning_user_roles cur
                      JOIN users u ON u.id = cur.user_id
                      WHERE u.email = $2 AND cur.business_id = $1
                  )
                """,
                business_id,
                email,
            )

            if not existing_role:
                await db.pool.execute(
                    """
                    INSERT INTO cleaning_user_roles
                        (user_id, business_id, role, team_id, invited_by,
                         invited_at, is_active)
                    VALUES ($1, $2, 'cleaner', $3, $4, $5, false)
                    """,
                    str(user_row["id"]) if user_row else None,
                    business_id,
                    str(team_id),
                    user_id,
                    now,
                )
