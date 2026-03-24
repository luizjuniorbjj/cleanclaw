-- Migration 018: Extend cleaning_clients status CHECK to include 'paused' and 'former'
--
-- Problem: Pydantic model and service layer use 'paused' and 'former' statuses,
-- but the DB CHECK constraint only allows 'active', 'inactive', 'blocked'.
-- The service had a lossy mapping (paused->inactive, former->inactive) which
-- prevented distinguishing paused from truly inactive clients.
--
-- Fix: Extend the CHECK constraint to match the application model.

ALTER TABLE cleaning_clients
    DROP CONSTRAINT IF EXISTS cleaning_clients_status_check;

ALTER TABLE cleaning_clients
    ADD CONSTRAINT cleaning_clients_status_check
    CHECK (status IN ('active', 'inactive', 'blocked', 'paused', 'former'));
