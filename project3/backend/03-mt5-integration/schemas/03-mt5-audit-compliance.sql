-- ============================================================================
-- MT5 EA Integration - Audit Trail & Compliance Tables
-- ============================================================================
-- Regulatory compliance, audit logging, and risk management
-- CRITICAL: Trading with real money requires complete audit trail
-- Supports: MiFID II, ESMA regulations, broker compliance requirements
-- ============================================================================

\c suho_trading;

-- ============================================================================
-- 11. AUDIT LOG (TIME-SERIES)
-- ============================================================================
-- Immutable audit trail for ALL system actions
-- Required for: Regulatory compliance, dispute resolution, forensic analysis
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_audit_log (
    -- Primary identifiers
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Who
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    account_id UUID,
    session_id UUID,

    -- What
    event_type VARCHAR(50) NOT NULL,               -- 'account_created', 'trade_executed', 'signal_generated', etc.
    event_category VARCHAR(30) NOT NULL,           -- 'account', 'trading', 'signal', 'configuration', 'authentication'
    action VARCHAR(50) NOT NULL,                   -- 'create', 'update', 'delete', 'execute', 'reject'
    resource_type VARCHAR(50),                     -- 'account', 'order', 'signal', 'settings'
    resource_id VARCHAR(100),

    -- Context
    event_description TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',           -- 'debug', 'info', 'warning', 'error', 'critical'

    -- Where
    source_service VARCHAR(50),                    -- 'api-gateway', 'ea', 'ml-engine', 'data-bridge'
    source_ip INET,
    source_user_agent TEXT,
    source_location VARCHAR(100),                  -- Geographic location (if available)

    -- Request details
    request_id UUID,
    correlation_id VARCHAR(100),
    api_endpoint VARCHAR(255),
    http_method VARCHAR(10),
    request_payload JSONB,

    -- Response details
    response_status INTEGER,
    response_payload JSONB,
    execution_time_ms INTEGER,

    -- Changes (before/after)
    changes_before JSONB,
    changes_after JSONB,

    -- Security
    authentication_method VARCHAR(50),             -- 'api_key', 'jwt', 'oauth', 'ea_hash'
    authorization_result BOOLEAN,
    security_flags JSONB,                          -- Suspicious activity flags

    -- Compliance
    regulatory_tags TEXT[],                        -- ['mifid_ii', 'esma', 'gdpr']
    retention_until TIMESTAMPTZ,                   -- Data retention policy
    is_sensitive BOOLEAN DEFAULT false,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CHECK (event_category IN ('account', 'trading', 'signal', 'configuration', 'authentication', 'system')),
    CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical'))
);

-- Convert to TimescaleDB hypertable (1-day chunks)
SELECT create_hypertable(
    'mt5_audit_log',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Add tenant partitioning
SELECT add_dimension(
    'mt5_audit_log',
    'tenant_id',
    number_partitions => 4,
    if_not_exists => TRUE
);

-- Indexes for audit queries
CREATE INDEX idx_audit_log_tenant_time ON mt5_audit_log(tenant_id, time DESC);
CREATE INDEX idx_audit_log_user_time ON mt5_audit_log(user_id, time DESC)
    WHERE user_id IS NOT NULL;
CREATE INDEX idx_audit_log_event_type ON mt5_audit_log(event_type, time DESC);
CREATE INDEX idx_audit_log_category_severity ON mt5_audit_log(event_category, severity, time DESC);
CREATE INDEX idx_audit_log_resource ON mt5_audit_log(resource_type, resource_id, time DESC);
CREATE INDEX idx_audit_log_security ON mt5_audit_log(time DESC)
    WHERE severity IN ('error', 'critical') OR authorization_result = false;

-- Retention policy (7 years for compliance)
SELECT add_retention_policy('mt5_audit_log',
    INTERVAL '7 years',
    if_not_exists => TRUE
);

-- Row-Level Security
ALTER TABLE mt5_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_audit_log ON mt5_audit_log
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Read-only policy (audit logs are immutable)
CREATE POLICY audit_log_insert_only ON mt5_audit_log
    FOR INSERT
    TO suho_service
    WITH CHECK (true);

-- Prevent updates and deletes (immutable audit trail)
CREATE POLICY audit_log_no_update ON mt5_audit_log
    FOR UPDATE
    TO suho_service
    USING (false);

CREATE POLICY audit_log_no_delete ON mt5_audit_log
    FOR DELETE
    TO suho_service
    USING (false);

-- Comments
COMMENT ON TABLE mt5_audit_log IS 'Immutable audit trail for regulatory compliance (7-year retention)';
COMMENT ON COLUMN mt5_audit_log.regulatory_tags IS 'Compliance tags: mifid_ii, esma, gdpr, etc.';


-- ============================================================================
-- 12. RISK EVENTS (TIME-SERIES)
-- ============================================================================
-- Tracks risk management events: breaches, warnings, margin calls
-- Used for: Risk monitoring, account protection, compliance reporting
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_risk_events (
    -- Primary identifiers
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    time TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Account
    account_id UUID NOT NULL REFERENCES mt5_user_accounts(account_id) ON DELETE CASCADE,
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL,               -- 'max_drawdown', 'margin_call', 'daily_loss_limit', 'position_size_limit'
    severity VARCHAR(20) NOT NULL,                 -- 'warning', 'critical', 'violation'
    description TEXT NOT NULL,

    -- Risk metrics
    current_balance DECIMAL(15,2),
    current_equity DECIMAL(15,2),
    margin_level DECIMAL(8,2),
    drawdown DECIMAL(15,2),
    drawdown_percent DECIMAL(8,4),

    -- Thresholds
    threshold_type VARCHAR(50),
    threshold_value DECIMAL(15,2),
    current_value DECIMAL(15,2),
    breach_amount DECIMAL(15,2),                   -- How much over the limit

    -- Actions taken
    action_taken VARCHAR(100),                     -- 'close_positions', 'disable_trading', 'send_alert', 'margin_call'
    positions_closed INTEGER DEFAULT 0,
    trading_disabled BOOLEAN DEFAULT false,
    alert_sent BOOLEAN DEFAULT false,

    -- Related trades
    affected_orders UUID[],                        -- Array of order_ids affected

    -- Resolution
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Constraints
    CHECK (event_type IN ('max_drawdown', 'margin_call', 'daily_loss_limit', 'position_size_limit', 'max_trades_per_day', 'equity_below_minimum')),
    CHECK (severity IN ('warning', 'critical', 'violation'))
);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'mt5_risk_events',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Indexes
CREATE INDEX idx_risk_events_account_time ON mt5_risk_events(account_id, time DESC);
CREATE INDEX idx_risk_events_type_severity ON mt5_risk_events(event_type, severity, time DESC);
CREATE INDEX idx_risk_events_unresolved ON mt5_risk_events(time DESC)
    WHERE resolved = false;

-- Row-Level Security
ALTER TABLE mt5_risk_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_risk_events ON mt5_risk_events
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_risk_events IS 'Risk management events and violations';
COMMENT ON COLUMN mt5_risk_events.action_taken IS 'Automated action: close_positions, disable_trading, send_alert';


-- ============================================================================
-- 13. COMPLIANCE REPORTS (SNAPSHOT)
-- ============================================================================
-- Pre-generated compliance reports for regulatory submission
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_compliance_reports (
    -- Primary identifiers
    report_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,

    -- Report details
    report_type VARCHAR(50) NOT NULL,              -- 'monthly_trading', 'annual_summary', 'mifid_transaction', 'risk_disclosure'
    report_period_start TIMESTAMPTZ NOT NULL,
    report_period_end TIMESTAMPTZ NOT NULL,
    generated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Scope
    account_ids UUID[],                            -- Accounts included in report
    user_ids VARCHAR(50)[],

    -- Report data
    report_data JSONB NOT NULL,                    -- Complete report in JSON format
    summary_statistics JSONB,

    -- Compliance framework
    regulatory_framework VARCHAR(50),              -- 'mifid_ii', 'esma', 'sec', 'finra'
    compliance_version VARCHAR(20),

    -- File storage
    report_file_path TEXT,                         -- PDF/CSV storage path
    report_file_hash VARCHAR(64),                  -- SHA-256 hash for integrity

    -- Status
    status VARCHAR(20) DEFAULT 'draft',            -- 'draft', 'submitted', 'approved', 'archived'
    submitted_at TIMESTAMPTZ,
    submitted_by VARCHAR(50),
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(50),

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CHECK (report_type IN ('monthly_trading', 'annual_summary', 'mifid_transaction', 'risk_disclosure', 'best_execution')),
    CHECK (status IN ('draft', 'submitted', 'approved', 'archived'))
);

-- Indexes
CREATE INDEX idx_compliance_reports_tenant ON mt5_compliance_reports(tenant_id, generated_at DESC);
CREATE INDEX idx_compliance_reports_type ON mt5_compliance_reports(report_type, report_period_start);
CREATE INDEX idx_compliance_reports_status ON mt5_compliance_reports(status, generated_at DESC);

-- Row-Level Security
ALTER TABLE mt5_compliance_reports ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_compliance_reports ON mt5_compliance_reports
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_compliance_reports IS 'Pre-generated regulatory compliance reports';


-- ============================================================================
-- 14. USER CONSENT & DISCLOSURES
-- ============================================================================
-- Tracks user consent for trading, risk disclosures, terms acceptance
-- Required for: GDPR compliance, financial regulations
-- ============================================================================

CREATE TABLE IF NOT EXISTS mt5_user_consents (
    -- Primary identifiers
    consent_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,

    -- Consent details
    consent_type VARCHAR(50) NOT NULL,             -- 'terms_of_service', 'risk_disclosure', 'data_processing', 'marketing'
    consent_version VARCHAR(20) NOT NULL,          -- Version of T&C/disclosure
    consent_given BOOLEAN NOT NULL,

    -- Timestamps
    consent_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    consent_expiry TIMESTAMPTZ,
    revoked_date TIMESTAMPTZ,

    -- Context
    consent_method VARCHAR(50),                    -- 'web_form', 'api', 'email', 'signed_document'
    ip_address INET,
    user_agent TEXT,
    document_url TEXT,                             -- Link to T&C document

    -- Verification
    signature_hash VARCHAR(255),                   -- Digital signature (if applicable)
    is_verified BOOLEAN DEFAULT false,
    verified_by VARCHAR(50),
    verified_at TIMESTAMPTZ,

    -- Status
    status VARCHAR(20) DEFAULT 'active',           -- 'active', 'expired', 'revoked'

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CHECK (consent_type IN ('terms_of_service', 'risk_disclosure', 'data_processing', 'marketing', 'trading_authorization')),
    CHECK (status IN ('active', 'expired', 'revoked'))
);

-- Indexes
CREATE INDEX idx_consents_user ON mt5_user_consents(tenant_id, user_id, consent_date DESC);
CREATE INDEX idx_consents_type_status ON mt5_user_consents(consent_type, status);
CREATE INDEX idx_consents_expiry ON mt5_user_consents(consent_expiry)
    WHERE status = 'active' AND consent_expiry IS NOT NULL;

-- Row-Level Security
ALTER TABLE mt5_user_consents ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_consents ON mt5_user_consents
    FOR ALL
    TO suho_service
    USING (tenant_id = current_setting('app.current_tenant_id', true));

-- Comments
COMMENT ON TABLE mt5_user_consents IS 'User consent tracking for GDPR and regulatory compliance';


-- ============================================================================
-- 15. HELPER FUNCTIONS
-- ============================================================================

-- Function: Log audit event
CREATE OR REPLACE FUNCTION log_audit_event(
    p_tenant_id VARCHAR(50),
    p_user_id VARCHAR(50),
    p_event_type VARCHAR(50),
    p_event_category VARCHAR(30),
    p_action VARCHAR(50),
    p_description TEXT,
    p_severity VARCHAR(20) DEFAULT 'info',
    p_metadata JSONB DEFAULT '{}'::jsonb
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO mt5_audit_log (
        tenant_id,
        user_id,
        event_type,
        event_category,
        action,
        event_description,
        severity,
        metadata,
        time
    ) VALUES (
        p_tenant_id,
        p_user_id,
        p_event_type,
        p_event_category,
        p_action,
        p_description,
        p_severity,
        p_metadata,
        NOW()
    ) RETURNING audit_id INTO v_audit_id;

    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function: Trigger risk event
CREATE OR REPLACE FUNCTION trigger_risk_event(
    p_account_id UUID,
    p_event_type VARCHAR(50),
    p_severity VARCHAR(20),
    p_description TEXT,
    p_threshold_value DECIMAL,
    p_current_value DECIMAL,
    p_action_taken VARCHAR(100) DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_event_id UUID;
    v_tenant_id VARCHAR(50);
    v_user_id VARCHAR(50);
    v_balance DECIMAL(15,2);
    v_equity DECIMAL(15,2);
BEGIN
    -- Get account details
    SELECT tenant_id, user_id INTO v_tenant_id, v_user_id
    FROM mt5_user_accounts
    WHERE account_id = p_account_id;

    -- Get latest balance
    SELECT balance, equity INTO v_balance, v_equity
    FROM mt5_account_balance_history
    WHERE account_id = p_account_id
    ORDER BY time DESC
    LIMIT 1;

    -- Insert risk event
    INSERT INTO mt5_risk_events (
        account_id,
        tenant_id,
        user_id,
        event_type,
        severity,
        description,
        current_balance,
        current_equity,
        threshold_type,
        threshold_value,
        current_value,
        breach_amount,
        action_taken,
        time
    ) VALUES (
        p_account_id,
        v_tenant_id,
        v_user_id,
        p_event_type,
        p_severity,
        p_description,
        v_balance,
        v_equity,
        p_event_type,
        p_threshold_value,
        p_current_value,
        p_current_value - p_threshold_value,
        p_action_taken,
        NOW()
    ) RETURNING event_id INTO v_event_id;

    -- Also log in audit trail
    PERFORM log_audit_event(
        v_tenant_id,
        v_user_id,
        'risk_event_triggered',
        'trading',
        'create',
        p_description,
        p_severity,
        jsonb_build_object(
            'event_id', v_event_id,
            'event_type', p_event_type,
            'threshold_value', p_threshold_value,
            'current_value', p_current_value
        )
    );

    RETURN v_event_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION log_audit_event(VARCHAR, VARCHAR, VARCHAR, VARCHAR, VARCHAR, TEXT, VARCHAR, JSONB) TO suho_service;
GRANT EXECUTE ON FUNCTION trigger_risk_event(UUID, VARCHAR, VARCHAR, TEXT, DECIMAL, DECIMAL, VARCHAR) TO suho_service;


-- ============================================================================
-- 16. AUDIT TRIGGERS
-- ============================================================================

-- Trigger: Log account creation
CREATE OR REPLACE FUNCTION audit_account_creation()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM log_audit_event(
        NEW.tenant_id,
        NEW.user_id,
        'account_created',
        'account',
        'create',
        format('MT5 account created: %s@%s (Login: %s)', NEW.mt5_account_number, NEW.broker_server, NEW.mt5_login),
        'info',
        jsonb_build_object(
            'account_id', NEW.account_id,
            'broker', NEW.broker_name,
            'account_type', NEW.account_type,
            'leverage', NEW.leverage
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_account_creation
    AFTER INSERT ON mt5_user_accounts
    FOR EACH ROW
    EXECUTE FUNCTION audit_account_creation();

-- Trigger: Log trade execution
CREATE OR REPLACE FUNCTION audit_trade_execution()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'open' AND OLD.status = 'pending' THEN
        PERFORM log_audit_event(
            NEW.tenant_id,
            NEW.user_id,
            'trade_executed',
            'trading',
            'execute',
            format('Trade executed: %s %s %.2f lots @ %.5f (Ticket: %s)',
                NEW.order_type, NEW.symbol, NEW.volume, NEW.open_price, NEW.ticket),
            'info',
            jsonb_build_object(
                'order_id', NEW.order_id,
                'ticket', NEW.ticket,
                'symbol', NEW.symbol,
                'order_type', NEW.order_type,
                'volume', NEW.volume,
                'price', NEW.open_price,
                'signal_id', NEW.signal_id
            )
        );
    ELSIF NEW.status = 'closed' AND OLD.status = 'open' THEN
        PERFORM log_audit_event(
            NEW.tenant_id,
            NEW.user_id,
            'trade_closed',
            'trading',
            'execute',
            format('Trade closed: Ticket %s, Profit: %.2f (%.2f pips)',
                NEW.ticket, NEW.profit, NEW.profit_pips),
            CASE WHEN NEW.profit < 0 THEN 'warning' ELSE 'info' END,
            jsonb_build_object(
                'order_id', NEW.order_id,
                'ticket', NEW.ticket,
                'profit', NEW.profit,
                'profit_pips', NEW.profit_pips,
                'close_reason', NEW.close_reason
            )
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_audit_trade_execution
    AFTER UPDATE ON mt5_trade_orders
    FOR EACH ROW
    EXECUTE FUNCTION audit_trade_execution();


-- ============================================================================
-- GRANTS
-- ============================================================================

GRANT SELECT, INSERT ON mt5_audit_log TO suho_service;
GRANT SELECT, INSERT, UPDATE ON mt5_risk_events TO suho_service;
GRANT SELECT, INSERT, UPDATE, DELETE ON mt5_compliance_reports TO suho_service;
GRANT SELECT, INSERT, UPDATE ON mt5_user_consents TO suho_service;

GRANT SELECT ON mt5_audit_log TO suho_readonly;
GRANT SELECT ON mt5_risk_events TO suho_readonly;
GRANT SELECT ON mt5_compliance_reports TO suho_readonly;
GRANT SELECT ON mt5_user_consents TO suho_readonly;

COMMIT;
