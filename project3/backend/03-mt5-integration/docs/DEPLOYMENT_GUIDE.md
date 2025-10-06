# MT5 EA Integration - Deployment Guide

## Quick Start

This guide walks you through deploying the complete MT5 EA integration system from scratch.

---

## Prerequisites

### System Requirements

- **OS:** Linux (Ubuntu 22.04+ recommended) or Docker
- **RAM:** 8 GB minimum, 16 GB recommended
- **CPU:** 4 cores minimum, 8 cores recommended
- **Disk:** 100 GB SSD (for database storage)

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| PostgreSQL | 14+ | Primary database |
| TimescaleDB | 2.10+ | Time-series extension |
| NATS | 2.10+ | Message broker |
| Kafka | 3.5+ | Event streaming (optional) |
| DragonflyDB | 1.21+ | Cache (Redis-compatible) |
| Node.js | 18+ | API Gateway |
| Python | 3.11+ | Data Bridge, ML services |

---

## Step 1: Database Setup

### 1.1 Install PostgreSQL + TimescaleDB

**Using Docker (Recommended):**

```bash
# Already configured in docker-compose.yml
docker-compose up -d postgresql
```

**Manual Installation (Ubuntu):**

```bash
# Add TimescaleDB repository
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -

# Install PostgreSQL + TimescaleDB
sudo apt update
sudo apt install postgresql-14 postgresql-14-timescaledb-2.10

# Initialize TimescaleDB
sudo timescaledb-tune --quiet --yes

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 1.2 Run Database Migrations

```bash
cd /mnt/g/khoirul/aitrading/project3/backend

# Set database credentials
export PGHOST=localhost
export PGPORT=5432
export PGUSER=suho_admin
export PGPASSWORD=suho_secure_password_2024
export PGDATABASE=suho_trading

# Run migrations in order
psql -f 03-mt5-integration/schemas/00-init-migration.sql
psql -f 03-mt5-integration/schemas/01-mt5-core-tables.sql
psql -f 03-mt5-integration/schemas/02-mt5-trading-tables.sql
psql -f 03-mt5-integration/schemas/03-mt5-audit-compliance.sql
```

### 1.3 Verify Installation

```bash
psql -c "SELECT * FROM health_check();"
```

**Expected Output:**

```
component              | status  | message
-----------------------|---------|---------------------------------
database               | healthy | Database connection OK
timescaledb            | healthy | TimescaleDB version: 2.14.2
hypertables            | healthy | 7 hypertables created
continuous_aggregates  | healthy | 2 continuous aggregates active
```

---

## Step 2: NATS Setup

### 2.1 Start NATS Server

**Using Docker:**

```bash
docker-compose up -d nats
```

**Manual Installation:**

```bash
# Download NATS
wget https://github.com/nats-io/nats-server/releases/download/v2.10.7/nats-server-v2.10.7-linux-amd64.tar.gz
tar -xzf nats-server-v2.10.7-linux-amd64.tar.gz
sudo mv nats-server-v2.10.7-linux-amd64/nats-server /usr/local/bin/

# Start with JetStream
nats-server --jetstream --store_dir=/data --http_port=8222
```

### 2.2 Create JetStream Streams

```bash
# Install NATS CLI
curl -sf https://binaries.nats.dev/nats-io/natscli/nats@latest | sh

# Connect to NATS
nats context save suho --server=nats://localhost:4222

# Create streams (based on nats-subjects.yaml)
nats stream add MT5_ACCOUNTS \
  --subjects="mt5.account.>" \
  --storage=file \
  --retention=interest \
  --max-age=24h \
  --max-msgs=1000000 \
  --max-bytes=10GB

nats stream add MT5_SIGNALS \
  --subjects="mt5.signal.>" \
  --storage=file \
  --retention=interest \
  --max-age=1h \
  --max-msgs=100000 \
  --max-bytes=1GB

nats stream add MT5_COMMANDS \
  --subjects="mt5.command.>,mt5.config.>" \
  --storage=file \
  --retention=interest \
  --max-age=24h \
  --max-msgs=10000 \
  --max-bytes=100MB

nats stream add INTERNAL \
  --subjects="internal.>" \
  --storage=file \
  --retention=workqueue \
  --max-age=1h \
  --max-msgs=1000000 \
  --max-bytes=5GB
```

### 2.3 Verify NATS Setup

```bash
nats stream ls
nats stream info MT5_ACCOUNTS
```

---

## Step 3: Application Services

### 3.1 Start Core Services

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Expected Output:**

```
NAME                  STATUS    PORTS
suho-postgresql       Up        5432:5432
suho-nats-server      Up        4222:4222, 8222:8222
suho-dragonflydb      Up        6379:6379
suho-central-hub      Up        7000:7000
suho-api-gateway      Up        8000-8002:8000-8002
suho-data-bridge      Up
```

### 3.2 Verify Service Health

```bash
# Central Hub
curl http://localhost:7000/health

# API Gateway
curl http://localhost:8000/health

# NATS
curl http://localhost:8222/healthz
```

---

## Step 4: MT5 EA Configuration

### 4.1 Generate API Key for User

```bash
psql -c "
-- Create test user account
INSERT INTO mt5_user_accounts (
    account_id,
    tenant_id,
    user_id,
    broker_name,
    broker_server,
    mt5_login,
    mt5_account_number,
    account_type,
    account_currency,
    leverage,
    api_key_hash
) VALUES (
    uuid_generate_v4(),
    'tenant_demo',
    'user_test_001',
    'ICMarkets',
    'ICMarkets-Demo01',
    67890,
    '12345',
    'demo',
    'USD',
    500,
    hash_api_key('test_api_key_change_in_production')
) RETURNING account_id, user_id;
"
```

**Save the `account_id` for EA configuration.**

### 4.2 Configure MT5 EA

In MT5 Terminal, go to **Expert Advisors** → **Suho Trading EA** → **Properties** → **Inputs**:

```
# Connection Settings
API_GATEWAY_URL = "http://your-server-ip:8000"
ACCOUNT_ID = "uuid-from-step-4.1"
API_KEY = "test_api_key_change_in_production"

# NATS Settings (optional, if EA connects directly)
NATS_URL = "nats://your-server-ip:4222"

# Trading Settings
ENABLE_TRADING = true
MAX_POSITION_SIZE = 1.0
MAX_DAILY_LOSS = 500.0
```

### 4.3 Test EA Connection

1. **Attach EA to chart** in MT5
2. **Check EA logs** (Experts tab): Should see "Connected to Suho Trading Platform"
3. **Verify in database:**

```bash
psql -c "
SELECT
    account_id,
    user_id,
    connection_status,
    last_connection_time,
    ea_version
FROM mt5_user_accounts
WHERE user_id = 'user_test_001';
"
```

**Expected Output:**

```
account_id            | user_id       | connection_status | last_connection_time      | ea_version
----------------------|---------------|-------------------|---------------------------|------------
uuid-xxxx-xxxx        | user_test_001 | online            | 2025-10-05 12:30:45+00    | v1.0.0
```

---

## Step 5: Testing Data Flow

### 5.1 Test EA → Backend (Inbound)

**Verify heartbeat messages:**

```bash
# Subscribe to NATS subject
nats sub "mt5.account.*.heartbeat"
```

**Expected Output (every 30 seconds):**

```
[#1] Received on "mt5.account.uuid-xxxx.heartbeat"
<binary data - 144 bytes>
```

**Verify data in database:**

```bash
psql -c "
SELECT
    account_id,
    status,
    connection_quality,
    latency_ms,
    time
FROM mt5_ea_heartbeat
WHERE time >= NOW() - INTERVAL '5 minutes'
ORDER BY time DESC
LIMIT 5;
"
```

### 5.2 Test Backend → EA (Outbound)

**Publish a test signal:**

```bash
# Using NATS CLI
nats pub "mt5.signal.uuid-xxxx.test-signal-001" "$(echo '{"action":"BUY","symbol":"EURUSD"}' | base64)"

# Or using psql (triggers backend signal service)
psql -c "
INSERT INTO mt5_trading_signals (
    signal_id,
    account_id,
    tenant_id,
    symbol,
    action,
    entry_price,
    stop_loss,
    take_profit,
    recommended_volume,
    model_version,
    strategy_name,
    confidence_score,
    valid_until
) VALUES (
    uuid_generate_v4(),
    'uuid-from-step-4.1',
    'tenant_demo',
    'EURUSD',
    'BUY',
    1.0953,
    1.0932,
    1.0982,
    0.10,
    'manual_test',
    'manual_signal',
    1.0,
    NOW() + INTERVAL '15 minutes'
);
"
```

**Check EA receives signal** (EA logs in MT5):

```
[Suho EA] Signal received: BUY EURUSD 0.10 lots @ 1.0953
[Suho EA] Executing trade...
[Suho EA] Trade executed: Ticket #123456789
```

### 5.3 Verify Complete Flow

```bash
# Check signal execution tracking
psql -c "
SELECT
    s.signal_id,
    s.symbol,
    s.action,
    s.status,
    s.confidence_score,
    e.executed,
    e.actual_entry_price,
    o.ticket,
    o.profit
FROM mt5_trading_signals s
LEFT JOIN mt5_signal_executions e ON s.signal_id = e.signal_id
LEFT JOIN mt5_trade_orders o ON s.executed_order_id = o.order_id
WHERE s.time >= NOW() - INTERVAL '1 hour'
ORDER BY s.time DESC;
"
```

---

## Step 6: Monitoring Setup

### 6.1 Database Monitoring

```bash
# View hypertable sizes
psql -c "SELECT * FROM v_hypertable_summary;"

# View continuous aggregates
psql -c "SELECT * FROM v_continuous_aggregates;"

# View chunk summary
psql -c "SELECT * FROM v_chunk_summary;"
```

### 6.2 NATS Monitoring

```bash
# Stream status
nats stream ls

# Consumer status
nats consumer ls MT5_ACCOUNTS

# Real-time monitoring
nats stream report --all
```

### 6.3 Application Logs

```bash
# API Gateway logs
docker logs -f suho-api-gateway

# Data Bridge logs
docker logs -f suho-data-bridge

# Central Hub logs
docker logs -f suho-central-hub
```

---

## Step 7: Production Optimization

### 7.1 Database Tuning

```sql
-- Analyze tables for optimal query plans
ANALYZE mt5_account_balance_history;
ANALYZE mt5_broker_quotes;
ANALYZE mt5_trade_orders;
ANALYZE mt5_trading_signals;

-- Set up automated VACUUM
ALTER TABLE mt5_trade_orders SET (autovacuum_vacuum_scale_factor = 0.05);

-- Enable parallel query execution
SET max_parallel_workers_per_gather = 4;
```

### 7.2 Retention Policies

```sql
-- Already configured in schemas, but verify:
SELECT * FROM timescaledb_information.job_stats
WHERE job_type = 'retention';
```

### 7.3 Backup Strategy

```bash
# Daily backup script
cat > /etc/cron.daily/backup-suho-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/mnt/backup/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)

# Full backup
pg_dump -U suho_admin -d suho_trading -F c -f "$BACKUP_DIR/suho_trading_$DATE.dump"

# Compress old backups (older than 7 days)
find "$BACKUP_DIR" -name "*.dump" -mtime +7 -exec gzip {} \;

# Delete backups older than 30 days
find "$BACKUP_DIR" -name "*.dump.gz" -mtime +30 -delete
EOF

chmod +x /etc/cron.daily/backup-suho-db.sh
```

---

## Step 8: Security Hardening

### 8.1 Change Default Passwords

```bash
# Update .env file
cp .env.example .env

# Edit .env (change ALL passwords)
nano .env
```

**Critical passwords to change:**
- `POSTGRES_PASSWORD`
- `DRAGONFLY_PASSWORD`
- `CLICKHOUSE_PASSWORD`
- `JWT_SECRET`
- API keys for users

### 8.2 Enable SSL/TLS

**PostgreSQL:**

```bash
# Generate SSL certificates
openssl req -new -x509 -days 365 -nodes -text -out server.crt -keyout server.key

# Configure PostgreSQL
sudo nano /etc/postgresql/14/main/postgresql.conf
# Add:
# ssl = on
# ssl_cert_file = '/path/to/server.crt'
# ssl_key_file = '/path/to/server.key'

sudo systemctl restart postgresql
```

**NATS:**

```bash
# Generate TLS certificates
nats-server --tlscert=server.crt --tlskey=server.key --tlsverify
```

### 8.3 Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 8000/tcp    # API Gateway (HTTP)
sudo ufw allow 443/tcp     # API Gateway (HTTPS)
sudo ufw deny 5432/tcp     # PostgreSQL (internal only)
sudo ufw deny 4222/tcp     # NATS (internal only)
sudo ufw enable
```

---

## Step 9: Scaling Considerations

### 9.1 Horizontal Scaling

**API Gateway (Stateless):**

```yaml
# docker-compose.yml
api-gateway:
  deploy:
    replicas: 3
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

**Load Balancer (Nginx):**

```nginx
upstream api_gateway {
    server api-gateway-1:8000;
    server api-gateway-2:8000;
    server api-gateway-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://api_gateway;
    }
}
```

### 9.2 Database Replication

**TimescaleDB Multi-Node:**

```sql
-- Add data nodes (on separate servers)
SELECT add_data_node('node1', host => 'db-node-1', database => 'suho_trading');
SELECT add_data_node('node2', host => 'db-node-2', database => 'suho_trading');

-- Distribute hypertables across nodes
SELECT set_replication_factor('mt5_broker_quotes', 2);
```

### 9.3 NATS Clustering

```bash
# nats-server-1.conf
cluster {
  name: suho-cluster
  listen: 0.0.0.0:6222
  routes: [
    nats://nats-server-2:6222
    nats://nats-server-3:6222
  ]
}

# Start cluster
nats-server -c nats-server-1.conf
```

---

## Troubleshooting

### Common Issues

**1. EA can't connect to API Gateway**

```bash
# Check firewall
sudo ufw status

# Check API Gateway logs
docker logs suho-api-gateway | grep ERROR

# Test connectivity
curl -v http://localhost:8000/health
```

**2. Missing data in database**

```bash
# Check Data Bridge is running
docker logs suho-data-bridge

# Check NATS queue
nats stream info MT5_ACCOUNTS

# Check database permissions
psql -c "\du"
```

**3. High database latency**

```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check missing indexes
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname NOT IN ('pg_catalog', 'information_schema');
```

---

## Verification Checklist

- [ ] PostgreSQL + TimescaleDB installed and running
- [ ] All database migrations executed successfully
- [ ] NATS server running with JetStream enabled
- [ ] All JetStream streams created
- [ ] Docker services (API Gateway, Data Bridge, Central Hub) running
- [ ] EA successfully connects and sends heartbeat
- [ ] Test signal published and received by EA
- [ ] Trade execution flow works end-to-end
- [ ] Audit logs being written
- [ ] Monitoring dashboards accessible
- [ ] Backups configured and tested
- [ ] Security hardening applied (passwords, SSL, firewall)

---

## Next Steps

1. **Integrate ML Model:** Connect ML prediction engine to signal generation
2. **Build Admin Dashboard:** Create web UI for monitoring accounts and trades
3. **Load Testing:** Test with 100+ concurrent EA connections
4. **Alerts:** Set up PagerDuty/Slack alerts for critical events
5. **Documentation:** Create user guides for EA setup and troubleshooting

---

**Support:**
- Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Documentation: `/docs/MT5_ARCHITECTURE.md`
- NATS Config: `/config/nats-subjects.yaml`
