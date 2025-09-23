# Core Layer Architecture (Level 1 + Level 2 dari Plan2)

## 🔧 Core Layer Overview

Core Layer mengimplementasikan **foundational services** yang mendukung semua operasi platform:

```yaml
Core_Layer_Composition:
  Level_1_Foundation: "Infrastructure Core, Error Handling, Logging System"
  Level_2_Connectivity: "API Gateway, Authentication, Service Registry, Inter-Service Communication"

AI_Trading_Heritage_Benefits:
  Central_Hub_Pattern: "Revolutionary infrastructure management pattern dari ai_trading"
  ErrorDNA_System: "Advanced error handling proven dalam production"
  Performance_Excellence: "6s startup, 95% memory optimization baseline"
  Service_Coordination: "Proven service registration dan discovery patterns"
```

---

## 🏗️ Level 1 - Foundation Services

### **1.1 Infrastructure Core** - Enhanced Central Hub

**Basis**: ai_trading Central Hub + Business Multi-Tenant Enhancement

#### **AI Trading Heritage Central Hub**:
```python
# Original Central Hub pattern dari ai_trading
class CentralHub:
    """Revolutionary infrastructure management approach dari ai_trading"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.services = {}
            self.configuration = {}
            self.ai_trading_heritage = {
                'singleton_pattern': 'Proven service coordination',
                'service_discovery': 'Production-tested registration',
                'config_management': 'Centralized configuration'
            }
            self.initialized = True
```

#### **Business Enhancement - Multi-Tenant Central Hub**:
```python
class BusinessCentralHub(CentralHub):
    """Enhanced Central Hub dengan multi-tenant business context"""

    def __init__(self):
        super().__init__()
        self.tenant_services = {}  # tenant_id -> services mapping
        self.business_config = BusinessConfigManager()
        self.tenant_isolation = TenantIsolationManager()

    def register_business_service(self, service_name: str, service_instance, tenant_context: TenantContext):
        """Register service dengan tenant isolation"""
        # Apply tenant wrapping
        tenant_service = self.tenant_isolation.wrap_service(service_instance, tenant_context)

        # Register dengan tenant-specific key
        tenant_key = f"{tenant_context.tenant_id}:{service_name}"
        self.tenant_services[tenant_key] = tenant_service

        # Also register in legacy services for backward compatibility
        self.services[service_name] = tenant_service

    def get_service(self, service_name: str, user_context: UserContext = None):
        """Get service dengan user context untuk tenant isolation"""
        if user_context:
            tenant_key = f"{user_context.tenant_id}:{service_name}"
            if tenant_key in self.tenant_services:
                return self.tenant_services[tenant_key]

        # Fallback ke legacy service
        return self.services.get(service_name)

    def get_business_configuration(self, config_key: str, user_context: UserContext):
        """Get configuration dengan business context"""
        return self.business_config.get_tenant_config(config_key, user_context)
```

#### **Service Registration Pattern**:
```python
class ServiceRegistrationManager:
    def __init__(self, central_hub: BusinessCentralHub):
        self.hub = central_hub

    def register_ai_trading_service(self, service_name: str, service_instance):
        """Register AI Trading heritage service"""
        enhanced_service = self.enhance_with_business_context(service_instance)
        self.hub.register_service(service_name, enhanced_service)

    def enhance_with_business_context(self, service_instance):
        """Add business context ke AI Trading services"""
        wrapper = BusinessServiceWrapper(service_instance)
        wrapper.add_tenant_awareness()
        wrapper.add_subscription_enforcement()
        wrapper.add_usage_tracking()
        return wrapper
```

### **1.2 Import Manager** - Enhanced Dependency Injection

**Basis**: ai_trading Import Manager + Business Dependencies

#### **AI Trading Heritage**:
```python
class ImportManager:
    """Centralized dependency management dari ai_trading"""
    def __init__(self):
        self.dependencies = {}
        self.ai_trading_heritage = {
            'dependency_resolution': 'Proven dependency injection',
            'module_loading': 'Dynamic module loading',
            'circular_detection': 'Circular dependency detection'
        }

    def resolve_dependency(self, dependency_name: str):
        """Resolve dependency dengan ai_trading pattern"""
        if dependency_name not in self.dependencies:
            self.dependencies[dependency_name] = self.load_dependency(dependency_name)
        return self.dependencies[dependency_name]
```

#### **Business Enhancement**:
```python
class BusinessImportManager(ImportManager):
    """Enhanced dengan business dan multi-tenant dependencies"""

    def __init__(self):
        super().__init__()
        self.business_dependencies = BusinessDependencyRegistry()
        self.tenant_dependencies = {}

    def resolve_business_dependency(self, dependency_name: str, user_context: UserContext):
        """Resolve dependency dengan business context"""
        # Check for tenant-specific dependency
        tenant_key = f"{user_context.tenant_id}:{dependency_name}"
        if tenant_key in self.tenant_dependencies:
            return self.tenant_dependencies[tenant_key]

        # Create tenant-specific instance
        base_dependency = self.resolve_dependency(dependency_name)
        tenant_dependency = self.create_tenant_instance(base_dependency, user_context)
        self.tenant_dependencies[tenant_key] = tenant_dependency

        return tenant_dependency

    def create_tenant_instance(self, base_dependency, user_context: UserContext):
        """Create tenant-isolated instance"""
        tenant_wrapper = TenantDependencyWrapper(base_dependency, user_context)
        tenant_wrapper.apply_subscription_limits(user_context.subscription_tier)
        return tenant_wrapper
```

### **1.3 Error Handling** - Enhanced ErrorDNA System

**Basis**: ai_trading ErrorDNA + Business Error Management

#### **AI Trading Heritage ErrorDNA**:
```python
class ErrorDNA:
    """Advanced error handling system dari ai_trading"""
    def __init__(self):
        self.error_patterns = {}
        self.recovery_strategies = {}
        self.ai_trading_heritage = {
            'error_classification': 'Advanced error categorization',
            'recovery_automation': 'Automated error recovery',
            'learning_system': 'Error pattern learning'
        }

    def handle_error(self, error: Exception, context: dict = None):
        """Handle error dengan ErrorDNA intelligence"""
        error_dna = self.analyze_error_dna(error)
        recovery_strategy = self.select_recovery_strategy(error_dna)
        return self.execute_recovery(recovery_strategy, error, context)
```

#### **Business Enhancement**:
```python
class BusinessErrorHandler(ErrorDNA):
    """Enhanced ErrorDNA dengan business context dan impact assessment"""

    def __init__(self):
        super().__init__()
        self.business_error_classifier = BusinessErrorClassifier()
        self.subscription_error_handler = SubscriptionErrorHandler()
        self.billing_error_manager = BillingErrorManager()

    def handle_business_error(self, error: Exception, user_context: UserContext):
        """Handle error dengan business impact assessment"""
        # Analyze error dengan business context
        business_error = self.business_error_classifier.classify(error, user_context)

        # Apply business-specific recovery
        if business_error.affects_billing:
            await self.billing_error_manager.handle_billing_error(business_error, user_context)

        if business_error.affects_subscription:
            await self.subscription_error_handler.handle_subscription_error(business_error, user_context)

        if business_error.affects_user_experience:
            await self.notify_user_of_error(business_error, user_context)

        # Apply base ErrorDNA handling
        return self.handle_error(error, {'business_context': business_error})

    async def notify_user_of_error(self, business_error: BusinessError, user_context: UserContext):
        """Notify user dengan subscription-appropriate messaging"""
        notification_service = await self.get_notification_service()

        message = self.create_user_friendly_message(business_error, user_context.subscription_tier)

        await notification_service.notify_user(
            user_id=user_context.user_id,
            message=message,
            severity=business_error.severity,
            channels=self.get_notification_channels(user_context.subscription_tier)
        )
```

### **1.4 Logging System** - Multi-Tenant Logging

**Basis**: ai_trading Logging + Business Multi-Tenant Isolation

#### **Business Logging Architecture**:
```python
class BusinessLoggingSystem:
    """Multi-tenant logging dengan business context"""

    def __init__(self):
        self.tenant_loggers = {}
        self.business_log_aggregator = BusinessLogAggregator()
        self.compliance_logger = ComplianceLogger()

    def get_tenant_logger(self, tenant_id: str) -> StructuredLogger:
        """Get isolated logger untuk specific tenant"""
        if tenant_id not in self.tenant_loggers:
            logger_config = {
                'tenant_id': tenant_id,
                'log_level': self.get_tenant_log_level(tenant_id),
                'retention_days': self.get_tenant_retention(tenant_id),
                'encryption': self.requires_encryption(tenant_id)
            }
            self.tenant_loggers[tenant_id] = StructuredLogger(logger_config)

        return self.tenant_loggers[tenant_id]

    def log_business_event(self, event: BusinessEvent, user_context: UserContext):
        """Log business event dengan full context"""
        tenant_logger = self.get_tenant_logger(user_context.tenant_id)

        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tenant_id': user_context.tenant_id,
            'user_id': user_context.user_id,
            'subscription_tier': user_context.subscription_tier,
            'event_type': event.type,
            'event_category': event.category,
            'event_data': event.data,
            'business_impact': event.business_impact,
            'compliance_required': event.requires_compliance_logging
        }

        # Log ke tenant-specific log
        tenant_logger.info(log_entry)

        # Log ke business aggregator untuk analytics
        self.business_log_aggregator.aggregate(log_entry)

        # Log ke compliance jika diperlukan
        if event.requires_compliance_logging:
            self.compliance_logger.log_compliance_event(log_entry)
```

---

## 🌐 Level 2 - Connectivity Services

### **2.1 API Gateway (Port 8000)** - Business-Enhanced Entry Point

**Basis**: ai_trading API Gateway + Multi-Tenant Business Features

#### **AI Trading Heritage**:
```python
class APIGateway:
    """Basic API Gateway dari ai_trading"""
    def __init__(self):
        self.routes = {}
        self.middleware = []
        self.ai_trading_heritage = {
            'basic_authentication': 'JWT token validation',
            'rate_limiting': 'Basic rate limiting',
            'service_routing': 'Service discovery routing'
        }
```

#### **Business Enhancement**:
```python
class BusinessAPIGateway(APIGateway):
    """Multi-tenant API Gateway dengan subscription-based features"""

    def __init__(self):
        super().__init__()
        self.subscription_manager = SubscriptionManager()
        self.tier_based_limiter = TierBasedRateLimiter()
        self.business_router = BusinessServiceRouter()
        self.usage_tracker = APIUsageTracker()

    async def handle_request(self, request: Request) -> Response:
        """Handle request dengan complete business logic"""
        try:
            # Extract user context
            user_context = await self.extract_user_context(request)

            # Validate subscription access
            if not await self.subscription_manager.can_access_endpoint(
                user_context, request.endpoint
            ):
                return self.create_subscription_error_response(user_context)

            # Apply tier-based rate limiting
            if not await self.tier_based_limiter.allow_request(user_context, request):
                return self.create_rate_limit_response(user_context)

            # Track usage untuk billing
            await self.usage_tracker.track_api_call(user_context, request)

            # Route ke appropriate service
            response = await self.business_router.route_request(request, user_context)

            # Add business headers
            response = self.add_business_headers(response, user_context)

            return response

        except Exception as e:
            return await self.handle_gateway_error(e, request)

    def create_subscription_error_response(self, user_context: UserContext) -> Response:
        """Create subscription-specific error response"""
        upgrade_url = self.get_upgrade_url(user_context.subscription_tier)

        return Response(
            status=403,
            data={
                'error': 'subscription_insufficient',
                'message': f'This feature requires {self.get_required_tier()} subscription',
                'current_tier': user_context.subscription_tier,
                'upgrade_url': upgrade_url
            }
        )
```

#### **Tier-Based Rate Limiting**:
```python
class TierBasedRateLimiter:
    def __init__(self):
        self.tier_limits = {
            'free': {'requests_per_minute': 100, 'burst_size': 10},
            'pro': {'requests_per_minute': 1000, 'burst_size': 100},
            'enterprise': {'requests_per_minute': 10000, 'burst_size': 1000}
        }

    async def allow_request(self, user_context: UserContext, request: Request) -> bool:
        """Check rate limit berdasarkan subscription tier"""
        tier_limit = self.tier_limits.get(user_context.subscription_tier, self.tier_limits['free'])

        # Implement sliding window rate limiting
        current_count = await self.get_current_request_count(
            user_context.user_id,
            window_minutes=1
        )

        return current_count < tier_limit['requests_per_minute']
```

### **2.2 Authentication** - Multi-Tenant JWT Security

#### **Business Authentication System**:
```python
class BusinessAuthenticationService:
    def __init__(self):
        self.jwt_manager = JWTManager()
        self.subscription_validator = SubscriptionValidator()
        self.tenant_manager = TenantManager()

    async def authenticate_user(self, credentials: UserCredentials) -> AuthenticationResult:
        """Authenticate user dengan business context"""
        # Validate credentials
        user = await self.validate_credentials(credentials)
        if not user:
            raise AuthenticationError("Invalid credentials")

        # Validate subscription status
        subscription_status = await self.subscription_validator.check_subscription(user.id)
        if subscription_status.is_expired:
            raise SubscriptionExpiredError("Subscription has expired")

        # Generate business JWT
        jwt_token = self.generate_business_jwt(user, subscription_status)

        return AuthenticationResult(
            user=user,
            token=jwt_token,
            subscription_status=subscription_status,
            tenant_context=await self.tenant_manager.get_tenant_context(user.tenant_id)
        )

    def generate_business_jwt(self, user: User, subscription: SubscriptionStatus) -> str:
        """Generate JWT dengan complete business context"""
        payload = {
            'user_id': user.id,
            'tenant_id': user.tenant_id,
            'subscription_tier': subscription.tier,
            'subscription_status': subscription.status,
            'permissions': subscription.get_tier_permissions(),
            'usage_limits': subscription.get_usage_limits(),
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'business_context': {
                'billing_customer_id': user.billing_customer_id,
                'enterprise_features': subscription.enterprise_features
            }
        }

        return jwt.encode(payload, self.jwt_manager.secret_key, algorithm='HS256')
```

### **2.3 Service Registry** - Business Service Discovery

#### **Business Service Discovery**:
```python
class BusinessServiceRegistry:
    def __init__(self):
        self.core_services = {}  # AI Trading heritage services
        self.business_services = {}  # New business services
        self.service_health_monitor = ServiceHealthMonitor()

    def register_service(self, service_info: BusinessServiceInfo):
        """Register service dengan business capabilities"""
        enhanced_info = {
            **service_info.dict(),
            'subscription_requirements': service_info.subscription_requirements,
            'business_features': service_info.business_features,
            'health_endpoint': service_info.health_endpoint,
            'tenant_aware': service_info.tenant_aware
        }

        if service_info.is_core_service:
            self.core_services[service_info.name] = enhanced_info
        else:
            self.business_services[service_info.name] = enhanced_info

        # Start health monitoring
        self.service_health_monitor.monitor_service(service_info)

    def discover_services(self, user_context: UserContext) -> List[ServiceInfo]:
        """Discover services available untuk user's subscription tier"""
        available_services = []

        # Check core services
        for service_name, service_info in self.core_services.items():
            if self.can_user_access_service(service_info, user_context):
                available_services.append(service_info)

        # Check business services
        for service_name, service_info in self.business_services.items():
            if self.can_user_access_service(service_info, user_context):
                available_services.append(service_info)

        return available_services

    def can_user_access_service(self, service_info: dict, user_context: UserContext) -> bool:
        """Check if user can access service berdasarkan subscription"""
        required_tier = service_info.get('subscription_requirements', {}).get('minimum_tier')
        if not required_tier:
            return True

        tier_hierarchy = ['free', 'pro', 'enterprise']
        user_tier_index = tier_hierarchy.index(user_context.subscription_tier)
        required_tier_index = tier_hierarchy.index(required_tier)

        return user_tier_index >= required_tier_index
```

### **2.4 Inter-Service Communication** - Business Service Coordination

#### **Service Communication Manager**:
```python
class BusinessServiceCommunicator:
    def __init__(self):
        self.service_registry = BusinessServiceRegistry()
        self.load_balancer = BusinessLoadBalancer()
        self.circuit_breaker = CircuitBreakerManager()

    async def call_service(self, service_name: str, method: str, data: dict, user_context: UserContext):
        """Call service dengan business context propagation"""
        # Get service info
        service_info = await self.service_registry.get_service(service_name)
        if not service_info:
            raise ServiceNotFoundError(f"Service {service_name} not found")

        # Check user access
        if not self.service_registry.can_user_access_service(service_info, user_context):
            raise ServiceAccessDeniedError(f"Insufficient subscription for {service_name}")

        # Get service endpoint
        endpoint = await self.load_balancer.get_service_endpoint(service_name, user_context)

        # Prepare request dengan business context
        request_data = {
            **data,
            'user_context': user_context.dict(),
            'business_metadata': {
                'subscription_tier': user_context.subscription_tier,
                'tenant_id': user_context.tenant_id,
                'request_id': self.generate_request_id()
            }
        }

        # Execute dengan circuit breaker
        return await self.circuit_breaker.execute(
            service_name,
            lambda: self.execute_service_call(endpoint, method, request_data)
        )
```

## 🔄 Core Layer Integration Patterns

### **Service Coordination Flow**:
```python
class CoreLayerOrchestrator:
    def __init__(self):
        self.central_hub = BusinessCentralHub()
        self.api_gateway = BusinessAPIGateway()
        self.auth_service = BusinessAuthenticationService()
        self.service_registry = BusinessServiceRegistry()

    async def initialize_core_layer(self):
        """Initialize complete core layer dengan AI Trading heritage"""
        # Register AI Trading heritage services
        await self.register_ai_trading_services()

        # Register business services
        await self.register_business_services()

        # Setup service communication
        await self.setup_service_mesh()

        # Start health monitoring
        await self.start_health_monitoring()

    async def register_ai_trading_services(self):
        """Register proven AI Trading services dengan business enhancement"""
        ai_services = [
            'data-bridge',      # Port 8001
            'performance-analytics',  # Port 8002
            'ai-orchestration', # Port 8003
            'deep-learning',    # Port 8004
            'ai-provider',      # Port 8005
            'ml-processing',    # Port 8006
            'trading-engine',   # Port 8007
            'database-service', # Port 8008
            'user-service'      # Port 8009
        ]

        for service_name in ai_services:
            service_instance = await self.load_ai_trading_service(service_name)
            enhanced_service = self.enhance_with_business_context(service_instance)
            self.central_hub.register_service(service_name, enhanced_service)
```

**Core Layer Status**: PLANNED - Foundation dengan AI Trading heritage + business enhancements
**Integration Pattern**: Central Hub coordination dengan multi-tenant business context