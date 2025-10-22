-- Migration 001: Initial agent registry schema
-- Description: Creates base tables for agent metadata, dependencies, and usage tracking
-- Requires: PostgreSQL 15+, pgvector extension
-- Applied: 2025-10-21

-- This migration is identical to schema.sql for the initial setup
-- Future migrations will be incremental changes only

\i ../schema.sql
