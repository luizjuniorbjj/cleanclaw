-- ============================================================================
-- Migration 019: CleanClaw Production Readiness
-- ============================================================================
-- Purpose: Consolidate all production-readiness changes for CleanClaw module
--
-- Changes:
--   1. Add metadata JSONB column to cleaning_clients
--   2. Fix cleaning_leads status CHECK constraint to include 'converted'
--   3. Create 8 production performance indexes
--   4. Recreate RLS policies with WITH CHECK on all 21 cleaning tables
--   5. Create non-superuser application role (cleanclaw_app)
--   6. Enable pg_trgm extension for future search capabilities
--
-- Idempotent: All statements use IF NOT EXISTS / DROP IF EXISTS
-- ============================================================================

BEGIN;

-- ============================================================================
-- 1. Missing column: metadata JSONB on cleaning_clients
-- ============================================================================

ALTER TABLE cleaning_clients ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}';
COMMENT ON COLUMN cleaning_clients.metadata IS 'Extensible metadata: stripe_customer_id, referral_code, custom fields';

-- ============================================================================
-- 2. Fix cleaning_leads status CHECK to include ''converted''
-- ============================================================================

ALTER TABLE cleaning_leads DROP CONSTRAINT IF EXISTS cleaning_leads_status_check;
ALTER TABLE cleaning_leads ADD CONSTRAINT cleaning_leads_status_check
    CHECK (status IN ('new', 'contacted', 'quoted', 'follow_up', 'won', 'lost', 'disqualified', 'converted'));

-- ============================================================================
-- 3. Production indexes (8 indexes)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_status_date
    ON cleaning_bookings(business_id, status, scheduled_date);

CREATE INDEX IF NOT EXISTS idx_cleaning_invoices_paid
    ON cleaning_invoices(business_id, paid_at) WHERE paid_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cleaning_clients_created
    ON cleaning_clients(business_id, created_at);

CREATE INDEX IF NOT EXISTS idx_cleaning_clients_metadata_stripe
    ON cleaning_clients USING GIN ((metadata->'stripe_customer_id')) WHERE metadata ? 'stripe_customer_id';

CREATE INDEX IF NOT EXISTS idx_cleaning_leads_created_date
    ON cleaning_leads(business_id, (created_at::date));

CREATE INDEX IF NOT EXISTS idx_cleaning_notifications_analytics
    ON cleaning_notifications(business_id, channel, (created_at::date));

CREATE INDEX IF NOT EXISTS idx_cleaning_reviews_booking
    ON cleaning_reviews(booking_id) WHERE booking_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_cleaning_bookings_client_date_status
    ON cleaning_bookings(client_id, scheduled_date, status);

-- ============================================================================
-- 4. RLS WITH CHECK on ALL 21 cleaning tables
-- ============================================================================

-- 4.1 cleaning_services
DROP POLICY IF EXISTS cleaning_services_isolation ON cleaning_services;
CREATE POLICY cleaning_services_isolation ON cleaning_services
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.2 cleaning_clients
DROP POLICY IF EXISTS cleaning_clients_isolation ON cleaning_clients;
CREATE POLICY cleaning_clients_isolation ON cleaning_clients
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.3 cleaning_team_members
DROP POLICY IF EXISTS cleaning_team_members_isolation ON cleaning_team_members;
CREATE POLICY cleaning_team_members_isolation ON cleaning_team_members
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.4 cleaning_team_availability
DROP POLICY IF EXISTS cleaning_team_availability_isolation ON cleaning_team_availability;
CREATE POLICY cleaning_team_availability_isolation ON cleaning_team_availability
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.5 cleaning_recurring_schedules
DROP POLICY IF EXISTS cleaning_recurring_schedules_isolation ON cleaning_recurring_schedules;
CREATE POLICY cleaning_recurring_schedules_isolation ON cleaning_recurring_schedules
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.6 cleaning_bookings
DROP POLICY IF EXISTS cleaning_bookings_isolation ON cleaning_bookings;
CREATE POLICY cleaning_bookings_isolation ON cleaning_bookings
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.7 cleaning_checklists
DROP POLICY IF EXISTS cleaning_checklists_isolation ON cleaning_checklists;
CREATE POLICY cleaning_checklists_isolation ON cleaning_checklists
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.8 cleaning_checklist_items
DROP POLICY IF EXISTS cleaning_checklist_items_isolation ON cleaning_checklist_items;
CREATE POLICY cleaning_checklist_items_isolation ON cleaning_checklist_items
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.9 cleaning_job_logs
DROP POLICY IF EXISTS cleaning_job_logs_isolation ON cleaning_job_logs;
CREATE POLICY cleaning_job_logs_isolation ON cleaning_job_logs
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.10 cleaning_invoices
DROP POLICY IF EXISTS cleaning_invoices_isolation ON cleaning_invoices;
CREATE POLICY cleaning_invoices_isolation ON cleaning_invoices
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.11 cleaning_invoice_items
DROP POLICY IF EXISTS cleaning_invoice_items_isolation ON cleaning_invoice_items;
CREATE POLICY cleaning_invoice_items_isolation ON cleaning_invoice_items
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.12 cleaning_reviews
DROP POLICY IF EXISTS cleaning_reviews_isolation ON cleaning_reviews;
CREATE POLICY cleaning_reviews_isolation ON cleaning_reviews
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.13 cleaning_leads
DROP POLICY IF EXISTS cleaning_leads_isolation ON cleaning_leads;
CREATE POLICY cleaning_leads_isolation ON cleaning_leads
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.14 cleaning_areas
DROP POLICY IF EXISTS cleaning_areas_isolation ON cleaning_areas;
CREATE POLICY cleaning_areas_isolation ON cleaning_areas
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.15 cleaning_pricing_rules
DROP POLICY IF EXISTS cleaning_pricing_rules_isolation ON cleaning_pricing_rules;
CREATE POLICY cleaning_pricing_rules_isolation ON cleaning_pricing_rules
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.16 cleaning_notifications
DROP POLICY IF EXISTS cleaning_notifications_isolation ON cleaning_notifications;
CREATE POLICY cleaning_notifications_isolation ON cleaning_notifications
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.17 cleaning_daily_analytics
DROP POLICY IF EXISTS cleaning_daily_analytics_isolation ON cleaning_daily_analytics;
CREATE POLICY cleaning_daily_analytics_isolation ON cleaning_daily_analytics
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.18 cleaning_teams
DROP POLICY IF EXISTS cleaning_teams_isolation ON cleaning_teams;
CREATE POLICY cleaning_teams_isolation ON cleaning_teams
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.19 cleaning_team_assignments (no direct business_id — joins via cleaning_teams)
DROP POLICY IF EXISTS cleaning_team_assignments_isolation ON cleaning_team_assignments;
CREATE POLICY cleaning_team_assignments_isolation ON cleaning_team_assignments
    USING (team_id IN (SELECT id FROM cleaning_teams WHERE business_id::text = current_setting('app.current_business_id', true)))
    WITH CHECK (team_id IN (SELECT id FROM cleaning_teams WHERE business_id::text = current_setting('app.current_business_id', true)));

-- 4.20 cleaning_client_schedules
DROP POLICY IF EXISTS cleaning_client_schedules_isolation ON cleaning_client_schedules;
CREATE POLICY cleaning_client_schedules_isolation ON cleaning_client_schedules
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- 4.21 cleaning_user_roles
DROP POLICY IF EXISTS cleaning_user_roles_isolation ON cleaning_user_roles;
CREATE POLICY cleaning_user_roles_isolation ON cleaning_user_roles
    USING (business_id::text = current_setting('app.current_business_id', true))
    WITH CHECK (business_id::text = current_setting('app.current_business_id', true));

-- ============================================================================
-- 5. Non-superuser application role
-- ============================================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cleanclaw_app') THEN
        CREATE ROLE cleanclaw_app LOGIN NOSUPERUSER;
    END IF;
END $$;

GRANT USAGE ON SCHEMA public TO cleanclaw_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cleanclaw_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO cleanclaw_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cleanclaw_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE ON SEQUENCES TO cleanclaw_app;

-- ============================================================================
-- 6. pg_trgm extension for future search
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

COMMIT;
