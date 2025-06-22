-- Migration: 001_initial_schema: Initial database schema
-- Created: 2024-01-01T00:00:00Z
-- Description: Create initial database schema for PHIP Backend

-- This migration will be automatically applied when the application starts
-- The actual table creation is handled by SQLAlchemy in the application code

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database schema version tracking
-- This table is created by the migration system itself

-- Application tables are created by SQLAlchemy models
-- See src/models/database.py for the complete schema definition
