-- Migration: Create NATS Message Queue for Circuit Breaker Fallback
-- Purpose: Store failed NATS messages during circuit OPEN state
-- Service: Tick Aggregator
-- Date: 2025-10-12

-- Create table for queuing failed NATS messages
CREATE TABLE IF NOT EXISTS nats_message_queue (
    id SERIAL PRIMARY KEY,
    correlation_id TEXT UNIQUE NOT NULL,
    message_data JSONB NOT NULL,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 5,
    next_retry_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_nats_queue_status ON nats_message_queue(status);
CREATE INDEX IF NOT EXISTS idx_nats_queue_next_retry ON nats_message_queue(next_retry_at) WHERE status = 'pending';
CREATE INDEX IF NOT EXISTS idx_nats_queue_correlation ON nats_message_queue(correlation_id);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_nats_queue_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS nats_queue_updated_at_trigger ON nats_message_queue;
CREATE TRIGGER nats_queue_updated_at_trigger
    BEFORE UPDATE ON nats_message_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_nats_queue_updated_at();

COMMENT ON TABLE nats_message_queue IS 'Fallback queue for NATS messages when circuit breaker is OPEN';

SELECT 'Migration 003: NATS Message Queue created successfully' AS status;
