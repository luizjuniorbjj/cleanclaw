-- ============================================
-- MIGRATION 013: Add cleaning_settings JSONB column to businesses table
-- ClaWtoBusiness Ecosystem
-- ============================================
-- Stores cleaning-specific business settings (business hours,
-- cancellation policy, notification preferences, etc.) as JSONB.
-- The application merges these with defaults at runtime.

ALTER TABLE businesses ADD COLUMN IF NOT EXISTS cleaning_settings JSONB DEFAULT '{}';

COMMENT ON COLUMN businesses.cleaning_settings IS 'CleanClaw business settings: hours, cancellation policy, notifications, schedule preferences';
