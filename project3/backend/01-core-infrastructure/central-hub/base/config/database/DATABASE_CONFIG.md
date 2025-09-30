# Database Infrastructure Services

## 🏗️ Purpose
**Pure infrastructure layer** providing multi-database services for SPARC Trading Platform. Contains only Docker containers and configuration files - no application logic.

## 📊 Infrastructure Services

### Databases
- **PostgreSQL** (TimescaleDB) - Primary OLTP database
- **ClickHouse** - Analytics OLAP database
- **DragonflyDB** - High-performance Redis cache
- **Weaviate** - Vector database for AI/ML
- **ArangoDB** - Multi-model graph database

### Message Queues
- **NATS** - Lightweight message streaming with JetStream
- **Kafka** - High-throughput message broker with Zookeeper

## 🚀 Quick Start

```bash
# Deploy all database services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs [service-name]

# Stop services
docker-compose down
```

## 📁 File Structure

```
database-service/
├── docker-compose.yml          # Main deployment configuration
├── postgresql.conf             # PostgreSQL optimization settings
├── clickhouse-config.xml       # ClickHouse server configuration
├── clickhouse-users.xml        # ClickHouse user management
├── init-scripts/               # Database initialization SQL
│   ├── 01-create-extensions.sql
│   └── 02-create-tables.sql
├── backups/                    # Backup files
└── README.md                   # This file
```

## 🔗 Service Endpoints

| Service | Port | Endpoint | Purpose |
|---------|------|----------|---------|
| PostgreSQL | 5432 | `suho-postgresql:5432` | Primary database |
| ClickHouse | 8123 | `suho-clickhouse:8123` | Analytics queries |
| DragonflyDB | 6379 | `suho-dragonflydb:6379` | Cache operations |
| Weaviate | 8080 | `suho-weaviate:8080` | Vector operations |
| ArangoDB | 8529 | `suho-arangodb:8529` | Graph operations |
| NATS | 4222 | `suho-nats-server:4222` | Message streaming |
| Kafka | 9092 | `suho-kafka:9092` | Message broker |

## ⚡ Performance Notes

- PostgreSQL configured for trading workloads (TimescaleDB)
- ClickHouse optimized for analytics queries
- DragonflyDB provides Redis-compatible caching
- All services include health checks and monitoring

## 🔧 Configuration Management

Database configurations are **static infrastructure** and managed via:
- Environment variables
- Docker Compose files
- Configuration files (postgresql.conf, clickhouse-config.xml)

For **application configurations**, see `central-hub/config/` system.

## 🌐 Network

All services run on `suho-trading-network` for secure internal communication.

---

**Note**: This is pure infrastructure. Application services are located in separate folders (central-hub, api-gateway, etc.)