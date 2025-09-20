-- User Service Security Schema
-- Enhanced security tables for authentication, sessions, and audit logging

-- Users table (already exists, adding security columns)
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_history JSONB DEFAULT '[]';
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_locked_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS account_locked_until TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS failed_login_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_changed_at TIMESTAMP DEFAULT NOW();

-- User Credentials table for secure password management
CREATE TABLE IF NOT EXISTS user_credentials (
    user_id UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt VARCHAR(255) NOT NULL DEFAULT gen_random_uuid()::text,
    last_password_change TIMESTAMP DEFAULT NOW(),
    password_history JSONB DEFAULT '[]',
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- Two-Factor Authentication
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret TEXT,
    recovery_codes JSONB DEFAULT '[]',
    backup_codes_used JSONB DEFAULT '[]',
    
    -- Security metadata
    security_questions JSONB DEFAULT '[]',
    last_security_check TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- User Sessions table for session management
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Session details
    ip_address INET NOT NULL,
    user_agent TEXT,
    device_info JSONB DEFAULT '{}',
    location_info JSONB DEFAULT '{}',
    
    -- Session lifecycle
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'expired', 'revoked')),
    
    -- Security flags
    is_suspicious BOOLEAN DEFAULT false,
    login_method VARCHAR(50) DEFAULT 'password',
    requires_verification BOOLEAN DEFAULT false,
    
    -- Indexes
    UNIQUE(session_id),
    INDEX idx_user_sessions_user_id (user_id),
    INDEX idx_user_sessions_expires_at (expires_at),
    INDEX idx_user_sessions_status (status)
);

-- Security Audit Log for comprehensive logging
CREATE TABLE IF NOT EXISTS security_audit_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(user_id),
    session_id UUID REFERENCES user_sessions(session_id),
    
    -- Event details
    ip_address INET,
    user_agent TEXT,
    endpoint TEXT,
    http_method VARCHAR(10),
    
    -- Event data
    event_data JSONB NOT NULL DEFAULT '{}',
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    
    -- Metadata
    service_name VARCHAR(50) DEFAULT 'user-service',
    trace_id UUID,
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes for performance
    INDEX idx_security_audit_event_type (event_type),
    INDEX idx_security_audit_user_id (user_id),
    INDEX idx_security_audit_created_at (created_at),
    INDEX idx_security_audit_severity (severity)
);

-- Rate Limiting table (backup to Redis)
CREATE TABLE IF NOT EXISTS rate_limit_violations (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL, -- IP, user_id, or other identifier
    identifier_type VARCHAR(50) NOT NULL, -- 'ip', 'user_id', 'email'
    violation_type VARCHAR(50) NOT NULL, -- 'login_attempts', 'api_calls', etc.
    violation_count INTEGER DEFAULT 1,
    first_violation TIMESTAMP DEFAULT NOW(),
    last_violation TIMESTAMP DEFAULT NOW(),
    blocked_until TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints and indexes
    UNIQUE(identifier, identifier_type, violation_type),
    INDEX idx_rate_limit_identifier (identifier),
    INDEX idx_rate_limit_type (violation_type),
    INDEX idx_rate_limit_blocked_until (blocked_until)
);

-- Password Reset Tokens
CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    
    -- Token lifecycle
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    
    -- Security
    ip_address INET,
    user_agent TEXT,
    is_used BOOLEAN DEFAULT false,
    
    -- Constraints
    UNIQUE(token_hash),
    INDEX idx_password_reset_user_id (user_id),
    INDEX idx_password_reset_expires_at (expires_at)
);

-- Email Verification Tokens
CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    token_hash TEXT NOT NULL,
    
    -- Token lifecycle
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    verified_at TIMESTAMP,
    
    -- Metadata
    verification_type VARCHAR(50) DEFAULT 'email_change', -- 'registration', 'email_change'
    is_verified BOOLEAN DEFAULT false,
    
    -- Constraints
    UNIQUE(token_hash),
    INDEX idx_email_verification_user_id (user_id),
    INDEX idx_email_verification_email (email)
);

-- User Permissions table (RBAC)
CREATE TABLE IF NOT EXISTS user_permissions (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Permission details
    resource_type VARCHAR(100) NOT NULL, -- 'users', 'projects', 'workflows'
    resource_id VARCHAR(255), -- Specific resource ID or '*' for all
    permission_type VARCHAR(50) NOT NULL, -- 'read', 'write', 'delete', 'admin'
    
    -- Permission lifecycle
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    granted_by UUID REFERENCES users(user_id),
    revoked_at TIMESTAMP,
    revoked_by UUID REFERENCES users(user_id),
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    
    -- Constraints and indexes
    UNIQUE(user_id, resource_type, resource_id, permission_type),
    INDEX idx_user_permissions_user_id (user_id),
    INDEX idx_user_permissions_resource (resource_type, resource_id),
    INDEX idx_user_permissions_active (is_active)
);

-- CSRF Tokens table
CREATE TABLE IF NOT EXISTS csrf_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    session_id UUID REFERENCES user_sessions(session_id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    
    -- Token details
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    used_at TIMESTAMP,
    is_used BOOLEAN DEFAULT false,
    
    -- Request details
    intended_action VARCHAR(100), -- The action this token is for
    ip_address INET,
    
    -- Constraints
    UNIQUE(token_hash),
    INDEX idx_csrf_tokens_user_id (user_id),
    INDEX idx_csrf_tokens_session_id (session_id),
    INDEX idx_csrf_tokens_expires_at (expires_at)
);

-- Suspicious Activity Detection
CREATE TABLE IF NOT EXISTS suspicious_activities (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    activity_type VARCHAR(100) NOT NULL,
    
    -- Activity details
    description TEXT,
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    ip_address INET,
    user_agent TEXT,
    
    -- Detection details
    detection_rules JSONB DEFAULT '[]',
    false_positive BOOLEAN DEFAULT false,
    investigated BOOLEAN DEFAULT false,
    investigated_by UUID REFERENCES users(user_id),
    investigated_at TIMESTAMP,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_suspicious_activities_user_id (user_id),
    INDEX idx_suspicious_activities_risk_score (risk_score),
    INDEX idx_suspicious_activities_created_at (created_at),
    INDEX idx_suspicious_activities_investigated (investigated)
);

-- Create triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
DROP TRIGGER IF EXISTS update_user_credentials_updated_at ON user_credentials;
CREATE TRIGGER update_user_credentials_updated_at 
    BEFORE UPDATE ON user_credentials 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for password history management
CREATE OR REPLACE FUNCTION check_password_history(
    p_user_id UUID,
    p_new_password_hash TEXT,
    p_history_length INTEGER DEFAULT 5
) RETURNS BOOLEAN AS $$
DECLARE
    password_history JSONB;
BEGIN
    -- Get current password history
    SELECT password_history INTO password_history 
    FROM user_credentials 
    WHERE user_id = p_user_id;
    
    -- Check if new password matches any in history
    IF password_history ? p_new_password_hash THEN
        RETURN FALSE; -- Password was used before
    END IF;
    
    RETURN TRUE; -- Password is new
END;
$$ LANGUAGE plpgsql;

-- Function to add password to history
CREATE OR REPLACE FUNCTION add_to_password_history(
    p_user_id UUID,
    p_password_hash TEXT,
    p_history_length INTEGER DEFAULT 5
) RETURNS VOID AS $$
DECLARE
    current_history JSONB;
    new_history JSONB;
BEGIN
    -- Get current history
    SELECT password_history INTO current_history 
    FROM user_credentials 
    WHERE user_id = p_user_id;
    
    -- Initialize if null
    IF current_history IS NULL THEN
        current_history := '[]'::jsonb;
    END IF;
    
    -- Add new password to beginning of array
    new_history := jsonb_build_array(p_password_hash) || current_history;
    
    -- Trim to max length
    IF jsonb_array_length(new_history) > p_history_length THEN
        new_history := (
            SELECT jsonb_agg(value)
            FROM (
                SELECT value, row_number() OVER () as rn
                FROM jsonb_array_elements(new_history) value
            ) t
            WHERE rn <= p_history_length
        );
    END IF;
    
    -- Update password history
    UPDATE user_credentials 
    SET password_history = new_history,
        last_password_change = NOW()
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Views for security reporting
CREATE OR REPLACE VIEW security_dashboard AS
SELECT 
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM user_sessions WHERE status = 'active' AND expires_at > NOW()) as active_sessions,
    (SELECT COUNT(*) FROM security_audit_log WHERE created_at > NOW() - INTERVAL '24 hours') as events_24h,
    (SELECT COUNT(*) FROM rate_limit_violations WHERE blocked_until > NOW()) as currently_blocked,
    (SELECT COUNT(*) FROM suspicious_activities WHERE created_at > NOW() - INTERVAL '7 days' AND investigated = false) as unresolved_suspicious_activities,
    (SELECT COUNT(*) FROM user_credentials WHERE two_factor_enabled = true) as users_with_2fa;

-- View for session analytics
CREATE OR REPLACE VIEW session_analytics AS
SELECT 
    DATE_TRUNC('hour', created_at) as hour,
    COUNT(*) as sessions_created,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(DISTINCT ip_address) as unique_ips,
    AVG(EXTRACT(EPOCH FROM (last_activity - created_at))/60) as avg_session_duration_minutes
FROM user_sessions
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- Indexes for performance optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_audit_recent ON security_audit_log(created_at) WHERE created_at > NOW() - INTERVAL '30 days';
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_sessions_recent ON user_sessions(created_at, user_id) WHERE created_at > NOW() - INTERVAL '7 days';

-- Comments for documentation
COMMENT ON TABLE user_credentials IS 'Secure storage of user authentication credentials with bcrypt hashing';
COMMENT ON TABLE user_sessions IS 'Active user sessions with comprehensive tracking and security metadata';
COMMENT ON TABLE security_audit_log IS 'Comprehensive security event logging for compliance and monitoring';
COMMENT ON TABLE rate_limit_violations IS 'Rate limiting violations tracking for abuse prevention';
COMMENT ON TABLE user_permissions IS 'Role-based access control permissions for fine-grained security';
COMMENT ON TABLE csrf_tokens IS 'CSRF protection tokens for state-changing operations';
COMMENT ON TABLE suspicious_activities IS 'Automated detection and tracking of suspicious user activities';