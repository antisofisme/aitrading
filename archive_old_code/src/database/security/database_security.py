"""
Database Security and Encryption Manager
Phase 1 Infrastructure Migration - Zero-Trust Security Model

Implements comprehensive database security:
- Field-level encryption for sensitive data
- Row-level security (RLS) for multi-tenancy
- Connection security and authentication
- Audit logging and compliance
- Access control and authorization
"""

import asyncio
import hashlib
import hmac
import secrets
import base64
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import bcrypt
import jwt

from .connection_pooling import DatabaseManager

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for data classification."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""
    AES_256_GCM = "aes_256_gcm"
    RSA_4096 = "rsa_4096"
    FERNET = "fernet"

@dataclass
class SecurityEvent:
    """Security event for audit logging."""
    event_type: str
    user_id: Optional[str]
    event_category: str
    severity: str
    description: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    risk_score: int = 0
    is_suspicious: bool = False

@dataclass
class AccessPolicy:
    """Access control policy definition."""
    resource_type: str
    user_roles: List[str]
    required_permissions: List[str]
    conditions: Dict[str, Any]
    expiry: Optional[datetime] = None

class FieldEncryption:
    """Field-level encryption for sensitive database fields."""

    def __init__(self, master_key: Optional[bytes] = None):
        if master_key:
            self.master_key = master_key
        else:
            self.master_key = Fernet.generate_key()

        self.cipher = Fernet(self.master_key)
        self.rsa_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096
        )
        self.rsa_public_key = self.rsa_key.public_key()

    def encrypt_symmetric(self, data: str) -> str:
        """Encrypt data using symmetric encryption (Fernet)."""
        try:
            encrypted_data = self.cipher.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Symmetric encryption failed: {e}")
            raise

    def decrypt_symmetric(self, encrypted_data: str) -> str:
        """Decrypt data using symmetric encryption."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Symmetric decryption failed: {e}")
            raise

    def encrypt_asymmetric(self, data: str) -> str:
        """Encrypt data using asymmetric encryption (RSA)."""
        try:
            encrypted_data = self.rsa_public_key.encrypt(
                data.encode('utf-8'),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return base64.b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Asymmetric encryption failed: {e}")
            raise

    def decrypt_asymmetric(self, encrypted_data: str) -> str:
        """Decrypt data using asymmetric encryption."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = self.rsa_key.decrypt(
                decoded_data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Asymmetric decryption failed: {e}")
            raise

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False

    def generate_api_key(self) -> str:
        """Generate secure API key."""
        return secrets.token_urlsafe(32)

    def derive_key_from_password(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode('utf-8'))

class JWTManager:
    """JWT token management for authentication and authorization."""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 7

    def create_access_token(self, user_id: str, roles: List[str],
                          permissions: List[str]) -> str:
        """Create JWT access token."""
        payload = {
            "user_id": user_id,
            "roles": roles,
            "permissions": permissions,
            "token_type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # JWT ID for token tracking
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token."""
        payload = {
            "user_id": user_id,
            "token_type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token")

    def refresh_access_token(self, refresh_token: str, roles: List[str],
                           permissions: List[str]) -> str:
        """Create new access token from refresh token."""
        try:
            payload = self.verify_token(refresh_token)

            if payload.get("token_type") != "refresh":
                raise ValueError("Invalid token type")

            return self.create_access_token(
                payload["user_id"], roles, permissions
            )
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise

class AccessControl:
    """Role-based access control (RBAC) and policy enforcement."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.policies: Dict[str, AccessPolicy] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """Load default access control policies."""
        self.policies = {
            "user_data": AccessPolicy(
                resource_type="user_data",
                user_roles=["user", "admin"],
                required_permissions=["read_own_data"],
                conditions={"user_id_match": True}
            ),
            "trading_accounts": AccessPolicy(
                resource_type="trading_accounts",
                user_roles=["user", "premium", "admin"],
                required_permissions=["manage_trading_accounts"],
                conditions={"subscription_active": True}
            ),
            "admin_functions": AccessPolicy(
                resource_type="admin_functions",
                user_roles=["admin"],
                required_permissions=["admin_access"],
                conditions={}
            ),
            "ml_models": AccessPolicy(
                resource_type="ml_models",
                user_roles=["premium", "enterprise", "admin"],
                required_permissions=["access_ml_features"],
                conditions={"subscription_tier": ["premium", "enterprise"]}
            )
        }

    async def check_access(self, user_id: str, resource_type: str,
                          action: str, context: Dict[str, Any] = None) -> bool:
        """Check if user has access to resource."""
        try:
            # Get user information
            user_info = await self._get_user_info(user_id)
            if not user_info:
                return False

            # Get policy for resource
            policy = self.policies.get(resource_type)
            if not policy:
                logger.warning(f"No policy found for resource type: {resource_type}")
                return False

            # Check role membership
            user_roles = user_info.get("roles", [])
            if not any(role in policy.user_roles for role in user_roles):
                return False

            # Check permissions
            user_permissions = user_info.get("permissions", [])
            if not any(perm in user_permissions for perm in policy.required_permissions):
                return False

            # Check conditions
            if not await self._evaluate_conditions(policy.conditions, user_info, context):
                return False

            # Check policy expiry
            if policy.expiry and datetime.utcnow() > policy.expiry:
                return False

            return True

        except Exception as e:
            logger.error(f"Access check failed: {e}")
            return False

    async def _get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information including roles and permissions."""
        try:
            query = """
            SELECT
                u.id, u.email, u.is_active, u.is_verified,
                us.status as subscription_status,
                st.name as subscription_tier,
                st.features
            FROM users u
            LEFT JOIN user_subscriptions us ON u.id = us.user_id AND us.status = 'active'
            LEFT JOIN subscription_tiers st ON us.tier_id = st.id
            WHERE u.id = $1
            """

            result = await self.db_manager.postgresql.execute_query(query, user_id)
            if not result:
                return None

            user_data = result[0]

            # Determine roles based on subscription and status
            roles = ["user"]
            if user_data["subscription_tier"] == "premium":
                roles.append("premium")
            elif user_data["subscription_tier"] == "enterprise":
                roles.extend(["premium", "enterprise"])

            if user_data["email"].endswith("@aitrading.local"):  # Admin check
                roles.append("admin")

            # Determine permissions
            permissions = ["read_own_data"]
            if user_data["subscription_status"] == "active":
                permissions.append("manage_trading_accounts")

                if user_data["subscription_tier"] in ["premium", "enterprise"]:
                    permissions.append("access_ml_features")

                if user_data["subscription_tier"] == "enterprise":
                    permissions.extend(["api_access", "custom_models"])

            if "admin" in roles:
                permissions.append("admin_access")

            return {
                "user_id": user_data["id"],
                "email": user_data["email"],
                "is_active": user_data["is_active"],
                "is_verified": user_data["is_verified"],
                "subscription_tier": user_data["subscription_tier"],
                "subscription_status": user_data["subscription_status"],
                "roles": roles,
                "permissions": permissions,
                "features": user_data["features"] or {}
            }

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    async def _evaluate_conditions(self, conditions: Dict[str, Any],
                                 user_info: Dict[str, Any],
                                 context: Dict[str, Any] = None) -> bool:
        """Evaluate access control conditions."""
        if not conditions:
            return True

        context = context or {}

        for condition, expected_value in conditions.items():
            if condition == "user_id_match":
                # Check if accessing own data
                resource_user_id = context.get("resource_user_id")
                if resource_user_id and resource_user_id != user_info["user_id"]:
                    return False

            elif condition == "subscription_active":
                if user_info.get("subscription_status") != "active":
                    return False

            elif condition == "subscription_tier":
                user_tier = user_info.get("subscription_tier")
                if user_tier not in expected_value:
                    return False

        return True

class SecurityEventLogger:
    """Security event logging and monitoring."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def log_security_event(self, event: SecurityEvent) -> bool:
        """Log security event to database."""
        try:
            query = """
            INSERT INTO security_events (
                user_id, event_type, event_category, severity,
                description, details, ip_address, user_agent,
                session_id, risk_score, is_suspicious
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """

            await self.db_manager.postgresql.execute_query(
                query,
                event.user_id,
                event.event_type,
                event.event_category,
                event.severity,
                event.description,
                json.dumps(event.details),
                event.ip_address,
                event.user_agent,
                event.session_id,
                event.risk_score,
                event.is_suspicious
            )

            # Also log to ClickHouse for analytics
            if self.db_manager.clickhouse:
                await self._log_to_clickhouse(event)

            return True

        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False

    async def _log_to_clickhouse(self, event: SecurityEvent):
        """Log security event to ClickHouse for analytics."""
        try:
            clickhouse_data = {
                'timestamp': datetime.utcnow(),
                'service_name': 'security_manager',
                'log_level': 'INFO' if event.severity in ['info', 'warning'] else 'ERROR',
                'user_id': event.user_id or '',
                'session_id': event.session_id or '',
                'message': f"{event.event_type}: {event.description}",
                'details': json.dumps(event.details),
                'context': json.dumps({
                    'event_category': event.event_category,
                    'severity': event.severity,
                    'risk_score': event.risk_score,
                    'is_suspicious': event.is_suspicious
                }),
                'error_category': event.event_category if event.severity == 'error' else '',
                'hostname': event.details.get('hostname', ''),
                'process_id': event.details.get('process_id', 0),
                'thread_id': event.details.get('thread_id', 0)
            }

            await self.db_manager.clickhouse.insert_data('logs_hot', [clickhouse_data])

        except Exception as e:
            logger.error(f"Failed to log security event to ClickHouse: {e}")

    async def get_security_events(self, user_id: Optional[str] = None,
                                event_type: Optional[str] = None,
                                severity: Optional[str] = None,
                                start_time: Optional[datetime] = None,
                                limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve security events with filtering."""
        try:
            conditions = []
            params = []
            param_count = 0

            if user_id:
                param_count += 1
                conditions.append(f"user_id = ${param_count}")
                params.append(user_id)

            if event_type:
                param_count += 1
                conditions.append(f"event_type = ${param_count}")
                params.append(event_type)

            if severity:
                param_count += 1
                conditions.append(f"severity = ${param_count}")
                params.append(severity)

            if start_time:
                param_count += 1
                conditions.append(f"created_at >= ${param_count}")
                params.append(start_time)

            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

            param_count += 1
            params.append(limit)

            query = f"""
            SELECT *
            FROM security_events
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count}
            """

            return await self.db_manager.postgresql.execute_query(query, *params)

        except Exception as e:
            logger.error(f"Failed to retrieve security events: {e}")
            return []

class DatabaseSecurity:
    """Main database security manager."""

    def __init__(self, db_manager: DatabaseManager, secret_key: str):
        self.db_manager = db_manager
        self.field_encryption = FieldEncryption()
        self.jwt_manager = JWTManager(secret_key)
        self.access_control = AccessControl(db_manager)
        self.security_logger = SecurityEventLogger(db_manager)

    async def initialize(self):
        """Initialize database security components."""
        try:
            # Set up RLS policies
            await self._setup_rls_policies()

            # Create security roles
            await self._create_security_roles()

            # Initialize audit logging
            await self._initialize_audit_logging()

            logger.info("Database security initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database security: {e}")
            raise

    async def _setup_rls_policies(self):
        """Set up Row Level Security policies."""
        try:
            # Enable RLS on all user tables
            rls_tables = [
                'users', 'user_subscriptions', 'user_tokens', 'user_sessions',
                'trading_accounts', 'user_preferences'
            ]

            for table in rls_tables:
                await self.db_manager.postgresql.execute_query(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")

            # Set current user context function
            await self.db_manager.postgresql.execute_query("""
            CREATE OR REPLACE FUNCTION set_current_user_id(user_id UUID)
            RETURNS void AS $$
            BEGIN
                PERFORM set_config('app.current_user_id', user_id::text, false);
            END;
            $$ LANGUAGE plpgsql SECURITY DEFINER;
            """)

        except Exception as e:
            logger.error(f"Failed to setup RLS policies: {e}")
            raise

    async def _create_security_roles(self):
        """Create database security roles."""
        try:
            roles = ['authenticated_users', 'api_service', 'admin_service']

            for role in roles:
                await self.db_manager.postgresql.execute_query(f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{role}') THEN
                        CREATE ROLE {role};
                    END IF;
                END
                $$;
                """)

        except Exception as e:
            logger.error(f"Failed to create security roles: {e}")
            raise

    async def _initialize_audit_logging(self):
        """Initialize audit logging triggers."""
        try:
            # Create audit log function
            await self.db_manager.postgresql.execute_query("""
            CREATE OR REPLACE FUNCTION audit_trigger_function()
            RETURNS TRIGGER AS $$
            BEGIN
                INSERT INTO security_events (
                    user_id, event_type, event_category, severity,
                    description, details
                ) VALUES (
                    current_setting('app.current_user_id', true)::UUID,
                    TG_OP,
                    'data_access',
                    'info',
                    'Database operation on ' || TG_TABLE_NAME,
                    jsonb_build_object(
                        'table', TG_TABLE_NAME,
                        'operation', TG_OP,
                        'timestamp', NOW()
                    )
                );

                IF TG_OP = 'DELETE' THEN
                    RETURN OLD;
                ELSE
                    RETURN NEW;
                END IF;
            END;
            $$ LANGUAGE plpgsql;
            """)

            # Add audit triggers to sensitive tables
            sensitive_tables = ['trading_accounts', 'user_subscriptions']

            for table in sensitive_tables:
                await self.db_manager.postgresql.execute_query(f"""
                DROP TRIGGER IF EXISTS audit_trigger ON {table};
                CREATE TRIGGER audit_trigger
                    AFTER INSERT OR UPDATE OR DELETE ON {table}
                    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
                """)

        except Exception as e:
            logger.error(f"Failed to initialize audit logging: {e}")
            raise

    async def encrypt_trading_credentials(self, login: str, password: str, server: str) -> Tuple[str, str, str]:
        """Encrypt MT5 trading credentials."""
        try:
            encrypted_login = self.field_encryption.encrypt_symmetric(login)
            encrypted_password = self.field_encryption.encrypt_symmetric(password)
            encrypted_server = self.field_encryption.encrypt_symmetric(server)

            return encrypted_login, encrypted_password, encrypted_server

        except Exception as e:
            logger.error(f"Failed to encrypt trading credentials: {e}")
            raise

    async def decrypt_trading_credentials(self, encrypted_login: str,
                                        encrypted_password: str,
                                        encrypted_server: str) -> Tuple[str, str, str]:
        """Decrypt MT5 trading credentials."""
        try:
            login = self.field_encryption.decrypt_symmetric(encrypted_login)
            password = self.field_encryption.decrypt_symmetric(encrypted_password)
            server = self.field_encryption.decrypt_symmetric(encrypted_server)

            return login, password, server

        except Exception as e:
            logger.error(f"Failed to decrypt trading credentials: {e}")
            raise

    async def authenticate_user(self, email: str, password: str,
                              ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """Authenticate user and return tokens."""
        try:
            # Get user from database
            query = """
            SELECT id, email, password_hash, is_active, is_verified, failed_login_attempts, locked_until
            FROM users
            WHERE email = $1 AND deleted_at IS NULL
            """

            result = await self.db_manager.postgresql.execute_query(query, email)
            if not result:
                await self._log_failed_login(None, email, ip_address, "user_not_found")
                return None

            user_data = result[0]
            user_id = user_data['id']

            # Check if account is locked
            if user_data['locked_until'] and datetime.now() < user_data['locked_until']:
                await self._log_failed_login(user_id, email, ip_address, "account_locked")
                return None

            # Check if account is active and verified
            if not user_data['is_active'] or not user_data['is_verified']:
                await self._log_failed_login(user_id, email, ip_address, "account_inactive")
                return None

            # Verify password
            if not self.field_encryption.verify_password(password, user_data['password_hash']):
                await self._handle_failed_login(user_id, email, ip_address)
                return None

            # Reset failed login attempts on successful login
            await self._reset_failed_login_attempts(user_id)

            # Get user info for token creation
            user_info = await self.access_control._get_user_info(user_id)
            if not user_info:
                return None

            # Create tokens
            access_token = self.jwt_manager.create_access_token(
                user_id, user_info['roles'], user_info['permissions']
            )
            refresh_token = self.jwt_manager.create_refresh_token(user_id)

            # Log successful login
            await self.security_logger.log_security_event(SecurityEvent(
                event_type="login_success",
                user_id=user_id,
                event_category="authentication",
                severity="info",
                description="User logged in successfully",
                details={"email": email, "roles": user_info['roles']},
                ip_address=ip_address,
                user_agent=user_agent
            ))

            return {
                "user_id": user_id,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_info": user_info
            }

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            await self._log_failed_login(None, email, ip_address, "system_error")
            return None

    async def _log_failed_login(self, user_id: str, email: str, ip_address: str, reason: str):
        """Log failed login attempt."""
        await self.security_logger.log_security_event(SecurityEvent(
            event_type="login_failed",
            user_id=user_id,
            event_category="authentication",
            severity="warning",
            description=f"Failed login attempt: {reason}",
            details={"email": email, "reason": reason},
            ip_address=ip_address,
            is_suspicious=True,
            risk_score=50
        ))

    async def _handle_failed_login(self, user_id: str, email: str, ip_address: str):
        """Handle failed login attempt with account locking."""
        try:
            # Increment failed login attempts
            query = """
            UPDATE users
            SET failed_login_attempts = failed_login_attempts + 1,
                locked_until = CASE
                    WHEN failed_login_attempts >= 4 THEN NOW() + INTERVAL '30 minutes'
                    ELSE NULL
                END
            WHERE id = $1
            RETURNING failed_login_attempts
            """

            result = await self.db_manager.postgresql.execute_query(query, user_id)
            failed_attempts = result[0]['failed_login_attempts'] if result else 0

            severity = "critical" if failed_attempts >= 5 else "warning"
            await self._log_failed_login(user_id, email, ip_address, "invalid_password")

        except Exception as e:
            logger.error(f"Failed to handle failed login: {e}")

    async def _reset_failed_login_attempts(self, user_id: str):
        """Reset failed login attempts after successful login."""
        try:
            query = """
            UPDATE users
            SET failed_login_attempts = 0, locked_until = NULL, last_login_at = NOW()
            WHERE id = $1
            """
            await self.db_manager.postgresql.execute_query(query, user_id)
        except Exception as e:
            logger.error(f"Failed to reset failed login attempts: {e}")

    async def check_permission(self, user_id: str, resource_type: str,
                             action: str, context: Dict[str, Any] = None) -> bool:
        """Check if user has permission for action on resource."""
        return await self.access_control.check_access(user_id, resource_type, action, context)

    async def health_check(self) -> Dict[str, Any]:
        """Perform security health check."""
        health = {
            'encryption': 'healthy',
            'access_control': 'healthy',
            'audit_logging': 'healthy',
            'status': 'healthy'
        }

        try:
            # Test encryption
            test_data = "security_test"
            encrypted = self.field_encryption.encrypt_symmetric(test_data)
            decrypted = self.field_encryption.decrypt_symmetric(encrypted)

            if decrypted != test_data:
                health['encryption'] = 'unhealthy'
                health['status'] = 'degraded'

            # Test access control
            test_user_info = await self.access_control._get_user_info("test_user_id")
            if test_user_info is None:
                health['access_control'] = 'warning'

            # Test audit logging
            test_event = SecurityEvent(
                event_type="health_check",
                user_id=None,
                event_category="system",
                severity="info",
                description="Security health check",
                details={"test": True}
            )

            logged = await self.security_logger.log_security_event(test_event)
            if not logged:
                health['audit_logging'] = 'unhealthy'
                health['status'] = 'degraded'

        except Exception as e:
            health['status'] = 'unhealthy'
            health['error'] = str(e)

        return health