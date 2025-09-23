# Internal Contract: Bidirectional Routing Engine

## Purpose
Central routing engine dalam API Gateway yang mengatur traffic flow untuk semua input dan output communications dengan intelligent load balancing dan circuit breaker protection.

## Architecture Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Router  │────│  Routing Engine  │────│  Output Router  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ Circuit │              │ Load    │              │ Circuit │
    │ Breaker │              │ Balance │              │ Breaker │
    └─────────┘              └─────────┘              └─────────┘
```

## Core Routing Schema
```protobuf
message RoutingEngine {
  RoutingConfig config = 1;
  repeated RouteDefinition routes = 2;
  LoadBalancer load_balancer = 3;
  CircuitBreaker circuit_breaker = 4;
  RoutingMetrics metrics = 5;
  int64 last_updated = 6;
}

message RoutingConfig {
  string engine_id = 1;               // "api-gateway-router-v1"
  int32 max_concurrent_routes = 2;    // 1000
  int32 route_timeout_ms = 3;         // 30000 (30 seconds)
  int32 health_check_interval = 4;    // 30 seconds
  bool enable_adaptive_routing = 5;   // Dynamic route optimization
  RetryPolicy default_retry = 6;
}

message RouteDefinition {
  string route_id = 1;                // "trading-engine-input"
  RouteType type = 2;                 // INPUT/OUTPUT/BIDIRECTIONAL
  RouteSource source = 3;             // Source configuration
  RouteDestination destination = 4;   // Target configuration
  RoutingRules rules = 5;             // Filtering and processing rules
  RouteHealth health = 6;             // Route health status
}

message RouteSource {
  SourceType type = 1;                // HTTP/WEBSOCKET/KAFKA/GRPC
  string endpoint = 2;                // Source endpoint/topic
  Authentication auth = 3;            // Authentication requirements
  repeated string allowed_origins = 4; // CORS configuration
  RateLimiting rate_limits = 5;       // Input rate limiting
}

message RouteDestination {
  DestinationType type = 1;           // HTTP/WEBSOCKET/KAFKA/GRPC
  repeated string endpoints = 2;      // Multiple endpoints for load balancing
  Authentication auth = 3;            // Destination authentication
  LoadBalanceStrategy strategy = 4;   // ROUND_ROBIN/WEIGHTED/LEAST_CONN
  FailoverConfig failover = 5;        // Failover configuration
}

message RoutingRules {
  repeated FilterRule filters = 1;    // Content filtering rules
  TransformationRule transform = 2;   // Data transformation rules
  SecurityRule security = 3;          // Security enforcement
  CompanyFilter company_filter = 4;   // Multi-tenant filtering
  UserFilter user_filter = 5;         // User-specific filtering
}

message FilterRule {
  string field_path = 1;              // "user_id", "company_id"
  FilterOperator operator = 2;        // EQUALS/CONTAINS/REGEX
  repeated string values = 3;         // Filter values
  FilterAction action = 4;            // ALLOW/DENY/TRANSFORM
}

message TransformationRule {
  InputFormat input_format = 1;       // PROTOBUF/JSON/XML
  OutputFormat output_format = 2;     // PROTOBUF/JSON/XML
  repeated FieldMapping mappings = 3; // Field transformations
  string transformation_script = 4;   // Custom transformation logic
}

message LoadBalancer {
  LoadBalanceStrategy strategy = 1;   // ROUND_ROBIN/WEIGHTED/ADAPTIVE
  repeated EndpointWeight weights = 2; // Endpoint weight configuration
  HealthChecker health_checker = 3;   // Health checking configuration
  AdaptiveConfig adaptive = 4;        // Adaptive load balancing
}

message CircuitBreaker {
  string circuit_id = 1;              // Unique circuit identifier
  CircuitState state = 2;             // CLOSED/OPEN/HALF_OPEN
  int32 failure_threshold = 3;        // 10 failures to open
  int32 success_threshold = 4;        // 5 successes to close
  int32 timeout_seconds = 5;          // 30 seconds timeout
  FailurePattern pattern = 6;         // What constitutes failure
  CircuitMetrics metrics = 7;         // Circuit performance metrics
}

message RoutingMetrics {
  int64 total_requests = 1;           // Total routed requests
  int64 successful_routes = 2;        // Successful routing count
  int64 failed_routes = 3;            // Failed routing count
  double average_latency_ms = 4;      // Average routing latency
  double p95_latency_ms = 5;          // 95th percentile latency
  int64 circuit_breaker_trips = 6;    // Circuit breaker activation count
  repeated RoutePerformance route_perf = 7; // Per-route performance
}

message RouteHealth {
  HealthStatus status = 1;            // HEALTHY/DEGRADED/DOWN
  double success_rate = 2;            // 0.99 (99%)
  double avg_response_time = 3;       // Average response time
  int64 last_success = 4;             // Last successful request timestamp
  int64 last_failure = 5;             // Last failed request timestamp
  string failure_reason = 6;          // Last failure reason
}

message EndpointWeight {
  string endpoint = 1;                // Endpoint URL/address
  int32 weight = 2;                   // Load balancing weight (1-100)
  bool enabled = 3;                   // Endpoint enabled status
  EndpointMetrics metrics = 4;        // Endpoint-specific metrics
}

message AdaptiveConfig {
  bool enable_adaptive = 1;           // Enable adaptive load balancing
  int32 learning_window_minutes = 2;  // 10 minutes learning window
  double latency_weight = 3;          // 0.6 (60% weight to latency)
  double throughput_weight = 4;       // 0.4 (40% weight to throughput)
  double adaptation_rate = 5;         // 0.1 (10% adaptation per window)
}

enum RouteType {
  INPUT_ROUTE = 0;                    // Incoming traffic routing
  OUTPUT_ROUTE = 1;                   // Outgoing traffic routing
  BIDIRECTIONAL_ROUTE = 2;            // Two-way communication
}

enum SourceType {
  HTTP_SOURCE = 0;
  WEBSOCKET_SOURCE = 1;
  KAFKA_SOURCE = 2;
  GRPC_SOURCE = 3;
}

enum DestinationType {
  HTTP_DEST = 0;
  WEBSOCKET_DEST = 1;
  KAFKA_DEST = 2;
  GRPC_DEST = 3;
}

enum LoadBalanceStrategy {
  ROUND_ROBIN = 0;
  WEIGHTED_ROUND_ROBIN = 1;
  LEAST_CONNECTIONS = 2;
  LEAST_LATENCY = 3;
  ADAPTIVE = 4;
}

enum CircuitState {
  CLOSED = 0;                         // Normal operation
  OPEN = 1;                           // Circuit breaker active
  HALF_OPEN = 2;                      // Testing recovery
}

enum FilterOperator {
  EQUALS = 0;
  NOT_EQUALS = 1;
  CONTAINS = 2;
  REGEX_MATCH = 3;
  GREATER_THAN = 4;
  LESS_THAN = 5;
}

enum FilterAction {
  ALLOW = 0;
  DENY = 1;
  TRANSFORM = 2;
  LOG_ONLY = 3;
}

enum HealthStatus {
  HEALTHY = 0;
  DEGRADED = 1;
  DOWN = 2;
  UNKNOWN = 3;
}
```

## Routing Decision Matrix

### **Input Routing Logic**
```javascript
// Pseudo-code for input routing decisions
function routeIncomingRequest(request) {
  // 1. Authentication & Authorization
  if (!validateAuth(request)) return REJECT;

  // 2. Rate Limiting Check
  if (!checkRateLimit(request.user_id)) return RATE_LIMITED;

  // 3. Multi-tenant Filtering
  if (!validateCompanyAccess(request)) return FORBIDDEN;

  // 4. Circuit Breaker Check
  if (circuitBreaker.isOpen(targetService)) return SERVICE_UNAVAILABLE;

  // 5. Load Balancing Selection
  endpoint = loadBalancer.selectEndpoint(targetService);

  // 6. Route to Selected Endpoint
  return forwardRequest(request, endpoint);
}
```

### **Output Routing Logic**
```javascript
// Pseudo-code for output routing decisions
function routeOutgoingData(data, user_preferences) {
  // 1. User Subscription Filtering
  filteredData = filterBySubscription(data, user_preferences);

  // 2. Channel Selection
  channels = selectChannels(data.priority, user_preferences);

  // 3. Format Transformation
  for (channel in channels) {
    formattedData = transformForChannel(filteredData, channel);

    // 4. Circuit Breaker Protection
    if (!circuitBreaker.isOpen(channel)) {
      sendToChannel(formattedData, channel);
    }
  }
}
```

## Performance Optimizations

### **Caching Strategy**
- **Route Cache**: Cache routing decisions untuk 5 minutes
- **Health Cache**: Cache endpoint health untuk 30 seconds
- **Authentication Cache**: Cache JWT validation untuk 10 minutes
- **Load Balancing Cache**: Cache endpoint selection untuk 1 minute

### **Connection Pooling**
- **HTTP Connections**: Reuse HTTP connections untuk outbound requests
- **WebSocket Pools**: Maintain WebSocket connection pools
- **Database Connections**: Pool database connections for metadata

### **Adaptive Routing**
- **Latency Monitoring**: Track endpoint response times
- **Throughput Analysis**: Monitor request success rates
- **Dynamic Weight Adjustment**: Adjust load balancing weights
- **Failure Pattern Recognition**: Learn from failure patterns

## Monitoring & Alerting

### **Key Metrics**
- **Routing Latency**: <2ms average routing decision time
- **Success Rate**: >99.9% successful routing
- **Circuit Breaker Health**: Track breaker state changes
- **Load Distribution**: Monitor endpoint load distribution

### **Alert Conditions**
- **High Latency**: Alert if routing latency >10ms
- **Circuit Breaker Trips**: Alert on circuit breaker activation
- **Endpoint Failures**: Alert if endpoint success rate <95%
- **Load Imbalance**: Alert if load distribution >20% imbalanced

### **Auto-Recovery Mechanisms**
- **Endpoint Health Recovery**: Automatic endpoint re-enablement
- **Circuit Breaker Reset**: Automatic circuit breaker reset
- **Load Rebalancing**: Dynamic load redistribution
- **Route Failover**: Automatic failover to backup routes