-- Dead Letter Queue (DLQ) table for Data Bridge
-- Stores failed messages after max retry attempts exceeded
--
-- Usage:
--   psql -U postgres -d suho_analytics -f 001_create_dlq_table.sql
--
-- Purpose:
--   - NO DATA LOSS: Messages that fail ClickHouse writes are persisted here
--   - Manual review: Operations team can investigate and replay failed messages
--   - Audit trail: Track failure patterns and error types

CREATE TABLE IF NOT EXISTS data_bridge_dlq (
    -- Primary key
    id BIGSERIAL PRIMARY KEY,

    -- Message identification
    correlation_id VARCHAR(255) UNIQUE NOT NULL,
    message_type VARCHAR(50) NOT NULL,  -- 'tick', 'aggregate', 'external'

    -- Message content (JSONB for queryability)
    message_data JSONB NOT NULL,

    -- Retry tracking
    retry_count INTEGER NOT NULL DEFAULT 0,
    first_attempt_time TIMESTAMP WITH TIME ZONE NOT NULL,
    last_error TEXT,

    -- Priority (for manual replay ordering)
    priority INTEGER NOT NULL,  -- 1=HIGH, 2=MEDIUM, 3=LOW

    -- Replay tracking
    replayed BOOLEAN DEFAULT FALSE,
    replayed_at TIMESTAMP WITH TIME ZONE,
    replay_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_dlq_correlation_id ON data_bridge_dlq(correlation_id);
CREATE INDEX IF NOT EXISTS idx_dlq_message_type ON data_bridge_dlq(message_type);
CREATE INDEX IF NOT EXISTS idx_dlq_created_at ON data_bridge_dlq(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_dlq_priority ON data_bridge_dlq(priority, created_at);
CREATE INDEX IF NOT EXISTS idx_dlq_replayed ON data_bridge_dlq(replayed) WHERE replayed = FALSE;

-- JSONB index for querying message content (e.g., find all EUR/USD failures)
CREATE INDEX IF NOT EXISTS idx_dlq_message_data_gin ON data_bridge_dlq USING GIN (message_data);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_data_bridge_dlq_updated_at
    BEFORE UPDATE ON data_bridge_dlq
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comment for documentation
COMMENT ON TABLE data_bridge_dlq IS 'Dead Letter Queue for failed ClickHouse writes - ensures no data loss';
COMMENT ON COLUMN data_bridge_dlq.correlation_id IS 'Unique message ID for tracking';
COMMENT ON COLUMN data_bridge_dlq.message_data IS 'Full message payload as JSONB for queryability';
COMMENT ON COLUMN data_bridge_dlq.retry_count IS 'Number of retry attempts before giving up (max 6)';
COMMENT ON COLUMN data_bridge_dlq.priority IS '1=HIGH (live), 2=MEDIUM (gap-fill), 3=LOW (historical)';
COMMENT ON COLUMN data_bridge_dlq.replayed IS 'TRUE if message was manually replayed to ClickHouse';

-- Example queries for operations team:

-- View recent failures
-- SELECT correlation_id, message_type, retry_count, last_error, created_at
-- FROM data_bridge_dlq
-- WHERE replayed = FALSE
-- ORDER BY priority ASC, created_at DESC
-- LIMIT 50;

-- Count failures by type
-- SELECT message_type, COUNT(*) as failure_count
-- FROM data_bridge_dlq
-- WHERE replayed = FALSE
-- GROUP BY message_type
-- ORDER BY failure_count DESC;

-- Find all EUR/USD failures
-- SELECT id, correlation_id, message_data->>'symbol' as symbol, last_error, created_at
-- FROM data_bridge_dlq
-- WHERE message_data->>'symbol' = 'EUR/USD'
-- AND replayed = FALSE
-- ORDER BY created_at DESC;

-- Mark messages as replayed
-- UPDATE data_bridge_dlq
-- SET replayed = TRUE, replayed_at = NOW(), replay_notes = 'Manually replayed after ClickHouse recovery'
-- WHERE id IN (...);
