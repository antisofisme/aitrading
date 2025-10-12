-- Migration: Create message queue table for NATS fallback
-- Purpose: Store failed NATS messages when circuit breaker is OPEN
-- Retry Strategy: Background job retries from this queue when NATS recovers

CREATE TABLE IF NOT EXISTS nats_message_queue (
    id BIGSERIAL PRIMARY KEY,

    -- Message content
    subject VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,

    -- Metadata
    symbol VARCHAR(20),
    timeframe VARCHAR(10),
    event_type VARCHAR(50) DEFAULT 'ohlcv',

    -- Tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    failed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    retry_count INT NOT NULL DEFAULT 0,
    max_retries INT NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending: waiting to retry
    -- processing: currently being retried
    -- success: successfully published
    -- failed: exceeded max retries

    error_message TEXT,
    published_at TIMESTAMPTZ,

    -- Partitioning hint
    tenant_id VARCHAR(50) DEFAULT 'system'
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_nats_queue_status_retry
    ON nats_message_queue(status, next_retry_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_nats_queue_symbol_timeframe
    ON nats_message_queue(symbol, timeframe, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_nats_queue_created_at
    ON nats_message_queue(created_at DESC);

-- Cleanup old messages (keep for 7 days)
CREATE INDEX IF NOT EXISTS idx_nats_queue_cleanup
    ON nats_message_queue(created_at)
    WHERE status IN ('success', 'failed');

-- Comments
COMMENT ON TABLE nats_message_queue IS
    'Fallback queue for NATS messages when circuit breaker is OPEN';

COMMENT ON COLUMN nats_message_queue.subject IS
    'NATS subject pattern (e.g., bars.EURUSD.5m)';

COMMENT ON COLUMN nats_message_queue.payload IS
    'OHLCV message payload as JSON';

COMMENT ON COLUMN nats_message_queue.retry_count IS
    'Number of retry attempts made';

COMMENT ON COLUMN nats_message_queue.next_retry_at IS
    'Next retry timestamp (exponential backoff)';

COMMENT ON COLUMN nats_message_queue.status IS
    'Message status: pending, processing, success, failed';
