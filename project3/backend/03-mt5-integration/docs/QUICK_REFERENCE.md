# MT5 Integration - Quick Reference Guide

Quick commands and queries for common operations.

---

## Database Queries

### Account Management

```sql
-- Get all active accounts
SELECT account_id, user_id, broker_name, connection_status, last_connection_time
FROM mt5_user_accounts
WHERE status = 'active'
ORDER BY last_connection_time DESC;

-- Get latest account balance
SELECT * FROM get_latest_account_balance('account-uuid-here');

-- Get account with open positions
SELECT
    a.account_id,
    a.user_id,
    COUNT(o.order_id) AS open_positions,
    SUM(o.profit) AS floating_pnl
FROM mt5_user_accounts a
LEFT JOIN mt5_trade_orders o ON a.account_id = o.account_id AND o.status = 'open'
GROUP BY a.account_id, a.user_id;
```

### Trading Statistics

```sql
-- Daily P&L by account
SELECT
    account_id,
    DATE(time) AS date,
    COUNT(*) AS total_trades,
    SUM(profit) FILTER (WHERE status = 'closed' AND profit > 0) AS winning_trades,
    SUM(profit) FILTER (WHERE status = 'closed' AND profit < 0) AS losing_trades,
    SUM(profit) FILTER (WHERE status = 'closed') AS total_pnl
FROM mt5_trade_orders
WHERE time >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY account_id, DATE(time)
ORDER BY account_id, date DESC;

-- Win rate by strategy
SELECT
    strategy_name,
    COUNT(*) AS total_trades,
    COUNT(*) FILTER (WHERE profit > 0) AS winning_trades,
    ROUND(100.0 * COUNT(*) FILTER (WHERE profit > 0) / COUNT(*), 2) AS win_rate_percent,
    AVG(profit) AS avg_profit,
    SUM(profit) AS total_profit
FROM mt5_trade_orders
WHERE status = 'closed'
  AND time >= NOW() - INTERVAL '90 days'
GROUP BY strategy_name
ORDER BY total_profit DESC;

-- Best/worst performing symbols
SELECT
    symbol,
    COUNT(*) AS trades,
    SUM(profit) AS total_profit,
    AVG(profit) AS avg_profit,
    AVG(profit_pips) AS avg_profit_pips
FROM mt5_trade_orders
WHERE status = 'closed'
  AND time >= NOW() - INTERVAL '30 days'
GROUP BY symbol
ORDER BY total_profit DESC;
```

### Signal Performance

```sql
-- Signal execution success rate
SELECT
    s.model_version,
    COUNT(*) AS total_signals,
    COUNT(*) FILTER (WHERE s.status = 'executed') AS executed,
    COUNT(*) FILTER (WHERE s.status = 'rejected') AS rejected,
    COUNT(*) FILTER (WHERE s.status = 'expired') AS expired,
    ROUND(100.0 * COUNT(*) FILTER (WHERE s.status = 'executed') / COUNT(*), 2) AS execution_rate
FROM mt5_trading_signals s
WHERE s.time >= NOW() - INTERVAL '7 days'
GROUP BY s.model_version
ORDER BY execution_rate DESC;

-- Signal profitability
SELECT
    s.strategy_name,
    s.model_version,
    COUNT(*) AS closed_trades,
    AVG(s.confidence_score) AS avg_confidence,
    COUNT(*) FILTER (WHERE e.profit > 0) AS winners,
    AVG(e.profit) AS avg_profit,
    SUM(e.profit) AS total_profit
FROM mt5_trading_signals s
JOIN mt5_signal_executions e ON s.signal_id = e.signal_id
WHERE e.trade_closed = true
  AND s.time >= NOW() - INTERVAL '30 days'
GROUP BY s.strategy_name, s.model_version
ORDER BY total_profit DESC;

-- Execution slippage analysis
SELECT
    symbol,
    AVG(price_difference) AS avg_slippage_pips,
    MAX(ABS(price_difference)) AS max_slippage,
    AVG(execution_latency_ms) AS avg_latency_ms
FROM mt5_signal_executions
WHERE executed = true
  AND time >= NOW() - INTERVAL '7 days'
GROUP BY symbol
ORDER BY avg_slippage_pips DESC;
```

### Broker Quote Analysis

```sql
-- Broker vs Market price deviation
SELECT
    symbol,
    AVG(price_deviation) AS avg_deviation_pips,
    STDDEV(price_deviation) AS stddev_deviation,
    MAX(ABS(price_deviation)) AS max_deviation,
    COUNT(*) AS sample_count
FROM mt5_broker_quotes
WHERE time >= NOW() - INTERVAL '24 hours'
  AND polygon_mid_price IS NOT NULL
GROUP BY symbol
ORDER BY avg_deviation_pips DESC;

-- Average spread by symbol
SELECT
    symbol,
    AVG(spread) AS avg_spread,
    MIN(spread) AS min_spread,
    MAX(spread) AS max_spread,
    market_session
FROM mt5_broker_quotes
WHERE time >= NOW() - INTERVAL '24 hours'
GROUP BY symbol, market_session
ORDER BY symbol, market_session;
```

### Risk Management

```sql
-- Accounts approaching risk limits
SELECT
    a.account_id,
    a.user_id,
    b.balance,
    b.equity,
    b.drawdown,
    b.drawdown_percent,
    a.max_daily_loss
FROM mt5_user_accounts a
JOIN LATERAL (
    SELECT balance, equity, drawdown, drawdown_percent
    FROM mt5_account_balance_history
    WHERE account_id = a.account_id
    ORDER BY time DESC
    LIMIT 1
) b ON true
WHERE b.drawdown_percent > 10.0  -- Alert threshold
ORDER BY b.drawdown_percent DESC;

-- Recent risk events
SELECT
    re.event_type,
    re.severity,
    re.account_id,
    a.user_id,
    re.description,
    re.action_taken,
    re.resolved,
    re.time
FROM mt5_risk_events re
JOIN mt5_user_accounts a ON re.account_id = a.account_id
WHERE re.time >= NOW() - INTERVAL '7 days'
ORDER BY re.time DESC;

-- Margin call candidates
SELECT
    a.account_id,
    a.user_id,
    b.balance,
    b.equity,
    b.margin_used,
    b.margin_level,
    COUNT(o.order_id) AS open_positions
FROM mt5_user_accounts a
JOIN LATERAL (
    SELECT balance, equity, margin_used, margin_level
    FROM mt5_account_balance_history
    WHERE account_id = a.account_id
    ORDER BY time DESC
    LIMIT 1
) b ON true
LEFT JOIN mt5_trade_orders o ON a.account_id = o.account_id AND o.status = 'open'
WHERE b.margin_level < 150.0  -- Margin call threshold
GROUP BY a.account_id, a.user_id, b.balance, b.equity, b.margin_used, b.margin_level
ORDER BY b.margin_level ASC;
```

### Audit & Compliance

```sql
-- Recent audit events by type
SELECT
    event_type,
    event_category,
    COUNT(*) AS event_count,
    COUNT(*) FILTER (WHERE severity = 'error') AS errors,
    COUNT(*) FILTER (WHERE severity = 'critical') AS critical
FROM mt5_audit_log
WHERE time >= NOW() - INTERVAL '24 hours'
GROUP BY event_type, event_category
ORDER BY event_count DESC;

-- User activity log
SELECT
    user_id,
    event_type,
    action,
    event_description,
    time
FROM mt5_audit_log
WHERE user_id = 'user-id-here'
  AND time >= NOW() - INTERVAL '7 days'
ORDER BY time DESC
LIMIT 50;

-- Failed authentication attempts
SELECT
    source_ip,
    user_id,
    COUNT(*) AS failed_attempts,
    MAX(time) AS last_attempt
FROM mt5_audit_log
WHERE event_type = 'authentication_failed'
  AND time >= NOW() - INTERVAL '1 hour'
GROUP BY source_ip, user_id
HAVING COUNT(*) > 3  -- More than 3 failures
ORDER BY failed_attempts DESC;
```

---

## NATS Commands

### Stream Management

```bash
# List all streams
nats stream ls

# View stream details
nats stream info MT5_ACCOUNTS
nats stream info MT5_SIGNALS
nats stream info MT5_COMMANDS

# View stream consumers
nats consumer ls MT5_ACCOUNTS

# Stream health report
nats stream report --all
```

### Publishing Messages

```bash
# Publish test heartbeat
nats pub "mt5.account.test-account.heartbeat" "$(echo '{\"status\":\"online\"}' | base64)"

# Publish test signal
nats pub "mt5.signal.test-account.test-signal-001" "$(echo '{\"action\":\"BUY\",\"symbol\":\"EURUSD\"}' | base64)"

# Publish emergency close command
nats pub "mt5.command.test-account.close_all" "$(echo '{\"reason\":\"manual\"}' | base64)"
```

### Subscribing to Messages

```bash
# Monitor all account events
nats sub "mt5.account.>"

# Monitor specific account heartbeats
nats sub "mt5.account.test-account.heartbeat"

# Monitor all trading signals
nats sub "mt5.signal.>"

# Monitor broker quotes for specific symbol
nats sub "mt5.account.*.quotes.EURUSD"

# Monitor trade executions
nats sub "mt5.account.*.trades.>"
```

### Consumer Management

```bash
# Create durable consumer
nats consumer add MT5_ACCOUNTS data-bridge-consumer \
  --filter "mt5.account.>" \
  --ack explicit \
  --max-deliver 3 \
  --deliver all

# View consumer info
nats consumer info MT5_ACCOUNTS data-bridge-consumer

# Check consumer lag
nats consumer report MT5_ACCOUNTS
```

---

## Maintenance Commands

### Database Maintenance

```sql
-- Vacuum and analyze (run weekly)
VACUUM ANALYZE mt5_account_balance_history;
VACUUM ANALYZE mt5_broker_quotes;
VACUUM ANALYZE mt5_trade_orders;
VACUUM ANALYZE mt5_trading_signals;

-- Reindex (if query performance degrades)
REINDEX TABLE mt5_trade_orders;
REINDEX TABLE mt5_broker_quotes;

-- Check table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Update statistics (for query planner)
ANALYZE;
```

### TimescaleDB Maintenance

```sql
-- View hypertable chunk status
SELECT * FROM v_chunk_summary;

-- Manual chunk compression (if automatic compression disabled)
SELECT compress_chunk(c.chunk_schema || '.' || c.chunk_name)
FROM timescaledb_information.chunks c
WHERE c.hypertable_name = 'mt5_broker_quotes'
  AND c.is_compressed = false
  AND c.range_end < NOW() - INTERVAL '7 days';

-- Check continuous aggregate refresh status
SELECT * FROM timescaledb_information.job_stats
WHERE job_type = 'continuous_aggregate';

-- Manually refresh continuous aggregate
CALL refresh_continuous_aggregate('mt5_balance_5min', NOW() - INTERVAL '1 day', NOW());
```

### Backup & Restore

```bash
# Full database backup
pg_dump -U suho_admin -d suho_trading -F c -f backup_$(date +%Y%m%d).dump

# Backup specific table
pg_dump -U suho_admin -d suho_trading -t mt5_trade_orders -F c -f trades_backup.dump

# Restore from backup
pg_restore -U suho_admin -d suho_trading_new backup_20251005.dump

# Backup TimescaleDB with compression
pg_dump -U suho_admin -d suho_trading -F c -Z 9 -f backup_compressed.dump.gz
```

---

## Monitoring Queries

### System Health

```sql
-- Database health check
SELECT * FROM health_check();

-- Connection count
SELECT
    datname,
    COUNT(*) AS connections,
    MAX(state) AS state
FROM pg_stat_activity
WHERE datname = 'suho_trading'
GROUP BY datname;

-- Long-running queries
SELECT
    pid,
    now() - query_start AS duration,
    state,
    query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query_start < NOW() - INTERVAL '1 minute'
ORDER BY duration DESC;

-- Lock contention
SELECT
    locktype,
    relation::regclass,
    mode,
    COUNT(*) AS lock_count
FROM pg_locks
WHERE granted = false
GROUP BY locktype, relation, mode
ORDER BY lock_count DESC;
```

### Performance Metrics

```sql
-- Top 10 slowest queries (requires pg_stat_statements)
SELECT
    SUBSTRING(query, 1, 100) AS query_preview,
    calls,
    ROUND(mean_exec_time::numeric, 2) AS avg_time_ms,
    ROUND(total_exec_time::numeric, 2) AS total_time_ms
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Cache hit ratio (should be >95%)
SELECT
    'cache_hit_ratio' AS metric,
    ROUND(100.0 * sum(heap_blks_hit) / NULLIF(sum(heap_blks_hit) + sum(heap_blks_read), 0), 2) AS percentage
FROM pg_statio_user_tables;

-- Table scan vs index scan ratio
SELECT
    schemaname,
    tablename,
    seq_scan AS table_scans,
    idx_scan AS index_scans,
    ROUND(100.0 * idx_scan / NULLIF(seq_scan + idx_scan, 0), 2) AS index_scan_percent
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY seq_scan DESC
LIMIT 10;
```

### EA Connectivity

```sql
-- Online/offline accounts
SELECT
    COUNT(*) FILTER (WHERE status = 'online') AS online,
    COUNT(*) FILTER (WHERE status = 'offline') AS offline,
    COUNT(*) FILTER (WHERE status = 'error') AS error,
    COUNT(*) AS total
FROM (
    SELECT DISTINCT ON (account_id)
        account_id,
        status
    FROM mt5_ea_heartbeat
    ORDER BY account_id, time DESC
) latest;

-- Accounts with no recent heartbeat (>5 minutes)
SELECT
    a.account_id,
    a.user_id,
    a.broker_name,
    a.connection_status,
    MAX(h.time) AS last_heartbeat,
    EXTRACT(EPOCH FROM (NOW() - MAX(h.time))) AS seconds_ago
FROM mt5_user_accounts a
LEFT JOIN mt5_ea_heartbeat h ON a.account_id = h.account_id
GROUP BY a.account_id, a.user_id, a.broker_name, a.connection_status
HAVING MAX(h.time) < NOW() - INTERVAL '5 minutes'
   OR MAX(h.time) IS NULL
ORDER BY last_heartbeat DESC NULLS FIRST;
```

---

## Common Admin Tasks

### Create New User Account

```sql
-- 1. Generate API key
SELECT generate_api_key() AS api_key;
-- → Save this API key securely!

-- 2. Create account
INSERT INTO mt5_user_accounts (
    account_id, tenant_id, user_id,
    broker_name, broker_server, mt5_login, mt5_account_number,
    account_type, account_currency, leverage,
    api_key_hash,
    max_daily_loss, max_position_size,
    allowed_symbols, trading_enabled
) VALUES (
    uuid_generate_v4(),
    'tenant_id_here',
    'user_id_here',
    'ICMarkets',
    'ICMarkets-Demo01',
    67890,
    '12345',
    'demo',
    'USD',
    500,
    hash_api_key('api_key_from_step_1'),
    500.00,
    1.0,
    ARRAY['EURUSD', 'GBPUSD', 'USDJPY'],
    true
) RETURNING account_id;

-- 3. Verify account created
SELECT * FROM mt5_user_accounts WHERE user_id = 'user_id_here';
```

### Disable Trading for Account

```sql
-- Disable trading
UPDATE mt5_user_accounts
SET trading_enabled = false,
    status = 'suspended'
WHERE account_id = 'account-uuid-here';

-- Close all open positions (send command via NATS)
-- nats pub "mt5.command.{account_id}.close_all" '{"reason":"admin_suspend"}'

-- Log action
SELECT log_audit_event(
    'tenant_id',
    'user_id',
    'trading_disabled',
    'account',
    'update',
    'Trading disabled by admin',
    'warning',
    '{"reason":"risk_limit_breach"}'::jsonb
);
```

### Generate Compliance Report

```sql
-- Monthly trading report
SELECT
    DATE_TRUNC('month', time) AS month,
    COUNT(*) AS total_trades,
    SUM(volume) AS total_volume,
    SUM(profit) FILTER (WHERE status = 'closed') AS total_pnl,
    COUNT(*) FILTER (WHERE profit > 0) AS winning_trades,
    COUNT(*) FILTER (WHERE profit < 0) AS losing_trades
FROM mt5_trade_orders
WHERE tenant_id = 'tenant_id_here'
  AND time >= DATE_TRUNC('year', NOW())
GROUP BY DATE_TRUNC('month', time)
ORDER BY month DESC;
```

---

## Troubleshooting

### Missing Data

```bash
# Check NATS queue depth
nats stream info MT5_ACCOUNTS

# Check Data Bridge logs
docker logs suho-data-bridge | grep ERROR

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### Performance Issues

```sql
-- Find missing indexes
SELECT
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats
WHERE schemaname = 'public'
  AND n_distinct > 100
  AND correlation < 0.1
ORDER BY n_distinct DESC;

-- Check for table bloat
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    ROUND(100.0 * pg_total_relation_size(schemaname||'.'||tablename) /
          NULLIF(pg_database_size(current_database()), 0), 2) AS percent_of_db
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Quick Links

- **Full Architecture:** `docs/MT5_ARCHITECTURE.md`
- **Deployment Guide:** `docs/DEPLOYMENT_GUIDE.md`
- **NATS Config:** `config/nats-subjects.yaml`
- **Schema Files:** `schemas/`
