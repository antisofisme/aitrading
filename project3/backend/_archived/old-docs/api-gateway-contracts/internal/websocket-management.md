# Internal Contract: WebSocket Management System

## Purpose
Comprehensive WebSocket connection management dalam API Gateway untuk real-time communication dengan Frontend Dashboard dan Client-MT5 applications dengan scalable connection pooling dan message routing.

## Architecture Overview
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Connection    │────│   Message        │────│   Subscription  │
│   Manager       │    │   Router         │    │   Manager       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
    ┌────▼────┐              ┌────▼────┐              ┌────▼────┐
    │ Session │              │ Message │              │ Channel │
    │ Store   │              │ Queue   │              │ Groups  │
    └─────────┘              └─────────┘              └─────────┘
```

## Core WebSocket Schema
```protobuf
message WebSocketManager {
  ManagerConfig config = 1;
  repeated ConnectionPool pools = 2;
  MessageRouter message_router = 3;
  SubscriptionManager subscriptions = 4;
  ConnectionMetrics metrics = 5;
  int64 last_updated = 6;
}

message ManagerConfig {
  string manager_id = 1;              // "ws-manager-v1"
  int32 max_connections = 2;          // 10000 concurrent connections
  int32 connection_timeout_ms = 3;    // 300000 (5 minutes)
  int32 heartbeat_interval_ms = 4;    // 30000 (30 seconds)
  int32 message_buffer_size = 5;      // 1000 messages per connection
  bool enable_compression = 6;        // Enable WebSocket compression
  CompressionConfig compression = 7;  // Compression configuration
}

message ConnectionPool {
  string pool_id = 1;                 // "frontend-pool", "mt5-pool"
  PoolType type = 2;                  // FRONTEND/MT5_CLIENT/ADMIN
  repeated WebSocketConnection connections = 3;
  PoolConfig config = 4;
  PoolMetrics metrics = 5;
}

message WebSocketConnection {
  string connection_id = 1;           // Unique connection identifier
  string user_id = 2;                 // Associated user
  string company_id = 3;              // Multi-tenant company ID
  ConnectionState state = 4;          // CONNECTING/CONNECTED/DISCONNECTED
  ConnectionInfo info = 5;            // Connection metadata
  SubscriptionList subscriptions = 6; // Active subscriptions
  MessageQueue message_queue = 7;     // Outbound message queue
  ConnectionMetrics conn_metrics = 8; // Connection-specific metrics
  int64 created_at = 9;              // Connection creation time
  int64 last_activity = 10;          // Last message timestamp
}

message ConnectionInfo {
  string remote_address = 1;          // Client IP address
  string user_agent = 2;              // Client user agent
  string protocol_version = 3;        // WebSocket protocol version
  repeated string extensions = 4;     // Enabled WebSocket extensions
  AuthenticationInfo auth = 5;        // Authentication information
  string session_id = 6;              // Session identifier
}

message MessageRouter {
  repeated RoutingRule rules = 1;     // Message routing rules
  MessageQueue global_queue = 2;      // Global message queue
  BroadcastConfig broadcast = 3;      // Broadcast configuration
  RoutingMetrics routing_metrics = 4; // Routing performance metrics
}

message RoutingRule {
  string rule_id = 1;                 // "trading-signals-route"
  MessageFilter filter = 2;           // Message filtering criteria
  RoutingTarget target = 3;           // Target destination
  TransformationRule transform = 4;   // Message transformation
  int32 priority = 5;                 // Rule priority (higher = first)
  bool enabled = 6;                   // Rule enabled status
}

message MessageFilter {
  repeated string message_types = 1;  // "trading_status", "notifications"
  repeated string user_ids = 2;       // Target user IDs
  repeated string company_ids = 3;    // Target company IDs
  repeated string channels = 4;       // Target channels
  FilterExpression expression = 5;    // Advanced filtering logic
}

message RoutingTarget {
  TargetType type = 1;                // INDIVIDUAL/GROUP/BROADCAST
  repeated string connection_ids = 2; // Target connection IDs
  string group_id = 3;               // Target group ID
  bool reliable_delivery = 4;         // Guarantee delivery
  int32 max_retries = 5;             // Max retry attempts
}

message SubscriptionManager {
  repeated ChannelGroup channels = 1; // Subscription channels
  SubscriptionRules rules = 2;        // Subscription management rules
  SubscriptionMetrics sub_metrics = 3; // Subscription metrics
}

message ChannelGroup {
  string group_id = 1;                // "trading-signals", "system-status"
  string group_name = 2;              // Human-readable name
  GroupType type = 3;                 // USER_SPECIFIC/COMPANY_WIDE/GLOBAL
  repeated string subscribed_users = 4; // Subscribed user IDs
  ChannelConfig config = 5;           // Channel configuration
  MessageBuffer buffer = 6;           // Message history buffer
}

message SubscriptionList {
  repeated Subscription subscriptions = 1;
  int64 last_updated = 2;
}

message Subscription {
  string subscription_id = 1;         // Unique subscription ID
  string channel_id = 2;              // Channel identifier
  SubscriptionType type = 3;          // REAL_TIME/BATCH/ON_DEMAND
  SubscriptionFilter filter = 4;      // Content filtering
  bool active = 5;                    // Subscription active status
  int64 created_at = 6;              // Subscription creation time
}

message MessageQueue {
  string queue_id = 1;                // Queue identifier
  repeated QueuedMessage messages = 2; // Queued messages
  QueueConfig config = 3;             // Queue configuration
  QueueMetrics queue_metrics = 4;     // Queue performance metrics
}

message QueuedMessage {
  string message_id = 1;              // Unique message ID
  string content = 2;                 // Message content
  MessagePriority priority = 3;       // Message priority
  int64 created_at = 4;              // Message creation time
  int64 expires_at = 5;              // Message expiration
  int32 retry_count = 6;             // Current retry count
  MessageMetadata metadata = 7;       // Additional metadata
}

message ConnectionMetrics {
  int64 messages_sent = 1;            // Total messages sent
  int64 messages_received = 2;        // Total messages received
  int64 bytes_sent = 3;               // Total bytes sent
  int64 bytes_received = 4;           // Total bytes received
  double avg_latency_ms = 5;          // Average message latency
  int64 connection_duration = 6;      // Connection duration in seconds
  int32 reconnection_count = 7;       // Number of reconnections
  int64 last_heartbeat = 8;          // Last heartbeat timestamp
}

enum PoolType {
  FRONTEND_POOL = 0;                  // Frontend dashboard connections
  MT5_CLIENT_POOL = 1;               // MT5 client connections
  ADMIN_POOL = 2;                    // Admin panel connections
  API_POOL = 3;                      // External API connections
}

enum ConnectionState {
  CONNECTING = 0;
  CONNECTED = 1;
  DISCONNECTING = 2;
  DISCONNECTED = 3;
  ERROR = 4;
}

enum TargetType {
  INDIVIDUAL = 0;                     // Single connection
  GROUP = 1;                         // Group of connections
  BROADCAST = 2;                     // All connections
  FILTERED = 3;                      // Filtered connections
}

enum GroupType {
  USER_SPECIFIC = 0;                 // User-specific channels
  COMPANY_WIDE = 1;                  // Company-wide channels
  GLOBAL = 2;                        // Global channels
  ADMIN_ONLY = 3;                    // Admin-only channels
}

enum SubscriptionType {
  REAL_TIME = 0;                     // Real-time updates
  BATCH = 1;                         // Batched updates
  ON_DEMAND = 2;                     // On-demand updates
  HISTORICAL = 3;                    // Historical data
}

enum MessagePriority {
  CRITICAL = 0;                      // Critical messages (system alerts)
  HIGH = 1;                          // High priority (trading signals)
  NORMAL = 2;                        // Normal priority (updates)
  LOW = 3;                           // Low priority (analytics)
}
```

## Connection Lifecycle Management

### **Connection Establishment**
```javascript
// WebSocket connection handshake process
function handleConnectionRequest(request) {
  // 1. Authentication Validation
  if (!validateJWT(request.headers.authorization)) {
    return rejectConnection(401, "Invalid authentication");
  }

  // 2. Rate Limiting Check
  if (!checkConnectionRateLimit(request.user_id)) {
    return rejectConnection(429, "Connection rate limit exceeded");
  }

  // 3. Pool Assignment
  pool = selectConnectionPool(request.client_type);
  if (pool.isFull()) {
    return rejectConnection(503, "Connection pool full");
  }

  // 4. Connection Creation
  connection = createConnection(request, pool);

  // 5. Subscription Initialization
  initializeDefaultSubscriptions(connection);

  return acceptConnection(connection);
}
```

### **Heartbeat Management**
```javascript
// Heartbeat mechanism for connection health
function heartbeatManager() {
  setInterval(() => {
    for (connection of activeConnections) {
      if (connection.isStale()) {
        sendHeartbeat(connection);

        // Mark connection for cleanup if unresponsive
        if (connection.missedHeartbeats > 3) {
          closeConnection(connection, "Heartbeat timeout");
        }
      }
    }
  }, HEARTBEAT_INTERVAL);
}
```

## Message Routing & Delivery

### **Real-time Message Distribution**
```javascript
// High-performance message routing
function routeMessage(message, connections) {
  // 1. Message Validation
  if (!validateMessage(message)) return;

  // 2. Target Selection
  targets = selectTargetConnections(message, connections);

  // 3. Message Transformation
  for (target of targets) {
    transformedMessage = transformForConnection(message, target);

    // 4. Delivery with Circuit Breaker
    if (!circuitBreaker.isOpen(target)) {
      deliverMessage(transformedMessage, target);
    } else {
      queueForLaterDelivery(message, target);
    }
  }
}
```

### **Subscription Management**
```javascript
// Dynamic subscription management
function handleSubscription(connection, subscriptionRequest) {
  // 1. Permission Validation
  if (!hasPermission(connection.user_id, subscriptionRequest.channel)) {
    return sendError(connection, "Insufficient permissions");
  }

  // 2. Subscription Creation
  subscription = createSubscription(subscriptionRequest);

  // 3. Channel Assignment
  assignToChannel(connection, subscription);

  // 4. Historical Data Delivery (if requested)
  if (subscriptionRequest.include_history) {
    sendHistoricalData(connection, subscription);
  }
}
```

## Performance Optimizations

### **Connection Pooling**
- **Pool Segregation**: Separate pools untuk different client types
- **Dynamic Scaling**: Auto-scale pools based on demand
- **Connection Reuse**: Efficient connection lifecycle management
- **Memory Optimization**: Optimized memory usage per connection

### **Message Batching**
- **Batch Accumulation**: Batch non-critical messages
- **Intelligent Timing**: Send batches at optimal intervals
- **Compression**: Compress large message batches
- **Priority Handling**: Ensure critical messages bypass batching

### **Caching Strategy**
- **Subscription Cache**: Cache subscription lists
- **Message Cache**: Cache frequently accessed messages
- **User Context Cache**: Cache user permissions dan preferences
- **Connection Metadata Cache**: Cache connection information

## Monitoring & Health Checks

### **Connection Health Monitoring**
```javascript
// Connection health assessment
function assessConnectionHealth() {
  for (connection of connections) {
    health = {
      latency: calculateLatency(connection),
      throughput: calculateThroughput(connection),
      errorRate: calculateErrorRate(connection),
      uptime: calculateUptime(connection)
    };

    updateConnectionHealth(connection.id, health);

    // Auto-remediation for unhealthy connections
    if (health.errorRate > 0.05) {
      attemptConnectionRecovery(connection);
    }
  }
}
```

### **Key Performance Metrics**
- **Connection Count**: Active connection monitoring
- **Message Throughput**: Messages per second capacity
- **Latency Tracking**: End-to-end message latency
- **Error Rates**: Connection dan message error rates
- **Resource Usage**: Memory dan CPU usage per connection

### **Auto-Recovery Mechanisms**
- **Connection Recovery**: Automatic reconnection handling
- **Message Replay**: Replay missed messages after reconnection
- **State Synchronization**: Sync connection state after recovery
- **Failover Support**: Automatic failover to backup instances

## Security Features

### **Connection Security**
- **TLS Enforcement**: Require WSS (WebSocket Secure)
- **JWT Validation**: Continuous token validation
- **IP Whitelisting**: Optional IP-based access control
- **Rate Limiting**: Per-user connection dan message limits

### **Message Security**
- **Content Validation**: Validate all incoming messages
- **Sanitization**: Sanitize message content
- **Encryption**: Optional message-level encryption
- **Audit Logging**: Log all security-relevant events