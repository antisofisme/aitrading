# AI Trading Platform - Comprehensive Monitoring System

## 🚀 Overview

A complete, enterprise-grade monitoring and alerting system designed specifically for AI trading platforms. This system provides real-time monitoring, intelligent alerting, interactive dashboards, and comprehensive logging capabilities with full coordination hooks support.

## 📊 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                 MonitoringOrchestrator                         │
│                   (Central Coordinator)                        │
├─────────────────┬─────────────────┬─────────────────┬─────────│
│   HealthMonitor │ MetricsCollector│  AlertManager   │Dashboard│
│                 │                 │                 │ Server  │
├─────────────────┼─────────────────┼─────────────────┼─────────│
│                 │                 │                 │         │
│ • System Health │ • Trading       │ • Multi-channel │ • Web UI│
│ • Application   │   Metrics       │   Notifications │ • Real- │
│   Components    │ • Performance   │ • Escalation    │   time  │
│ • Performance   │   Counters      │ • Deduplication │ • Inter-│
│   Monitoring    │ • Custom        │ • Rate Limiting │   active│
│                 │   Histograms    │                 │         │
└─────────────────┴─────────────────┴─────────────────┴─────────┘
         │                   │                   │         │
┌─────────────────┬─────────────────┬─────────────────┬─────────┐
│NotificationSvc  │  LogAggregator  │MonitoringConfig │   Tests │
│                 │                 │                 │         │
│ • Email         │ • Log Parsing   │ • Environment   │ • Unit  │
│ • Slack         │ • Pattern       │   Based Config  │ • Inte- │
│ • SMS           │   Detection     │ • Validation    │   gration│
│ • Webhooks      │ • Real-time     │ • Overrides     │ • E2E   │
│ • Discord       │   Analysis      │                 │         │
│ • Teams         │ • Alerting      │                 │         │
└─────────────────┴─────────────────┴─────────────────┴─────────┘
```

## 🏗️ Core Components

### 1. HealthMonitor (`/src/monitoring/health/HealthMonitor.js`)
- **Real-time health checks** for system and application components
- **Configurable thresholds** for CPU, memory, disk, and latency
- **Custom health checks** for trading engine, market data, risk manager
- **Automatic alert generation** on threshold violations
- **Historical health data** with configurable retention

**Key Features:**
- System health (CPU, memory, disk, uptime)
- Application health (database, trading engine, market data)
- Performance health (latency, throughput, error rates)
- Threshold-based alerting
- Metrics storage and cleanup

### 2. MetricsCollector (`/src/monitoring/metrics/MetricsCollector.js`)
- **Advanced metrics collection** with counters, gauges, and histograms
- **Trading-specific metrics** (P&L, trades, orders, risk)
- **Performance metrics** (latency, throughput)
- **Real-time aggregation** and analysis
- **Prometheus export** capability

**Metrics Types:**
- **Counters**: trades executed, orders placed, errors
- **Gauges**: portfolio value, system resources, active positions
- **Histograms**: latency distributions, trade duration, P&L

### 3. AlertManager (`/src/monitoring/alerts/AlertManager.js`)
- **Multi-severity alerting** (info, warning, critical)
- **Multiple notification channels** with retry logic
- **Alert escalation** for critical issues
- **Deduplication** to prevent spam
- **Rate limiting** protection
- **Configurable templates** for different channels

**Alert Features:**
- Severity-based channel routing
- Automatic escalation timers
- Rate limiting and deduplication
- Retry mechanisms with backoff
- Template-based notifications

### 4. DashboardServer (`/src/monitoring/dashboards/DashboardServer.js`)
- **Real-time web dashboard** with Socket.IO
- **Interactive visualizations** using Chart.js
- **Multiple dashboard views** (system, trading, alerts, metrics)
- **RESTful API** for metrics and status
- **Authentication support** for production

**Dashboard Features:**
- Real-time data updates via WebSocket
- Multiple themed layouts (dark/light)
- Interactive charts and graphs
- Alert management interface
- Metrics export functionality

### 5. NotificationService (`/src/monitoring/notifications/NotificationService.js`)
- **Multi-channel notifications** (Email, Slack, SMS, Webhooks, Discord, Teams)
- **Template-based messaging** with customization
- **Queue-based processing** with retry logic
- **Rate limiting** and delivery tracking
- **Priority-based routing**

**Supported Channels:**
- Email (SMTP with HTML templates)
- Slack (Rich message blocks)
- SMS (Twilio integration)
- Webhooks (Custom endpoints)
- Discord (Embed messages)
- Microsoft Teams (Adaptive cards)

### 6. LogAggregator (`/src/monitoring/logs/LogAggregator.js`)
- **Multi-source log collection** (files, directories, streams)
- **Real-time log analysis** with pattern detection
- **Anomaly detection** for security and performance
- **Structured log parsing** (JSON and text formats)
- **Threshold-based alerting** on error rates

**Log Analysis Features:**
- Error pattern detection
- Security event monitoring
- Performance bottleneck identification
- Trading-specific log analysis
- Configurable alerting thresholds

### 7. MonitoringConfig (`/src/monitoring/config/MonitoringConfig.js`)
- **Environment-based configuration** (dev, test, staging, prod)
- **Configuration validation** and merging
- **Threshold management** for all metrics
- **Template customization** for notifications
- **Export/import capabilities**

## 🚀 Quick Start

### Basic Usage

```javascript
const { createMonitoringSystem } = require('./src/monitoring');

// Quick start with defaults
const monitoring = await createMonitoringSystem('development');
await monitoring.start();

// Access dashboard at http://localhost:3001
```

### Advanced Configuration

```javascript
const { MonitoringSystem } = require('./src/monitoring');

const customConfig = {
  health: {
    checkInterval: 5000,
    thresholds: {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 80, critical: 90 }
    }
  },
  alerts: {
    channels: ['console', 'email', 'slack'],
    email: {
      smtp: { host: 'smtp.company.com' },
      from: 'alerts@company.com',
      to: 'admin@company.com'
    }
  },
  dashboard: {
    port: 3001,
    enableAuth: true
  }
};

const monitoring = new MonitoringSystem('production', customConfig);
await monitoring.start();
```

### CLI Usage

```bash
# Start with default configuration
node src/monitoring/index.js

# Start with specific environment and port
node src/monitoring/index.js production 3001
```

## 📈 Trading-Specific Features

### Trading Metrics
- **Trade execution tracking** (count, P&L, duration)
- **Order management metrics** (placed, filled, cancelled)
- **Portfolio monitoring** (value, positions, unrealized/realized P&L)
- **Risk metrics** (exposure ratio, VaR estimates)
- **Performance analytics** (win rate, Sharpe ratio, drawdown)

### Trading Alerts
- **Risk threshold violations** (exposure, drawdown limits)
- **Trading engine failures** and connectivity issues
- **Market data feed problems** and latency spikes
- **Order execution delays** and slippage alerts
- **Portfolio limit breaches** and margin calls

### Trading Dashboard
- **Real-time P&L charts** and position tracking
- **Risk exposure visualization** and limit monitoring
- **Trading performance metrics** and statistics
- **Market data feed status** and latency tracking
- **Order flow analysis** and execution analytics

## 🔧 Configuration Examples

### Development Environment
```javascript
{
  health: { checkInterval: 10000 },
  alerts: { channels: ['console'] },
  dashboard: { enableAuth: false },
  logs: { realTimeAnalysis: true }
}
```

### Production Environment
```javascript
{
  health: {
    checkInterval: 5000,
    thresholds: {
      cpu: { warning: 70, critical: 85 },
      memory: { warning: 80, critical: 90 }
    }
  },
  alerts: {
    channels: ['console', 'email', 'slack', 'webhook'],
    escalationDelays: [300000, 900000, 3600000],
    maxAlertsPerHour: 50
  },
  dashboard: {
    enableAuth: true,
    host: '0.0.0.0'
  },
  notifications: {
    email: { /* SMTP config */ },
    slack: { webhookUrl: process.env.SLACK_WEBHOOK },
    sms: { /* Twilio config */ }
  }
}
```

## 🧪 Testing

Comprehensive test suite covering all components:

### Test Files
- `tests/monitoring/HealthMonitor.test.js` - Health monitoring tests
- `tests/monitoring/MetricsCollector.test.js` - Metrics collection tests
- `tests/monitoring/AlertManager.test.js` - Alert management tests
- `tests/monitoring/MonitoringOrchestrator.test.js` - Integration tests

### Running Tests
```bash
# Run all monitoring tests
npm test -- tests/monitoring/

# Run specific component tests
npm test -- tests/monitoring/HealthMonitor.test.js

# Run with coverage
npm run test:coverage
```

## 🔌 Claude Flow Integration

The monitoring system is fully integrated with Claude Flow for coordination:

### Coordination Hooks
- **Pre-task hooks**: Store monitoring configuration and setup
- **Post-task hooks**: Export metrics and session data
- **Session management**: Restore and persist monitoring state
- **Memory coordination**: Share metrics and alerts across agents

### Hook Usage
```javascript
// Automatic coordination (enabled by default)
const monitoring = new MonitoringOrchestrator({
  coordination: {
    enableHooks: true,
    memoryNamespace: 'aitrading-monitoring'
  }
});

// Manual hook execution
await monitoring.executePreStartHooks();
await monitoring.executePostStopHooks();
```

## 📊 Dashboard Features

### Real-time Monitoring
- **Live metrics updates** via WebSocket connections
- **Interactive charts** with Chart.js integration
- **Multi-view dashboards** (overview, trading, system, alerts)
- **Real-time alerts** and notification display
- **Historical data visualization** with time range selection

### Dashboard Views
1. **Overview**: System health, trading summary, active alerts
2. **Trading**: P&L charts, position tracking, performance metrics
3. **System**: Resource usage, component health, uptime
4. **Alerts**: Active alerts, alert history, suppression management
5. **Metrics**: Real-time metrics table, export functionality

### API Endpoints
- `GET /api/health` - System health status
- `GET /api/metrics/summary` - Metrics overview
- `GET /api/alerts/active` - Active alerts
- `GET /api/trading/performance` - Trading metrics
- `GET /api/system/status` - System status
- `GET /api/export/metrics` - Export metrics (JSON/CSV)

## 🚨 Alert Configuration

### Severity Levels
- **Info**: Console notifications only
- **Warning**: Console + Slack/Webhook
- **Critical**: All channels (email, SMS, Slack, webhooks)

### Alert Channels
```javascript
{
  email: {
    smtp: { host, port, auth },
    templates: { subject, html, text }
  },
  slack: {
    webhookUrl: 'https://hooks.slack.com/...',
    channel: '#alerts'
  },
  sms: {
    provider: 'twilio',
    accountSid: 'AC...',
    authToken: '...'
  },
  webhook: {
    url: 'https://api.company.com/alerts',
    headers: { 'Authorization': 'Bearer ...' }
  }
}
```

### Escalation Rules
- **Level 1**: 5 minutes - Additional notifications
- **Level 2**: 15 minutes - Manager notifications
- **Level 3**: 1 hour - Executive escalation

## 🔍 Log Analysis

### Supported Log Sources
- **Application logs** (trading engine, risk manager)
- **System logs** (OS events, hardware metrics)
- **Access logs** (API calls, user actions)
- **Error logs** (exceptions, failures)
- **Security logs** (authentication, authorization)

### Pattern Detection
- **Error patterns**: Critical failures, exceptions
- **Security patterns**: Unauthorized access, breaches
- **Performance patterns**: Slow queries, bottlenecks
- **Trading patterns**: Large positions, unusual activity

### Alert Triggers
- **Error rate thresholds**: >10 errors/minute
- **Warning rate thresholds**: >50 warnings/minute
- **Security events**: Immediate alerts
- **Performance degradation**: Latency spikes

## 🌍 Environment Support

### Development
- Relaxed thresholds for testing
- Console-only alerts
- No authentication required
- Verbose logging enabled

### Testing
- Fast intervals for quick feedback
- Short retention periods
- Mock notification channels
- Isolated configurations

### Staging
- Production-like configuration
- Limited alert channels
- Authentication enabled
- Performance testing ready

### Production
- Strict monitoring thresholds
- Full alert channel coverage
- Security hardening
- High availability setup

## 📝 Best Practices

### Threshold Configuration
- Set **warning thresholds** at 70-80% of capacity
- Set **critical thresholds** at 85-95% of capacity
- Use **different thresholds** for different environments
- Monitor **baseline performance** before setting thresholds

### Alert Management
- Use **rate limiting** to prevent alert storms
- Implement **deduplication** for similar alerts
- Set up **escalation paths** for critical issues
- Create **runbooks** for common alerts

### Performance Optimization
- Use **appropriate intervals** for checks and aggregation
- Implement **data retention** policies for metrics
- Enable **compression** for log storage
- Monitor **monitoring system** resource usage

### Security Considerations
- Enable **authentication** for production dashboards
- Use **encrypted channels** for sensitive notifications
- Implement **access controls** for configuration
- **Audit** all configuration changes

## 🔧 Troubleshooting

### Common Issues
1. **High Memory Usage**: Adjust retention periods, enable compression
2. **Slow Dashboard**: Reduce data points, optimize queries
3. **Missing Alerts**: Check thresholds, verify channel configuration
4. **Log Parsing Errors**: Validate log formats, update patterns

### Debug Mode
```javascript
const monitoring = new MonitoringSystem('development', {
  debug: true,
  logs: { logLevel: 'debug' }
});
```

### Health Checks
```bash
# Check system status
curl http://localhost:3001/api/health

# Verify metrics collection
curl http://localhost:3001/api/metrics/summary

# Test alert channels
curl -X POST http://localhost:3001/api/alerts/test
```

## 🚀 Future Enhancements

### Planned Features
- **Machine learning** for anomaly detection
- **Predictive alerting** based on trends
- **Advanced dashboard** widgets and customization
- **Mobile app** for alerts and monitoring
- **Integration** with external monitoring tools

### Extensibility
- **Plugin system** for custom metrics
- **Webhook integrations** for third-party tools
- **Custom dashboard** components
- **Advanced alert** routing and filtering

---

## 📞 Support

For questions, issues, or contributions:

1. **Documentation**: Check this file and component-specific docs
2. **Tests**: Run the comprehensive test suite
3. **Configuration**: Use the configuration validation tools
4. **Monitoring**: Check the dashboard and logs for issues

The monitoring system is designed to be robust, scalable, and maintainable for enterprise AI trading platform deployments.