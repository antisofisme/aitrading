# Internal Contract: Bidirectional Routing Engine

## Purpose
Central routing engine dalam API Gateway yang mengatur traffic flow untuk semua input dan output communications dengan integration ke Central Hub untuk service discovery dan backend coordination.

## Architecture Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Router  │────│  Routing Engine  │────│  Output Router  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ Tenant  │              │ Central │              │ Format  │
    │ Filter  │              │ Hub API │              │ Output  │
    └─────────┘              └─────────┘              └─────────┘
```

## Core Routing Schema
```protobuf
message RoutingEngine {
  RoutingConfig config = 1;
  repeated RouteDefinition routes = 2;
  CentralHubIntegration central_hub = 3;
  RoutingMetrics metrics = 4;
  int64 last_updated = 5;
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
  string service_name = 2;            // Service name for Central Hub discovery
  Authentication auth = 3;            // Destination authentication
  FailoverConfig failover = 4;        // Failover configuration
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

message CentralHubIntegration {
  string hub_endpoint = 1;            // Central Hub service endpoint
  int32 discovery_timeout_ms = 2;     // 5000ms service discovery timeout
  int32 cache_ttl_seconds = 3;        // 30 seconds cache TTL
  bool enable_fallback_cache = 4;     // Use cache when Hub unavailable
  Authentication hub_auth = 5;        // Central Hub authentication
}

message ServiceDiscoveryCache {
  string service_name = 1;            // Service identifier
  repeated string endpoints = 2;      // Cached healthy endpoints
  int64 last_updated = 3;             // Last cache update timestamp
  int64 expires_at = 4;               // Cache expiration timestamp
  HealthStatus status = 5;            // Last known health status
}

message RoutingMetrics {
  int64 total_requests = 1;           // Total routed requests
  int64 successful_routes = 2;        // Successful routing count
  int64 failed_routes = 3;            // Failed routing count
  double average_latency_ms = 4;      // Average routing latency
  double p95_latency_ms = 5;          // 95th percentile latency
  int64 service_discovery_failures = 6; // Central Hub discovery failures
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

message ServiceEndpoint {
  string service_name = 1;            // Service name in Central Hub
  string endpoint_url = 2;            // Actual endpoint URL
  HealthStatus health = 3;            // Health status from Central Hub
  int64 last_health_check = 4;        // Last health check timestamp
}

message CentralHubConfig {
  bool enable_service_discovery = 1;  // Enable Central Hub integration
  int32 discovery_interval_seconds = 2; // 30 seconds discovery refresh
  int32 health_check_timeout_ms = 3;  // 5000ms health check timeout
  int32 max_retry_attempts = 4;       // 3 max retry attempts
  bool enable_cache_fallback = 5;     // Use cache when Hub unavailable
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

enum ServiceDiscoveryStrategy {
  CENTRAL_HUB_PRIMARY = 0;            // Use Central Hub as primary
  CACHE_FALLBACK = 1;                 // Use cache when Hub unavailable
  HYBRID_DISCOVERY = 2;               // Combine Hub + local cache
}

enum CacheStrategy {
  NO_CACHE = 0;                       // Always query Central Hub
  SHORT_CACHE = 1;                    // 30 second cache TTL
  LONG_CACHE = 2;                     // 5 minute cache TTL
  PERSISTENT_CACHE = 3;               // Cache survives restarts
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

  // 4. Service Discovery via Central Hub
  endpoint = await centralHub.queryServiceEndpoint(targetService);
  if (!endpoint) return SERVICE_UNAVAILABLE;

  // 5. Direct Service Call
  return await callServiceDirectly(request, endpoint);
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

    // 4. Service Health Check via Central Hub
    if (await centralHub.isServiceHealthy(channel)) {
      await sendDirectlyToService(formattedData, channel);
    }
  }
}
```

## Performance Optimizations

### **Caching Strategy**
- **Route Cache**: Cache routing decisions untuk 5 minutes
- **Service Discovery Cache**: Cache Central Hub endpoint data untuk 30 seconds
- **Authentication Cache**: Cache JWT validation untuk 10 minutes
- **Health Status Cache**: Cache service health status untuk 1 minute

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
- **Central Hub Integration**: Track service discovery performance
- **Endpoint Health**: Monitor service availability via Central Hub

### **Alert Conditions**
- **High Latency**: Alert if routing latency >10ms
- **Central Hub Unavailable**: Alert on service discovery failures
- **Endpoint Failures**: Alert if endpoint success rate <95%
- **Service Discovery Issues**: Alert on Central Hub communication problems

### **Auto-Recovery Mechanisms**
- **Service Discovery Fallback**: Cache-based routing when Central Hub unavailable
- **Health Status Refresh**: Periodic Central Hub health data updates
- **Route Failover**: Automatic failover to backup routes via Central Hub
- **Connection Recovery**: Automatic Central Hub reconnection