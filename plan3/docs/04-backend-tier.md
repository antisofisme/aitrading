# Backend Tier - Complete Services Architecture (Berdasarkan Plan2)

## 🏗️ Backend Architecture Overview

Backend Tier mengimplementasikan **Level 1-4 dari Plan2** dalam **3 Layer Structure**:

```
Backend Tier (Level 1-4)
├── 🗄️ Database Layer (Level 1.2)
├── 🔧 Core Layer (Level 1 + Level 2)
└── 💼 Business Layer (Level 3 + Level 4)
```

## 🗄️ Database Layer (Level 1.2 - Database Basic)

### **Multi-Database Architecture** (dari Plan2):
**Basis**: ai_trading Database Service (Port 8006) + Dedicated Database Service (Port 8008)

#### **5 Database Stack** (AI Trading Heritage):
```yaml
Database_Stack:
  PostgreSQL: "User data, configurations, subscription data"
  ClickHouse: "High-frequency trading data, analytics"
  DragonflyDB: "Caching layer"
  Weaviate: "Vector embeddings untuk AI"
  ArangoDB: "Graph relationships"
```

#### **Database Service Implementation**:
```python
# Database Service (Port 8008) - Dedicated multi-database management
class DatabaseService:
    def __init__(self):
        self.connections = {
            'postgresql': PostgreSQLConnection(),
            'clickhouse': ClickHouseConnection(),
            'dragonflydb': DragonflyConnection(),
            'weaviate': WeaviateConnection(),
            'arangodb': ArangoConnection()
        }

    async def execute_query(self, db_type: str, query: Query, user_context: UserContext):
        """Execute query dengan multi-tenant isolation"""
        # Apply tenant isolation
        isolated_query = self.apply_tenant_isolation(query, user_context)

        # Execute on appropriate database
        connection = self.connections[db_type]
        result = await connection.execute(isolated_query)

        # Apply subscription-based result filtering
        return self.apply_subscription_filter(result, user_context.subscription_tier)
```

#### **Multi-Tenant Data Isolation**:
```python
class MultiTenantDataManager:
    def apply_tenant_isolation(self, query: Query, user_context: UserContext) -> Query:
        """Apply tenant isolation ke database queries"""
        if query.table in self.tenant_tables:
            query.add_where_clause(f"tenant_id = '{user_context.tenant_id}'")

        if query.involves_user_data:
            query.add_where_clause(f"user_id = '{user_context.user_id}'")

        return query

    def apply_subscription_filter(self, result: QueryResult, tier: str) -> QueryResult:
        """Filter results berdasarkan subscription tier"""
        tier_limits = {
            'free': {'max_rows': 100, 'historical_days': 7},
            'pro': {'max_rows': 10000, 'historical_days': 90},
            'enterprise': {'max_rows': 'unlimited', 'historical_days': 'unlimited'}
        }

        limits = tier_limits[tier]
        return result.apply_limits(limits)
```

---

## 🔧 Core Layer (Level 1 Foundation + Level 2 Connectivity)

### **Level 1 - Foundation Services**:

#### **1.1 Infrastructure Core** - Central Hub Pattern:
```python
# Enhanced Central Hub dari ai_trading + Business Context
class BusinessCentralHub:
    def __init__(self):
        self.ai_trading_base = CentralHub()  # Heritage
        self.tenant_manager = TenantManager()
        self.business_services = {}

    def register_business_service(self, service_name: str, service_instance, tenant_context: TenantContext):
        """Register service dengan tenant context"""
        tenant_service = TenantAwareService(service_instance, tenant_context)
        self.business_services[f"{tenant_context.tenant_id}:{service_name}"] = tenant_service

    def get_service(self, service_name: str, user_context: UserContext):
        """Get service dengan user context"""
        tenant_key = f"{user_context.tenant_id}:{service_name}"
        return self.business_services.get(tenant_key)
```

#### **1.3 Error Handling** - Enhanced ErrorDNA:
```python
# ErrorDNA System dengan Business Context
class BusinessErrorHandler:
    def __init__(self):
        self.error_dna_base = ErrorDNA()  # AI Trading Heritage
        self.business_context = BusinessErrorContext()

    def handle_business_error(self, error: Exception, user_context: UserContext):
        """Handle errors dengan business impact assessment"""
        error_classification = self.classify_business_error(error, user_context)

        if error_classification.affects_billing:
            await self.notify_billing_service(error, user_context)

        if error_classification.affects_user_experience:
            await self.notify_user(error, user_context)

        return self.error_dna_base.handle_error(error)
```

#### **1.4 Logging System** - Multi-Tenant Logging:
```python
class BusinessLoggingSystem:
    def __init__(self):
        self.tenant_loggers = {}

    def get_tenant_logger(self, tenant_id: str) -> Logger:
        """Get isolated logger untuk tenant"""
        if tenant_id not in self.tenant_loggers:
            self.tenant_loggers[tenant_id] = self.create_tenant_logger(tenant_id)
        return self.tenant_loggers[tenant_id]

    def log_business_event(self, event: BusinessEvent, user_context: UserContext):
        """Log business events dengan tenant isolation"""
        logger = self.get_tenant_logger(user_context.tenant_id)
        logger.info({
            'event_type': event.type,
            'user_id': user_context.user_id,
            'subscription_tier': user_context.subscription_tier,
            'timestamp': datetime.utcnow(),
            'data': event.data
        })
```

### **Level 2 - Connectivity Services**:

#### **2.1 API Gateway (Port 8000)** - Multi-Tenant Routing:
```python
# Business-enhanced API Gateway
class BusinessAPIGateway:
    def __init__(self):
        self.ai_trading_base = APIGateway()  # Heritage
        self.subscription_manager = SubscriptionManager()
        self.rate_limiter = TierBasedRateLimiter()

    async def route_request(self, request: Request) -> Response:
        """Route request dengan multi-tenant dan subscription context"""
        # Extract user context
        user_context = await self.extract_user_context(request)

        # Check subscription access
        if not await self.subscription_manager.can_access_endpoint(
            user_context, request.endpoint
        ):
            return Response(status=403, message="Subscription tier insufficient")

        # Apply rate limiting
        if not await self.rate_limiter.allow_request(user_context, request):
            return Response(status=429, message="Rate limit exceeded")

        # Route to appropriate service
        return await self.route_to_service(request, user_context)
```

#### **2.2 Authentication** - JWT Multi-Tenant Security:
```python
class BusinessAuthenticationService:
    def generate_business_jwt(self, user: User) -> JWT:
        """Generate JWT dengan business context"""
        payload = {
            'user_id': user.id,
            'tenant_id': user.tenant_id,
            'subscription_tier': user.subscription_tier,
            'permissions': user.get_tier_permissions(),
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, self.secret_key)

    async def validate_business_token(self, token: str) -> UserContext:
        """Validate token dan return business context"""
        payload = jwt.decode(token, self.secret_key)
        user_context = UserContext(
            user_id=payload['user_id'],
            tenant_id=payload['tenant_id'],
            subscription_tier=payload['subscription_tier']
        )
        return user_context
```

#### **2.3 Service Registry** - Business Service Discovery:
```python
class BusinessServiceRegistry:
    def __init__(self):
        self.core_services = {}  # AI Trading heritage services
        self.business_services = {}  # New business services

    def register_service(self, service_name: str, service_info: ServiceInfo):
        """Register service dengan business capabilities"""
        enhanced_info = ServiceInfo(
            **service_info.dict(),
            business_features=service_info.business_features,
            subscription_requirements=service_info.subscription_requirements
        )

        if service_info.is_core_service:
            self.core_services[service_name] = enhanced_info
        else:
            self.business_services[service_name] = enhanced_info
```

---

## 💼 Business Layer (Level 3 Data Flow + Level 4 Intelligence)

### **Level 3 - Data Flow Services**:

#### **3.1 MT5 Integration** - Enhanced Data Bridge (Port 8001):
```python
# Business-enhanced Data Bridge
class BusinessDataBridge:
    def __init__(self):
        self.ai_trading_base = DataBridge()  # 18+ ticks/second heritage
        self.business_targets = {
            'ticks_per_second': 50,  # 178% improvement target
            'latency_ms': 10,
            'availability': 99.99
        }

    async def stream_market_data(self, user_context: UserContext):
        """Stream MT5 data dengan user isolation"""
        while True:
            # Get raw market data
            raw_ticks = await self.ai_trading_base.get_mt5_ticks()

            # Apply subscription filtering
            filtered_ticks = self.apply_subscription_filter(raw_ticks, user_context)

            # Add user context
            user_ticks = self.add_user_context(filtered_ticks, user_context)

            # Stream to backend services
            await self.stream_to_services(user_ticks)

            # Track usage for billing
            await self.track_usage(len(user_ticks), user_context)
```

#### **3.2-3.4 Data Processing Pipeline**:
```python
class BusinessDataPipeline:
    def __init__(self):
        self.validation_service = DataValidationService()
        self.processing_service = DataProcessingService()
        self.storage_service = StorageService()

    async def process_user_data(self, raw_data: RawData, user_context: UserContext):
        """Complete data pipeline dengan user context"""
        # 3.2 Data Validation
        validated_data = await self.validation_service.validate(raw_data, user_context)

        # 3.3 Data Processing
        processed_data = await self.processing_service.process(validated_data, user_context)

        # 3.4 Storage Strategy
        await self.storage_service.store(processed_data, user_context)

        return processed_data
```

### **Level 4 - Intelligence Services**:

#### **4.1 AI Orchestration (Port 8003)** - Multi-Model Orchestrator:
```python
class BusinessAIOrchestrator:
    def __init__(self):
        self.ai_trading_base = AIOrchestration()  # Heritage
        self.multi_agent_framework = MultiAgentFramework()

    async def orchestrate_ai_decision(self, market_data: MarketData, user_context: UserContext):
        """Orchestrate AI decision dengan multi-agent coordination"""
        # Get available agents for user tier
        available_agents = self.get_tier_agents(user_context.subscription_tier)

        # Coordinate multi-agent analysis
        agent_analyses = await self.multi_agent_framework.analyze_market(
            market_data, available_agents, user_context
        )

        # Generate consensus decision
        consensus_decision = await self.generate_consensus(agent_analyses)

        return consensus_decision
```

#### **Multi-Agent Framework** (dari Plan2):
```python
class MultiAgentFramework:
    def __init__(self):
        self.research_agents = {
            'market_analysis': MarketAnalysisAgent(),
            'news_sentiment': NewsSentimentAgent(),
            'technical_indicator': TechnicalIndicatorAgent(),
            'fundamental_analysis': FundamentalAnalysisAgent()
        }

        self.decision_agents = {
            'strategy_formulation': StrategyFormulationAgent(),
            'risk_assessment': RiskAssessmentAgent(),
            'portfolio_optimization': PortfolioOptimizationAgent(),
            'execution_timing': ExecutionTimingAgent()
        }

        self.learning_agents = {
            'performance_analysis': PerformanceAnalysisAgent(),
            'model_improvement': ModelImprovementAgent(),
            'adaptation': AdaptationAgent(),
            'knowledge_synthesis': KnowledgeSynthesisAgent()
        }

    def get_tier_agents(self, subscription_tier: str) -> List[Agent]:
        """Get available agents berdasarkan subscription tier"""
        tier_agents = {
            'free': ['market_analysis'],
            'pro': ['market_analysis', 'technical_indicator', 'risk_assessment'],
            'enterprise': list(self.research_agents.keys()) +
                        list(self.decision_agents.keys()) +
                        list(self.learning_agents.keys())
        }
        return tier_agents.get(subscription_tier, [])
```

#### **4.2 Deep Learning (Port 8004)**:
```python
class BusinessDeepLearning:
    def __init__(self):
        self.neural_networks = {
            'lstm_predictor': LSTMPredictor(),
            'cnn_pattern_recognizer': CNNPatternRecognizer(),
            'transformer_analyzer': TransformerAnalyzer(),
            'gan_data_augmenter': GANDataAugmenter()
        }

    async def neural_analysis(self, data: ProcessedData, user_context: UserContext):
        """Neural network analysis dengan subscription limits"""
        tier_models = self.get_tier_models(user_context.subscription_tier)

        analyses = {}
        for model_name in tier_models:
            model = self.neural_networks[model_name]
            analysis = await model.analyze(data, user_context)
            analyses[model_name] = analysis

        return self.combine_neural_analyses(analyses)
```

#### **4.3 ML Processing (Port 8006)**:
```python
class BusinessMLProcessing:
    def __init__(self):
        self.ml_algorithms = {
            'random_forest': RandomForestProcessor(),
            'xgboost': XGBoostProcessor(),
            'svm': SVMProcessor(),
            'linear_regression': LinearRegressionProcessor(),
            'kmeans_clustering': KMeansProcessor()
        }

    async def ml_analysis(self, features: ProcessedFeatures, user_context: UserContext):
        """Traditional ML analysis dengan tier-based access"""
        tier_algorithms = self.get_tier_algorithms(user_context.subscription_tier)

        results = {}
        for algo_name in tier_algorithms:
            algorithm = self.ml_algorithms[algo_name]
            result = await algorithm.process(features, user_context)
            results[algo_name] = result

        return self.ensemble_ml_results(results)
```

#### **4.4 Trading Engine (Port 8007)**:
```python
class BusinessTradingEngine:
    def __init__(self):
        self.ai_trading_base = TradingEngine()  # Heritage
        self.business_features = BusinessTradingFeatures()

    async def execute_trade(self, trade_signal: TradeSignal, user_context: UserContext):
        """Execute trade dengan business constraints"""
        # Check subscription limits
        if not await self.check_trading_limits(user_context):
            raise TradingLimitExceeded("Subscription tier limit reached")

        # Apply risk management
        risk_assessed_signal = await self.assess_risk(trade_signal, user_context)

        # Execute via ai_trading base
        execution_result = await self.ai_trading_base.execute(risk_assessed_signal)

        # Track for billing
        await self.track_trade_execution(execution_result, user_context)

        return execution_result
```

## 🔄 Service Integration Patterns

### **Core Service Dependencies** (dari Plan2):
```python
class ServiceDependencyManager:
    def __init__(self):
        self.dependencies = {
            'api_gateway': [],  # Entry point
            'data_bridge': ['database_service'],
            'performance_analytics': ['all_services'],
            'ai_services': ['database_service', 'ai_provider'],
            'trading_engine': ['database_service', 'data_bridge'],
            'user_service': ['database_service']
        }

        self.business_dependencies = {
            'user_management': ['database_service'],
            'subscription_service': ['user_management', 'database_service'],
            'payment_gateway': ['subscription_service'],
            'notification_service': ['user_management'],
            'billing_service': ['subscription_service', 'payment_gateway']
        }
```

### **Performance Targets** (dari Plan2):
```yaml
Backend_Performance_Targets:
  AI_Decision_Making: "<15ms (85% improvement dari ai_trading baseline)"
  Order_Execution: "<1.2ms (76% improvement dari ai_trading baseline)"
  Data_Processing: "50+ ticks/second (178% improvement)"
  System_Availability: "99.99% (business-grade enhancement)"
  Multi_Tenant_Scalability: "2000+ concurrent users"

Service_Performance:
  API_Gateway: "<10ms routing latency"
  Database_Service: "<100ms query response"
  Data_Bridge: "50+ ticks/second processing"
  AI_Services: "<15ms decision latency"
  Trading_Engine: "<1.2ms execution time"
```

## 🔒 Backend Security Architecture

### **Multi-Tenant Security**:
```python
class BackendSecurityManager:
    def __init__(self):
        self.tenant_isolation = TenantIsolationManager()
        self.subscription_enforcer = SubscriptionEnforcer()
        self.audit_logger = AuditLogger()

    async def secure_request(self, request: Request, user_context: UserContext):
        """Apply comprehensive security untuk backend request"""
        # Tenant isolation
        isolated_request = await self.tenant_isolation.isolate(request, user_context)

        # Subscription enforcement
        authorized_request = await self.subscription_enforcer.authorize(
            isolated_request, user_context
        )

        # Audit logging
        await self.audit_logger.log_request(authorized_request, user_context)

        return authorized_request
```

**Backend Tier Status**: PLANNED - Foundation untuk complete AI trading platform
**Performance Foundation**: AI Trading heritage + business enhancements untuk enterprise scalability