-- PostgreSQL Initialization Script for Neliti Database Service
-- Uses existing schemas from src/schemas/postgresql/user_auth_schemas.py

-- Create main database and user
\c postgres postgres;

-- Create database if not exists
SELECT 'CREATE DATABASE neliti_main OWNER neliti_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'neliti_main')\gexec

-- Connect to the main database
\c neliti_main neliti_user;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS auth_system;
CREATE SCHEMA IF NOT EXISTS user_management;
CREATE SCHEMA IF NOT EXISTS ml_metadata;
CREATE SCHEMA IF NOT EXISTS trading_metadata;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA auth_system TO neliti_user;
GRANT ALL PRIVILEGES ON SCHEMA user_management TO neliti_user;
GRANT ALL PRIVILEGES ON SCHEMA ml_metadata TO neliti_user;
GRANT ALL PRIVILEGES ON SCHEMA trading_metadata TO neliti_user;

-- Users table - core user authentication (from existing schemas)
CREATE TABLE IF NOT EXISTS auth_system.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_premium BOOLEAN DEFAULT false,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    verification_token VARCHAR(255),
    verification_expires TIMESTAMP,
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    backup_codes TEXT[],
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
);

-- User sessions table - session management
CREATE TABLE IF NOT EXISTS auth_system.user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    refresh_token VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255),
    device_name VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    location VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT NOW(),
    logout_at TIMESTAMP,
    force_logout BOOLEAN DEFAULT false
);

-- User profiles table - extended user information
CREATE TABLE IF NOT EXISTS user_management.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    phone_number VARCHAR(20),
    date_of_birth DATE,
    country VARCHAR(100),
    timezone VARCHAR(100) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    currency VARCHAR(10) DEFAULT 'USD',
    risk_profile VARCHAR(50) DEFAULT 'moderate',
    trading_experience VARCHAR(50) DEFAULT 'beginner',
    investment_goals TEXT[],
    risk_tolerance INTEGER DEFAULT 5,
    preferred_symbols TEXT[],
    notification_preferences JSONB DEFAULT '{}',
    ui_preferences JSONB DEFAULT '{}',
    avatar_url VARCHAR(500),
    bio TEXT,
    social_links JSONB DEFAULT '{}',
    kyc_status VARCHAR(50) DEFAULT 'pending',
    kyc_documents JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- MT5 accounts table - trading account management
CREATE TABLE IF NOT EXISTS user_management.mt5_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    account_login BIGINT NOT NULL,
    account_server VARCHAR(100) NOT NULL,
    account_name VARCHAR(255),
    account_type VARCHAR(50),
    broker VARCHAR(100),
    currency VARCHAR(10),
    leverage INTEGER,
    balance DECIMAL(15, 2),
    equity DECIMAL(15, 2),
    margin DECIMAL(15, 2),
    free_margin DECIMAL(15, 2),
    margin_level DECIMAL(10, 2),
    profit DECIMAL(15, 2),
    is_active BOOLEAN DEFAULT true,
    is_connected BOOLEAN DEFAULT false,
    last_connection TIMESTAMP,
    connection_status VARCHAR(50) DEFAULT 'disconnected',
    api_credentials JSONB DEFAULT '{}',
    trading_permissions JSONB DEFAULT '{}',
    risk_settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, account_login, account_server)
);

-- API keys table - API access management
CREATE TABLE IF NOT EXISTS auth_system.api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    key_name VARCHAR(100) NOT NULL,
    api_key VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    permissions JSONB DEFAULT '[]',
    scopes TEXT[] DEFAULT '{}',
    allowed_ips TEXT[],
    rate_limit INTEGER DEFAULT 1000,
    requests_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    
    UNIQUE(user_id, key_name)
);

-- User permissions table - granular access control
CREATE TABLE IF NOT EXISTS auth_system.user_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth_system.users(id) ON DELETE CASCADE,
    permission VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    granted_by UUID REFERENCES auth_system.users(id),
    granted_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    
    UNIQUE(user_id, permission, resource_type, resource_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON auth_system.users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON auth_system.users(username);
CREATE INDEX IF NOT EXISTS idx_users_active ON auth_system.users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_role ON auth_system.users(role);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON auth_system.user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON auth_system.user_sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON auth_system.user_sessions(is_active);
CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_management.user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_mt5_accounts_user_id ON user_management.mt5_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_mt5_accounts_login ON user_management.mt5_accounts(account_login);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON auth_system.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON auth_system.api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON auth_system.user_permissions(user_id);

-- Create trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER users_updated_at_trigger
    BEFORE UPDATE ON auth_system.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER user_profiles_updated_at_trigger
    BEFORE UPDATE ON user_management.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER mt5_accounts_updated_at_trigger
    BEFORE UPDATE ON user_management.mt5_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: admin123 - $2b$12$ hash)
INSERT INTO auth_system.users (username, email, password_hash, salt, is_active, is_verified, role) 
VALUES (
    'admin', 
    'admin@neliti.local', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWD3pjmTrLJWfB4u',
    'default_salt',
    true, 
    true,
    'admin'
) ON CONFLICT (username) DO NOTHING;

-- Insert sample user profile for admin
INSERT INTO user_management.user_profiles (user_id, country, risk_profile, trading_experience) 
SELECT u.id, 'Indonesia', 'moderate', 'expert'
FROM auth_system.users u WHERE u.username = 'admin'
ON CONFLICT DO NOTHING;

-- Log completion
SELECT 'PostgreSQL initialization completed successfully - User auth tables created from existing schemas' as status;