# Input Contract: Notification-Hub → API Gateway

## Purpose
Notification-Hub mengirim system status, health alerts, dan operational notifications ke API Gateway untuk distribution ke user channels (Telegram, Dashboard).

## Protocol Buffer Schema
**Source**: `central-hub/static/proto/notifications/notification-input.proto`
**Message Type**: `NotificationInput`
**Transport**: HTTP POST dengan Protocol Buffers binary

## Data Flow
1. System services → Notification-Hub → Collect health status dan alerts
2. Notification-Hub aggregate dan generate notifications
3. Send ke API Gateway via HTTP POST
4. API Gateway route ke appropriate user channels

## Schema Definition
```protobuf
message NotificationInput {
  string user_id = 1;
  string company_id = 2;
  repeated SystemNotification notifications = 3;
  ServiceHealthStatus health_status = 4;
  repeated AlertEvent alerts = 5;
  int64 timestamp = 6;
  string correlation_id = 7;
}

message SystemNotification {
  NotificationType type = 1;          // SYSTEM/TRADING/PERFORMANCE/SECURITY
  NotificationPriority priority = 2;  // LOW/MEDIUM/HIGH/CRITICAL
  string title = 3;                   // "MT5 Connection Lost"
  string message = 4;                 // Detailed notification message
  string source_service = 5;          // "client-mt5"
  NotificationAction action = 6;      // Required user action
  int64 expires_at = 7;              // Notification expiration
  string notification_id = 8;         // Unique identifier
}

message ServiceHealthStatus {
  string service_name = 1;            // "trading-engine"
  HealthStatus status = 2;            // HEALTHY/DEGRADED/DOWN/UNKNOWN
  double cpu_usage = 3;               // 0.75 (75%)
  double memory_usage = 4;            // 0.85 (85%)
  int32 active_connections = 5;       // Current connection count
  double response_time_ms = 6;        // Average response time
  int64 uptime_seconds = 7;           // Service uptime
  repeated string error_messages = 8; // Recent error logs
}

message AlertEvent {
  AlertType type = 1;                 // PERFORMANCE/SECURITY/TRADING/SYSTEM
  AlertSeverity severity = 2;         // INFO/WARNING/ERROR/CRITICAL
  string description = 3;             // "High CPU usage detected"
  string affected_service = 4;        // Service experiencing issue
  AlertMetrics metrics = 5;           // Performance metrics
  string resolution_steps = 6;        // Suggested actions
  bool auto_resolved = 7;             // If alert auto-resolved
  int64 alert_timestamp = 8;          // When alert was triggered
}

message NotificationAction {
  ActionType type = 1;                // VIEW/ACKNOWLEDGE/RESTART/CONFIGURE
  string action_url = 2;              // Dashboard link or API endpoint
  string button_text = 3;             // "Restart Service"
  ActionParams params = 4;            // Additional action parameters
}

message ActionParams {
  string service_id = 1;              // Target service for action
  map<string, string> parameters = 2; // Key-value action parameters
  bool requires_confirmation = 3;     // If action needs user confirmation
}

message AlertMetrics {
  double threshold_value = 1;         // Alert threshold
  double current_value = 2;           // Current metric value
  string metric_unit = 3;             // "%" or "ms" or "count"
  double duration_minutes = 4;        // How long metric exceeded threshold
}

enum NotificationType {
  SYSTEM_STATUS = 0;
  TRADING_UPDATE = 1;
  PERFORMANCE_ALERT = 2;
  SECURITY_WARNING = 3;
  MAINTENANCE_NOTICE = 4;
}

enum NotificationPriority {
  LOW = 0;
  MEDIUM = 1;
  HIGH = 2;
  CRITICAL = 3;
}

enum HealthStatus {
  HEALTHY = 0;
  DEGRADED = 1;
  DOWN = 2;
  UNKNOWN = 3;
}

enum AlertType {
  PERFORMANCE_ALERT = 0;
  SECURITY_ALERT = 1;
  TRADING_ALERT = 2;
  SYSTEM_ALERT = 3;
}

enum AlertSeverity {
  INFO = 0;
  WARNING = 1;
  ERROR = 2;
  CRITICAL = 3;
}

enum ActionType {
  VIEW_DETAILS = 0;
  ACKNOWLEDGE = 1;
  RESTART_SERVICE = 2;
  CONFIGURE_SETTINGS = 3;
  CONTACT_SUPPORT = 4;
}
```

## Processing Requirements
- **Priority Filtering**: Route critical alerts immediately
- **User Subscription**: Filter notifications based on user subscription tier
- **Rate Limiting**: Prevent notification spam (max 5/minute per user)
- **Deduplication**: Avoid sending duplicate notifications within 1 hour

## Output Destinations
- **Critical Alerts** → Telegram Bot (immediate notification)
- **System Status** → Frontend Dashboard (real-time updates)
- **Performance Metrics** → Analytics Service (historical tracking)
- **Maintenance Notices** → Email Service (scheduled notifications)

## Alert Escalation Rules
- **Critical Severity** → Immediate notification to all channels
- **High Priority** → Telegram + Dashboard notification
- **Medium Priority** → Dashboard notification only
- **Low Priority** → Dashboard history log only

## Security Requirements
- **Access Control**: Verify user has permission to receive notifications
- **Data Sanitization**: Remove sensitive information from messages
- **Audit Trail**: Log all notification deliveries
- **Encryption**: Encrypt notification payloads during transit