-- Migration: Create Dead Letter Queue for Data Bridge
-- Purpose: Store failed ClickHouse writes after retry exhaustion
-- Service: Data Bridge
-- Date: 2025-10-12

-- Create Dead Letter Queue table
CREATE TABLE IF NOT EXISTS data_bridge_dlq (
    id BIGSERIAL PRIMARY KEY,
    correlation_id VARCHAR(255) UNIQUE,
    message_type VARCHAR(50) NOT NULL,
    message_data JSONB NOT NULL,
    retry_count INTEGER NOT NULL,
    first_attempt_time TIMESTAMP NOT NULL,
    last_error TEXT,
    priority INTEGER DEFAULT 2,
    replayed BOOLEAN DEFAULT FALSE,
    replayed_at TIMESTAMP,
    replay_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_dlq_correlation_id ON data_bridge_dlq(correlation_id);
CREATE INDEX IF NOT EXISTS idx_dlq_message_type ON data_bridge_dlq(message_type);
CREATE INDEX IF NOT EXISTS idx_dlq_created_at ON data_bridge_dlq(created_at);
CREATE INDEX IF NOT EXISTS idx_dlq_priority ON data_bridge_dlq(priority);
CREATE INDEX IF NOT EXISTS idx_dlq_replayed ON data_bridge_dlq(replayed);
CREATE INDEX IF NOT EXISTS idx_dlq_message_data_gin ON data_bridge_dlq USING gin(message_data);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_dlq_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS dlq_updated_at_trigger ON data_bridge_dlq;
CREATE TRIGGER dlq_updated_at_trigger
    BEFORE UPDATE ON data_bridge_dlq
    FOR EACH ROW
    EXECUTE FUNCTION update_dlq_updated_at();

-- Add comments
COMMENT ON TABLE data_bridge_dlq IS 'Dead Letter Queue for messages that failed after max retries';
COMMENT ON COLUMN data_bridge_dlq.message_type IS 'Type: tick, aggregate, or external';
COMMENT ON COLUMN data_bridge_dlq.message_data IS 'Full message payload in JSONB (queryable)';
COMMENT ON COLUMN data_bridge_dlq.priority IS '1=HIGH (live), 2=MEDIUM (gap-fill), 3=LOW (historical)';
COMMENT ON COLUMN data_bridge_dlq.replayed IS 'TRUE if manually replayed successfully';

SELECT 'Migration 001: Data Bridge DLQ created successfully' AS status;
