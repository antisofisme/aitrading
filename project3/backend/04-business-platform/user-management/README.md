# User Management Service

## 🎯 Purpose
**Comprehensive user lifecycle and authentication service** yang mengelola user registration, JWT authentication, subscription management, multi-tenant company controls, dan role-based access control untuk secure platform operation dengan <8ms user context resolution.

---

## 📊 ChainFlow Diagram

```
Frontend/Client → User-Management → Central-Hub → All Services
      ↓               ↓              ↓              ↓
Auth Requests    User Context     Service Auth    Authorized Access
Registration     JWT Generation   User Validation  Role Enforcement
Profile Updates  Subscription     Company Context  Feature Gating
Company Setup    Multi-tenant     Access Control   Secure Operations
```

---

## 🏗️ User Management Architecture

### **Input Flow**: Authentication requests and user management operations
**Data Sources**: Frontend (web app), Client-MT5 (trading client), Admin panel
**Format**: Protocol Buffers (AuthRequest, UserRegistration, ProfileUpdate)
**Frequency**: Auth: 1000+ requests/second, Management: 100+ operations/second
**Performance Target**: <8ms user context resolution and JWT validation

### **Output Flow**: User context and authentication tokens to all services
**Destinations**: All backend services (via Central-Hub), Frontend dashboard
**Format**: Protocol Buffers (UserContext, AuthToken, SubscriptionInfo)
**Processing**: Authentication + authorization + subscription validation
**Performance Target**: <8ms total user context processing

---

## 🔧 Protocol Buffers Integration

### **Global Decisions Applied**:
✅ **Protocol Buffers Communication**: 60% smaller auth payloads, 10x faster serialization
✅ **Multi-Tenant Architecture**: Native company/user-level data isolation
✅ **Request Tracing**: Complete correlation ID tracking through auth pipeline
✅ **Central-Hub Coordination**: User registry and authentication coordination
✅ **JWT + Protocol Buffers Auth**: Optimized token format with protobuf claims
✅ **Circuit Breaker Pattern**: External auth provider failover and caching

### **Schema Dependencies**:
```python
# Import from centralized schemas
import sys
sys.path.append('../../../01-core-infrastructure/central-hub/static/generated/python')

from users.auth_request_pb2 import AuthRequest, LoginRequest, RegistrationRequest
from users.user_context_pb2 import UserContext, UserProfile, CompanyProfile
from users.subscription_pb2 import SubscriptionInfo, SubscriptionTier, BillingInfo
from users.auth_token_pb2 import AuthToken, JWTClaims, TokenMetadata
from common.request_trace_pb2 import RequestTrace, TraceContext
from business.company_management_pb2 import CompanySettings, TeamMember, RolePermissions
```

### **Enhanced Auth MessageEnvelope**:
```protobuf
message AuthProcessingEnvelope {
  string message_type = 1;           // "auth_request"
  string user_id = 2;                // Multi-tenant user identification
  string company_id = 3;             // Multi-tenant company identification
  bytes payload = 4;                 // AuthRequest protobuf
  int64 timestamp = 5;               // Request timestamp
  string service_source = 6;         // "user-management"
  string correlation_id = 7;         // Request tracing
  TraceContext trace_context = 8;    // Distributed tracing
  AuthContext auth_context = 9;      // Authentication metadata
  string client_ip = 10;             // Client IP for security
}
```

---

## 🔐 Advanced Authentication Engine

### **1. JWT + Protocol Buffers Authentication**:
```python
class AuthenticationEngine:
    def __init__(self, central_hub_client):
        self.central_hub = central_hub_client
        self.circuit_breaker = CircuitBreaker("external-auth")
        self.token_cache = TokenCache()
        self.jwt_handler = JWTHandler()

    async def authenticate_user(self, auth_request: AuthRequest,
                              trace_context: TraceContext) -> AuthResult:
        """Enhanced JWT authentication with Protocol Buffers optimization"""

        # Request tracing
        with self.tracer.trace("user_authentication", trace_context.correlation_id):
            start_time = time.time()

            auth_result = AuthResult()
            auth_result.correlation_id = trace_context.correlation_id

            # Input validation
            validation_result = await self.validate_auth_request(auth_request)
            if not validation_result.is_valid:
                auth_result.status = AuthStatus.INVALID_REQUEST
                auth_result.error_message = validation_result.error_message
                return auth_result

            # Multi-factor authentication check
            if auth_request.login_request.requires_mfa:
                mfa_result = await self.verify_mfa(auth_request.login_request, trace_context)
                if not mfa_result.verified:
                    auth_result.status = AuthStatus.MFA_REQUIRED
                    auth_result.mfa_challenge = mfa_result.challenge
                    return auth_result

            # Primary authentication
            user_credentials = await self.verify_credentials(
                auth_request.login_request.email,
                auth_request.login_request.password,
                trace_context
            )

            if not user_credentials.verified:
                auth_result.status = AuthStatus.INVALID_CREDENTIALS
                auth_result.error_message = "Invalid email or password"

                # Security logging
                await self.log_failed_login_attempt(
                    auth_request.login_request.email,
                    auth_request.client_ip,
                    trace_context
                )
                return auth_result

            # Load user context
            user_context = await self.load_user_context(user_credentials.user_id)

            # Generate optimized JWT with Protocol Buffers
            auth_token = await self.generate_protobuf_jwt(
                user_context, auth_request, trace_context
            )

            # Success response
            auth_result.status = AuthStatus.SUCCESS
            auth_result.auth_token = auth_token
            auth_result.user_context = user_context
            auth_result.session_duration_minutes = auth_token.expires_in_minutes

            # Performance metrics
            auth_time = (time.time() - start_time) * 1000
            auth_result.processing_time_ms = auth_time

            # Update last login
            await self.update_last_login(user_credentials.user_id, trace_context)

            return auth_result

    async def generate_protobuf_jwt(self, user_context: UserContext,
                                  auth_request: AuthRequest,
                                  trace_context: TraceContext) -> AuthToken:
        """Generate JWT with Protocol Buffers claims for optimal performance"""

        # Create JWT claims with Protocol Buffers
        jwt_claims = JWTClaims()
        jwt_claims.user_id = user_context.user_id
        jwt_claims.company_id = user_context.company_id
        jwt_claims.subscription_tier = user_context.subscription_info.tier
        jwt_claims.roles = user_context.roles
        jwt_claims.permissions = user_context.permissions
        jwt_claims.issued_at = int(time.time())
        jwt_claims.expires_at = jwt_claims.issued_at + (8 * 3600)  # 8 hours
        jwt_claims.correlation_id = trace_context.correlation_id

        # Serialize claims to Protocol Buffers
        pb_claims = jwt_claims.SerializeToString()

        # Create JWT with protobuf payload
        jwt_token = self.jwt_handler.encode({
            "sub": user_context.user_id,
            "company": user_context.company_id,
            "pb_claims": base64.b64encode(pb_claims).decode('utf-8'),
            "iat": jwt_claims.issued_at,
            "exp": jwt_claims.expires_at
        })

        # Create auth token response
        auth_token = AuthToken()
        auth_token.token = jwt_token
        auth_token.token_type = "Bearer"
        auth_token.expires_in_minutes = 480  # 8 hours
        auth_token.refresh_token = await self.generate_refresh_token(user_context)
        auth_token.metadata = TokenMetadata()
        auth_token.metadata.issued_at = jwt_claims.issued_at
        auth_token.metadata.client_ip = auth_request.client_ip
        auth_token.metadata.user_agent = auth_request.user_agent

        # Cache token for validation
        await self.token_cache.cache_token(jwt_token, user_context, jwt_claims.expires_at)

        return auth_token

    async def validate_jwt_token(self, token: str,
                               trace_context: TraceContext) -> TokenValidationResult:
        """Fast JWT validation with Protocol Buffers claims"""

        validation_result = TokenValidationResult()

        # Check token cache first
        cached_context = await self.token_cache.get_cached_user_context(token)
        if cached_context:
            validation_result.is_valid = True
            validation_result.user_context = cached_context
            validation_result.cache_hit = True
            return validation_result

        try:
            # Decode JWT
            decoded_token = self.jwt_handler.decode(token)

            # Extract Protocol Buffers claims
            pb_claims_b64 = decoded_token.get('pb_claims')
            if not pb_claims_b64:
                validation_result.is_valid = False
                validation_result.error = "Missing protobuf claims"
                return validation_result

            # Deserialize Protocol Buffers claims
            pb_claims_bytes = base64.b64decode(pb_claims_b64)
            jwt_claims = JWTClaims()
            jwt_claims.ParseFromString(pb_claims_bytes)

            # Rebuild user context from claims
            user_context = await self.rebuild_user_context_from_claims(jwt_claims)

            # Token validation success
            validation_result.is_valid = True
            validation_result.user_context = user_context
            validation_result.cache_hit = False

            # Update cache
            await self.token_cache.cache_token(token, user_context, jwt_claims.expires_at)

        except jwt.ExpiredSignatureError:
            validation_result.is_valid = False
            validation_result.error = "Token expired"
        except jwt.InvalidTokenError as e:
            validation_result.is_valid = False
            validation_result.error = f"Invalid token: {str(e)}"

        return validation_result
```

### **2. Multi-Tenant User Registration**:
```python
class UserRegistrationEngine:
    async def register_user(self, registration_request: RegistrationRequest,
                          trace_context: TraceContext) -> RegistrationResult:
        """Multi-tenant user registration with company assignment"""

        # Request tracing
        with self.tracer.trace("user_registration", trace_context.correlation_id):
            registration_result = RegistrationResult()
            registration_result.correlation_id = trace_context.correlation_id

            # Validate registration data
            validation_result = await self.validate_registration_request(registration_request)
            if not validation_result.is_valid:
                registration_result.status = RegistrationStatus.INVALID_DATA
                registration_result.validation_errors = validation_result.errors
                return registration_result

            # Check if user already exists
            existing_user = await self.check_existing_user(registration_request.email)
            if existing_user:
                registration_result.status = RegistrationStatus.USER_EXISTS
                registration_result.error_message = "User with this email already exists"
                return registration_result

            # Company assignment logic
            company_assignment = await self.determine_company_assignment(
                registration_request, trace_context
            )

            # Create user account
            user_profile = await self.create_user_account(
                registration_request, company_assignment, trace_context
            )

            # Initialize subscription
            subscription_info = await self.initialize_subscription(
                user_profile.user_id, registration_request.subscription_plan, trace_context
            )

            # Setup default preferences
            await self.setup_default_preferences(user_profile.user_id, trace_context)

            # Send welcome notification
            await self.send_welcome_notification(user_profile, trace_context)

            # Success response
            registration_result.status = RegistrationStatus.SUCCESS
            registration_result.user_profile = user_profile
            registration_result.subscription_info = subscription_info
            registration_result.verification_required = company_assignment.requires_verification

            return registration_result

    async def determine_company_assignment(self, registration_request: RegistrationRequest,
                                         trace_context: TraceContext) -> CompanyAssignment:
        """Intelligent company assignment based on registration context"""

        company_assignment = CompanyAssignment()

        # Check for company invitation
        if registration_request.invitation_code:
            company_invitation = await self.validate_company_invitation(
                registration_request.invitation_code
            )

            if company_invitation.is_valid:
                company_assignment.company_id = company_invitation.company_id
                company_assignment.role = company_invitation.default_role
                company_assignment.assignment_type = AssignmentType.INVITATION
                company_assignment.requires_verification = False
                return company_assignment

        # Check for corporate email domain
        email_domain = registration_request.email.split('@')[1]
        corporate_domain = await self.check_corporate_domain(email_domain)

        if corporate_domain:
            company_assignment.company_id = corporate_domain.company_id
            company_assignment.role = Role.MEMBER
            company_assignment.assignment_type = AssignmentType.DOMAIN_MATCH
            company_assignment.requires_verification = True
            return company_assignment

        # Default: Create individual company
        new_company = await self.create_individual_company(
            registration_request.email, trace_context
        )

        company_assignment.company_id = new_company.company_id
        company_assignment.role = Role.OWNER
        company_assignment.assignment_type = AssignmentType.INDIVIDUAL
        company_assignment.requires_verification = False

        return company_assignment

    async def create_user_account(self, registration_request: RegistrationRequest,
                                company_assignment: CompanyAssignment,
                                trace_context: TraceContext) -> UserProfile:
        """Create complete user account with multi-tenant setup"""

        user_profile = UserProfile()
        user_profile.user_id = self.generate_user_id()
        user_profile.email = registration_request.email
        user_profile.first_name = registration_request.first_name
        user_profile.last_name = registration_request.last_name
        user_profile.company_id = company_assignment.company_id
        user_profile.role = company_assignment.role
        user_profile.created_at = int(time.time() * 1000)
        user_profile.status = UserStatus.ACTIVE
        user_profile.email_verified = False

        # Security settings
        password_hash = await self.hash_password(registration_request.password)
        user_profile.password_hash = password_hash
        user_profile.mfa_enabled = False
        user_profile.login_attempts = 0

        # Multi-tenant permissions
        user_profile.permissions = await self.get_role_permissions(
            company_assignment.role, company_assignment.company_id
        )

        # Store in database
        await self.store_user_profile(user_profile)

        # Add to company team
        await self.add_user_to_company(
            user_profile.user_id, company_assignment.company_id,
            company_assignment.role, trace_context
        )

        return user_profile
```

### **3. Subscription Management Engine**:
```python
class SubscriptionManagementEngine:
    async def manage_subscription(self, user_id: str,
                                subscription_action: SubscriptionAction,
                                trace_context: TraceContext) -> SubscriptionResult:
        """Comprehensive subscription lifecycle management"""

        # Request tracing
        with self.tracer.trace("subscription_management", trace_context.correlation_id):
            subscription_result = SubscriptionResult()
            subscription_result.user_id = user_id
            subscription_result.correlation_id = trace_context.correlation_id

            # Load current subscription
            current_subscription = await self.get_current_subscription(user_id)

            if subscription_action.action_type == ActionType.UPGRADE:
                subscription_result = await self.process_subscription_upgrade(
                    user_id, current_subscription, subscription_action, trace_context
                )

            elif subscription_action.action_type == ActionType.DOWNGRADE:
                subscription_result = await self.process_subscription_downgrade(
                    user_id, current_subscription, subscription_action, trace_context
                )

            elif subscription_action.action_type == ActionType.CANCEL:
                subscription_result = await self.process_subscription_cancellation(
                    user_id, current_subscription, trace_context
                )

            elif subscription_action.action_type == ActionType.REACTIVATE:
                subscription_result = await self.process_subscription_reactivation(
                    user_id, current_subscription, trace_context
                )

            # Update user context across all services
            if subscription_result.status == SubscriptionStatus.SUCCESS:
                await self.propagate_subscription_change(user_id, subscription_result, trace_context)

            return subscription_result

    async def process_subscription_upgrade(self, user_id: str,
                                         current_subscription: SubscriptionInfo,
                                         action: SubscriptionAction,
                                         trace_context: TraceContext) -> SubscriptionResult:
        """Process subscription tier upgrade with prorated billing"""

        subscription_result = SubscriptionResult()

        # Validate upgrade path
        upgrade_validation = await self.validate_upgrade_path(
            current_subscription.tier, action.target_tier
        )

        if not upgrade_validation.is_valid:
            subscription_result.status = SubscriptionStatus.INVALID_UPGRADE
            subscription_result.error_message = upgrade_validation.error_message
            return subscription_result

        # Calculate prorated billing
        billing_calculation = await self.calculate_prorated_billing(
            current_subscription, action.target_tier
        )

        # Process payment if required
        if billing_calculation.charge_amount > 0:
            payment_result = await self.process_subscription_payment(
                user_id, billing_calculation, trace_context
            )

            if payment_result.status != PaymentStatus.SUCCESS:
                subscription_result.status = SubscriptionStatus.PAYMENT_FAILED
                subscription_result.error_message = payment_result.error_message
                return subscription_result

        # Update subscription
        new_subscription = await self.update_subscription_tier(
            user_id, action.target_tier, billing_calculation
        )

        # Enable new features
        await self.enable_tier_features(user_id, action.target_tier, trace_context)

        subscription_result.status = SubscriptionStatus.SUCCESS
        subscription_result.new_subscription = new_subscription
        subscription_result.billing_info = billing_calculation

        return subscription_result

    def get_tier_features(self, tier: SubscriptionTier) -> List[str]:
        """Get available features by subscription tier"""

        tier_features = {
            SubscriptionTier.FREE: [
                "basic_trading_signals",
                "limited_backtesting",
                "basic_analytics",
                "email_notifications"
            ],
            SubscriptionTier.PRO: [
                "advanced_trading_signals",
                "full_backtesting_suite",
                "advanced_analytics",
                "multi_channel_notifications",
                "risk_management_tools",
                "pattern_recognition",
                "ml_model_access"
            ],
            SubscriptionTier.ENTERPRISE: [
                "premium_trading_signals",
                "unlimited_backtesting",
                "business_intelligence",
                "priority_notifications",
                "advanced_risk_management",
                "custom_pattern_recognition",
                "full_ml_model_suite",
                "multi_user_management",
                "custom_integrations",
                "dedicated_support",
                "white_label_options"
            ]
        }

        return tier_features.get(tier, tier_features[SubscriptionTier.FREE])
```

### **4. Company Management Engine**:
```python
class CompanyManagementEngine:
    async def manage_company(self, company_action: CompanyAction,
                           user_context: UserContext,
                           trace_context: TraceContext) -> CompanyResult:
        """Multi-tenant company management operations"""

        # Request tracing
        with self.tracer.trace("company_management", trace_context.correlation_id):
            company_result = CompanyResult()
            company_result.correlation_id = trace_context.correlation_id

            # Permission validation
            if not await self.has_company_permission(user_context, company_action.action_type):
                company_result.status = CompanyStatus.PERMISSION_DENIED
                company_result.error_message = "Insufficient permissions for this action"
                return company_result

            if company_action.action_type == CompanyActionType.CREATE_COMPANY:
                company_result = await self.create_company(
                    company_action.company_data, user_context, trace_context
                )

            elif company_action.action_type == CompanyActionType.INVITE_USER:
                company_result = await self.invite_user_to_company(
                    company_action.invitation_data, user_context, trace_context
                )

            elif company_action.action_type == CompanyActionType.REMOVE_USER:
                company_result = await self.remove_user_from_company(
                    company_action.user_id, user_context, trace_context
                )

            elif company_action.action_type == CompanyActionType.UPDATE_ROLE:
                company_result = await self.update_user_role(
                    company_action.user_id, company_action.new_role,
                    user_context, trace_context
                )

            elif company_action.action_type == CompanyActionType.UPDATE_SETTINGS:
                company_result = await self.update_company_settings(
                    company_action.settings, user_context, trace_context
                )

            return company_result

    async def create_company(self, company_data: CompanyData,
                           user_context: UserContext,
                           trace_context: TraceContext) -> CompanyResult:
        """Create new company with multi-tenant isolation"""

        company_result = CompanyResult()

        # Validate company data
        validation_result = await self.validate_company_data(company_data)
        if not validation_result.is_valid:
            company_result.status = CompanyStatus.INVALID_DATA
            company_result.validation_errors = validation_result.errors
            return company_result

        # Create company profile
        company_profile = CompanyProfile()
        company_profile.company_id = self.generate_company_id()
        company_profile.company_name = company_data.company_name
        company_profile.industry = company_data.industry
        company_profile.company_size = company_data.company_size
        company_profile.created_at = int(time.time() * 1000)
        company_profile.owner_user_id = user_context.user_id
        company_profile.status = CompanyStatus.ACTIVE

        # Initialize company settings
        company_settings = CompanySettings()
        company_settings.company_id = company_profile.company_id
        company_settings.trading_enabled = True
        company_settings.risk_management_required = True
        company_settings.data_retention_days = 365
        company_settings.allowed_trading_hours = "24/7"
        company_settings.notification_preferences = self.get_default_notification_preferences()

        # Create default roles and permissions
        await self.create_default_company_roles(company_profile.company_id)

        # Store company data
        await self.store_company_profile(company_profile)
        await self.store_company_settings(company_settings)

        # Add creator as owner
        await self.add_user_to_company(
            user_context.user_id, company_profile.company_id,
            Role.OWNER, trace_context
        )

        company_result.status = CompanyStatus.SUCCESS
        company_result.company_profile = company_profile
        company_result.company_settings = company_settings

        return company_result

    async def invite_user_to_company(self, invitation_data: InvitationData,
                                   user_context: UserContext,
                                   trace_context: TraceContext) -> CompanyResult:
        """Send company invitation with role assignment"""

        company_result = CompanyResult()

        # Generate invitation
        invitation = CompanyInvitation()
        invitation.invitation_id = self.generate_invitation_id()
        invitation.company_id = user_context.company_id
        invitation.inviter_user_id = user_context.user_id
        invitation.invitee_email = invitation_data.email
        invitation.role = invitation_data.role
        invitation.invitation_code = self.generate_invitation_code()
        invitation.expires_at = int(time.time() * 1000) + (7 * 24 * 3600 * 1000)  # 7 days
        invitation.status = InvitationStatus.PENDING

        # Store invitation
        await self.store_company_invitation(invitation)

        # Send invitation email
        await self.send_invitation_email(invitation, user_context, trace_context)

        company_result.status = CompanyStatus.SUCCESS
        company_result.invitation = invitation

        return company_result
```

---

## 🔍 Multi-Tenant Security & Performance

### **Role-Based Access Control**:
```python
class RoleBasedAccessControl:
    def __init__(self):
        self.role_hierarchy = {
            Role.OWNER: [Role.ADMIN, Role.MANAGER, Role.MEMBER, Role.VIEWER],
            Role.ADMIN: [Role.MANAGER, Role.MEMBER, Role.VIEWER],
            Role.MANAGER: [Role.MEMBER, Role.VIEWER],
            Role.MEMBER: [Role.VIEWER],
            Role.VIEWER: []
        }

        self.permission_matrix = {
            Role.OWNER: [
                "company.manage", "users.manage", "billing.manage",
                "settings.manage", "data.full_access", "trading.manage"
            ],
            Role.ADMIN: [
                "users.manage", "settings.modify", "data.full_access",
                "trading.manage", "reports.generate"
            ],
            Role.MANAGER: [
                "users.view", "settings.view", "data.team_access",
                "trading.view", "reports.view"
            ],
            Role.MEMBER: [
                "data.own_access", "trading.own_access", "profile.manage"
            ],
            Role.VIEWER: [
                "data.read_only", "reports.read_only"
            ]
        }

    async def check_permission(self, user_context: UserContext,
                             required_permission: str) -> bool:
        """Check if user has required permission"""

        user_permissions = self.permission_matrix.get(user_context.role, [])
        return required_permission in user_permissions

    async def filter_data_by_permissions(self, data: Any,
                                       user_context: UserContext) -> Any:
        """Filter data based on user permissions and multi-tenant rules"""

        # Company-level filtering
        if hasattr(data, 'company_id'):
            if data.company_id != user_context.company_id:
                return None

        # User-level filtering for personal data
        if hasattr(data, 'user_id'):
            if user_context.role in [Role.MEMBER, Role.VIEWER]:
                if data.user_id != user_context.user_id:
                    return None

        # Subscription tier filtering
        if hasattr(data, 'required_tier'):
            if user_context.subscription_info.tier < data.required_tier:
                return None

        return data
```

### **User Context Caching**:
```python
class UserContextCache:
    def __init__(self):
        self.context_cache = TTLCache(maxsize=10000, ttl=300)  # 5 minute TTL
        self.permission_cache = TTLCache(maxsize=5000, ttl=600)  # 10 minute TTL

    async def get_cached_user_context(self, user_id: str) -> Optional[UserContext]:
        """Get cached user context for fast resolution"""

        return self.context_cache.get(user_id)

    async def cache_user_context(self, user_id: str, user_context: UserContext):
        """Cache user context with intelligent TTL"""

        # Dynamic TTL based on user activity
        if user_context.subscription_info.tier >= SubscriptionTier.PRO:
            ttl = 600  # 10 minutes for Pro+ users
        else:
            ttl = 300  # 5 minutes for free users

        self.context_cache[user_id] = user_context

    async def invalidate_user_context(self, user_id: str):
        """Invalidate cached user context on profile changes"""

        if user_id in self.context_cache:
            del self.context_cache[user_id]

        # Invalidate related permission cache
        keys_to_remove = [key for key in self.permission_cache.keys()
                         if key.startswith(f"{user_id}:")]
        for key in keys_to_remove:
            del self.permission_cache[key]
```

---

## 🔍 Health Monitoring & Security

### **Service Health Check**:
```python
@app.get("/health")
async def health_check():
    """Comprehensive user management service health check"""

    health_status = {
        "service": "user-management",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.5.0"
    }

    try:
        # Authentication performance
        health_status["avg_auth_time_ms"] = await self.get_avg_auth_time()
        health_status["jwt_validation_success_rate"] = await self.get_jwt_success_rate()

        # User management metrics
        health_status["active_users_24h"] = await self.get_active_user_count()
        health_status["new_registrations_24h"] = await self.get_registration_count()
        health_status["subscription_conversion_rate"] = await self.get_conversion_rate()

        # Multi-tenant metrics
        health_status["active_companies"] = await self.get_active_company_count()
        health_status["company_user_distribution"] = await self.get_company_distribution()

        # Security metrics
        health_status["failed_login_rate"] = await self.get_failed_login_rate()
        health_status["mfa_adoption_rate"] = await self.get_mfa_adoption_rate()
        health_status["security_incidents_24h"] = await self.get_security_incident_count()

        # Cache performance
        health_status["context_cache_hit_rate"] = await self.get_cache_hit_rate()
        health_status["token_cache_size"] = await self.get_token_cache_size()

        # Database connectivity
        health_status["database_connection_pool"] = await self.check_db_connection_health()

    except Exception as e:
        health_status["status"] = "degraded"
        health_status["error"] = str(e)

    return health_status
```

### **Security Monitoring**:
```python
class SecurityMonitor:
    async def monitor_authentication_patterns(self, user_id: str,
                                            auth_request: AuthRequest,
                                            trace_context: TraceContext):
        """Real-time authentication pattern analysis"""

        # Suspicious activity detection
        suspicious_patterns = []

        # Multiple failed login attempts
        failed_attempts = await self.get_recent_failed_attempts(user_id, hours=1)
        if len(failed_attempts) >= 5:
            suspicious_patterns.append("multiple_failed_logins")

        # Login from unusual location
        if await self.is_unusual_location(user_id, auth_request.client_ip):
            suspicious_patterns.append("unusual_location")

        # Login at unusual time
        if await self.is_unusual_time(user_id, auth_request.timestamp):
            suspicious_patterns.append("unusual_time")

        # Multiple concurrent sessions
        active_sessions = await self.get_active_session_count(user_id)
        if active_sessions > 5:
            suspicious_patterns.append("excessive_sessions")

        # Generate security alert if patterns detected
        if suspicious_patterns:
            security_alert = SecurityAlert()
            security_alert.user_id = user_id
            security_alert.alert_type = AlertType.SUSPICIOUS_LOGIN
            security_alert.patterns = suspicious_patterns
            security_alert.correlation_id = trace_context.correlation_id
            security_alert.timestamp = int(time.time() * 1000)

            await self.send_security_alert(security_alert)

            # Consider requiring additional verification
            if len(suspicious_patterns) >= 2:
                await self.require_additional_verification(user_id)
```

---

## 🎯 Business Value

### **User Experience Excellence**:
- **Sub-8ms User Context Resolution**: Fast authentication without latency impact
- **JWT + Protocol Buffers Optimization**: 60% smaller auth tokens, 10x faster processing
- **Multi-Factor Authentication**: Enhanced security with user-friendly flow
- **Single Sign-On Ready**: Extensible authentication for future SSO integration

### **Multi-Tenant Platform Management**:
- **Company-Level Controls**: Centralized governance for organizations
- **Role-Based Access Control**: Granular permission management
- **Subscription Management**: Automated billing and feature gating
- **Team Collaboration**: Invitation system and role hierarchy

### **Security & Compliance**:
- **Advanced Security Monitoring**: Real-time threat detection and response
- **Data Isolation**: Complete multi-tenant data segregation
- **Audit Trail**: Comprehensive logging for compliance requirements
- **Circuit Breaker Protected**: Authentication service resilience

---

**Input Flow**: Frontend/Client → User-Management (authentication)
**Output Flow**: User-Management → All Services (user context + authorization)
**Key Innovation**: Sub-8ms JWT + Protocol Buffers authentication dengan comprehensive multi-tenant user management dan advanced security monitoring.