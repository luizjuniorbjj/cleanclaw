-- ============================================
-- MIGRATION 014: Fix cleaning_bookings FK constraint
-- ============================================
-- The recurring_schedule_id column was referencing cleaning_recurring_schedules (v1)
-- but client schedules are stored in cleaning_client_schedules (v3).
-- This migration fixes the FK to point to the correct table.
-- Safe to run multiple times (IF EXISTS).
-- ============================================

ALTER TABLE cleaning_bookings DROP CONSTRAINT IF EXISTS cleaning_bookings_recurring_schedule_id_fkey;
ALTER TABLE cleaning_bookings DROP CONSTRAINT IF EXISTS cleaning_bookings_client_schedule_id_fkey;

ALTER TABLE cleaning_bookings
    ADD CONSTRAINT cleaning_bookings_client_schedule_id_fkey
    FOREIGN KEY (recurring_schedule_id) REFERENCES cleaning_client_schedules(id) ON DELETE SET NULL;
