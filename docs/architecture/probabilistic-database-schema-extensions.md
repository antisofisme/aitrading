# Probabilistic Enhancement Database Schema Extensions

## Overview

This document defines the comprehensive database schema extensions required to support the probabilistic enhancement architecture across all database systems in the AI trading platform.

## 1. ClickHouse Schema Extensions (High-Frequency Analytics)

### 1.1 Enhanced Trading Decisions with Probability Metadata

```sql
-- Enhanced trading decisions with complete probability metadata
CREATE TABLE trading_decisions_probabilistic (
    id UUID,
    timestamp DateTime64(3),
    symbol String,
    decision Enum8('BUY' = 1, 'SELL' = 2, 'HOLD' = 3),
    user_id UUID,

    -- Multi-Layer Probability Data
    indicator_probabilities Array(Tuple(String, Float64, Float64, Float64)), -- (indicator, confidence, probability, reliability)
    ensemble_probability Float64,
    meta_validation_score Float64,

    -- Confidence Metrics
    aggregated_confidence Float64,
    epistemic_uncertainty Float64,  -- Model uncertainty
    aleatoric_uncertainty Float64,  -- Data uncertainty
    consensus_strength Float64,     -- Agreement between models
    divergence_score Float64,       -- Disagreement level

    -- Risk Metrics with Confidence
    position_size Float64,
    confidence_adjusted_size Float64,
    risk_level String,
    max_drawdown_estimate Float64,
    uncertainty_penalty Float64,

    -- Performance Prediction
    expected_return Float64,
    confidence_interval_lower Float64,
    confidence_interval_upper Float64,
    probability_success Float64,

    -- Model and Context Metadata
    model_versions Array(Tuple(String, String)), -- (model_name, version)
    market_regime String,
    volatility_score Float64,

    -- Execution Tracking
    execution_latency_ms UInt32,
    probability_calculation_time_ms UInt32,

    -- Multi-tenant support
    tenant_id String
) ENGINE = MergeTree()
ORDER BY (tenant_id, symbol, timestamp)
PARTITION BY (tenant_id, toYYYYMM(timestamp))
SETTINGS index_granularity = 8192;

-- Real-time probability metrics for live monitoring
CREATE TABLE probability_metrics_realtime (
    timestamp DateTime64(3),
    symbol String,
    service_name String, -- 'ml-supervised', 'ml-deep-learning', 'probabilistic-learning'
    user_id UUID,

    -- Layer-specific probabilities
    layer_type Enum8('indicator' = 1, 'ensemble' = 2, 'meta' = 3),
    layer_confidence Float64,
    layer_uncertainty Float64,

    -- Performance metrics
    prediction_accuracy Float64,
    calibration_score Float64,
    processing_time_ms UInt32,

    -- Model state
    model_version String,
    last_training_update DateTime64(3),

    tenant_id String
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp, service_name)
PARTITION BY (tenant_id, toYYYYMM(timestamp))
TTL timestamp + INTERVAL 30 DAY
SETTINGS index_granularity = 4096;

-- Model feedback and learning tracking
CREATE TABLE model_feedback_events (
    feedback_id UUID,
    prediction_id UUID,
    timestamp DateTime64(3),
    symbol String,
    user_id UUID,

    -- Outcome comparison
    predicted_direction Enum8('BUY' = 1, 'SELL' = 2, 'HOLD' = 3),
    actual_direction Enum8('BUY' = 1, 'SELL' = 2, 'HOLD' = 3),
    predicted_confidence Float64,
    actual_return Float64,
    expected_return Float64,
    success Boolean,

    -- Error analysis
    prediction_error Float64,
    confidence_calibration_error Float64,
    impact_score Float64, -- How much this affects model training

    -- Learning updates triggered
    models_updated Array(String),
    update_magnitude Float64,
    retraining_triggered Boolean,

    -- Market context at time of feedback
    market_volatility Float64,
    market_regime String,

    tenant_id String
) ENGINE = MergeTree()
ORDER BY (tenant_id, timestamp, symbol)
PARTITION BY (tenant_id, toYYYYMM(timestamp))
SETTINGS index_granularity = 8192;

-- Probabilistic performance analytics
CREATE TABLE probabilistic_performance_analytics (
    date Date,
    symbol String,
    user_id UUID,

    -- Daily performance summary
    total_predictions UInt32,
    successful_predictions UInt32,
    accuracy_rate Float64,

    -- Confidence analysis
    avg_confidence Float64,
    avg_uncertainty Float64,
    confidence_calibration Float64,

    -- Return analysis
    total_return Float64,
    confidence_weighted_return Float64,
    max_drawdown Float64,
    sharpe_ratio Float64,

    -- Risk metrics
    avg_position_size Float64,
    risk_adjusted_return Float64,
    uncertainty_penalty_total Float64,

    tenant_id String
) ENGINE = SummingMergeTree()
ORDER BY (tenant_id, date, symbol, user_id)
PARTITION BY (tenant_id, toYYYYMM(date))
SETTINGS index_granularity = 8192;
```

### 1.2 Materialized Views for Real-time Analytics

```sql
-- Real-time confidence monitoring
CREATE MATERIALIZED VIEW confidence_monitoring_mv
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, symbol, minute_bucket)
AS SELECT
    tenant_id,
    symbol,
    toStartOfMinute(timestamp) as minute_bucket,
    avgState(aggregated_confidence) as avg_confidence,
    avgState(epistemic_uncertainty) as avg_uncertainty,
    countState() as prediction_count,
    avgState(probability_calculation_time_ms) as avg_processing_time
FROM trading_decisions_probabilistic
GROUP BY tenant_id, symbol, minute_bucket;

-- Model performance tracking
CREATE MATERIALIZED VIEW model_performance_mv
ENGINE = AggregatingMergeTree()
ORDER BY (tenant_id, model_name, hour_bucket)
AS SELECT
    tenant_id,
    arrayJoin(model_versions).1 as model_name,
    toStartOfHour(timestamp) as hour_bucket,
    avgState(aggregated_confidence) as avg_confidence,
    countState() as usage_count,
    avgState(execution_latency_ms) as avg_latency
FROM trading_decisions_probabilistic
GROUP BY tenant_id, model_name, hour_bucket;
```

## 2. PostgreSQL Schema Extensions (Configuration & User Data)

### 2.1 Probabilistic Model Configuration

```sql
-- Probabilistic model registry and configuration
CREATE TABLE probabilistic_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- 'indicator', 'ensemble', 'meta', 'adaptive'
    version VARCHAR(20) NOT NULL,

    -- Model configuration
    parameters JSONB NOT NULL,
    hyperparameters JSONB,
    uncertainty_method VARCHAR(50), -- 'bayesian', 'ensemble', 'dropout', 'quantile'

    -- Performance metrics
    accuracy DECIMAL(5,4),
    calibration_score DECIMAL(5,4),
    brier_score DECIMAL(6,5),
    sharpe_ratio DECIMAL(6,4),

    -- Lifecycle management
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_trained TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'deprecated', 'experimental', 'training'

    -- Deployment tracking
    deployed_at TIMESTAMP WITH TIME ZONE,
    deployment_environment VARCHAR(20), -- 'development', 'staging', 'production'
    deployment_config JSONB,

    -- Multi-tenant support
    tenant_id UUID,
    is_shared BOOLEAN DEFAULT false, -- Can be shared across tenants

    UNIQUE(model_name, version, tenant_id)
);

-- User-specific probabilistic preferences
CREATE TABLE user_probability_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,

    -- Risk tolerance settings
    risk_tolerance DECIMAL(3,2) DEFAULT 0.5, -- 0.0 (conservative) to 1.0 (aggressive)
    confidence_threshold DECIMAL(3,2) DEFAULT 0.7, -- Minimum confidence for trades
    uncertainty_tolerance DECIMAL(3,2) DEFAULT 0.3, -- Maximum acceptable uncertainty

    -- Model preferences
    preferred_indicators TEXT[], -- Array of preferred indicator names
    indicator_weights JSONB, -- Custom weights for indicators {"rsi": 0.3, "macd": 0.4, ...}
    ensemble_method VARCHAR(50) DEFAULT 'weighted_average', -- 'simple_average', 'weighted_average', 'voting'

    -- Adaptive learning settings
    learning_rate DECIMAL(4,3) DEFAULT 0.001,
    adaptation_sensitivity DECIMAL(3,2) DEFAULT 0.5, -- How quickly to adapt to new data
    memory_decay_factor DECIMAL(4,3) DEFAULT 0.95, -- How much to weight historical vs recent data

    -- Notification preferences
    confidence_alert_threshold DECIMAL(3,2) DEFAULT 0.9, -- Alert when confidence exceeds this
    uncertainty_warning_threshold DECIMAL(3,2) DEFAULT 0.6, -- Warn when uncertainty exceeds this
    feedback_frequency VARCHAR(20) DEFAULT 'daily', -- 'real-time', 'hourly', 'daily', 'weekly'

    -- Performance tracking preferences
    track_calibration BOOLEAN DEFAULT true,
    track_feature_importance BOOLEAN DEFAULT true,
    enable_auto_retraining BOOLEAN DEFAULT true,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model training history and versioning
CREATE TABLE model_training_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID REFERENCES probabilistic_models(id) ON DELETE CASCADE,
    training_session_id UUID NOT NULL,

    -- Training details
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    status VARCHAR(20) NOT NULL, -- 'running', 'completed', 'failed', 'cancelled'

    -- Training data
    training_data_size INTEGER,
    validation_data_size INTEGER,
    test_data_size INTEGER,
    data_time_range TSTZRANGE, -- Time range of training data

    -- Training configuration
    hyperparameters JSONB,
    training_config JSONB,

    -- Results
    final_accuracy DECIMAL(6,4),
    final_calibration_score DECIMAL(6,4),
    final_brier_score DECIMAL(7,5),
    validation_metrics JSONB,

    -- Performance comparison
    previous_model_accuracy DECIMAL(6,4),
    improvement_percentage DECIMAL(5,2),

    -- Error tracking
    error_message TEXT,
    error_details JSONB,

    -- Multi-tenant support
    tenant_id UUID,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Probabilistic configuration templates
CREATE TABLE probability_config_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- 'conservative', 'balanced', 'aggressive', 'custom'

    -- Template configuration
    config JSONB NOT NULL, -- Complete configuration object

    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMP WITH TIME ZONE,

    -- Template metadata
    created_by UUID REFERENCES users(id),
    is_public BOOLEAN DEFAULT false,
    tags TEXT[],

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 2.2 Indexes for Performance

```sql
-- Indexes for probabilistic models
CREATE INDEX idx_probabilistic_models_type_status ON probabilistic_models(model_type, status) WHERE status = 'active';
CREATE INDEX idx_probabilistic_models_tenant ON probabilistic_models(tenant_id, status);
CREATE INDEX idx_probabilistic_models_performance ON probabilistic_models(accuracy DESC, calibration_score DESC) WHERE status = 'active';

-- Indexes for user preferences
CREATE INDEX idx_user_prefs_risk_tolerance ON user_probability_preferences(risk_tolerance, confidence_threshold);
CREATE INDEX idx_user_prefs_learning ON user_probability_preferences(learning_rate, adaptation_sensitivity);

-- Indexes for training history
CREATE INDEX idx_training_history_model ON model_training_history(model_id, started_at DESC);
CREATE INDEX idx_training_history_status ON model_training_history(status, started_at DESC);
CREATE INDEX idx_training_history_tenant ON model_training_history(tenant_id, completed_at DESC);
```

## 3. Redis Schema Extensions (Caching & Real-time Data)

### 3.1 Probability Cache Structures

```python
# Redis key patterns for probabilistic caching

# L1 Cache: Real-time probability scores (TTL: 60 seconds)
probability_cache_l1 = "prob:l1:{symbol}:{timestamp_minute}"

# L2 Cache: Aggregated confidence metrics (TTL: 300 seconds)
confidence_cache_l2 = "conf:l2:{symbol}:{model_type}:{timestamp_5min}"

# L3 Cache: Model prediction cache (TTL: 900 seconds)
prediction_cache_l3 = "pred:l3:{model_id}:{feature_hash}"

# User-specific probability settings cache (TTL: 3600 seconds)
user_prefs_cache = "user:prefs:{user_id}"

# Real-time uncertainty tracking (TTL: 120 seconds)
uncertainty_tracking = "uncertainty:{symbol}:{service_name}"

# Model performance metrics cache (TTL: 1800 seconds)
model_performance_cache = "perf:{model_name}:{time_bucket}"

# Adaptive learning state cache (TTL: 7200 seconds)
learning_state_cache = "learning:{model_id}:{user_id}"
```

### 3.2 Redis Stream Patterns for Real-time Updates

```python
# Redis streams for real-time probability updates
confidence_updates_stream = "confidence_updates"
uncertainty_alerts_stream = "uncertainty_alerts"
model_performance_stream = "model_performance"
learning_events_stream = "learning_events"
calibration_drift_stream = "calibration_drift"
```

## 4. Weaviate Schema Extensions (Vector Database)

### 4.1 Probabilistic Pattern Embeddings

```python
# Weaviate schema for probabilistic pattern storage
probabilistic_pattern_schema = {
    "class": "ProbabilisticPattern",
    "description": "Market patterns with associated probability and confidence metrics",
    "properties": [
        {
            "name": "pattern_id",
            "dataType": ["string"],
            "description": "Unique pattern identifier"
        },
        {
            "name": "symbol",
            "dataType": ["string"],
            "description": "Trading symbol"
        },
        {
            "name": "pattern_vector",
            "dataType": ["number[]"],
            "description": "High-dimensional pattern representation"
        },
        {
            "name": "confidence_score",
            "dataType": ["number"],
            "description": "Pattern confidence score (0-1)"
        },
        {
            "name": "uncertainty_vector",
            "dataType": ["number[]"],
            "description": "Uncertainty representation for each dimension"
        },
        {
            "name": "success_probability",
            "dataType": ["number"],
            "description": "Historical success probability"
        },
        {
            "name": "pattern_type",
            "dataType": ["string"],
            "description": "Type of pattern (technical, fundamental, sentiment)"
        },
        {
            "name": "market_regime",
            "dataType": ["string"],
            "description": "Market regime when pattern occurred"
        },
        {
            "name": "created_at",
            "dataType": ["date"],
            "description": "Pattern creation timestamp"
        },
        {
            "name": "tenant_id",
            "dataType": ["string"],
            "description": "Multi-tenant identifier"
        }
    ],
    "vectorizer": "none"  # We'll provide our own vectors
}

# Schema for uncertainty embeddings
uncertainty_embedding_schema = {
    "class": "UncertaintyEmbedding",
    "description": "Embeddings representing uncertainty in market predictions",
    "properties": [
        {
            "name": "embedding_id",
            "dataType": ["string"]
        },
        {
            "name": "symbol",
            "dataType": ["string"]
        },
        {
            "name": "uncertainty_vector",
            "dataType": ["number[]"],
            "description": "Multi-dimensional uncertainty representation"
        },
        {
            "name": "epistemic_uncertainty",
            "dataType": ["number"],
            "description": "Model uncertainty component"
        },
        {
            "name": "aleatoric_uncertainty",
            "dataType": ["number"],
            "description": "Data uncertainty component"
        },
        {
            "name": "context_similarity",
            "dataType": ["number"],
            "description": "Similarity to historical contexts"
        },
        {
            "name": "timestamp",
            "dataType": ["date"]
        },
        {
            "name": "tenant_id",
            "dataType": ["string"]
        }
    ],
    "vectorizer": "none"
}
```

## 5. ArangoDB Schema Extensions (Graph Database)

### 5.1 Probabilistic Dependency Graphs

```javascript
// ArangoDB collections for probabilistic relationships

// Nodes: Probabilistic components
db._create("probabilistic_nodes");
db.probabilistic_nodes.ensureIndex({ type: "hash", fields: ["component_type", "tenant_id"] });

// Edges: Probability flow and dependencies
db._createEdgeCollection("probability_dependencies");
db.probability_dependencies.ensureIndex({ type: "hash", fields: ["dependency_type", "confidence_impact"] });

// Graph structure for confidence propagation
db._create("confidence_propagation");

// Example node document structure
{
  "_key": "model_xgboost_v1_2",
  "component_type": "ml_model",
  "component_name": "XGBoost Supervised Learning",
  "confidence_contribution": 0.85,
  "uncertainty_contribution": 0.15,
  "tenant_id": "tenant_123",
  "last_updated": "2024-01-20T10:30:00Z",
  "performance_metrics": {
    "accuracy": 0.78,
    "calibration": 0.82,
    "reliability": 0.88
  }
}

// Example edge document structure
{
  "_from": "probabilistic_nodes/indicator_rsi",
  "_to": "probabilistic_nodes/ensemble_aggregator",
  "dependency_type": "probability_input",
  "weight": 0.25,
  "confidence_impact": 0.8,
  "uncertainty_propagation": 0.2,
  "tenant_id": "tenant_123",
  "created_at": "2024-01-20T10:30:00Z"
}
```

## 6. Migration Scripts and Data Integrity

### 6.1 Database Migration Strategy

```sql
-- Migration script for existing data
BEGIN;

-- 1. Add probability columns to existing tables
ALTER TABLE trading_decisions ADD COLUMN IF NOT EXISTS aggregated_confidence DECIMAL(4,3);
ALTER TABLE trading_decisions ADD COLUMN IF NOT EXISTS uncertainty_score DECIMAL(4,3);
ALTER TABLE trading_decisions ADD COLUMN IF NOT EXISTS probability_metadata JSONB;

-- 2. Backfill default probability values for existing records
UPDATE trading_decisions
SET aggregated_confidence = 0.5,
    uncertainty_score = 0.5,
    probability_metadata = '{"backfilled": true, "default_values": true}'::jsonb
WHERE aggregated_confidence IS NULL;

-- 3. Create new probability-specific tables
-- (Include all CREATE TABLE statements from above)

-- 4. Set up data integrity constraints
ALTER TABLE user_probability_preferences
ADD CONSTRAINT chk_risk_tolerance CHECK (risk_tolerance >= 0.0 AND risk_tolerance <= 1.0);

ALTER TABLE user_probability_preferences
ADD CONSTRAINT chk_confidence_threshold CHECK (confidence_threshold >= 0.0 AND confidence_threshold <= 1.0);

-- 5. Create triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_probability_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_prefs_timestamp
    BEFORE UPDATE ON user_probability_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_probability_timestamp();

COMMIT;
```

### 6.2 Data Validation Procedures

```sql
-- Data validation for probabilistic integrity
CREATE OR REPLACE FUNCTION validate_probability_data()
RETURNS TABLE(
    validation_issue TEXT,
    affected_records BIGINT,
    severity VARCHAR(10)
) AS $$
BEGIN
    -- Check for invalid confidence scores
    RETURN QUERY
    SELECT
        'Invalid confidence scores (outside 0-1 range)' as validation_issue,
        COUNT(*) as affected_records,
        'HIGH' as severity
    FROM trading_decisions_probabilistic
    WHERE aggregated_confidence < 0 OR aggregated_confidence > 1;

    -- Check for missing probability metadata
    RETURN QUERY
    SELECT
        'Missing probability metadata' as validation_issue,
        COUNT(*) as affected_records,
        'MEDIUM' as severity
    FROM trading_decisions_probabilistic
    WHERE indicator_probabilities = [] OR ensemble_probability IS NULL;

    -- Check for inconsistent uncertainty values
    RETURN QUERY
    SELECT
        'Inconsistent uncertainty values' as validation_issue,
        COUNT(*) as affected_records,
        'MEDIUM' as severity
    FROM trading_decisions_probabilistic
    WHERE epistemic_uncertainty + aleatoric_uncertainty > 1.0;

END;
$$ LANGUAGE plpgsql;
```

## 7. Performance Optimization

### 7.1 Partitioning Strategy

```sql
-- Partition strategy for large probabilistic tables
CREATE TABLE trading_decisions_probabilistic_template (
    LIKE trading_decisions_probabilistic INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions
CREATE TABLE trading_decisions_probabilistic_2024_01
    PARTITION OF trading_decisions_probabilistic_template
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE trading_decisions_probabilistic_2024_02
    PARTITION OF trading_decisions_probabilistic_template
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Auto-create future partitions
SELECT partman.create_parent(
    p_parent_table => 'public.trading_decisions_probabilistic_template',
    p_control => 'timestamp',
    p_type => 'range',
    p_interval => 'monthly'
);
```

### 7.2 Indexing Strategy

```sql
-- Composite indexes for probabilistic queries
CREATE INDEX CONCURRENTLY idx_prob_decisions_confidence_time
ON trading_decisions_probabilistic (aggregated_confidence DESC, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_prob_decisions_symbol_confidence
ON trading_decisions_probabilistic (symbol, aggregated_confidence DESC)
WHERE aggregated_confidence >= 0.7;

CREATE INDEX CONCURRENTLY idx_prob_decisions_uncertainty_symbol
ON trading_decisions_probabilistic (epistemic_uncertainty, symbol, timestamp);

-- Partial indexes for active models
CREATE INDEX CONCURRENTLY idx_active_models_performance
ON probabilistic_models (accuracy DESC, calibration_score DESC)
WHERE status = 'active';
```

This comprehensive database schema extension provides the foundation for the probabilistic enhancement architecture while maintaining compatibility with the existing 11 production microservices and supporting multi-tenant operations.