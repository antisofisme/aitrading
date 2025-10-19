---
name: notification-hub
description: Centralized alert routing service that sends trading alerts, system notifications, and performance warnings to Telegram, Email, SMS, and webhooks with rate limiting and priority management
license: MIT
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Grep
metadata:
  type: Supporting Services (Notifications)
  phase: Supporting Services (Phase 4)
  status: To Implement
  priority: P3 (Medium - user notifications)
  port: 8017
  dependencies:
    - central-hub
    - nats
  version: 1.0.0
---

# Notification Hub Service

Centralized alert routing service that receives notifications from all services via NATS, applies intelligent routing rules based on severity and type, and delivers to multiple channels (Telegram, Email, SMS, webhooks) with rate limiting and priority management.

## When to Use This Skill

Use this skill when:
- Setting up alert delivery channels
- Configuring notification routing rules
- Implementing rate limiting for alerts
- Debugging notification delivery issues
- Adding new notification channels
- Managing alert priorities and escalation

## Service Overview

**Type:** Supporting Services (Alert Routing)
**Port:** 8017
**Input:** NATS (`*.alert.*` from all services)
**Output:** External APIs (Telegram, Email, SMS, Webhooks)
**Channels:** Telegram, Email, SMS, Discord, Slack, Custom Webhooks
**Features:** Priority management, rate limiting, deduplication

**Dependencies:**
- **Upstream**: All services (alerts via NATS)
- **Downstream**: None (external API integrations only)
- **Infrastructure**: NATS cluster

## Key Capabilities

- Multi-channel alert delivery (Telegram, Email, SMS)
- Intelligent routing based on severity and type
- Rate limiting and deduplication
- Priority-based escalation
- Template-based message formatting
- Delivery tracking and retry logic
- Channel health monitoring

## Architecture

### Data Flow

```
NATS: *.alert.* (subscribe from all services)
  ↓
notification-hub
  ├─→ Parse alert (severity, type, metadata)
  ├─→ Apply routing rules
  ├─→ Check rate limits
  ├─→ Deduplicate similar alerts
  ├─→ Format message per channel
  ↓
├─→ Telegram Bot API
├─→ Email SMTP (SendGrid/AWS SES)
├─→ SMS Gateway (Twilio)
├─→ Webhooks (Discord/Slack/Custom)
└─→ Log delivery status
```

### Alert Severity Levels

**1. CRITICAL:**
- Examples: System down, trading halted, max drawdown exceeded
- Channels: All (Telegram + Email + SMS)
- Rate limit: None (always send)
- Response: Immediate action required

**2. HIGH:**
- Examples: Service degraded, high slippage, position limit reached
- Channels: Telegram + Email
- Rate limit: Max 10/hour
- Response: Investigate soon

**3. MEDIUM:**
- Examples: Low Sharpe ratio, strategy underperforming
- Channels: Telegram only
- Rate limit: Max 5/hour
- Response: Review when convenient

**4. LOW:**
- Examples: Data gap detected, minor config change
- Channels: Email only (daily digest)
- Rate limit: Batched every 24 hours
- Response: Informational only

**5. INFO:**
- Examples: Service started, model trained successfully
- Channels: Logs only (no external notifications)
- Rate limit: N/A
- Response: None required

### Routing Rules

**Rule Priority:**
```
1. Override rules (user-defined exceptions)
2. Severity-based rules (CRITICAL → all channels)
3. Type-based rules (trading alerts → Telegram)
4. Default rules (fallback to Email)
```

**Example Rules:**
```json
{
  "rules": [
    {
      "name": "Trading Halted - Critical",
      "condition": "type == 'trading_halted'",
      "channels": ["telegram", "email", "sms"],
      "priority": "critical",
      "rate_limit": null
    },
    {
      "name": "Drawdown Alerts - High Priority",
      "condition": "type == 'drawdown_limit' AND severity >= 'high'",
      "channels": ["telegram", "email"],
      "priority": "high",
      "rate_limit": "10/hour"
    },
    {
      "name": "Data Quality - Medium Priority",
      "condition": "source == 'data-bridge' AND type == 'gap_detected'",
      "channels": ["telegram"],
      "priority": "medium",
      "rate_limit": "5/hour"
    }
  ]
}
```

### Configuration

**Operational Config (Central Hub):**
```json
{
  "operational": {
    "telegram": {
      "enabled": true,
      "default_chat_id": "-1001234567890",
      "parse_mode": "Markdown",
      "rate_limit_per_hour": 30
    },
    "email": {
      "enabled": true,
      "smtp_provider": "sendgrid",
      "default_recipients": ["admin@example.com"],
      "rate_limit_per_hour": 20
    },
    "sms": {
      "enabled": false,
      "provider": "twilio",
      "emergency_numbers": ["+1234567890"],
      "rate_limit_per_day": 10
    },
    "webhooks": {
      "enabled": true,
      "endpoints": [
        {
          "name": "Discord Trading Channel",
          "url": "https://discord.com/api/webhooks/...",
          "filter": "trading.*"
        }
      ]
    },
    "rate_limiting": {
      "enabled": true,
      "global_limit_per_hour": 50,
      "deduplication_window_minutes": 5
    },
    "message_formatting": {
      "include_timestamp": true,
      "include_service_name": true,
      "use_emoji": true
    }
  }
}
```

**Environment Variables (Secrets):**
```bash
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SENDGRID_API_KEY=your_sendgrid_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
DISCORD_WEBHOOK_URL=your_discord_webhook_url
```

## Examples

### Example 1: Fetch Config from Central Hub

```python
from shared.components.config import ConfigClient

# Initialize client
client = ConfigClient(
    service_name="notification-hub",
    safe_defaults={
        "operational": {
            "telegram": {"enabled": True},
            "rate_limiting": {"enabled": True}
        }
    }
)
await client.init_async()

# Get config
config = await client.get_config()
telegram_enabled = config['operational']['telegram']['enabled']
rate_limit = config['operational']['rate_limiting']['global_limit_per_hour']
print(f"Telegram enabled: {telegram_enabled}, Rate limit: {rate_limit}/hour")
```

### Example 2: Subscribe to All Alerts

```python
from nats.aio.client import Client as NATS
from notification_hub import AlertRouter

nc = NATS()
await nc.connect(servers=["nats://nats-1:4222"])

router = AlertRouter()

# Subscribe to all alert topics
async def alert_handler(msg):
    subject = msg.subject
    data = json.loads(msg.data.decode())

    # Parse alert
    alert = {
        "source": subject.split('.')[0],  # e.g., "risk-management"
        "type": data.get('type'),
        "severity": data.get('severity', 'medium'),
        "message": data.get('message'),
        "metadata": data.get('data', {})
    }

    # Route to appropriate channels
    await router.route_alert(alert)

# Subscribe to all services' alerts
await nc.subscribe("*.alert.*", cb=alert_handler)
```

### Example 3: Send Telegram Notification

```python
from notification_hub import TelegramNotifier

notifier = TelegramNotifier(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    default_chat_id=config['telegram']['default_chat_id']
)

# Format alert message
message = f"""
🚨 **CRITICAL ALERT**

**Service:** Risk Management
**Type:** Drawdown Limit Exceeded
**Severity:** CRITICAL

📊 **Details:**
- Current Drawdown: 16.5%
- Max Allowed: 15.0%
- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️ **Action Required:** Trading halted automatically
"""

# Send notification
await notifier.send_message(
    text=message,
    parse_mode="Markdown",
    disable_notification=False  # Sound alert for critical
)
```

### Example 4: Implement Rate Limiting

```python
from notification_hub import RateLimiter

limiter = RateLimiter()

async def send_alert_with_rate_limit(alert):
    channel = "telegram"
    severity = alert['severity']

    # Check rate limit
    if severity == "critical":
        # No rate limit for critical alerts
        allowed = True
    else:
        allowed = await limiter.check_limit(
            channel=channel,
            limit=config['telegram']['rate_limit_per_hour'],
            window_hours=1
        )

    if allowed:
        await send_to_channel(channel, alert)
        await limiter.record_send(channel)
    else:
        logger.warning(f"Rate limit exceeded for {channel}, alert dropped: {alert['type']}")
        # Queue for daily digest instead
        await queue_for_digest(alert)
```

### Example 5: Deduplicate Similar Alerts

```python
from notification_hub import AlertDeduplicator

deduplicator = AlertDeduplicator(
    window_minutes=config['deduplication_window_minutes']
)

async def process_alert(alert):
    # Create fingerprint for deduplication
    fingerprint = f"{alert['source']}:{alert['type']}:{alert.get('symbol', '')}"

    # Check if similar alert sent recently
    if await deduplicator.is_duplicate(fingerprint):
        logger.info(f"Duplicate alert suppressed: {fingerprint}")
        return

    # Send alert
    await route_alert(alert)

    # Record for deduplication
    await deduplicator.record_alert(fingerprint)
```

### Example 6: Send Email via SendGrid

```python
from notification_hub import EmailNotifier

notifier = EmailNotifier(
    api_key=os.getenv("SENDGRID_API_KEY"),
    default_sender="noreply@trading-system.com"
)

# Send email
await notifier.send_email(
    to=config['email']['default_recipients'],
    subject="[MEDIUM] Low Sharpe Ratio Detected",
    body="""
    <h2>Performance Alert</h2>
    <p><strong>Service:</strong> Performance Monitoring</p>
    <p><strong>Type:</strong> Low Sharpe Ratio</p>
    <p><strong>Details:</strong></p>
    <ul>
        <li>Current Sharpe: 0.85</li>
        <li>Threshold: 1.0</li>
        <li>Period: Last 30 days</li>
    </ul>
    <p>Please review strategy performance.</p>
    """,
    html=True
)
```

### Example 7: Send SMS via Twilio

```python
from notification_hub import SMSNotifier

notifier = SMSNotifier(
    account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
    auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
    from_number="+1234567890"
)

# Send SMS (critical alerts only)
if alert['severity'] == 'critical':
    await notifier.send_sms(
        to=config['sms']['emergency_numbers'],
        body=f"CRITICAL: {alert['type']} - {alert['message'][:100]}"
    )
```

## Guidelines

- **ALWAYS** use ConfigClient for operational settings (channel config, rate limits)
- **NEVER** send notifications without rate limiting (prevent spam)
- **ALWAYS** deduplicate similar alerts (avoid notification fatigue)
- **VERIFY** API credentials before sending
- **ENSURE** message formatting appropriate per channel
- **VALIDATE** delivery success and retry on failure

## Critical Rules

1. **Config Hierarchy:**
   - API keys, tokens → ENV variables
   - Channel settings, rate limits → Central Hub
   - Safe defaults → ConfigClient fallback

2. **Rate Limiting (Mandatory):**
   - **ENFORCE** rate limits per channel
   - **EXEMPT** critical alerts from rate limits
   - **QUEUE** rate-limited alerts for digest

3. **Deduplication:**
   - **CHECK** for duplicate alerts (5-minute window)
   - **SUPPRESS** similar alerts
   - **COMBINE** into single notification if possible

4. **Priority Management:**
   - **ROUTE** critical alerts to all channels
   - **ESCALATE** high-priority alerts appropriately
   - **BATCH** low-priority alerts into digests

5. **Delivery Tracking:**
   - **LOG** all delivery attempts
   - **RETRY** failed deliveries (max 3 attempts)
   - **ALERT** if delivery consistently fails

## Common Tasks

### Add New Telegram Bot
1. Create bot via @BotFather
2. Get bot token
3. Set TELEGRAM_BOT_TOKEN environment variable
4. Update Central Hub config with chat ID
5. Test with sample alert

### Configure Email Notifications
1. Set up SendGrid/AWS SES account
2. Get API key
3. Set SENDGRID_API_KEY environment variable
4. Update Central Hub config with recipients
5. Test email delivery

### Implement Custom Webhook
1. Get webhook URL (Discord/Slack/Custom)
2. Add to Central Hub config endpoints
3. Define filter pattern
4. Test webhook delivery
5. Monitor delivery success rate

### Debug Missing Notifications
1. Check NATS subscription active
2. Verify alert published to NATS
3. Review routing rules (alert matched?)
4. Check rate limiting (alert suppressed?)
5. Verify channel credentials valid

## Troubleshooting

### Issue 1: Telegram Notifications Not Arriving
**Symptoms:** Alerts not appearing in Telegram
**Solution:**
- Verify TELEGRAM_BOT_TOKEN set correctly
- Check chat_id correct (use @userinfobot)
- Test bot manually with `/start`
- Review Telegram API error logs
- Check rate limiting (alerts suppressed?)

### Issue 2: Too Many Notifications (Spam)
**Symptoms:** Notification fatigue, excessive alerts
**Solution:**
- Enable rate limiting in config
- Reduce global_limit_per_hour
- Increase deduplication window
- Review alert severity levels (too many critical?)
- Implement batching for low-priority alerts

### Issue 3: Email Delivery Failing
**Symptoms:** Emails not received
**Solution:**
- Verify SENDGRID_API_KEY correct
- Check sender domain verified
- Review recipient email addresses
- Check spam folder
- Test with SendGrid dashboard

### Issue 4: Alerts Not Being Routed
**Symptoms:** Alerts received but not sent to channels
**Solution:**
- Check NATS subscription active
- Verify routing rules match alert type
- Review alert severity mapping
- Test routing logic manually
- Check channel enabled in config

### Issue 5: High Latency in Delivery
**Symptoms:** Delays > 10 seconds
**Solution:**
- Check external API response times
- Review queue depth (backlog?)
- Increase notification workers
- Test network connectivity
- Consider async delivery

## Validation Checklist

After making changes to this service:
- [ ] NATS subscribes to `*.alert.*` (all alerts)
- [ ] Telegram notifications working (test with sample alert)
- [ ] Email notifications working (check inbox)
- [ ] Rate limiting active (verify limits enforced)
- [ ] Deduplication working (duplicate alerts suppressed)
- [ ] Routing rules correct (critical → all channels)
- [ ] Delivery tracking logged
- [ ] Failed deliveries retried
- [ ] ConfigClient fetching from Central Hub
- [ ] Hot-reload responding to config updates

## Related Skills

- `central-hub` - Provides operational config and service discovery
- `risk-management` - Sends trading alerts
- `performance-monitoring` - Sends performance alerts
- `data-bridge` - Sends data quality alerts
- All services - Send alerts to notification-hub

## References

- Full Documentation: `docs/SERVICE_ARCHITECTURE_AND_FLOW.md` (lines 770-787)
- Planning Guide: `docs/PLANNING_SKILL_GUIDE.md` (Service 17, lines 2852-3050)
- Flow + Messaging: `docs/SERVICE_FLOW_TREE_WITH_MESSAGING.md` (lines 788-820)
- Config Architecture: `docs/CONFIG_ARCHITECTURE.md`
- Central Hub Skill: `.claude/skills/central-hub/SKILL.md`
- Code: `05-supporting-services/notification-hub/`

---

**Created:** 2025-10-19
**Version:** 1.0.0
**Status:** To Implement
