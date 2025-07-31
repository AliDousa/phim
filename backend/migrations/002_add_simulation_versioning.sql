-- Migration: Add optimistic locking to simulations table
-- Date: 2025-01-31
-- Description: Add version column for optimistic locking to prevent race conditions

-- Add version column for optimistic locking
ALTER TABLE simulations ADD COLUMN version INTEGER NOT NULL DEFAULT 1;

-- Create index on version for performance
CREATE INDEX idx_simulations_version ON simulations(version);

-- Update constraint to include new status values if needed
ALTER TABLE simulations DROP CONSTRAINT IF EXISTS ck_valid_status;
ALTER TABLE simulations ADD CONSTRAINT ck_valid_status 
    CHECK (status IN ('pending', 'queued', 'running', 'completed', 'failed', 'cancelled'));

-- Add comment to document the version column purpose
COMMENT ON COLUMN simulations.version IS 'Version number for optimistic locking to prevent race conditions during concurrent updates';