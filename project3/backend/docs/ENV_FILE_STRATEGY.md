# Environment Variables Strategy - Centralized vs Per-Service

**Date:** 2025-10-19
**Status:** Architecture Decision

---

## TL;DR

**Recommendation:**
- **Development (Docker Compose)**: ✅ **1 centralized `.env` file** di root
- **Production (Kubernetes)**: ✅ **Secret management tool** (Vault, AWS Secrets Manager)
- **Local Testing**: Per-service `.env.example` untuk dokumentasi

---

## Config Hierarchy Recap

Berdasarkan Central Hub architecture:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: SECRETS (Environment Variables)                │
│ - API Keys (POLYGON_API_KEY, DUKASCOPY_USER)           │
│ - Passwords (DB passwords, NATS creds)                 │
│ - Tokens (JWT secrets, API tokens)                     │
│ 📍 LOCATION: .env file or Secret Manager               │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 2: OPERATIONAL CONFIG (Central Hub Database)      │
│ - Symbols, Timeframes, Thresholds                      │
│ - Batch sizes, Schedules, Limits                       │
│ - Feature flags, Business logic settings               │
│ 📍 LOCATION: PostgreSQL service_configs table          │
└─────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────┐
│ Layer 3: INFRASTRUCTURE CONFIG (Environment Variables)  │
│ - NATS URLs, Kafka brokers, DB hosts                   │
│ - Service ports, Log levels                            │
│ - Instance IDs, Worker counts                          │
│ 📍 LOCATION: .env file or docker-compose.yml           │
└─────────────────────────────────────────────────────────┘
```

---

## Strategy by Environment

### 1. Development (Docker Compose) - ✅ RECOMMENDED

**Approach:** Centralized `.env` file di root + `docker-compose.yml`

**File Structure:**
```
project3/backend/
├── .env                          # ✅ Centralized secrets + infrastructure
├── .env.example                  # Template (committed to git)
├── docker-compose.yml            # Injects .env to all services
│
├── 00-data-ingestion/
│   ├── polygon-live-collector/
│   │   └── .env.example          # Per-service documentation
│   └── polygon-historical-downloader/
│       └── .env.example
│
└── 01-core-infrastructure/
    └── central-hub/
        └── .env.example
```

**Root `.env` Example:**
```bash
# ========================================
# SECRETS (Layer 1)
# ========================================
POLYGON_API_KEY=your_polygon_key_here
DUKASCOPY_USER=your_dukascopy_user
DUKASCOPY_PASSWORD=your_dukascopy_pass

# Database passwords
CLICKHOUSE_PASSWORD=clickhouse_secure_2024
POSTGRES_PASSWORD=postgres_secure_2024

# ========================================
# INFRASTRUCTURE (Layer 3)
# ========================================
# NATS Cluster
NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222

# Kafka
KAFKA_BROKERS=suho-kafka:9092

# ClickHouse
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=suho_analytics
CLICKHOUSE_DATABASE=suho_analytics

# PostgreSQL (Central Hub)
CENTRAL_HUB_DB_HOST=suho-postgresql
CENTRAL_HUB_DB_PORT=5432
CENTRAL_HUB_DB_NAME=central_hub
CENTRAL_HUB_DB_USER=suho_admin

# Service ports (optional, can be in docker-compose.yml)
POLYGON_LIVE_COLLECTOR_PORT=8001
POLYGON_HISTORICAL_PORT=8002
CENTRAL_HUB_PORT=8000
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  polygon-live-collector:
    env_file:
      - .env  # ✅ Inject centralized .env
    environment:
      - INSTANCE_ID=polygon-live-collector-1
      - LOG_LEVEL=INFO
    # ... rest of config

  polygon-historical-downloader:
    env_file:
      - .env  # ✅ Same .env for all services
    environment:
      - INSTANCE_ID=polygon-historical-downloader-1
      - LOG_LEVEL=INFO

  central-hub:
    env_file:
      - .env
    environment:
      - INSTANCE_ID=central-hub-1
```

**Benefits:**
- ✅ Single source of truth for secrets
- ✅ Easy to manage and update
- ✅ No duplication of secrets
- ✅ Works with docker-compose out of the box

**Drawbacks:**
- ⚠️ All services have access to all secrets (security concern)
- ⚠️ Large .env file (but organized with comments)

---

### 2. Production (Kubernetes) - ✅ BEST PRACTICE

**Approach:** Secret management tool + Kubernetes Secrets/ConfigMaps

**File Structure:**
```
k8s/
├── base/
│   ├── configmap-infrastructure.yaml    # Infrastructure config (Layer 3)
│   └── secrets.yaml                     # Secrets (Layer 1) - NOT committed
│
├── overlays/
│   ├── dev/
│   │   ├── configmap-infrastructure.yaml
│   │   └── secrets-dev.yaml
│   ├── staging/
│   └── production/
│       ├── configmap-infrastructure.yaml
│       └── secrets-prod.yaml (from Vault/AWS Secrets Manager)
│
└── services/
    ├── polygon-live-collector/
    │   └── deployment.yaml
    └── polygon-historical-downloader/
        └── deployment.yaml
```

**ConfigMap (Infrastructure - Layer 3):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: infrastructure-config
  namespace: suho-trading
data:
  NATS_URL: "nats://nats-1.nats:4222,nats://nats-2.nats:4222"
  KAFKA_BROKERS: "kafka-0.kafka:9092,kafka-1.kafka:9092"
  CLICKHOUSE_HOST: "clickhouse.clickhouse:9000"
  CLICKHOUSE_USER: "suho_analytics"
  CLICKHOUSE_DATABASE: "suho_analytics"
```

**Secret (Secrets - Layer 1):**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: suho-trading
type: Opaque
stringData:
  POLYGON_API_KEY: "your_polygon_key"
  DUKASCOPY_PASSWORD: "your_dukascopy_pass"
  CLICKHOUSE_PASSWORD: "clickhouse_secure_2024"
```

**Deployment (polygon-live-collector):**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: polygon-live-collector
spec:
  template:
    spec:
      containers:
      - name: polygon-live-collector
        envFrom:
          - configMapRef:
              name: infrastructure-config  # ✅ Infrastructure config
          - secretRef:
              name: api-secrets           # ✅ Secrets
        env:
          - name: INSTANCE_ID
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
```

**Secret Management (Production):**

**Option 1: AWS Secrets Manager**
```bash
# Store secret
aws secretsmanager create-secret \
  --name suho-trading/polygon-api-key \
  --secret-string "your_polygon_key"

# Retrieve in deployment (via CSI driver or init container)
```

**Option 2: HashiCorp Vault**
```bash
# Store secret
vault kv put secret/suho-trading/polygon \
  api_key="your_polygon_key"

# Inject via Vault Agent
```

**Benefits:**
- ✅ **Namespace isolation**: Secrets scoped per namespace
- ✅ **RBAC**: Fine-grained access control
- ✅ **Audit trail**: Who accessed what secret when
- ✅ **Rotation**: Automatic secret rotation
- ✅ **Encryption**: Secrets encrypted at rest

---

### 3. Per-Service `.env.example` (Documentation)

**Purpose:** Template untuk developer lokal

**Example (`polygon-live-collector/.env.example`):**
```bash
# ========================================
# Polygon Live Collector - Environment Variables
# Copy this to root .env and fill in actual values
# ========================================

# SECRETS (Layer 1)
POLYGON_API_KEY=your_polygon_api_key_here

# INFRASTRUCTURE (Layer 3)
NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222
KAFKA_BROKERS=suho-kafka:9092
TIMESCALEDB_HOST=suho-timescaledb
TIMESCALEDB_PORT=5432
TIMESCALEDB_USER=suho_market_data
TIMESCALEDB_PASSWORD=timescale_secure_2024
TIMESCALEDB_DATABASE=suho_market_data

# SERVICE SPECIFIC
INSTANCE_ID=polygon-live-collector-1
LOG_LEVEL=INFO

# NOTE: Operational config (symbols, timeframes) comes from Central Hub
```

**Usage:**
```bash
# Developer setup
cp polygon-live-collector/.env.example ../.env
# Edit .env with actual values
docker-compose up polygon-live-collector
```

---

## Comparison Table

| Aspect | Centralized .env (Dev) | Per-Service .env | Kubernetes Secrets |
|--------|------------------------|------------------|-------------------|
| **Development** | ✅ Best | ⚠️ Duplication | ❌ Overkill |
| **Production** | ❌ Not secure | ❌ Not secure | ✅ Best |
| **Maintenance** | ✅ Easy | ❌ Hard | ✅ Automated |
| **Security** | ⚠️ All services see all secrets | ⚠️ Same | ✅ RBAC, encryption |
| **Secret Rotation** | ❌ Manual | ❌ Manual | ✅ Automated |
| **Audit Trail** | ❌ No | ❌ No | ✅ Yes |

---

## Recommendation Summary

### ✅ For Docker Compose (Development)

1. **Use centralized `.env` at root**
   ```
   project3/backend/.env  (NOT committed to git)
   ```

2. **Add `.env.example` per service** (documentation only)
   ```
   polygon-live-collector/.env.example  (committed)
   ```

3. **Inject via docker-compose.yml**
   ```yaml
   env_file:
     - .env
   ```

### ✅ For Kubernetes (Production)

1. **Use Secret management tool:**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault

2. **Split config:**
   - **Secrets (Layer 1)** → Kubernetes Secret (from Vault)
   - **Infrastructure (Layer 3)** → Kubernetes ConfigMap
   - **Operational (Layer 2)** → Central Hub PostgreSQL

3. **Never commit secrets to git**

---

## Security Best Practices

### ❌ NEVER DO:
```bash
# Bad: Hardcoded in code
POLYGON_API_KEY = "pk_abc123xyz"

# Bad: Committed to git
git add .env
git commit -m "Add secrets"  # ❌ NEVER!

# Bad: Same secret for all environments
PROD_API_KEY = DEV_API_KEY  # ❌ NEVER!
```

### ✅ ALWAYS DO:
```bash
# Good: From environment
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")

# Good: .gitignore
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore

# Good: Different secrets per environment
.env.dev    # Development keys
.env.prod   # Production keys (from Vault)

# Good: Template committed
.env.example  # No actual secrets, just structure
```

---

## Migration Path

**Current State:**
- Mixed: Some services have local YAML config + ENV
- No centralized secret management

**Target State:**
1. **Development**: Root `.env` + docker-compose
2. **Production**: Vault + Kubernetes Secrets
3. **Operational config**: Central Hub (already done)

**Steps:**
1. ✅ Create root `.env.example` template
2. ✅ Update docker-compose.yml to use `env_file: .env`
3. ✅ Add `.env.example` per service (documentation)
4. ✅ Ensure `.env` in `.gitignore`
5. 🔄 Test all services with centralized .env
6. 🔄 Plan Kubernetes migration (Vault + Secrets)

---

## Example: Root `.env` Structure

```bash
# ========================================
# SUHO AI TRADING SYSTEM - ENVIRONMENT VARIABLES
# ========================================
# IMPORTANT: Never commit this file to git!
# Use .env.example as template
# ========================================

# ========================================
# LAYER 1: SECRETS (API Keys, Passwords)
# ========================================

# Data Sources
POLYGON_API_KEY=pk_your_polygon_key_here
DUKASCOPY_USER=your_dukascopy_username
DUKASCOPY_PASSWORD=your_dukascopy_password
FRED_API_KEY=your_fred_api_key

# Databases
CLICKHOUSE_PASSWORD=clickhouse_secure_2024
POSTGRES_PASSWORD=postgres_secure_2024
TIMESCALEDB_PASSWORD=timescale_secure_2024

# Messaging
NATS_TOKEN=optional_nats_token
KAFKA_SASL_PASSWORD=optional_kafka_password

# Authentication
JWT_SECRET_KEY=your_jwt_secret_for_dashboard
DASHBOARD_ADMIN_PASSWORD=your_admin_password

# Broker
MT5_PASSWORD=your_mt5_broker_password

# Notifications
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
SENDGRID_API_KEY=your_sendgrid_api_key
TWILIO_AUTH_TOKEN=your_twilio_auth_token

# ========================================
# LAYER 3: INFRASTRUCTURE CONFIG
# ========================================

# NATS Cluster (3 nodes)
NATS_URL=nats://nats-1:4222,nats://nats-2:4222,nats://nats-3:4222

# Kafka
KAFKA_BROKERS=suho-kafka:9092

# ClickHouse
CLICKHOUSE_HOST=suho-clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=suho_analytics
CLICKHOUSE_DATABASE=suho_analytics

# TimescaleDB
TIMESCALEDB_HOST=suho-timescaledb
TIMESCALEDB_PORT=5432
TIMESCALEDB_USER=suho_market_data
TIMESCALEDB_DATABASE=suho_market_data

# PostgreSQL (Central Hub)
CENTRAL_HUB_DB_HOST=suho-postgresql
CENTRAL_HUB_DB_PORT=5432
CENTRAL_HUB_DB_NAME=central_hub
CENTRAL_HUB_DB_USER=suho_admin
CENTRAL_HUB_DB_PASSWORD=central_hub_secure_2024

# Redis/DragonflyDB
DRAGONFLY_HOST=suho-dragonfly
DRAGONFLY_PORT=6379

# ========================================
# LAYER 2: OPERATIONAL CONFIG
# (Stored in Central Hub PostgreSQL)
# ========================================
# NOTE: These are NOT in .env, but in Central Hub database:
# - Symbols, Timeframes, Thresholds
# - Batch sizes, Schedules
# - Feature flags, Business logic
# Access via ConfigClient API
```

---

## Conclusion

**For Development (Docker Compose):**
```
✅ Use: Centralized .env at root
✅ Add: .env.example per service (documentation)
✅ Inject: via docker-compose.yml env_file
```

**For Production (Kubernetes):**
```
✅ Use: Vault/AWS Secrets Manager
✅ Split: Secrets (Layer 1) vs ConfigMap (Layer 3)
✅ Centralize: Operational config in Central Hub (Layer 2)
```

**NEVER:**
```
❌ Commit .env to git
❌ Hardcode secrets in code
❌ Share production secrets in Slack/Email
❌ Use same secrets for dev/staging/prod
```

---

**Created:** 2025-10-19
**Status:** Architecture Decision
**Next:** Implement root .env + update docker-compose.yml
