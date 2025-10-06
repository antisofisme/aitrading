-- =======================================================================
-- TIMESCALEDB REAL-TIME PREDICTIONS SCHEMA
-- =======================================================================
-- Stores real-time ML predictions with pattern matching results
-- Optimized for high-frequency writes and time-series queries
-- =======================================================================

\c suho_trading;

SET search_path TO public, ml_registry;

-- =======================================================================
-- TABLE 1: REAL-TIME PREDICTIONS
-- =======================================================================
-- Stores all predictions made by deployed models

CREATE TABLE IF NOT EXISTS ml_predictions (
    -- Time and identity
    time TIMESTAMPTZ NOT NULL,
    prediction_id UUID DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Model information
    model_id UUID NOT NULL,                -- Foreign key to ml_registry.models
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20) NOT NULL,

    -- Trading pair
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,

    -- Input features snapshot (for debugging)
    input_features JSONB,                  -- Key features used for this prediction
    -- Example: {"close": 1.0850, "rsi_14": 65.3, "macd_histogram": 0.0012}

    -- Prediction outputs
    prediction_type VARCHAR(50) NOT NULL,  -- 'classification', 'regression', 'probability'

    -- For classification: direction prediction
    predicted_direction INT,               -- 1 (bullish), 0 (neutral), -1 (bearish)
    direction_confidence DECIMAL(5, 4),    -- 0.0 - 1.0

    -- For regression: price/return prediction
    predicted_price DECIMAL(18, 5),
    predicted_return DECIMAL(10, 8),       -- Expected return percentage

    -- Probability distribution (for multi-class)
    probabilities JSONB,
    -- Example: {"bullish": 0.65, "neutral": 0.20, "bearish": 0.15}

    -- Risk estimates
    predicted_max_gain DECIMAL(10, 8),     -- Expected max favorable movement
    predicted_max_loss DECIMAL(10, 8),     -- Expected max adverse movement
    predicted_volatility DECIMAL(10, 8),   -- Expected volatility

    -- Prediction quality indicators
    confidence_score DECIMAL(5, 4) NOT NULL, -- Overall confidence (0-1)
    uncertainty DECIMAL(5, 4),             -- Prediction uncertainty
    model_agreement_score DECIMAL(5, 4),   -- If ensemble, agreement between models

    -- Pattern matching results (from Weaviate)
    similar_pattern_count INT DEFAULT 0,
    top_similar_pattern_id UUID,
    pattern_similarity_score DECIMAL(5, 4), -- Cosine similarity with most similar pattern
    historical_pattern_outcome VARCHAR(20), -- 'profitable', 'loss', 'breakeven'

    -- Trading signal generation
    signal_generated BOOLEAN DEFAULT FALSE,
    signal_type VARCHAR(20),               -- 'buy', 'sell', 'hold'
    signal_strength DECIMAL(5, 4),         -- Signal strength (0-1)
    entry_price DECIMAL(18, 5),
    stop_loss DECIMAL(18, 5),
    take_profit DECIMAL(18, 5),

    -- Execution tracking
    executed BOOLEAN DEFAULT FALSE,
    execution_time TIMESTAMPTZ,
    execution_price DECIMAL(18, 5),

    -- Actual outcome (for feedback loop)
    actual_direction INT,                  -- Actual direction observed
    actual_return DECIMAL(10, 8),          -- Actual return
    actual_max_gain DECIMAL(10, 8),
    actual_max_loss DECIMAL(10, 8),
    outcome_recorded_at TIMESTAMPTZ,

    -- Prediction accuracy (calculated after outcome)
    direction_correct BOOLEAN,
    return_error DECIMAL(10, 8),           -- |predicted - actual|
    absolute_percentage_error DECIMAL(10, 8),

    -- Latency tracking
    inference_latency_ms DECIMAL(10, 2),   -- Time to generate prediction
    total_latency_ms DECIMAL(10, 2),       -- Including feature computation

    -- Metadata
    prediction_context JSONB,              -- Additional context
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable('ml_predictions', 'time', chunk_time_interval => INTERVAL '1 day');

-- Add tenant dimension for partitioning
SELECT add_dimension('ml_predictions', 'tenant_id', number_partitions => 4);

-- Indexes for fast queries
CREATE INDEX idx_ml_predictions_tenant_symbol_time
ON ml_predictions (tenant_id, symbol, time DESC);

CREATE INDEX idx_ml_predictions_model_time
ON ml_predictions (model_id, time DESC);

CREATE INDEX idx_ml_predictions_user_time
ON ml_predictions (tenant_id, user_id, time DESC);

CREATE INDEX idx_ml_predictions_signal
ON ml_predictions (signal_generated, signal_type, time DESC);

CREATE INDEX idx_ml_predictions_executed
ON ml_predictions (executed, execution_time);

-- Partial index for unverified predictions (pending outcome)
CREATE INDEX idx_ml_predictions_pending_outcome
ON ml_predictions (time DESC)
WHERE outcome_recorded_at IS NULL;

-- Row-level security
ALTER TABLE ml_predictions ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_ml_predictions ON ml_predictions
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 2: TRADE RESULTS (FEEDBACK LOOP)
-- =======================================================================
-- Stores actual trade execution results for model improvement

CREATE TABLE IF NOT EXISTS trade_results (
    -- Time and identity
    time TIMESTAMPTZ NOT NULL,
    trade_id UUID DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Link to prediction
    prediction_id UUID,                    -- Can be NULL for manual trades
    model_id UUID,

    -- Trading pair
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,

    -- Trade details
    trade_type VARCHAR(10) NOT NULL,       -- 'buy', 'sell'
    entry_time TIMESTAMPTZ NOT NULL,
    entry_price DECIMAL(18, 5) NOT NULL,
    position_size DECIMAL(18, 8) NOT NULL, -- Lot size or contracts

    exit_time TIMESTAMPTZ,
    exit_price DECIMAL(18, 5),
    exit_reason VARCHAR(50),               -- 'take_profit', 'stop_loss', 'manual', 'timeout'

    -- Risk management
    stop_loss DECIMAL(18, 5),
    take_profit DECIMAL(18, 5),
    risk_reward_ratio DECIMAL(6, 2),

    -- Performance
    pnl_pips DECIMAL(10, 4),
    pnl_percent DECIMAL(10, 6),
    pnl_amount DECIMAL(18, 2),
    pnl_currency VARCHAR(10),

    -- Trade classification
    outcome VARCHAR(20),                   -- 'win', 'loss', 'breakeven'
    trade_duration_seconds INT,

    -- Market conditions at entry
    market_conditions JSONB,
    -- Example: {
    --   "rsi": 65.3,
    --   "atr": 0.0015,
    --   "trend": "bullish",
    --   "volatility": "medium",
    --   "session": "london"
    -- }

    -- Slippage tracking
    expected_entry_price DECIMAL(18, 5),
    slippage_pips DECIMAL(10, 4),
    commission DECIMAL(18, 2),

    -- Execution quality
    execution_quality_score DECIMAL(5, 4), -- How well the trade was executed

    -- Notes
    notes TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('trade_results', 'time', chunk_time_interval => INTERVAL '1 day');

-- Add tenant dimension
SELECT add_dimension('trade_results', 'tenant_id', number_partitions => 4);

-- Indexes
CREATE INDEX idx_trade_results_tenant_symbol_time
ON trade_results (tenant_id, symbol, time DESC);

CREATE INDEX idx_trade_results_prediction
ON trade_results (prediction_id);

CREATE INDEX idx_trade_results_outcome
ON trade_results (outcome, time DESC);

CREATE INDEX idx_trade_results_user_time
ON trade_results (tenant_id, user_id, time DESC);

-- Row-level security
ALTER TABLE trade_results ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_trade_results ON trade_results
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 3: MODEL PERFORMANCE METRICS (Time-Series)
-- =======================================================================
-- Tracks model performance over time for drift detection

CREATE TABLE IF NOT EXISTS model_performance_timeseries (
    time TIMESTAMPTZ NOT NULL,
    tenant_id VARCHAR(50) NOT NULL,
    model_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,

    -- Aggregation window
    window_size INTERVAL NOT NULL,         -- '1 hour', '1 day', '7 days'

    -- Prediction metrics
    total_predictions INT,
    predictions_with_outcome INT,
    avg_confidence DECIMAL(5, 4),

    -- Accuracy metrics
    accuracy DECIMAL(6, 4),                -- Correct direction predictions / total
    precision DECIMAL(6, 4),               -- TP / (TP + FP)
    recall DECIMAL(6, 4),                  -- TP / (TP + FN)
    f1_score DECIMAL(6, 4),

    -- Regression metrics
    mae DECIMAL(10, 8),                    -- Mean Absolute Error
    rmse DECIMAL(10, 8),                   -- Root Mean Squared Error
    mape DECIMAL(10, 8),                   -- Mean Absolute Percentage Error

    -- Trading performance
    total_trades INT,
    winning_trades INT,
    losing_trades INT,
    win_rate DECIMAL(6, 4),
    avg_pnl_pips DECIMAL(10, 4),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(10, 6),

    -- Calibration
    calibration_error DECIMAL(6, 4),       -- How well probabilities match outcomes

    -- Latency
    avg_inference_latency_ms DECIMAL(10, 2),
    p95_inference_latency_ms DECIMAL(10, 2),
    p99_inference_latency_ms DECIMAL(10, 2),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('model_performance_timeseries', 'time', chunk_time_interval => INTERVAL '7 days');

-- Add tenant dimension
SELECT add_dimension('model_performance_timeseries', 'tenant_id', number_partitions => 4);

-- Indexes
CREATE INDEX idx_performance_ts_model_time
ON model_performance_timeseries (model_id, time DESC);

CREATE INDEX idx_performance_ts_tenant_symbol
ON model_performance_timeseries (tenant_id, symbol, time DESC);

-- Row-level security
ALTER TABLE model_performance_timeseries ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_performance_ts ON model_performance_timeseries
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- CONTINUOUS AGGREGATES - Automatic roll-ups
-- =======================================================================

-- Hourly prediction statistics
CREATE MATERIALIZED VIEW ml_predictions_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS hour,
    tenant_id,
    model_id,
    symbol,
    COUNT(*) as prediction_count,
    AVG(confidence_score) as avg_confidence,
    AVG(CASE WHEN direction_correct THEN 1.0 ELSE 0.0 END) as accuracy,
    AVG(inference_latency_ms) as avg_latency_ms,
    COUNT(*) FILTER (WHERE signal_generated) as signals_generated,
    COUNT(*) FILTER (WHERE executed) as executions
FROM ml_predictions
WHERE outcome_recorded_at IS NOT NULL  -- Only completed predictions
GROUP BY hour, tenant_id, model_id, symbol;

-- Daily trading performance
CREATE MATERIALIZED VIEW trade_results_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', time) AS day,
    tenant_id,
    user_id,
    symbol,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE outcome = 'win') as winning_trades,
    COUNT(*) FILTER (WHERE outcome = 'loss') as losing_trades,
    AVG(pnl_pips) as avg_pnl_pips,
    SUM(pnl_amount) as total_pnl_amount,
    AVG(trade_duration_seconds) as avg_duration_seconds,
    AVG(risk_reward_ratio) as avg_risk_reward
FROM trade_results
WHERE exit_time IS NOT NULL  -- Only closed trades
GROUP BY day, tenant_id, user_id, symbol;

-- Add refresh policies (auto-update)
SELECT add_continuous_aggregate_policy('ml_predictions_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

SELECT add_continuous_aggregate_policy('trade_results_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day');

-- =======================================================================
-- DATA RETENTION POLICIES
-- =======================================================================

-- Keep raw predictions for 90 days
SELECT add_retention_policy('ml_predictions', INTERVAL '90 days');

-- Keep trade results for 3 years
SELECT add_retention_policy('trade_results', INTERVAL '1095 days');

-- Keep performance timeseries for 1 year
SELECT add_retention_policy('model_performance_timeseries', INTERVAL '365 days');

-- =======================================================================
-- FUNCTIONS: Update trade results when prediction outcome is recorded
-- =======================================================================

CREATE OR REPLACE FUNCTION update_prediction_from_trade()
RETURNS TRIGGER AS $$
BEGIN
    -- Update the corresponding prediction with actual outcome
    UPDATE ml_predictions
    SET
        actual_direction = CASE
            WHEN NEW.pnl_pips > 0 THEN 1
            WHEN NEW.pnl_pips < 0 THEN -1
            ELSE 0
        END,
        actual_return = NEW.pnl_percent,
        direction_correct = CASE
            WHEN NEW.pnl_pips > 0 AND predicted_direction = 1 THEN TRUE
            WHEN NEW.pnl_pips < 0 AND predicted_direction = -1 THEN TRUE
            ELSE FALSE
        END,
        outcome_recorded_at = NEW.exit_time,
        updated_at = NOW()
    WHERE prediction_id = NEW.prediction_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_prediction_outcome
AFTER INSERT OR UPDATE ON trade_results
FOR EACH ROW
WHEN (NEW.exit_time IS NOT NULL AND NEW.prediction_id IS NOT NULL)
EXECUTE FUNCTION update_prediction_from_trade();

-- =======================================================================
-- VIEWS: Useful analytics queries
-- =======================================================================

-- Real-time model leaderboard
CREATE OR REPLACE VIEW model_leaderboard AS
SELECT
    m.model_id,
    m.model_name,
    m.version,
    m.target_symbol,
    m.target_timeframe,
    COUNT(p.prediction_id) as total_predictions,
    AVG(p.confidence_score) as avg_confidence,
    AVG(CASE WHEN p.direction_correct THEN 1.0 ELSE 0.0 END) as accuracy,
    AVG(p.inference_latency_ms) as avg_latency_ms,
    MAX(p.time) as last_prediction_time
FROM ml_registry.models m
LEFT JOIN ml_predictions p ON m.model_id = p.model_id
WHERE p.outcome_recorded_at IS NOT NULL
  AND p.time >= NOW() - INTERVAL '7 days'
GROUP BY m.model_id, m.model_name, m.version, m.target_symbol, m.target_timeframe
ORDER BY accuracy DESC;

-- Trading performance summary
CREATE OR REPLACE VIEW trading_performance_summary AS
SELECT
    tenant_id,
    user_id,
    symbol,
    COUNT(*) as total_trades,
    COUNT(*) FILTER (WHERE outcome = 'win') as wins,
    COUNT(*) FILTER (WHERE outcome = 'loss') as losses,
    ROUND(COUNT(*) FILTER (WHERE outcome = 'win')::DECIMAL / NULLIF(COUNT(*), 0), 4) as win_rate,
    ROUND(AVG(pnl_pips), 2) as avg_pnl_pips,
    ROUND(SUM(pnl_amount), 2) as total_pnl,
    ROUND(AVG(risk_reward_ratio), 2) as avg_risk_reward
FROM trade_results
WHERE time >= NOW() - INTERVAL '30 days'
  AND exit_time IS NOT NULL
GROUP BY tenant_id, user_id, symbol;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO suho_service;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO suho_readonly;

COMMIT;
