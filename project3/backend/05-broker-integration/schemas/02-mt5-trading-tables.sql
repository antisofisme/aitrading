-- ============================================================================
-- MT5 EA Integration - Trading & Signal Management Tables
-- ============================================================================
-- Handles trade orders, signal generation, execution tracking, and feedback loops
-- Connects ML predictions → Trading signals → EA execution → Results
--
-- CRITICAL: This schema enables the complete trading loop:
-- 1. ML generates predictions (on Polygon data)
-- 2. Backend creates trading signals (adjusted for broker quotes)
-- 3. EA executes trades (on user's broker)
-- 4. Results feed back to ML for model improvement
-- ============================================================================

\c suho_trading;

-- ============================================================================
-- 6. TRADE ORDERS (TIME-SERIES)
-- ============================================================================
-- Master table for ALL trade orders: pending, open, closed
-- Tracks complete trade lifecycle from signal → execution → close
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_trade_orders (
    -- Primary identifiers
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket BIGINT UNIQUE,                          -- MT5 ticket number (assigned after execution)

    -- Account & Time
    account_id UUID NOT NULL REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Order details
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(20) NOT NULL,               -- 'BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP'
    volume DECIMAL(10,2) NOT NULL,                 -- Lot size

    -- Price levels
    requested_price DECIMAL(10,5),                 -- Price when signal generated
    open_price DECIMAL(10,5),                      -- Actual execution price
    close_price DECIMAL(10,5),                     -- Close price (if closed)
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),

    -- Execution details
    open_time TIMESTAMPTZ,
    close_time TIMESTAMPTZ,
    expiration_time TIMESTAMPTZ,

    -- Financial results
    commission DECIMAL(10,2) DEFAULT 0,
    swap DECIMAL(10,2) DEFAULT 0,
    profit DECIMAL(15,2),                          -- Realized profit (when closed)
    profit_pips DECIMAL(8,2),                      -- Profit in pips

    -- Status tracking
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'open', 'closed', 'cancelled', 'rejected', 'expired'
    close_reason VARCHAR(50),                      -- 'take_profit', 'stop_loss', 'manual', 'margin_call', 'signal'

    -- Source & Attribution
    signal_id UUID,                                -- Links to trading_signals table
    strategy_name VARCHAR(100),                    -- Strategy that generated this trade
    magic_number INTEGER,                          -- MT5 magic number for EA identification

    -- Execution tracking
    slippage_pips DECIMAL(6,2),                    -- Execution slippage
    execution_latency_ms INTEGER,                  -- Time from signal → execution
    broker_error_code INTEGER,
    broker_error_message TEXT,

    -- Risk metrics
    risk_reward_ratio DECIMAL(6,2),
    position_size_percent DECIMAL(6,4),            -- Position size as % of balance
    drawdown_at_open DECIMAL(15,2),                -- Account drawdown when opened

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CHECK (volume > 0),
    CHECK (status IN ('pending', 'open', 'closed', 'cancelled', 'rejected', 'expired')),
    CHECK (order_type IN ('BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP'))
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'mt5_trade_orders',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add tenant partitioning
SELECT add_dimension(
    'mt5_trade_orders',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- Indexes for performance
CREATE INDEX idx_trade_orders_account_time ON mt5_trade_orders(account_id, time DESC);
CREATE INDEX idx_trade_orders_ticket ON mt5_trade_orders(ticket) WHERE ticket IS NOT NULL;
CREATE INDEX idx_trade_orders_signal ON mt5_trade_orders(signal_id) WHERE signal_id IS NOT NULL;
CREATE INDEX idx_trade_orders_status ON mt5_trade_orders(status, time DESC);
CREATE INDEX idx_trade_orders_symbol_time ON mt5_trade_orders(tenant_id, symbol, time DESC);
CREATE INDEX idx_trade_orders_open_trades ON mt5_trade_orders(account_id, status, time DESC)
    WHERE status = 'open';

-- Continuous aggregate for daily trade statistics
CREATE MATERIALIZED VIEW mt5_trade_stats_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    account_id,
    tenant_id,
    symbol,
    COUNT(*) AS total_trades,
    COUNT(*) FILTER (WHERE status = 'closed') AS closed_trades,
    COUNT(*) FILTER (WHERE profit > 0) AS winning_trades,
    COUNT(*) FILTER (WHERE profit < 0) AS losing_trades,
    SUM(profit) FILTER (WHERE status = 'closed') AS total_profit,
    AVG(profit) FILTER (WHERE status = 'closed') AS avg_profit,
    SUM(volume) AS total_volume,
    AVG(slippage_pips) AS avg_slippage,
    AVG(execution_latency_ms) AS avg_execution_latency
FROM mt5_trade_orders
GROUP BY day, account_id, tenant_id, symbol;

-- Refresh policy
SELECT add_continuous_aggregate_policy('mt5_trade_stats_daily',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Row-Level Security
ALTER TABLE mt5_trade_orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_trade_orders ON mt5_trade_orders
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_trade_orders IS 'Complete trade order lifecycle: pending → open → closed';
COMMENT ON COLUMN mt5_trade_orders.signal_id IS 'Links to trading_signals table for ML feedback loop';
COMMENT ON COLUMN mt5_trade_orders.slippage_pips IS 'Difference between requested and executed price';


-- ============================================================================
-- 7. TRADING SIGNALS (TIME-SERIES)
-- ============================================================================
-- ML-generated trading signals sent to users
-- IMPORTANT: Signals are generated on Polygon data, but execution uses broker quotes
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_trading_signals (
    -- Primary identifiers
    signal_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Target account (NULL = broadcast to all accounts)
    account_id UUID REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),                           -- NULL = broadcast signal

    -- Signal details
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL,                   -- 'BUY', 'SELL', 'CLOSE'
    signal_type VARCHAR(20) NOT NULL,              -- 'entry', 'exit', 'modify', 'close_all'

    -- Price levels (from ML model)
    entry_price DECIMAL(10,5),
    stop_loss DECIMAL(10,5),
    take_profit DECIMAL(10,5),

    -- Alternate price levels (for broker quote adjustments)
    entry_price_range_min DECIMAL(10,5),           -- Allow execution within range
    entry_price_range_max DECIMAL(10,5),

    -- Position sizing
    recommended_volume DECIMAL(10,2),
    max_risk_percent DECIMAL(6,4),                 -- Max risk as % of balance
    position_size_method VARCHAR(50),              -- 'fixed', 'risk_based', 'kelly_criterion'

    -- ML Model information
    model_version VARCHAR(50) NOT NULL,
    strategy_name VARCHAR(100) NOT NULL,
    confidence_score DECIMAL(5,4),                 -- 0-1 confidence
    feature_importance JSONB,                      -- Key features that triggered signal

    -- Market context (from Polygon data)
    polygon_bid DECIMAL(10,5),
    polygon_ask DECIMAL(10,5),
    polygon_timestamp TIMESTAMPTZ,
    market_condition VARCHAR(50),                  -- 'trending', 'ranging', 'volatile', 'calm'

    -- Validity
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,                       -- Signal expires after this time
    is_valid BOOLEAN DEFAULT true,

    -- Execution tracking
    status VARCHAR(20) DEFAULT 'pending',          -- 'pending', 'sent', 'executed', 'rejected', 'expired', 'cancelled'
    sent_to_ea_at TIMESTAMPTZ,
    executed_order_id UUID,                        -- Links to mt5_trade_orders

    -- Performance tracking
    execution_success BOOLEAN,
    rejection_reason TEXT,

    -- Risk management
    max_simultaneous_trades INTEGER DEFAULT 1,
    requires_confirmation BOOLEAN DEFAULT false,
    priority INTEGER DEFAULT 5,                    -- 1-10, higher = more important

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CHECK (action IN ('BUY', 'SELL', 'CLOSE', 'CLOSE_ALL')),
    CHECK (signal_type IN ('entry', 'exit', 'modify', 'close_all')),
    CHECK (confidence_score BETWEEN 0 AND 1),
    CHECK (status IN ('pending', 'sent', 'executed', 'rejected', 'expired', 'cancelled'))
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'mt5_trading_signals',
    'time',
    chunk_time_interval => INTERVAL '6 hours',
    if_not_exists => TRUE
);

-- Add tenant partitioning
SELECT add_dimension(
    'mt5_trading_signals',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_signals_account_time ON mt5_trading_signals(account_id, time DESC)
    WHERE account_id IS NOT NULL;
CREATE INDEX idx_signals_status_time ON mt5_trading_signals(status, time DESC);
CREATE INDEX idx_signals_pending ON mt5_trading_signals(time DESC)
    WHERE status = 'pending' AND is_valid = true;
CREATE INDEX idx_signals_executed_order ON mt5_trading_signals(executed_order_id)
    WHERE executed_order_id IS NOT NULL;
CREATE INDEX idx_signals_model_version ON mt5_trading_signals(model_version, time DESC);
CREATE INDEX idx_signals_strategy ON mt5_trading_signals(strategy_name, time DESC);

-- Retention policy (keep signals for 90 days)
SELECT add_retention_policy('mt5_trading_signals',
    INTERVAL '90 days',
    if_not_exists => TRUE
);

-- Row-Level Security
ALTER TABLE mt5_trading_signals ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_signals ON mt5_trading_signals
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_trading_signals IS 'ML-generated trading signals sent to MT5 EA';
COMMENT ON COLUMN mt5_trading_signals.polygon_bid IS 'Market price from Polygon (may differ from broker)';
COMMENT ON COLUMN mt5_trading_signals.entry_price_range_min IS 'Allow execution within price range to handle broker differences';


-- ============================================================================
-- 8. SIGNAL EXECUTION TRACKING (FEEDBACK LOOP)
-- ============================================================================
-- Tracks signal → execution → result flow for ML model improvement
-- CRITICAL: This is the feedback loop for continuous model refinement
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_signal_executions (
    -- Primary identifiers
    execution_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Links
    signal_id UUID NOT NULL REFERENCES mt5_trading_signals(signal_id) ON DELETE CASCADE,
    order_id UUID REFERENCES mt5_trade_orders(order_id) ON DELETE SET NULL,
    account_id UUID NOT NULL REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,

    -- Execution details
    executed BOOLEAN NOT NULL,
    execution_time TIMESTAMPTZ,
    execution_latency_ms INTEGER,                  -- Signal generation → execution

    -- Price comparison (ML prediction vs actual)
    signal_entry_price DECIMAL(10,5),              -- Predicted entry price
    actual_entry_price DECIMAL(10,5),              -- Actual execution price
    price_difference DECIMAL(8,5),                 -- Slippage/deviation

    broker_quote_at_signal DECIMAL(10,5),          -- Broker quote when signal generated
    broker_quote_at_execution DECIMAL(10,5),       -- Broker quote when executed

    -- Result tracking (for closed trades)
    trade_closed BOOLEAN DEFAULT false,
    close_time TIMESTAMPTZ,
    profit DECIMAL(15,2),
    profit_pips DECIMAL(8,2),

    -- Performance metrics
    signal_quality_score DECIMAL(5,4),             -- Post-execution quality assessment
    execution_success_rate DECIMAL(5,4),           -- Historical success rate of this strategy

    -- Rejection tracking
    rejected BOOLEAN DEFAULT false,
    rejection_reason VARCHAR(255),
    rejection_category VARCHAR(50),                -- 'risk_limit', 'price_deviation', 'market_condition', 'ea_error'

    -- Market conditions (at execution time)
    market_volatility DECIMAL(8,4),
    spread_at_execution DECIMAL(6,2),
    liquidity_score DECIMAL(5,4),

    -- Feedback for ML
    feedback_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processed', 'included_in_training'
    feedback_processed_at TIMESTAMPTZ,
    model_update_batch_id UUID,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CHECK (feedback_status IN ('pending', 'processed', 'included_in_training'))
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'mt5_signal_executions',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_signal_exec_signal_id ON mt5_signal_executions(signal_id, time DESC);
CREATE INDEX idx_signal_exec_order_id ON mt5_signal_executions(order_id) WHERE order_id IS NOT NULL;
CREATE INDEX idx_signal_exec_feedback ON mt5_signal_executions(feedback_status, time DESC)
    WHERE feedback_status = 'pending';
CREATE INDEX idx_signal_exec_account ON mt5_signal_executions(account_id, time DESC);

-- Row-Level Security
ALTER TABLE mt5_signal_executions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_signal_exec ON mt5_signal_executions
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_signal_executions IS 'Feedback loop: signal → execution → result for ML model improvement';
COMMENT ON COLUMN mt5_signal_executions.price_difference IS 'Signal price vs actual execution price (slippage)';
COMMENT ON COLUMN mt5_signal_executions.feedback_status IS 'Tracks if result has been fed back to ML training pipeline';


-- ============================================================================
-- 9. POSITION MANAGEMENT (REAL-TIME VIEW)
-- ============================================================================
-- Real-time view of all open positions per account
-- ============================================================================

CREATE OR REPLACE VIEW mt5_open_positions AS
SELECT
    o.order_id,
    o.ticket,
    o.account_id,
    o.tenant_id,
    o.user_id,
    o.symbol,
    o.order_type,
    o.volume,
    o.open_price,
    o.stop_loss,
    o.take_profit,
    o.open_time,
    o.profit,
    o.profit_pips,
    o.signal_id,
    o.strategy_name,

    -- Calculate current P&L (requires current market price from broker quotes)
    CASE
        WHEN o.order_type = 'BUY' THEN
            (SELECT LAST(q.bid, q.time)
             FROM mt5_broker_quotes q
             WHERE q.account_id = o.account_id
               AND q.symbol = o.symbol
               AND q.time >= NOW() - INTERVAL '5 minutes'
            ) - o.open_price
        WHEN o.order_type = 'SELL' THEN
            o.open_price - (SELECT LAST(q.ask, q.time)
             FROM mt5_broker_quotes q
             WHERE q.account_id = o.account_id
               AND q.symbol = o.symbol
               AND q.time >= NOW() - INTERVAL '5 minutes'
            )
    END AS current_pips,

    -- Risk metrics
    CASE
        WHEN o.stop_loss IS NOT NULL THEN
            ABS(o.open_price - o.stop_loss) * o.volume * 100000
    END AS risk_amount,

    -- Duration
    EXTRACT(EPOCH FROM (NOW() - o.open_time))/3600 AS hours_open,

    o.metadata
FROM mt5_trade_orders o
WHERE o.status = 'open'
ORDER BY o.open_time DESC;

-- Comments
COMMENT ON VIEW mt5_open_positions IS 'Real-time view of all open positions with current P&L';


-- ============================================================================
-- 10. HELPER FUNCTIONS
-- ============================================================================

-- Function: Create signal execution record when order is filled
CREATE OR REPLACE FUNCTION track_signal_execution()
RETURNS TRIGGER AS $$
BEGIN
    -- Only track if order has a signal_id and is newly opened
    IF NEW.signal_id IS NOT NULL AND NEW.status = 'open' AND OLD.status = 'pending' THEN
        INSERT INTO mt5_signal_executions (
            signal_id,
            order_id,
            account_id,
            tenant_id,
            time,
            executed,
            execution_time,
            actual_entry_price,
            executed
        ) VALUES (
            NEW.signal_id,
            NEW.order_id,
            NEW.account_id,
            NEW.tenant_id,
            NOW(),
            true,
            NOW(),
            NEW.open_price,
            true
        );

        -- Update signal status
        UPDATE mt5_trading_signals
        SET status = 'executed',
            executed_order_id = NEW.order_id,
            updated_at = NOW()
        WHERE signal_id = NEW.signal_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-track signal executions
CREATE TRIGGER trigger_track_signal_execution
    AFTER UPDATE ON mt5_trade_orders
    FOR EACH ROW
    EXECUTE FUNCTION track_signal_execution();

-- Function: Mark signal execution as closed when trade closes
CREATE OR REPLACE FUNCTION update_signal_execution_result()
RETURNS TRIGGER AS $$
BEGIN
    -- Update execution record when trade closes
    IF NEW.status = 'closed' AND OLD.status = 'open' THEN
        UPDATE mt5_signal_executions
        SET
            trade_closed = true,
            close_time = NEW.close_time,
            profit = NEW.profit,
            profit_pips = NEW.profit_pips,
            feedback_status = 'pending',
            metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{close_reason}',
                to_jsonb(NEW.close_reason)
            )
        WHERE order_id = NEW.order_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Auto-update execution results
CREATE TRIGGER trigger_update_signal_execution_result
    AFTER UPDATE ON mt5_trade_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_signal_execution_result();

-- Comments
COMMENT ON FUNCTION track_signal_execution() IS 'Auto-creates execution tracking record when signal is executed';
COMMENT ON FUNCTION update_signal_execution_result() IS 'Auto-updates execution record when trade closes';


-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_trade_orders TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_trading_signals TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_signal_executions TO suho_service;
GRANT SELECT ON mt5_open_positions TO suho_service;

GRANT SELECT ON mt5_trade_orders TO suho_readonly;
GRANT SELECT ON mt5_trading_signals TO suho_readonly;
GRANT SELECT ON mt5_signal_executions TO suho_readonly;
GRANT SELECT ON mt5_open_positions TO suho_readonly;

COMMIT;
