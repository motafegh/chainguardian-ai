-- Add semantic security feature columns to features table
-- Run this after creating the initial schema

ALTER TABLE features
ADD COLUMN IF NOT EXISTS cei_violations INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cei_safe_functions INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS cei_pattern_score REAL DEFAULT 1.0,
ADD COLUMN IF NOT EXISTS has_reentrancy_guard BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS functions_with_reentrancy_guard INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS state_before_call_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS state_after_call_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS unchecked_calls_in_critical_context INTEGER DEFAULT 0;

-- Update stats query to include semantic features
COMMENT ON COLUMN features.cei_violations IS 'Count of CEI pattern violations (state after external call)';
COMMENT ON COLUMN features.cei_pattern_score IS 'CEI compliance score (0-1, 1 = perfect)';
COMMENT ON COLUMN features.has_reentrancy_guard IS 'Has reentrancy protection (mutex/guard)';
