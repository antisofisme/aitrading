-- =======================================================================
-- POSTGRESQL MODEL REGISTRY SCHEMA
-- =======================================================================
-- Central registry for ML/DL models with versioning and metadata
-- Stores model metadata, not the actual model binaries (stored in S3/MinIO)
-- =======================================================================

\c suho_trading;

-- Create ML schema
CREATE SCHEMA IF NOT EXISTS ml_registry;

SET search_path TO ml_registry, public;

-- =======================================================================
-- TABLE 1: MODEL REGISTRY
-- =======================================================================
-- Master table for all ML/DL models

CREATE TABLE IF NOT EXISTS models (
    -- Primary identifiers
    model_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),                   -- NULL for shared models

    -- Model metadata
    model_name VARCHAR(100) NOT NULL,      -- "eurusd_lstm_1h_v3"
    model_type VARCHAR(50) NOT NULL,       -- 'lstm', 'transformer', 'xgboost', 'random_forest'
    task_type VARCHAR(50) NOT NULL,        -- 'classification', 'regression', 'reinforcement'

    -- Target details
    target_symbol VARCHAR(20) NOT NULL,    -- 'EUR/USD', 'XAU/USD', 'all' (for multi-asset)
    target_timeframe VARCHAR(10) NOT NULL, -- '1h', '4h', '1d'
    prediction_horizon VARCHAR(20) NOT NULL, -- '1h', '4h', '1d', 'multi' (multi-horizon)

    -- Model version and status
    version VARCHAR(20) NOT NULL,          -- "v1.0.0", "v2.3.1"
    status VARCHAR(20) DEFAULT 'draft',    -- 'draft', 'training', 'testing', 'production', 'archived'

    -- Model architecture
    architecture JSONB,                    -- Full model architecture config
    -- Example: {
    --   "layers": [
    --     {"type": "lstm", "units": 128, "dropout": 0.2},
    --     {"type": "dense", "units": 64, "activation": "relu"},
    --     {"type": "output", "units": 3, "activation": "softmax"}
    --   ],
    --   "optimizer": "adam",
    --   "loss": "categorical_crossentropy"
    -- }

    -- Hyperparameters
    hyperparameters JSONB,
    -- Example: {
    --   "learning_rate": 0.001,
    --   "batch_size": 32,
    --   "epochs": 100,
    --   "early_stopping_patience": 10,
    --   "sequence_length": 60,
    --   "features": ["close", "rsi_14", "macd_histogram", ...]
    -- }

    -- Feature configuration
    features_used TEXT[],                  -- Array of feature column names
    feature_count INT,
    feature_version VARCHAR(20),           -- Links to ml_features.feature_version

    -- Training data info
    training_data_start TIMESTAMPTZ,
    training_data_end TIMESTAMPTZ,
    training_sample_count BIGINT,
    validation_sample_count BIGINT,
    test_sample_count BIGINT,

    -- Model storage
    model_storage_type VARCHAR(20) DEFAULT 's3', -- 's3', 'minio', 'local'
    model_storage_path TEXT,               -- "s3://models/tenant_001/eurusd_lstm_1h_v3.h5"
    model_size_bytes BIGINT,

    -- Performance metrics
    metrics JSONB,
    -- Example: {
    --   "accuracy": 0.67,
    --   "precision": 0.65,
    --   "recall": 0.70,
    --   "f1_score": 0.675,
    --   "auc_roc": 0.72,
    --   "train_loss": 0.45,
    --   "val_loss": 0.52,
    --   "test_loss": 0.54,
    --   "sharpe_ratio": 1.8,  -- For trading performance
    --   "win_rate": 0.58
    -- }

    -- Deployment info
    deployed_at TIMESTAMPTZ,
    deployment_endpoint TEXT,              -- API endpoint if deployed
    inference_latency_ms DECIMAL(10, 2),   -- Average inference time

    -- Model provenance
    parent_model_id UUID REFERENCES models(model_id), -- For model lineage
    experiment_id UUID,                    -- Link to MLflow/experiment tracking

    -- User notes
    description TEXT,
    tags TEXT[],

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    trained_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT unique_model_version UNIQUE (tenant_id, model_name, version)
);

-- Indexes
CREATE INDEX idx_models_tenant ON models (tenant_id);
CREATE INDEX idx_models_status ON models (status);
CREATE INDEX idx_models_symbol_timeframe ON models (target_symbol, target_timeframe);
CREATE INDEX idx_models_type ON models (model_type);
CREATE INDEX idx_models_created_at ON models (created_at DESC);

-- Row-level security
ALTER TABLE models ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_models ON models
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 2: MODEL VERSIONS (Alternative design - normalized)
-- =======================================================================
-- If you prefer separating versions from models table
-- (Current design: denormalized - all in models table)

-- =======================================================================
-- TABLE 3: MODEL TRAINING JOBS
-- =======================================================================
-- Tracks all training attempts, including failed ones

CREATE TABLE IF NOT EXISTS training_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,

    -- Job details
    job_status VARCHAR(20) DEFAULT 'queued', -- 'queued', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INT,

    -- Training configuration
    config JSONB,                          -- Hyperparameters for this run

    -- Progress tracking
    current_epoch INT,
    total_epochs INT,
    current_loss DECIMAL(12, 8),
    current_val_loss DECIMAL(12, 8),
    best_val_loss DECIMAL(12, 8),

    -- Resource usage
    gpu_used BOOLEAN DEFAULT FALSE,
    cpu_cores INT,
    memory_mb INT,
    compute_provider VARCHAR(50),          -- 'local', 'aws', 'gcp', 'e2b_sandbox'

    -- Training logs
    log_path TEXT,
    tensorboard_path TEXT,

    -- Results
    final_metrics JSONB,
    model_checkpoint_path TEXT,

    -- Error handling
    error_message TEXT,
    error_traceback TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_training_jobs_model ON training_jobs (model_id);
CREATE INDEX idx_training_jobs_status ON training_jobs (job_status);
CREATE INDEX idx_training_jobs_created_at ON training_jobs (created_at DESC);

-- Row-level security
ALTER TABLE training_jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_training_jobs ON training_jobs
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 4: MODEL EVALUATION HISTORY
-- =======================================================================
-- Stores evaluation results over time (for model degradation detection)

CREATE TABLE IF NOT EXISTS model_evaluations (
    evaluation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,

    -- Evaluation dataset
    dataset_type VARCHAR(20) NOT NULL,     -- 'validation', 'test', 'live_backtest'
    dataset_start TIMESTAMPTZ,
    dataset_end TIMESTAMPTZ,
    sample_count BIGINT,

    -- Performance metrics
    metrics JSONB NOT NULL,

    -- Comparison with baseline
    baseline_model_id UUID REFERENCES models(model_id),
    improvement_over_baseline DECIMAL(6, 4), -- Percentage improvement

    -- Statistical significance
    p_value DECIMAL(10, 8),                -- For A/B testing
    confidence_interval JSONB,             -- {"lower": 0.62, "upper": 0.71}

    -- Notes
    notes TEXT,

    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_evaluations_model ON model_evaluations (model_id);
CREATE INDEX idx_evaluations_evaluated_at ON model_evaluations (evaluated_at DESC);

-- Row-level security
ALTER TABLE model_evaluations ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_evaluations ON model_evaluations
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 5: MODEL DEPLOYMENT HISTORY
-- =======================================================================
-- Tracks all model deployments (production releases)

CREATE TABLE IF NOT EXISTS model_deployments (
    deployment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,

    -- Deployment details
    environment VARCHAR(20) NOT NULL,      -- 'staging', 'production', 'canary'
    deployment_type VARCHAR(20),           -- 'blue_green', 'canary', 'rolling'
    traffic_percentage INT DEFAULT 100,    -- For canary deployments

    -- Endpoint information
    endpoint_url TEXT,
    api_key_hash TEXT,

    -- Deployment status
    status VARCHAR(20) DEFAULT 'active',   -- 'active', 'inactive', 'rollback'
    deployed_by VARCHAR(100),

    -- Rollback capability
    previous_model_id UUID REFERENCES models(model_id),
    rollback_reason TEXT,

    deployed_at TIMESTAMPTZ DEFAULT NOW(),
    deactivated_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_deployments_model ON model_deployments (model_id);
CREATE INDEX idx_deployments_status ON model_deployments (status);
CREATE INDEX idx_deployments_environment ON model_deployments (environment);

-- Row-level security
ALTER TABLE model_deployments ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_deployments ON model_deployments
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 6: MODEL ALERTS
-- =======================================================================
-- Alerts for model performance degradation

CREATE TABLE IF NOT EXISTS model_alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID REFERENCES models(model_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,

    -- Alert details
    alert_type VARCHAR(50) NOT NULL,       -- 'performance_degradation', 'high_latency', 'data_drift'
    severity VARCHAR(20) NOT NULL,         -- 'info', 'warning', 'critical'

    -- Alert trigger
    metric_name VARCHAR(50),
    current_value DECIMAL(12, 6),
    threshold_value DECIMAL(12, 6),

    -- Message
    message TEXT NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'open',     -- 'open', 'acknowledged', 'resolved'
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_alerts_model ON model_alerts (model_id);
CREATE INDEX idx_alerts_status ON model_alerts (status);
CREATE INDEX idx_alerts_severity ON model_alerts (severity);
CREATE INDEX idx_alerts_created_at ON model_alerts (created_at DESC);

-- Row-level security
ALTER TABLE model_alerts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_alerts ON model_alerts
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- TABLE 7: EXPERIMENT TRACKING (Optional - use MLflow instead)
-- =======================================================================
-- Lightweight experiment tracking (if not using MLflow)

CREATE TABLE IF NOT EXISTS experiments (
    experiment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    experiment_name VARCHAR(100) NOT NULL,
    description TEXT,
    objective VARCHAR(50),                 -- 'maximize_accuracy', 'minimize_loss'

    -- Experiment parameters
    parameter_space JSONB,                 -- For hyperparameter tuning

    -- Results summary
    best_model_id UUID REFERENCES models(model_id),
    best_metric_value DECIMAL(12, 6),

    -- Status
    status VARCHAR(20) DEFAULT 'running',  -- 'running', 'completed', 'failed'

    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_experiments_tenant ON experiments (tenant_id);
CREATE INDEX idx_experiments_status ON experiments (status);

-- Row-level security
ALTER TABLE experiments ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_experiments ON experiments
FOR ALL TO suho_service
USING (tenant_id = current_setting('app.current_tenant_id', true));

-- =======================================================================
-- FUNCTIONS: Automatic timestamp updates
-- =======================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_models_updated_at BEFORE UPDATE ON models
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_jobs_updated_at BEFORE UPDATE ON training_jobs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =======================================================================
-- VIEWS: Useful queries
-- =======================================================================

-- Active production models
CREATE OR REPLACE VIEW active_production_models AS
SELECT
    m.*,
    md.endpoint_url,
    md.deployed_at as production_deployed_at
FROM models m
JOIN model_deployments md ON m.model_id = md.model_id
WHERE m.status = 'production'
  AND md.status = 'active'
  AND md.environment = 'production';

-- Model performance summary
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT
    m.model_id,
    m.tenant_id,
    m.model_name,
    m.version,
    m.target_symbol,
    m.target_timeframe,
    m.status,
    m.metrics,
    COUNT(DISTINCT e.evaluation_id) as evaluation_count,
    AVG((e.metrics->>'accuracy')::DECIMAL) as avg_accuracy,
    MAX(e.evaluated_at) as last_evaluated_at
FROM models m
LEFT JOIN model_evaluations e ON m.model_id = e.model_id
GROUP BY m.model_id;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ml_registry TO suho_service;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ml_registry TO suho_service;
GRANT SELECT ON ALL TABLES IN SCHEMA ml_registry TO suho_readonly;

COMMIT;
