# Internal Contract: Account Failover Notification

## Overview
Internal notification system for OANDA account failover events within the collector service.

## Direction
`AccountManager` → `StreamManager`, `API Layer`, `Health Monitor`

## Trigger Conditions
- Active account health check fails
- Maximum failure threshold reached
- Manual failover triggered
- Account enters cooldown period

## Data Schema

```javascript
{
  // Event metadata
  event_type: "account_failover",
  event_id: "uuid-v4",
  timestamp: 1234567890,

  // Account transition
  failover: {
    from_account: {
      account_id: "7030924",
      priority: 1,
      failure_count: 3,
      reason: "connection_timeout"
    },
    to_account: {
      account_id: "7030925",
      priority: 2,
      is_healthy: true
    },
    failover_duration_ms: 1250
  },

  // Impact assessment
  impact: {
    affected_streams: 8,
    reconnection_required: true,
    estimated_downtime_ms: 2000
  },

  // Health status
  system_health: {
    total_accounts: 4,
    healthy_accounts: 2,
    failed_accounts: 2,
    accounts_in_cooldown: 1
  }
}
```

## Processing Rules

### 1. StreamManager Response
- Immediately pause affected streams
- Store current stream positions
- Reconnect streams with new account
- Resume streaming operations

### 2. API Layer Response
- Update active account reference
- Retry failed requests with new account
- Log failover event for audit

### 3. Health Monitor Response
- Update health metrics
- Send alert if no healthy accounts remain
- Track failover frequency
- Report to Central Hub

## Validation Rules

1. **from_account** must be currently active account
2. **to_account** must be in healthy state
3. **failover_duration_ms** must be > 0
4. **affected_streams** must match current stream count

## Alert Conditions

### Critical Alerts
- No healthy accounts available
- Failover to last available account
- Failover frequency > 3 per minute

### Warning Alerts
- Failover to lower priority account
- Multiple accounts in cooldown
- Partial stream recovery

## Recovery Procedures

### Automatic Recovery
1. Pause all streams
2. Switch to new account
3. Reconnect streams sequentially
4. Verify data continuity
5. Resume normal operations

### Manual Intervention Required
- All accounts failed
- Repeated failover loop detected
- Configuration error detected

## Example Usage

```javascript
// AccountManager publishes failover event
eventBus.publish('account.failover', {
  event_type: 'account_failover',
  event_id: generateUUID(),
  timestamp: Date.now(),
  failover: {
    from_account: currentAccount,
    to_account: newAccount,
    failover_duration_ms: duration
  },
  impact: {
    affected_streams: activeStreams.length,
    reconnection_required: true
  }
});

// StreamManager subscribes and handles
eventBus.subscribe('account.failover', async (event) => {
  await this.pauseStreams();
  await this.updateAccountCredentials(event.failover.to_account);
  await this.reconnectStreams();
});
```

## Monitoring Metrics

- **Failover Frequency**: Failovers per hour
- **Failover Duration**: Average time to complete failover
- **Recovery Success Rate**: Percentage of successful stream recoveries
- **Account Availability**: Percentage of time with healthy accounts

## Related Contracts
- `health-report-to-central-hub.js` - Reports failover events
- `heartbeat-stream-to-central-hub.js` - Includes failover metrics
- `pricing-stream-to-data-bridge.js` - Affected by account changes
