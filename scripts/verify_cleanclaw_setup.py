"""
Verify CleanClaw database setup is complete and correct.

Checks all tables, RLS, indexes, roles, and seed data.
Outputs green checkmarks for PASS, red X for FAIL, with summary counts.

Usage:
    python scripts/verify_cleanclaw_setup.py

Requires:
    - DATABASE_URL or CLEANCLAW_DATABASE_URL env var set
    - asyncpg installed
"""

import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg

DATABASE_URL = os.getenv("CLEANCLAW_DATABASE_URL", os.getenv("DATABASE_URL"))

BUSINESS_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "cleanneworleans.business")

# All 21 cleaning tables (migrations 011 + 012)
EXPECTED_TABLES = [
    "cleaning_services",
    "cleaning_clients",
    "cleaning_team_members",
    "cleaning_team_availability",
    "cleaning_recurring_schedules",
    "cleaning_bookings",
    "cleaning_checklists",
    "cleaning_checklist_items",
    "cleaning_job_logs",
    "cleaning_invoices",
    "cleaning_invoice_items",
    "cleaning_reviews",
    "cleaning_leads",
    "cleaning_areas",
    "cleaning_pricing_rules",
    "cleaning_notifications",
    "cleaning_daily_analytics",
    # v3 tables (migration 012)
    "cleaning_teams",
    "cleaning_team_assignments",
    "cleaning_client_schedules",
    "cleaning_user_roles",
    # Template tables (seed data)
    "cleaning_service_templates",
    "cleaning_checklist_templates",
]

# Tables that MUST have RLS enabled (all except template tables)
RLS_TABLES = [t for t in EXPECTED_TABLES if "template" not in t]

# Key indexes from migration 019
EXPECTED_INDEXES_019 = [
    "idx_cleaning_bookings_status_date",
    "idx_cleaning_invoices_paid",
    "idx_cleaning_clients_created",
    "idx_cleaning_clients_metadata_stripe",
    "idx_cleaning_leads_created_date",
    "idx_cleaning_notifications_analytics",
    "idx_cleaning_reviews_booking",
    "idx_cleaning_bookings_client_date_status",
]


# ── Helpers ──────────────────────────────────────────────

pass_count = 0
fail_count = 0
warn_count = 0


def ok(msg):
    global pass_count
    pass_count += 1
    print(f"  \033[32m✓\033[0m {msg}")


def fail(msg):
    global fail_count
    fail_count += 1
    print(f"  \033[31m✗\033[0m {msg}")


def warn(msg):
    global warn_count
    warn_count += 1
    print(f"  \033[33m⚠\033[0m {msg}")


# ── Checks ───────────────────────────────────────────────

async def check_tables(conn):
    """Check all cleaning tables exist."""
    print("\n[1] Cleaning tables")

    existing = await conn.fetch("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name LIKE 'cleaning_%'
        ORDER BY table_name
    """)
    existing_set = {r["table_name"] for r in existing}

    for table in EXPECTED_TABLES:
        if table in existing_set:
            ok(table)
        else:
            fail(f"{table} — MISSING")

    # Report any unexpected cleaning tables
    unexpected = existing_set - set(EXPECTED_TABLES)
    for t in sorted(unexpected):
        warn(f"{t} — unexpected table (not in expected list)")


async def check_rls(conn):
    """Check RLS is enabled on all cleaning tables."""
    print("\n[2] Row Level Security (RLS)")

    rls_status = await conn.fetch("""
        SELECT relname, relrowsecurity
        FROM pg_class
        WHERE relname = ANY($1::text[])
    """, RLS_TABLES)
    rls_map = {r["relname"]: r["relrowsecurity"] for r in rls_status}

    for table in RLS_TABLES:
        if table not in rls_map:
            fail(f"{table} — table not found")
        elif rls_map[table]:
            ok(f"{table} — RLS enabled")
        else:
            fail(f"{table} — RLS NOT enabled")


async def check_indexes_019(conn):
    """Check production indexes from migration 019 exist."""
    print("\n[3] Production indexes (migration 019)")

    existing = await conn.fetch("""
        SELECT indexname FROM pg_indexes
        WHERE schemaname = 'public'
          AND indexname = ANY($1::text[])
    """, EXPECTED_INDEXES_019)
    existing_set = {r["indexname"] for r in existing}

    for idx in EXPECTED_INDEXES_019:
        if idx in existing_set:
            ok(idx)
        else:
            fail(f"{idx} — MISSING")


async def check_app_role(conn):
    """Check cleanclaw_app role exists."""
    print("\n[4] Application role")

    role = await conn.fetchrow("""
        SELECT rolname, rolsuper, rolcanlogin
        FROM pg_roles WHERE rolname = 'cleanclaw_app'
    """)
    if role:
        ok(f"cleanclaw_app role exists (login={role['rolcanlogin']}, superuser={role['rolsuper']})")
        if role["rolsuper"]:
            warn("cleanclaw_app is SUPERUSER — should be non-superuser")
    else:
        fail("cleanclaw_app role — MISSING")


async def check_business(conn):
    """Check Clean New Orleans business exists with correct data."""
    print("\n[5] Clean New Orleans business")

    biz = await conn.fetchrow("""
        SELECT id, name, slug, owner_id, cleaning_settings
        FROM businesses WHERE id = $1
    """, BUSINESS_ID)

    if not biz:
        fail("Business not found — run seed_clean_new_orleans.py first")
        return

    ok(f"Business exists: {biz['name']} ({biz['slug']})")

    if biz["slug"] == "clean-new-orleans":
        ok("Slug is correct")
    else:
        fail(f"Slug mismatch: expected 'clean-new-orleans', got '{biz['slug']}'")

    if biz["cleaning_settings"]:
        settings = biz["cleaning_settings"]
        if isinstance(settings, str):
            import json
            settings = json.loads(settings)
        if settings.get("timezone") == "America/Chicago":
            ok("Timezone: America/Chicago")
        else:
            fail(f"Timezone mismatch: {settings.get('timezone')}")
    else:
        fail("cleaning_settings is empty")


async def check_service_templates(conn):
    """Check service templates are populated."""
    print("\n[6] Service templates")

    count = await conn.fetchval("SELECT COUNT(*) FROM cleaning_service_templates")
    if count >= 12:
        ok(f"{count} service templates in database")
    elif count > 0:
        warn(f"Only {count} service templates (expected >= 12)")
    else:
        fail("No service templates — migration 011 seed data missing")


async def check_business_services(conn):
    """Check services were copied for the business."""
    print("\n[7] Business services (copied from templates)")

    count = await conn.fetchval(
        "SELECT COUNT(*) FROM cleaning_services WHERE business_id = $1",
        BUSINESS_ID,
    )
    if count >= 12:
        ok(f"{count} services for Clean New Orleans")
    elif count > 0:
        warn(f"Only {count} services (expected >= 12)")
    else:
        fail("No services — run seed_clean_new_orleans.py")


async def check_areas(conn):
    """Check service areas for NOLA exist."""
    print("\n[8] Service areas (New Orleans)")

    areas = await conn.fetch("""
        SELECT name, city, state, zip_codes, is_active
        FROM cleaning_areas WHERE business_id = $1
        ORDER BY priority
    """, BUSINESS_ID)

    if len(areas) >= 8:
        ok(f"{len(areas)} service areas configured")
        for a in areas:
            status = "active" if a["is_active"] else "inactive"
            zips = len(a["zip_codes"]) if a["zip_codes"] else 0
            ok(f"  {a['name']} ({a['city']}, {a['state']}) — {zips} zips — {status}")
    elif len(areas) > 0:
        warn(f"Only {len(areas)} areas (expected >= 8)")
    else:
        fail("No service areas — run seed_clean_new_orleans.py")


async def check_owner_role(conn):
    """Check owner role is assigned."""
    print("\n[9] Owner role")

    role = await conn.fetchrow("""
        SELECT user_id, role, is_active
        FROM cleaning_user_roles
        WHERE business_id = $1 AND role = 'owner'
    """, BUSINESS_ID)

    if role:
        ok(f"Owner role assigned (user={role['user_id']}, active={role['is_active']})")
    else:
        fail("No owner role — run seed_clean_new_orleans.py")


async def check_pricing_rules(conn):
    """Check pricing rules exist."""
    print("\n[10] Pricing rules")

    count = await conn.fetchval(
        "SELECT COUNT(*) FROM cleaning_pricing_rules WHERE business_id = $1",
        BUSINESS_ID,
    )
    if count >= 10:
        ok(f"{count} pricing rules configured")
    elif count > 0:
        warn(f"Only {count} pricing rules (expected >= 10)")
    else:
        fail("No pricing rules — run seed_clean_new_orleans.py")


async def check_teams(conn):
    """Check teams exist."""
    print("\n[11] Teams")

    teams = await conn.fetch("""
        SELECT name, color, is_active, max_daily_jobs
        FROM cleaning_teams WHERE business_id = $1
        ORDER BY name
    """, BUSINESS_ID)

    if len(teams) >= 3:
        ok(f"{len(teams)} teams configured")
        for t in teams:
            ok(f"  {t['name']} ({t['color']}) — max {t['max_daily_jobs']} jobs/day")
    elif len(teams) > 0:
        warn(f"Only {len(teams)} teams (expected >= 3)")
    else:
        fail("No teams — run seed_clean_new_orleans.py")


async def check_rls_policies(conn):
    """Check RLS policies with WITH CHECK exist on all tables."""
    print("\n[12] RLS policies (WITH CHECK)")

    policies = await conn.fetch("""
        SELECT tablename, policyname, cmd, qual IS NOT NULL AS has_using,
               with_check IS NOT NULL AS has_with_check
        FROM pg_policies
        WHERE schemaname = 'public'
          AND tablename LIKE 'cleaning_%'
          AND tablename NOT LIKE 'cleaning_%_template%'
        ORDER BY tablename
    """)

    # Group by table
    table_policies = {}
    for p in policies:
        table_policies.setdefault(p["tablename"], []).append(p)

    for table in RLS_TABLES:
        pols = table_policies.get(table, [])
        if not pols:
            fail(f"{table} — no RLS policy")
        else:
            has_with_check = any(p["has_with_check"] for p in pols)
            if has_with_check:
                ok(f"{table} — policy with WITH CHECK")
            else:
                warn(f"{table} — policy exists but missing WITH CHECK (migration 019)")


async def check_extensions(conn):
    """Check required extensions."""
    print("\n[13] Extensions")

    for ext_name in ["uuid-ossp", "pg_trgm"]:
        ext = await conn.fetchrow(
            "SELECT extname FROM pg_extension WHERE extname = $1", ext_name
        )
        if ext:
            ok(f"{ext_name} extension installed")
        else:
            fail(f"{ext_name} extension — MISSING")


# ── Main ─────────────────────────────────────────────────

async def verify():
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL or CLEANCLAW_DATABASE_URL not set.")
        sys.exit(1)

    print("=" * 60)
    print("CleanClaw — Setup Verification")
    print("=" * 60)

    conn = await asyncpg.connect(DATABASE_URL)

    try:
        await check_tables(conn)
        await check_rls(conn)
        await check_indexes_019(conn)
        await check_app_role(conn)
        await check_business(conn)
        await check_service_templates(conn)
        await check_business_services(conn)
        await check_areas(conn)
        await check_owner_role(conn)
        await check_pricing_rules(conn)
        await check_teams(conn)
        await check_rls_policies(conn)
        await check_extensions(conn)

    finally:
        await conn.close()

    # ── Summary ──────────────────────────────────────
    print("\n" + "=" * 60)
    total = pass_count + fail_count + warn_count
    print(f"  Results: {total} checks")
    print(f"    \033[32m✓ PASS: {pass_count}\033[0m")
    if warn_count:
        print(f"    \033[33m⚠ WARN: {warn_count}\033[0m")
    if fail_count:
        print(f"    \033[31m✗ FAIL: {fail_count}\033[0m")
    print("=" * 60)

    if fail_count > 0:
        print("\n  Action required: Fix FAIL items above.")
        print("  Common fixes:")
        print("    - Run migrations: psql $DATABASE_URL -f database/migrations/011_cleaning_module.sql")
        print("    - Run seed: python scripts/seed_clean_new_orleans.py")
        sys.exit(1)
    else:
        print("\n  All checks passed! CleanClaw is ready.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(verify())
