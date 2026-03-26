"""
Seed script for Clean New Orleans — first Xcleaners client.

Creates the business, copies service templates, sets up service areas,
pricing rules, teams, and owner role. Idempotent (safe to run multiple times).

Usage:
    python scripts/seed_clean_new_orleans.py

Requires:
    - Migrations 011-019 already applied
    - DATABASE_URL or XCLEANERS_DATABASE_URL env var set
    - asyncpg installed
"""

import asyncio
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg

DATABASE_URL = os.getenv("XCLEANERS_DATABASE_URL", os.getenv("DATABASE_URL"))

# UUIDs (deterministic for reproducibility)
OWNER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "cleanneworleans.owner")
BUSINESS_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "cleanneworleans.business")


# ── Service Areas ────────────────────────────────────────

AREAS = [
    ("French Quarter / CBD", ["70112", "70116", "70130"], "New Orleans"),
    ("Uptown / Garden District", ["70115", "70118", "70130"], "New Orleans"),
    ("Mid-City / Gentilly", ["70119", "70122", "70125"], "New Orleans"),
    ("Lakeview / Metairie", ["70124", "70001", "70002", "70005"], "New Orleans"),
    ("Bywater / Marigny", ["70117", "70116"], "New Orleans"),
    ("Algiers / West Bank", ["70114", "70131"], "New Orleans"),
    ("New Orleans East", ["70126", "70127", "70128", "70129"], "New Orleans"),
    ("Kenner / River Ridge", ["70062", "70065", "70123"], "Kenner"),
]


# ── Pricing Rules ────────────────────────────────────────

PRICING_RULES = [
    # (name, rule_type, service_slug_or_none, conditions, amount, percentage, priority)
    ("Standard Clean - Base Price", "base_price", "standard-clean", {}, 120.00, None, 1),
    ("Deep Clean - Base Price", "base_price", "deep-clean", {}, 200.00, None, 2),
    ("Move-In/Out - Base Price", "base_price", "move-in-out", {}, 250.00, None, 3),
    ("Post-Construction - Base Price", "base_price", "post-construction", {}, 300.00, None, 4),
    ("Weekly Recurring Discount", "discount", None, {"frequency": "weekly"}, None, 15.00, 10),
    ("Biweekly Recurring Discount", "discount", None, {"frequency": "biweekly"}, None, 8.00, 11),
    ("Monthly Recurring Discount", "discount", None, {"frequency": "monthly"}, None, 5.00, 12),
    ("Extra Bedroom Surcharge", "addon", None, {"bedrooms_gte": 4}, 25.00, None, 20),
    ("Extra Bathroom Surcharge", "addon", None, {"bathrooms_gte": 3}, 20.00, None, 21),
    ("Large Home Premium (2000+ sqft)", "surcharge", None, {"square_feet_gte": 2000}, 40.00, None, 22),
    ("Pet Surcharge", "surcharge", None, {"has_pets": True}, 25.00, None, 25),
    ("Weekend Premium", "multiplier", None, {"day_of_week": [0, 6]}, None, 15.00, 30),
]


# ── Teams ────────────────────────────────────────────────

TEAMS = [
    ("Team Alpha", "#1A73E8"),   # Blue
    ("Team Beta", "#10B981"),    # Green
    ("Team Gamma", "#F59E0B"),   # Amber
]


# ── Cleaning Settings ────────────────────────────────────

CLEANING_SETTINGS = json.dumps({
    "business_hours": {"start": "07:00", "end": "18:00"},
    "cancellation_policy_hours": 24,
    "default_payment_terms_days": 15,
    "timezone": "America/Chicago",
    "tax_rate": 0.0,
    "currency": "USD",
    "language": "en",
    "notifications": {
        "sms": True,
        "email": True,
        "push": True,
    },
})


# ── Helpers ──────────────────────────────────────────────

async def seed_owner(conn):
    """Create owner user if not exists."""
    await conn.execute("""
        INSERT INTO users (id, email, nome)
        VALUES ($1, 'admin@cleanneworleans.com', 'Clean New Orleans Admin')
        ON CONFLICT (id) DO NOTHING
    """, OWNER_ID)
    print(f"  [OK] Owner user: {OWNER_ID}")


async def seed_business(conn):
    """Create the Clean New Orleans business."""
    await conn.execute("""
        INSERT INTO businesses (id, name, slug, owner_id, cleaning_settings)
        VALUES ($1, 'Clean New Orleans', 'clean-new-orleans', $2, $3::jsonb)
        ON CONFLICT (id) DO NOTHING
    """, BUSINESS_ID, OWNER_ID, CLEANING_SETTINGS)
    print(f"  [OK] Business: {BUSINESS_ID} (clean-new-orleans)")


async def seed_services_from_templates(conn):
    """Copy service templates into business services."""
    existing = await conn.fetchval(
        "SELECT COUNT(*) FROM cleaning_services WHERE business_id = $1",
        BUSINESS_ID,
    )
    if existing > 0:
        print(f"  [SKIP] Services already exist ({existing} found)")
        return existing

    templates = await conn.fetch("""
        SELECT name, slug, description, category, suggested_base_price,
               price_unit, estimated_duration_minutes, min_team_size, icon, sort_order
        FROM cleaning_service_templates
        ORDER BY sort_order
    """)

    count = 0
    for t in templates:
        await conn.execute("""
            INSERT INTO cleaning_services (
                business_id, name, slug, description, category,
                base_price, price_unit, estimated_duration_minutes,
                min_team_size, icon, sort_order, is_active
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true)
            ON CONFLICT (business_id, slug) DO NOTHING
        """,
            BUSINESS_ID, t["name"], t["slug"], t["description"], t["category"],
            t["suggested_base_price"], t["price_unit"],
            t["estimated_duration_minutes"], t["min_team_size"],
            t["icon"], t["sort_order"],
        )
        count += 1

    print(f"  [OK] Copied {count} service templates -> cleaning_services")
    return count


async def seed_areas(conn):
    """Create service areas for New Orleans metro."""
    existing = await conn.fetchval(
        "SELECT COUNT(*) FROM cleaning_areas WHERE business_id = $1",
        BUSINESS_ID,
    )
    if existing > 0:
        print(f"  [SKIP] Areas already exist ({existing} found)")
        return

    for i, (name, zips, city) in enumerate(AREAS):
        await conn.execute("""
            INSERT INTO cleaning_areas (business_id, name, zip_codes, city, state, is_active, priority)
            VALUES ($1, $2, $3, $4, 'LA', true, $5)
            ON CONFLICT DO NOTHING
        """, BUSINESS_ID, name, zips, city, i + 1)

    print(f"  [OK] Created {len(AREAS)} service areas")


async def seed_owner_role(conn):
    """Assign owner role in cleaning_user_roles."""
    await conn.execute("""
        INSERT INTO cleaning_user_roles (user_id, business_id, role, is_active)
        VALUES ($1, $2, 'owner', true)
        ON CONFLICT (user_id, business_id, role) DO NOTHING
    """, OWNER_ID, BUSINESS_ID)
    print(f"  [OK] Owner role assigned")


async def seed_pricing_rules(conn):
    """Create default pricing rules for New Orleans market."""
    existing = await conn.fetchval(
        "SELECT COUNT(*) FROM cleaning_pricing_rules WHERE business_id = $1",
        BUSINESS_ID,
    )
    if existing > 0:
        print(f"  [SKIP] Pricing rules already exist ({existing} found)")
        return

    # Build a slug -> service_id map for linking rules to services
    services = await conn.fetch(
        "SELECT id, slug FROM cleaning_services WHERE business_id = $1",
        BUSINESS_ID,
    )
    slug_to_id = {s["slug"]: s["id"] for s in services}

    count = 0
    for name, rule_type, service_slug, conditions, amount, percentage, priority in PRICING_RULES:
        service_id = slug_to_id.get(service_slug) if service_slug else None
        await conn.execute("""
            INSERT INTO cleaning_pricing_rules (
                business_id, service_id, name, rule_type,
                conditions, amount, percentage, priority, is_active
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, true)
        """,
            BUSINESS_ID, service_id, name, rule_type,
            json.dumps(conditions), amount, percentage, priority,
        )
        count += 1

    print(f"  [OK] Created {count} pricing rules")


async def seed_teams(conn):
    """Create sample team structure."""
    existing = await conn.fetchval(
        "SELECT COUNT(*) FROM cleaning_teams WHERE business_id = $1",
        BUSINESS_ID,
    )
    if existing > 0:
        print(f"  [SKIP] Teams already exist ({existing} found)")
        return

    for name, color in TEAMS:
        team_id = uuid.uuid5(uuid.NAMESPACE_DNS, f"cleanneworleans.team.{name}")
        await conn.execute("""
            INSERT INTO cleaning_teams (id, business_id, name, color, is_active, max_daily_jobs)
            VALUES ($1, $2, $3, $4, true, 6)
            ON CONFLICT (id) DO NOTHING
        """, team_id, BUSINESS_ID, name, color)

    print(f"  [OK] Created {len(TEAMS)} teams")


# ── Main ─────────────────────────────────────────────────

async def seed():
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL or XCLEANERS_DATABASE_URL not set.")
        sys.exit(1)

    print("=" * 60)
    print("Xcleaners — Seed Clean New Orleans")
    print("=" * 60)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("\n[1] Creating owner user...")
        await seed_owner(conn)

        print("\n[2] Creating business...")
        await seed_business(conn)

        print("\n[3] Copying service templates...")
        await seed_services_from_templates(conn)

        print("\n[4] Creating service areas (NOLA metro)...")
        await seed_areas(conn)

        print("\n[5] Assigning owner role...")
        await seed_owner_role(conn)

        print("\n[6] Creating pricing rules...")
        await seed_pricing_rules(conn)

        print("\n[7] Creating teams...")
        await seed_teams(conn)

        # ── Summary ──────────────────────────────────────
        print("\n" + "=" * 60)
        services_count = await conn.fetchval(
            "SELECT COUNT(*) FROM cleaning_services WHERE business_id = $1", BUSINESS_ID)
        areas_count = await conn.fetchval(
            "SELECT COUNT(*) FROM cleaning_areas WHERE business_id = $1", BUSINESS_ID)
        rules_count = await conn.fetchval(
            "SELECT COUNT(*) FROM cleaning_pricing_rules WHERE business_id = $1", BUSINESS_ID)
        teams_count = await conn.fetchval(
            "SELECT COUNT(*) FROM cleaning_teams WHERE business_id = $1", BUSINESS_ID)

        print(f"  Clean New Orleans seeded successfully!")
        print(f"  Business ID : {BUSINESS_ID}")
        print(f"  Owner ID    : {OWNER_ID}")
        print(f"  Slug        : clean-new-orleans")
        print(f"  Services    : {services_count}")
        print(f"  Areas       : {areas_count}")
        print(f"  Pricing     : {rules_count} rules")
        print(f"  Teams       : {teams_count}")
        print("=" * 60)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
