-- ============================================
-- MIGRATION 012: CleanClaw v3 — Teams, Schedules, User Roles
-- ClaWtoBusiness Ecosystem
-- ============================================
-- Adds 4 new tables and modifies 2 existing tables for v3:
--   NEW:  cleaning_teams, cleaning_team_assignments,
--         cleaning_client_schedules, cleaning_user_roles
--   MOD:  cleaning_team_members (add invitation fields, drop pin_hash)
--         cleaning_bookings (add team_id)
--
-- All tables scoped by business_id for multi-tenant isolation.
-- Safe to run on a live system (additive first, then ALTER).
-- ============================================

BEGIN;

-- ============================================
-- 1. CLEANING_TEAMS
-- ============================================
-- Named groups of cleaners (Team Alpha, Morning Crew).
-- Teams are the primary scheduling unit in v3.
CREATE TABLE IF NOT EXISTS cleaning_teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    color VARCHAR(7) DEFAULT '#3B82F6',              -- hex color for calendar UI
    team_lead_id UUID REFERENCES cleaning_team_members(id) ON DELETE SET NULL,
    max_daily_jobs INTEGER DEFAULT 6,
    service_area_ids UUID[] DEFAULT '{}',             -- array of cleaning_areas.id
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_cleaning_teams_name UNIQUE (business_id, name)
);

CREATE INDEX IF NOT EXISTS idx_cleaning_teams_biz
    ON cleaning_teams(business_id) WHERE is_active = true;

DROP TRIGGER IF EXISTS tr_cleaning_teams_updated_at ON cleaning_teams;
CREATE TRIGGER tr_cleaning_teams_updated_at
    BEFORE UPDATE ON cleaning_teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 2. CLEANING_TEAM_ASSIGNMENTS
-- ============================================
-- Maps team members to teams with date ranges (supports rotation).
-- A member can be on exactly one active team at a time.
CREATE TABLE IF NOT EXISTS cleaning_team_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id UUID NOT NULL REFERENCES cleaning_teams(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES cleaning_team_members(id) ON DELETE CASCADE,
    role_in_team VARCHAR(20) DEFAULT 'member' CHECK (role_in_team IN (
        'lead', 'member', 'trainee'
    )),
    effective_from DATE NOT NULL DEFAULT CURRENT_DATE,
    effective_until DATE,                              -- NULL = indefinite
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_cleaning_team_assign UNIQUE (team_id, member_id, effective_from)
);

-- Find which team a member currently belongs to
CREATE INDEX IF NOT EXISTS idx_cleaning_team_assign_member
    ON cleaning_team_assignments(member_id) WHERE is_active = true;

-- List all members of a team
CREATE INDEX IF NOT EXISTS idx_cleaning_team_assign_team
    ON cleaning_team_assignments(team_id) WHERE is_active = true;


-- ============================================
-- 3. CLEANING_CLIENT_SCHEDULES
-- ============================================
-- Recurring service agreements per client.
-- The schedule engine reads these to auto-generate daily bookings.
CREATE TABLE IF NOT EXISTS cleaning_client_schedules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    client_id UUID NOT NULL REFERENCES cleaning_clients(id) ON DELETE CASCADE,
    service_id UUID NOT NULL REFERENCES cleaning_services(id) ON DELETE RESTRICT,
    frequency VARCHAR(20) NOT NULL CHECK (frequency IN (
        'weekly', 'biweekly', 'monthly', 'sporadic'
    )),
    custom_interval_days INTEGER,                      -- only when frequency='sporadic'
    preferred_day_of_week SMALLINT CHECK (preferred_day_of_week BETWEEN 0 AND 6),
    preferred_time_start TIME,
    preferred_time_end TIME,
    preferred_team_id UUID REFERENCES cleaning_teams(id) ON DELETE SET NULL,
    agreed_price NUMERIC(10,2),                        -- locked recurring price
    estimated_duration_minutes INTEGER,
    min_team_size INTEGER DEFAULT 1,
    next_occurrence DATE,                              -- precomputed for efficient scheduling
    notes TEXT,                                         -- special instructions
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN (
        'active', 'paused', 'cancelled'
    )),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scheduler reads this: "give me all active schedules due on or before DATE"
CREATE INDEX IF NOT EXISTS idx_cleaning_client_sched_next
    ON cleaning_client_schedules(business_id, next_occurrence)
    WHERE status = 'active';

-- Find all schedules for a specific client
CREATE INDEX IF NOT EXISTS idx_cleaning_client_sched_client
    ON cleaning_client_schedules(client_id);

-- Find schedules assigned to a specific team
CREATE INDEX IF NOT EXISTS idx_cleaning_client_sched_team
    ON cleaning_client_schedules(preferred_team_id)
    WHERE preferred_team_id IS NOT NULL;

DROP TRIGGER IF EXISTS tr_cleaning_client_sched_updated_at ON cleaning_client_schedules;
CREATE TRIGGER tr_cleaning_client_sched_updated_at
    BEFORE UPDATE ON cleaning_client_schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================
-- 4. CLEANING_USER_ROLES
-- ============================================
-- Maps platform users to cleaning-specific roles within a business.
-- Replaces PIN-based auth: all users log in via platform (OAuth/email).
CREATE TABLE IF NOT EXISTS cleaning_user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN (
        'owner', 'homeowner', 'team_lead', 'cleaner'
    )),
    team_id UUID REFERENCES cleaning_teams(id) ON DELETE SET NULL,
    invited_by UUID REFERENCES users(id) ON DELETE SET NULL,
    invited_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_cleaning_user_role UNIQUE (user_id, business_id, role)
);

-- List all users with a given role in a business (e.g. all cleaners)
CREATE INDEX IF NOT EXISTS idx_cleaning_user_roles_biz_role
    ON cleaning_user_roles(business_id, role);

-- Find all businesses a user belongs to
CREATE INDEX IF NOT EXISTS idx_cleaning_user_roles_user
    ON cleaning_user_roles(user_id) WHERE is_active = true;


-- ============================================
-- 5. MODIFY: cleaning_team_members
-- ============================================
-- Add invitation fields for onboarding flow.
-- user_id already exists in 011 but we ensure it is there.

-- Add invitation_email: email used for the invite (may differ from user email)
ALTER TABLE cleaning_team_members
    ADD COLUMN IF NOT EXISTS invitation_email VARCHAR(255);

-- Add invitation_status: tracks whether cleaner accepted the platform invite
ALTER TABLE cleaning_team_members
    ADD COLUMN IF NOT EXISTS invitation_status VARCHAR(20) DEFAULT 'none'
    CHECK (invitation_status IN ('none', 'pending', 'accepted', 'expired'));

-- Add invited_at: when the invitation was sent
ALTER TABLE cleaning_team_members
    ADD COLUMN IF NOT EXISTS invited_at TIMESTAMPTZ;

-- Drop pin_hash: auth is now via platform login (OAuth / email+password)
-- Safe: column may not exist if 011 was never applied on this env.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'cleaning_team_members' AND column_name = 'pin_hash'
    ) THEN
        ALTER TABLE cleaning_team_members DROP COLUMN pin_hash;
    END IF;
END $$;


-- ============================================
-- 6. MODIFY: cleaning_bookings
-- ============================================
-- Add team_id: primary team assignment (replaces JSONB assigned_team).
-- lead_cleaner_id remains for backward compat but team_id is preferred.

ALTER TABLE cleaning_bookings
    ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES cleaning_teams(id) ON DELETE SET NULL;

-- Team daily schedule query: "show me Team A's jobs for March 20"
CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_team_date
    ON cleaning_bookings(business_id, team_id, scheduled_date)
    WHERE team_id IS NOT NULL;


-- ============================================
-- ROW LEVEL SECURITY (RLS) — New Tables
-- ============================================

ALTER TABLE cleaning_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_team_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_client_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE cleaning_user_roles ENABLE ROW LEVEL SECURITY;

-- cleaning_teams: isolation by business_id
DROP POLICY IF EXISTS cleaning_teams_isolation ON cleaning_teams;
CREATE POLICY cleaning_teams_isolation ON cleaning_teams
    USING (business_id::text = current_setting('app.current_business_id', true));

-- cleaning_team_assignments: isolation via team -> business_id
-- Assignments don't have a direct business_id, so we join through cleaning_teams.
-- For performance, use a subquery policy.
DROP POLICY IF EXISTS cleaning_team_assignments_isolation ON cleaning_team_assignments;
CREATE POLICY cleaning_team_assignments_isolation ON cleaning_team_assignments
    USING (
        team_id IN (
            SELECT id FROM cleaning_teams
            WHERE business_id::text = current_setting('app.current_business_id', true)
        )
    );

-- cleaning_client_schedules: isolation by business_id
DROP POLICY IF EXISTS cleaning_client_schedules_isolation ON cleaning_client_schedules;
CREATE POLICY cleaning_client_schedules_isolation ON cleaning_client_schedules
    USING (business_id::text = current_setting('app.current_business_id', true));

-- cleaning_user_roles: isolation by business_id
DROP POLICY IF EXISTS cleaning_user_roles_isolation ON cleaning_user_roles;
CREATE POLICY cleaning_user_roles_isolation ON cleaning_user_roles
    USING (business_id::text = current_setting('app.current_business_id', true));


-- ============================================
-- VIEWS — Team Schedule
-- ============================================

-- Daily schedule per team: shows all jobs for a team on a given date
-- with client info, service type, and timing.
CREATE OR REPLACE VIEW v_cleaning_team_daily_schedule AS
SELECT
    b.business_id,
    COALESCE(b.team_id, NULL) AS team_id,
    t.name AS team_name,
    t.color AS team_color,
    b.id AS booking_id,
    b.scheduled_date,
    b.scheduled_start,
    b.scheduled_end,
    b.estimated_duration_minutes,
    b.status,
    b.address_line1,
    b.city,
    b.zip_code,
    b.latitude,
    b.longitude,
    b.access_instructions,
    b.special_instructions,
    c.id AS client_id,
    c.first_name || ' ' || COALESCE(c.last_name, '') AS client_name,
    c.phone AS client_phone,
    s.name AS service_name,
    s.category AS service_category,
    b.quoted_price,
    b.lead_cleaner_id,
    lc.first_name || ' ' || COALESCE(lc.last_name, '') AS lead_cleaner_name
FROM cleaning_bookings b
JOIN cleaning_clients c ON c.id = b.client_id
JOIN cleaning_services s ON s.id = b.service_id
LEFT JOIN cleaning_teams t ON t.id = b.team_id
LEFT JOIN cleaning_team_members lc ON lc.id = b.lead_cleaner_id
WHERE b.status NOT IN ('cancelled', 'no_show')
ORDER BY b.scheduled_date, b.scheduled_start;

-- Team workload summary: jobs per team for a date range
CREATE OR REPLACE VIEW v_cleaning_team_workload AS
SELECT
    b.business_id,
    b.team_id,
    t.name AS team_name,
    t.max_daily_jobs,
    b.scheduled_date,
    COUNT(*) AS jobs_count,
    COALESCE(SUM(b.estimated_duration_minutes), 0) AS total_minutes,
    COUNT(*) FILTER (WHERE b.status = 'completed') AS completed,
    COUNT(*) FILTER (WHERE b.status IN ('scheduled', 'confirmed')) AS pending,
    COUNT(*) FILTER (WHERE b.status = 'in_progress') AS in_progress
FROM cleaning_bookings b
JOIN cleaning_teams t ON t.id = b.team_id
WHERE b.team_id IS NOT NULL
  AND b.status NOT IN ('cancelled', 'no_show')
GROUP BY b.business_id, b.team_id, t.name, t.max_daily_jobs, b.scheduled_date;

-- Update today's schedule view to include team_id (replace from 011)
CREATE OR REPLACE VIEW v_cleaning_today_schedule AS
SELECT
    b.id AS booking_id,
    b.business_id,
    b.scheduled_start,
    b.scheduled_end,
    b.status,
    c.first_name || ' ' || COALESCE(c.last_name, '') AS client_name,
    c.address_line1 AS client_address,
    c.city AS client_city,
    s.name AS service_name,
    b.quoted_price,
    b.assigned_team,
    b.lead_cleaner_id,
    b.team_id,
    t.name AS team_name,
    t.color AS team_color
FROM cleaning_bookings b
JOIN cleaning_clients c ON c.id = b.client_id
JOIN cleaning_services s ON s.id = b.service_id
LEFT JOIN cleaning_teams t ON t.id = b.team_id
WHERE b.scheduled_date = CURRENT_DATE
  AND b.status NOT IN ('cancelled', 'no_show');


-- ============================================
-- COMMENTS — Table documentation
-- ============================================
COMMENT ON TABLE cleaning_teams IS 'Named groups of cleaners (Team A, Morning Crew). Primary scheduling unit in v3.';
COMMENT ON TABLE cleaning_team_assignments IS 'Maps cleaners to teams with date ranges. Supports rotation and temporary assignments.';
COMMENT ON TABLE cleaning_client_schedules IS 'Recurring service agreements. Schedule engine reads these to auto-generate daily bookings.';
COMMENT ON TABLE cleaning_user_roles IS 'Maps platform users to cleaning roles (owner/homeowner/team_lead/cleaner) within a business.';

COMMENT ON COLUMN cleaning_teams.service_area_ids IS 'Array of cleaning_areas.id UUIDs for geographic preference.';
COMMENT ON COLUMN cleaning_teams.max_daily_jobs IS 'Maximum jobs this team should be assigned per day.';
COMMENT ON COLUMN cleaning_client_schedules.next_occurrence IS 'Precomputed next date for efficient scheduler queries.';
COMMENT ON COLUMN cleaning_client_schedules.custom_interval_days IS 'Only used when frequency=sporadic. Number of days between services.';
COMMENT ON COLUMN cleaning_user_roles.team_id IS 'For team_lead/cleaner roles: which team this user belongs to.';
COMMENT ON COLUMN cleaning_bookings.team_id IS 'v3: Primary team assignment. Replaces JSONB assigned_team for structured queries.';
COMMENT ON COLUMN cleaning_team_members.invitation_status IS 'v3: Tracks onboarding invite status (none/pending/accepted/expired).';

COMMIT;
