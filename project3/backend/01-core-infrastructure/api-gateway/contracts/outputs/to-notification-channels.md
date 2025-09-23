# Output Contract: API Gateway → Notification Channels

## Purpose
API Gateway mengirim structured notifications ke multiple channels (Telegram, Email, SMS, Push Notifications) berdasarkan user preferences dan notification priority.

## Protocol Buffer Schema
**Source**: `central-hub/static/proto/notifications/channel-output.proto`
**Message Type**: `ChannelNotification`
**Transport**: HTTP POST dengan Protocol Buffers binary

## Data Flow
1. API Gateway receive notifications from multiple sources
2. Apply user preferences dan priority filtering
3. Format notifications per channel requirements
4. Send ke appropriate notification channels

## Channel Types

### **1. Telegram Channel**
```protobuf
message TelegramChannelOutput {
  string bot_token = 1;               // Telegram bot authentication
  string chat_id = 2;                 // Target chat ID
  TelegramMessage message = 3;
  NotificationMetadata metadata = 4;
}

message TelegramMessage {
  string text = 1;                    // Formatted message text
  string parse_mode = 2;              // "Markdown" or "HTML"
  TelegramKeyboard keyboard = 3;      // Inline keyboard buttons
  bool disable_notification = 4;     // Silent notification
  string thread_id = 5;               // For group chat threads
}
```

### **2. Email Channel**
```protobuf
message EmailChannelOutput {
  string smtp_config = 1;             // SMTP server configuration
  EmailMessage message = 2;
  NotificationMetadata metadata = 3;
}

message EmailMessage {
  string to_email = 1;                // Recipient email
  string subject = 2;                 // Email subject
  string html_body = 3;               // HTML email content
  string text_body = 4;               // Plain text fallback
  repeated EmailAttachment attachments = 5;
  EmailPriority priority = 6;         // HIGH/NORMAL/LOW
}
```

### **3. SMS Channel**
```protobuf
message SMSChannelOutput {
  string provider_config = 1;         // SMS provider (Twilio, etc.)
  SMSMessage message = 2;
  NotificationMetadata metadata = 3;
}

message SMSMessage {
  string phone_number = 1;            // Recipient phone number
  string message_text = 2;            // SMS content (max 160 chars)
  string country_code = 3;            // "+62" for Indonesia
}
```

### **4. Push Notification Channel**
```protobuf
message PushChannelOutput {
  string fcm_config = 1;              // Firebase Cloud Messaging config
  PushMessage message = 2;
  NotificationMetadata metadata = 3;
}

message PushMessage {
  string device_token = 1;            // Target device FCM token
  string title = 2;                   // Notification title
  string body = 3;                    // Notification body
  map<string, string> data = 4;       // Additional data payload
  PushNotificationOptions options = 5;
}
```

## Universal Schema
```protobuf
message ChannelNotification {
  string user_id = 1;
  string company_id = 2;
  NotificationContent content = 3;
  repeated ChannelOutput channels = 4;
  NotificationRules rules = 5;
  int64 timestamp = 6;
  string correlation_id = 7;
}

message NotificationContent {
  string notification_id = 1;         // Unique identifier
  NotificationType type = 2;          // TRADING/SYSTEM/ALERT/INFO
  NotificationPriority priority = 3;  // CRITICAL/HIGH/MEDIUM/LOW
  string title = 4;                   // "Trading Signal Generated"
  string message = 5;                 // Main notification content
  string source_service = 6;          // "trading-engine"
  NotificationData data = 7;          // Structured notification data
  int64 expires_at = 8;              // Notification expiration
}

message ChannelOutput {
  ChannelType channel = 1;            // TELEGRAM/EMAIL/SMS/PUSH
  ChannelConfig config = 2;           // Channel-specific configuration
  string formatted_content = 3;       // Pre-formatted content for channel
  DeliveryOptions delivery = 4;       // Delivery preferences
}

message NotificationRules {
  repeated string enabled_channels = 1; // User-enabled channels
  TimeWindow quiet_hours = 2;         // Do not disturb hours
  FrequencyLimits limits = 3;         // Rate limiting rules
  PriorityFiltering filtering = 4;    // Priority-based filtering
}

message NotificationData {
  map<string, string> key_values = 1; // Structured data for templating
  repeated ActionButton actions = 2;   // Available user actions
  string deep_link = 3;               // App deep link
  repeated MediaAttachment media = 4;  // Images, charts, etc.
}

message ActionButton {
  string text = 1;                    // "View Signal"
  string action_type = 2;             // "url", "callback", "deeplink"
  string action_value = 3;            // URL or callback data
  bool primary = 4;                   // Primary action button
}

message DeliveryOptions {
  DeliveryPriority priority = 1;      // IMMEDIATE/SCHEDULED/BATCH
  int64 scheduled_time = 2;           // For scheduled delivery
  int32 retry_attempts = 3;           // Max retry attempts
  int32 retry_delay_seconds = 4;      // Delay between retries
}

message TimeWindow {
  string start_time = 1;              // "22:00" (10 PM)
  string end_time = 2;                // "07:00" (7 AM)
  string timezone = 3;                // "Asia/Jakarta"
}

message FrequencyLimits {
  int32 max_per_hour = 1;             // Max notifications per hour
  int32 max_per_day = 2;              // Max notifications per day
  bool batch_similar = 3;             // Batch similar notifications
}

enum ChannelType {
  TELEGRAM = 0;
  EMAIL = 1;
  SMS = 2;
  PUSH_NOTIFICATION = 3;
  WEBHOOK = 4;
}

enum NotificationType {
  TRADING_SIGNAL = 0;
  SYSTEM_ALERT = 1;
  PERFORMANCE_UPDATE = 2;
  SECURITY_WARNING = 3;
  MAINTENANCE_NOTICE = 4;
  ACCOUNT_UPDATE = 5;
}

enum NotificationPriority {
  CRITICAL = 0;                       // Immediate delivery, all channels
  HIGH = 1;                          // Fast delivery, primary channels
  MEDIUM = 2;                        // Normal delivery, user preferences
  LOW = 3;                           // Batch delivery, minimal channels
}

enum DeliveryPriority {
  IMMEDIATE = 0;                     // Send immediately
  SCHEDULED = 1;                     // Send at specific time
  BATCH = 2;                         // Batch with similar notifications
}

enum EmailPriority {
  EMAIL_HIGH = 0;
  EMAIL_NORMAL = 1;
  EMAIL_LOW = 2;
}
```

## Channel-Specific Processing

### **Telegram Processing**
- **Message Formatting**: Convert to Markdown/HTML
- **Button Generation**: Create inline keyboards for actions
- **Rate Limiting**: Respect Telegram API limits (30 messages/second)
- **Error Handling**: Handle blocked users, invalid chat IDs

### **Email Processing**
- **Template Engine**: Apply HTML email templates
- **Attachment Handling**: Include charts, reports as attachments
- **Deliverability**: DKIM signing, SPF validation
- **Bounce Handling**: Process bounce notifications

### **SMS Processing**
- **Character Limits**: Truncate or split long messages
- **International Format**: Format phone numbers correctly
- **Cost Optimization**: Use SMS only for critical notifications
- **Delivery Reports**: Track SMS delivery status

### **Push Notification Processing**
- **Platform Targeting**: Handle iOS/Android differences
- **Rich Content**: Include images, actions in push notifications
- **Badge Management**: Update app badge counts
- **Silent Notifications**: Background app updates

## User Preference Management
- **Channel Selection**: User chooses preferred notification channels
- **Quiet Hours**: Respect user-defined do not disturb periods
- **Content Filtering**: Filter notifications by type/priority
- **Frequency Control**: Rate limiting based on user preferences

## Delivery Tracking
- **Delivery Status**: Track successful/failed deliveries per channel
- **Read Receipts**: Track notification open rates (where available)
- **Action Tracking**: Monitor user interaction with notifications
- **Performance Metrics**: Channel-specific delivery performance

## Security Requirements
- **Token Protection**: Secure storage of API keys dan tokens
- **Data Encryption**: Encrypt notification content in transit
- **Privacy Compliance**: GDPR/privacy law compliance
- **Access Control**: Verify user permissions for each channel