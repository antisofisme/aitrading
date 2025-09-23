# Output Contract: API Gateway → Telegram Webhook

## Purpose
API Gateway mengirim trading signals dan notifications ke Telegram Bot untuk real-time user alerts via Telegram messaging.

## Protocol
**Format**: HTTP POST dengan JSON payload
**Transport**: HTTPS Webhook ke Telegram Bot API
**Authentication**: Bot token authentication

## Data Flow
1. Trading Engine → API Gateway → Trading signals
2. API Gateway format untuk Telegram Bot
3. Send via Telegram Bot API webhook
4. User receive notification di Telegram chat

## Telegram Bot API Integration

### **Bot Configuration**
```json
{
  "bot_token": "YOUR_BOT_TOKEN",
  "webhook_url": "https://api.telegram.org/bot{token}/sendMessage",
  "chat_discovery": "https://api.telegram.org/bot{token}/getUpdates"
}
```

### **Message Types**

### **1. Trading Signal Notification**
```json
{
  "chat_id": "123456789",
  "text": "🔔 *TRADING SIGNAL*\n\n📈 *BUY EURUSD*\n💰 Entry: 1.0845\n🛑 Stop Loss: 1.0820\n🎯 Take Profit: 1.0880\n📊 Confidence: 85%\n⏰ Time: 10:30 UTC\n\n_AI Analysis: Strong bullish pattern detected_",
  "parse_mode": "Markdown",
  "reply_markup": {
    "inline_keyboard": [
      [
        {"text": "✅ Execute", "callback_data": "execute_signal_789"},
        {"text": "❌ Ignore", "callback_data": "ignore_signal_789"}
      ],
      [
        {"text": "📊 View Chart", "url": "https://dashboard.com/chart/EURUSD"}
      ]
    ]
  }
}
```

### **2. Execution Confirmation**
```json
{
  "chat_id": "123456789",
  "text": "✅ *TRADE EXECUTED*\n\n📈 BUY EURUSD\n💰 Price: 1.0846\n📊 Volume: 0.1 lot\n🎫 Ticket: #12345678\n⏰ Executed: 10:31 UTC\n\n💵 Account Balance: $10,005.00",
  "parse_mode": "Markdown"
}
```

### **3. Performance Alert**
```json
{
  "chat_id": "123456789",
  "text": "📊 *DAILY SUMMARY*\n\n✅ Profitable Trades: 8\n❌ Loss Trades: 2\n📈 Win Rate: 80%\n💰 Net Profit: +$125.50\n📊 Total Trades: 10\n\n🎯 Keep up the good work!",
  "parse_mode": "Markdown",
  "reply_markup": {
    "inline_keyboard": [
      [
        {"text": "📈 View Dashboard", "url": "https://dashboard.com/analytics"}
      ]
    ]
  }
}
```

### **4. System Alert**
```json
{
  "chat_id": "123456789",
  "text": "⚠️ *SYSTEM ALERT*\n\n🔌 MT5 Connection Lost\n⏰ Time: 10:35 UTC\n🔄 Auto-reconnecting...\n\n_Please check your MT5 terminal_",
  "parse_mode": "Markdown"
}
```

### **5. Risk Management Alert**
```json
{
  "chat_id": "123456789",
  "text": "🚨 *RISK ALERT*\n\n📉 Daily Loss Limit Reached\n💰 Loss: -$200.00\n🛑 Auto-trading DISABLED\n\n_Trading will resume tomorrow_",
  "parse_mode": "Markdown",
  "reply_markup": {
    "inline_keyboard": [
      [
        {"text": "📊 View Positions", "url": "https://dashboard.com/positions"}
      ]
    ]
  }
}
```

## Schema Definition (Internal Processing)
```protobuf
message TelegramNotification {
  string user_id = 1;
  string telegram_chat_id = 2;
  NotificationType type = 3;
  TelegramMessage message = 4;
  int64 timestamp = 5;
  bool urgent = 6;
}

message TelegramMessage {
  string text = 1;                    // Formatted message text
  string parse_mode = 2;              // "Markdown" or "HTML"
  TelegramKeyboard keyboard = 3;      // Optional inline keyboard
  bool disable_notification = 4;     // Silent notification
}

message TelegramKeyboard {
  repeated TelegramButton buttons = 1;
}

message TelegramButton {
  string text = 1;
  string callback_data = 2;           // For callback buttons
  string url = 3;                     // For URL buttons
}

enum NotificationType {
  TRADING_SIGNAL = 0;
  EXECUTION_CONFIRM = 1;
  PERFORMANCE_ALERT = 2;
  SYSTEM_ALERT = 3;
  RISK_ALERT = 4;
}
```

## User Management
- **Chat ID Discovery**: User link Telegram account via dashboard
- **Subscription Filtering**: Different notifications per subscription tier
- **User Preferences**: Enable/disable notification types
- **Rate Limiting**: Max 10 messages/minute per user

## Error Handling
- **Bot API Errors**: Retry dengan exponential backoff
- **Invalid Chat ID**: Log error, update user profile
- **Message Too Long**: Split into multiple messages
- **Rate Limit Hit**: Queue messages dengan delay

## Security Requirements
- **Bot Token Protection**: Secure storage dan rotation
- **User Verification**: Verify Telegram user belongs to platform user
- **Message Sanitization**: Prevent injection attacks
- **Content Filtering**: No sensitive data dalam messages