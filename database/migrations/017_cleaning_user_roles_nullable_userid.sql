-- Migration 017: Allow NULL user_id in cleaning_user_roles for pending invites
--
-- Problem: The invite flow creates a role record before the user registers/accepts.
-- The user_id is set to NULL during invite creation and filled in on acceptance.
-- But user_id was NOT NULL, causing INSERT failures for pending invites.
--
-- Fix: Make user_id nullable. The UNIQUE constraint on (user_id, business_id, role)
-- still works — NULL values are distinct in PostgreSQL unique constraints.
-- Also drop the FK ON DELETE CASCADE since NULL user_id has no FK to follow.

ALTER TABLE cleaning_user_roles
    ALTER COLUMN user_id DROP NOT NULL;
