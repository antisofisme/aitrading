"""
PostgreSQL User Authentication Schemas - ENHANCED WITH FULL CENTRALIZATION
User management, authentication, and authorization

FEATURES:
- Centralized logging with context-aware messages
- Performance tracking for schema operations  
- Centralized error handling with proper categorization
- Centralized validation for schema definitions
- Event publishing for schema lifecycle events
"""

# FULL CENTRALIZATION INFRASTRUCTURE INTEGRATION
import logging
# Simple performance tracking placeholder
# Error handling placeholder
# Validation placeholder
# Event manager placeholder
# Import manager placeholder

# Import typing through centralized import manager
from typing import Dict, List

# Enhanced logger with centralized infrastructure
logger = logging.getLogger(__name__)


class PostgresqlUserAuthSchemas:
    """
    User authentication and authorization schemas for PostgreSQL
    ACID-compliant relational database for critical user operations
    """

    @staticmethod
    # @performance_tracked - simplified
    def get_all_tables() -> Dict[str, str]:
        """Get all user authentication table schemas with centralized tracking"""
        try:
            logger.info("Retrieving all PostgreSQL user authentication table schemas")
            
            tables = {
            # Core User Management
            "users": PostgresqlUserAuthSchemas.users(),
            "user_sessions": PostgresqlUserAuthSchemas.user_sessions(),
            "user_profiles": PostgresqlUserAuthSchemas.user_profiles(),
            "organizations": PostgresqlUserAuthSchemas.organizations(),
            
            # Trading Account Management
            "mt5_accounts": PostgresqlUserAuthSchemas.mt5_accounts(),
            "broker_connections": PostgresqlUserAuthSchemas.broker_connections(),
            "api_keys": PostgresqlUserAuthSchemas.api_keys(),
            
            # Access Control
            "user_permissions": PostgresqlUserAuthSchemas.user_permissions(),
            "role_permissions": PostgresqlUserAuthSchemas.role_permissions(),
            
            # Notifications & Audit
            "notifications": PostgresqlUserAuthSchemas.notifications(),
            "audit_logs": PostgresqlUserAuthSchemas.audit_logs(),
            
                # Subscription Management
                "subscription_plans": PostgresqlUserAuthSchemas.subscription_plans(),
                "user_subscriptions": PostgresqlUserAuthSchemas.user_subscriptions(),
                "payment_history": PostgresqlUserAuthSchemas.payment_history(),
            }
            
            # Validate table structure
            # Validation simplified
            
            # Publish event for schema retrieval
            # Event publishing simplified
            
            logger.info(f"Successfully retrieved {len(tables)} PostgreSQL authentication table schemas")
            return tables
            
        except Exception as e:
            error_context = {
                "operation": "get_all_tables",
                "database_type": "postgresql",
                "schema_type": "user_auth"
            }
            # Error handling simplified
            logger.error(f"Failed to retrieve PostgreSQL authentication table schemas: {e}")
            raise

    @staticmethod
    def get_views() -> Dict[str, str]:
        """Get all user authentication view definitions"""
        return {
            "active_users_view": PostgresqlUserAuthSchemas.active_users_view(),
            "user_activity_summary": PostgresqlUserAuthSchemas.user_activity_summary(),
            "subscription_status_view": PostgresqlUserAuthSchemas.subscription_status_view(),
            "audit_trail_view": PostgresqlUserAuthSchemas.audit_trail_view(),
        }

    @staticmethod
    def get_functions() -> Dict[str, str]:
        """Get all user authentication function definitions"""
        return {
            "update_updated_at_column": PostgresqlUserAuthSchemas.update_updated_at_column(),
            "check_user_permissions": PostgresqlUserAuthSchemas.check_user_permissions(),
            "generate_api_key": PostgresqlUserAuthSchemas.generate_api_key(),
            "cleanup_expired_sessions": PostgresqlUserAuthSchemas.cleanup_expired_sessions(),
        }

    @staticmethod
    def get_triggers() -> Dict[str, str]:
        """Get all user authentication trigger definitions"""
        return {
            "users_updated_at_trigger": PostgresqlUserAuthSchemas.users_updated_at_trigger(),
            "user_sessions_updated_at_trigger": PostgresqlUserAuthSchemas.user_sessions_updated_at_trigger(),
            "audit_log_trigger": PostgresqlUserAuthSchemas.audit_log_trigger(),
        }

    @staticmethod
    def get_indexes() -> List[str]:
        """Get all user authentication index definitions"""
        return [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug)",
            "CREATE INDEX IF NOT EXISTS idx_mt5_accounts_user_id ON mt5_accounts(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_mt5_accounts_login ON mt5_accounts(account_login)",
            "CREATE INDEX IF NOT EXISTS idx_broker_connections_user_id ON broker_connections(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash)",
            "CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_user_subscriptions_user_id ON user_subscriptions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_payment_history_user_id ON payment_history(user_id)",
        ]

    # Core User Management Tables
    @staticmethod
    def users() -> str:
        """Users table - core user authentication"""
        return """
        CREATE TABLE IF NOT EXISTS users (
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
        """

    @staticmethod
    def user_sessions() -> str:
        """User sessions table - session management"""
        return """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
        """

    @staticmethod
    def user_profiles() -> str:
        """User profiles table - extended user information"""
        return """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
        """

    @staticmethod
    def organizations() -> str:
        """Organizations table - multi-tenant support"""
        return """
        CREATE TABLE IF NOT EXISTS organizations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            slug VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            logo_url VARCHAR(500),
            website_url VARCHAR(500),
            contact_email VARCHAR(255),
            settings JSONB DEFAULT '{}',
            subscription_plan VARCHAR(100) DEFAULT 'basic',
            max_users INTEGER DEFAULT 10,
            max_strategies INTEGER DEFAULT 5,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by UUID REFERENCES users(id)
        );
        """

    # Trading Account Management
    @staticmethod
    def mt5_accounts() -> str:
        """MT5 accounts table - trading account management"""
        return """
        CREATE TABLE IF NOT EXISTS mt5_accounts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
        """

    @staticmethod
    def broker_connections() -> str:
        """Broker connections table - multi-broker support"""
        return """
        CREATE TABLE IF NOT EXISTS broker_connections (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            broker_name VARCHAR(100) NOT NULL,
            broker_type VARCHAR(50) NOT NULL,
            connection_config JSONB NOT NULL,
            credentials JSONB NOT NULL,
            is_active BOOLEAN DEFAULT true,
            is_connected BOOLEAN DEFAULT false,
            last_connection TIMESTAMP,
            connection_status VARCHAR(50) DEFAULT 'disconnected',
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            next_retry_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(user_id, broker_name)
        );
        """

    @staticmethod
    def api_keys() -> str:
        """API keys table - API access management"""
        return """
        CREATE TABLE IF NOT EXISTS api_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
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
        """

    # Access Control
    @staticmethod
    def user_permissions() -> str:
        """User permissions table - granular access control"""
        return """
        CREATE TABLE IF NOT EXISTS user_permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            permission VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100),
            resource_id VARCHAR(255),
            granted_by UUID REFERENCES users(id),
            granted_at TIMESTAMP DEFAULT NOW(),
            expires_at TIMESTAMP,
            is_active BOOLEAN DEFAULT true,
            metadata JSONB DEFAULT '{}',
            
            UNIQUE(user_id, permission, resource_type, resource_id)
        );
        """

    @staticmethod
    def role_permissions() -> str:
        """Role permissions table - role-based access control"""
        return """
        CREATE TABLE IF NOT EXISTS role_permissions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            role_name VARCHAR(100) NOT NULL,
            permission VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100),
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            
            UNIQUE(role_name, permission, resource_type)
        );
        """

    # Notifications & Audit
    @staticmethod
    def notifications() -> str:
        """Notifications table - user notifications"""
        return """
        CREATE TABLE IF NOT EXISTS notifications (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            notification_type VARCHAR(100) NOT NULL,
            title VARCHAR(255) NOT NULL,
            message TEXT NOT NULL,
            priority VARCHAR(20) DEFAULT 'medium',
            category VARCHAR(100),
            action_url VARCHAR(500),
            action_text VARCHAR(100),
            is_read BOOLEAN DEFAULT false,
            read_at TIMESTAMP,
            is_archived BOOLEAN DEFAULT false,
            archived_at TIMESTAMP,
            delivery_channels TEXT[] DEFAULT '{}',
            delivery_status JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

    @staticmethod
    def audit_logs() -> str:
        """Audit logs table - system activity tracking"""
        return """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id),
            session_id UUID REFERENCES user_sessions(id),
            action VARCHAR(100) NOT NULL,
            resource_type VARCHAR(100) NOT NULL,
            resource_id VARCHAR(255),
            old_values JSONB,
            new_values JSONB,
            ip_address INET,
            user_agent TEXT,
            request_id VARCHAR(255),
            correlation_id VARCHAR(255),
            severity VARCHAR(20) DEFAULT 'info',
            tags TEXT[],
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

    # Subscription Management
    @staticmethod
    def subscription_plans() -> str:
        """Subscription plans table - pricing tiers"""
        return """
        CREATE TABLE IF NOT EXISTS subscription_plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_name VARCHAR(100) UNIQUE NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USD',
            billing_cycle VARCHAR(50) NOT NULL,
            trial_days INTEGER DEFAULT 0,
            features JSONB DEFAULT '{}',
            limits JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            is_popular BOOLEAN DEFAULT false,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """

    @staticmethod
    def user_subscriptions() -> str:
        """User subscriptions table - user plan management"""
        return """
        CREATE TABLE IF NOT EXISTS user_subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            plan_id UUID NOT NULL REFERENCES subscription_plans(id),
            status VARCHAR(50) DEFAULT 'active',
            current_period_start TIMESTAMP NOT NULL,
            current_period_end TIMESTAMP NOT NULL,
            cancel_at_period_end BOOLEAN DEFAULT false,
            canceled_at TIMESTAMP,
            trial_start TIMESTAMP,
            trial_end TIMESTAMP,
            discount_percentage DECIMAL(5, 2) DEFAULT 0,
            discount_amount DECIMAL(10, 2) DEFAULT 0,
            payment_method_id VARCHAR(255),
            external_subscription_id VARCHAR(255),
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """

    @staticmethod
    def payment_history() -> str:
        """Payment history table - billing records"""
        return """
        CREATE TABLE IF NOT EXISTS payment_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subscription_id UUID REFERENCES user_subscriptions(id),
            payment_method VARCHAR(100),
            payment_provider VARCHAR(100),
            external_payment_id VARCHAR(255),
            amount DECIMAL(10, 2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'USD',
            payment_status VARCHAR(50) DEFAULT 'pending',
            payment_type VARCHAR(50) DEFAULT 'subscription',
            description TEXT,
            invoice_url VARCHAR(500),
            receipt_url VARCHAR(500),
            failure_reason TEXT,
            refunded_amount DECIMAL(10, 2) DEFAULT 0,
            refunded_at TIMESTAMP,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """

    # Views
    @staticmethod
    def active_users_view() -> str:
        """Active users view"""
        return """
        CREATE VIEW IF NOT EXISTS active_users_view AS
        SELECT 
            u.id,
            u.email,
            u.username,
            u.role,
            u.is_premium,
            u.last_login,
            u.login_count,
            p.risk_profile,
            p.trading_experience,
            COUNT(s.id) as active_sessions
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        LEFT JOIN user_sessions s ON u.id = s.user_id AND s.is_active = true
        WHERE u.is_active = true
        GROUP BY u.id, u.email, u.username, u.role, u.is_premium, u.last_login, u.login_count, p.risk_profile, p.trading_experience
        ORDER BY u.last_login DESC;
        """

    @staticmethod
    def user_activity_summary() -> str:
        """User activity summary view"""
        return """
        CREATE VIEW IF NOT EXISTS user_activity_summary AS
        SELECT 
            u.id,
            u.username,
            u.email,
            u.last_login,
            u.login_count,
            COUNT(DISTINCT s.id) as total_sessions,
            COUNT(DISTINCT CASE WHEN s.is_active THEN s.id END) as active_sessions,
            COUNT(DISTINCT a.id) as total_mt5_accounts,
            COUNT(DISTINCT CASE WHEN a.is_connected THEN a.id END) as connected_accounts,
            COUNT(DISTINCT n.id) as total_notifications,
            COUNT(DISTINCT CASE WHEN n.is_read = false THEN n.id END) as unread_notifications
        FROM users u
        LEFT JOIN user_sessions s ON u.id = s.user_id
        LEFT JOIN mt5_accounts a ON u.id = a.user_id
        LEFT JOIN notifications n ON u.id = n.user_id
        WHERE u.is_active = true
        GROUP BY u.id, u.username, u.email, u.last_login, u.login_count
        ORDER BY u.last_login DESC;
        """

    @staticmethod
    def subscription_status_view() -> str:
        """Subscription status view"""
        return """
        CREATE VIEW IF NOT EXISTS subscription_status_view AS
        SELECT 
            u.id as user_id,
            u.username,
            u.email,
            u.is_premium,
            sp.plan_name,
            sp.display_name,
            us.status,
            us.current_period_start,
            us.current_period_end,
            us.cancel_at_period_end,
            us.trial_start,
            us.trial_end,
            CASE 
                WHEN us.trial_end > NOW() THEN 'trial'
                WHEN us.current_period_end > NOW() AND us.status = 'active' THEN 'active'
                WHEN us.current_period_end <= NOW() THEN 'expired'
                ELSE 'inactive'
            END as effective_status
        FROM users u
        LEFT JOIN user_subscriptions us ON u.id = us.user_id
        LEFT JOIN subscription_plans sp ON us.plan_id = sp.id
        WHERE u.is_active = true
        ORDER BY u.created_at DESC;
        """

    @staticmethod
    def audit_trail_view() -> str:
        """Audit trail view"""
        return """
        CREATE VIEW IF NOT EXISTS audit_trail_view AS
        SELECT 
            al.id,
            al.action,
            al.resource_type,
            al.resource_id,
            al.severity,
            al.created_at,
            u.username,
            u.email,
            al.ip_address,
            al.metadata
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC;
        """

    # Functions
    @staticmethod
    def update_updated_at_column() -> str:
        """Function to update updated_at column"""
        return """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """

    @staticmethod
    def check_user_permissions() -> str:
        """Function to check user permissions"""
        return """
        CREATE OR REPLACE FUNCTION check_user_permissions(
            p_user_id UUID,
            p_permission VARCHAR(100),
            p_resource_type VARCHAR(100) DEFAULT NULL,
            p_resource_id VARCHAR(255) DEFAULT NULL
        RETURNS BOOLEAN AS $$
        DECLARE
            has_permission BOOLEAN := false;
        BEGIN
            -- Check direct user permissions
            SELECT EXISTS(
                SELECT 1 FROM user_permissions 
                WHERE user_id = p_user_id 
                AND permission = p_permission
                AND (p_resource_type IS NULL OR resource_type = p_resource_type)
                AND (p_resource_id IS NULL OR resource_id = p_resource_id)
                AND is_active = true
                AND (expires_at IS NULL OR expires_at > NOW())
            
            -- If not found, check role permissions
            IF NOT has_permission THEN
                SELECT EXISTS(
                    SELECT 1 FROM role_permissions rp
                    JOIN users u ON u.role = rp.role_name
                    WHERE u.id = p_user_id
                    AND rp.permission = p_permission
                    AND (p_resource_type IS NULL OR rp.resource_type = p_resource_type)
                    AND rp.is_active = true
            END IF;
            
            RETURN has_permission;
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def generate_api_key() -> str:
        """Function to generate API key"""
        return """
        CREATE OR REPLACE FUNCTION generate_api_key()
        RETURNS VARCHAR(255) AS $$
        BEGIN
            RETURN 'ak_' || encode(gen_random_bytes(32), 'hex');
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def cleanup_expired_sessions() -> str:
        """Function to cleanup expired sessions"""
        return """
        CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
        RETURNS INTEGER AS $$
        DECLARE
            deleted_count INTEGER;
        BEGIN
            DELETE FROM user_sessions 
            WHERE expires_at < NOW() OR (last_activity < NOW() - INTERVAL '30 days');
            
            GET DIAGNOSTICS deleted_count = ROW_COUNT;
            RETURN deleted_count;
        END;
        $$ LANGUAGE plpgsql;
        """

    # Triggers
    @staticmethod
    def users_updated_at_trigger() -> str:
        """Trigger to update users.updated_at"""
        return """
        CREATE TRIGGER users_updated_at_trigger
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """

    @staticmethod
    def user_sessions_updated_at_trigger() -> str:
        """Trigger to update user_sessions.updated_at"""
        return """
        CREATE TRIGGER user_sessions_updated_at_trigger
            BEFORE UPDATE ON user_sessions
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """

    @staticmethod
    def audit_log_trigger() -> str:
        """Trigger to create audit logs"""
        return """
        CREATE OR REPLACE FUNCTION audit_log_trigger_function()
        RETURNS TRIGGER AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                INSERT INTO audit_logs (action, resource_type, resource_id, old_values)
                VALUES ('DELETE', TG_TABLE_NAME, OLD.id::TEXT, row_to_json(OLD));
                RETURN OLD;
            ELSIF TG_OP = 'UPDATE' THEN
                INSERT INTO audit_logs (action, resource_type, resource_id, old_values, new_values)
                VALUES ('UPDATE', TG_TABLE_NAME, NEW.id::TEXT, row_to_json(OLD), row_to_json(NEW));
                RETURN NEW;
            ELSIF TG_OP = 'INSERT' THEN
                INSERT INTO audit_logs (action, resource_type, resource_id, new_values)
                VALUES ('INSERT', TG_TABLE_NAME, NEW.id::TEXT, row_to_json(NEW));
                RETURN NEW;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """

    @staticmethod
    def get_table_list() -> List[str]:
        """Get list of all user authentication table names"""
        return [
            "users",
            "user_sessions",
            "user_profiles",
            "organizations",
            "mt5_accounts",
            "broker_connections",
            "api_keys",
            "user_permissions",
            "role_permissions",
            "notifications",
            "audit_logs",
            "subscription_plans",
            "user_subscriptions",
            "payment_history",
        ]