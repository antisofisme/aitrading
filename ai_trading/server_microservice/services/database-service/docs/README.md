# Database Service - Comprehensive Documentation

**Enterprise Multi-Database Service for Neliti AI Trading Platform**

## Overview

The Database Service is the centralized data persistence and management service supporting 6 different database systems for the Neliti AI Trading Platform. It provides a unified API interface for all database operations while maintaining optimal performance for high-frequency trading requirements.

## Quick Navigation

### 📚 **Core Documentation**
- [Architecture Overview](./ARCHITECTURE.md) - Complete system architecture and component relationships
- [API Reference](./api/) - Comprehensive API documentation for all endpoints
- [Configuration Guide](./guides/CONFIGURATION.md) - Database connections and environment setup
- [Performance Guide](./guides/PERFORMANCE.md) - Optimization strategies and benchmarks

### 🗄️ **Database Documentation**
- [Schema Reference](./schemas/) - Complete schema documentation for all 6 databases
- [Migration Guide](./guides/MIGRATION.md) - Schema versioning and deployment procedures
- [Multi-Database Integration](./guides/MULTI_DATABASE.md) - Cross-database operations and relationships

### 🛠️ **Operational Guides**
- [Troubleshooting](./guides/TROUBLESHOOTING.md) - Error handling and diagnostics
- [Monitoring](./guides/MONITORING.md) - Health checks and performance monitoring
- [Deployment](./guides/DEPLOYMENT.md) - Production deployment and scaling

### 💡 **Examples & Tutorials**
- [Usage Examples](./examples/) - Practical code examples and integration patterns
- [High-Frequency Trading](./examples/HFT_INTEGRATION.md) - MT5 bridge integration examples

## Supported Databases

| Database | Type | Primary Use Case | Port | Status |
|----------|------|------------------|------|--------|
| **ClickHouse** | Time-Series | Trading data, ticks, indicators | 8123 | ✅ Active |
| **PostgreSQL** | Relational | User auth, metadata | 5432 | ✅ Active |
| **ArangoDB** | Graph | Strategy relationships | 8529 | ✅ Active |
| **Weaviate** | Vector | AI embeddings, patterns | 8080 | ✅ Active |
| **DragonflyDB** | Cache | High-performance caching | 6379 | ✅ Active |
| **Redpanda** | Streaming | Real-time data streaming | 9092 | ✅ Active |

## Key Features

### 🚀 **High-Performance Architecture**
- **Connection Pooling**: Optimized connection management for all database types
- **Query Optimization**: Database-specific query building and execution
- **Batch Processing**: High-throughput operations for trading data
- **Caching Layer**: Multi-tier caching for improved response times

### 🔒 **Enterprise Security**
- **SQL Injection Prevention**: Parameterized queries and input sanitization
- **Connection Security**: Encrypted connections and credential management
- **Access Control**: Role-based access and API key authentication
- **Audit Logging**: Comprehensive operation logging and monitoring

### 📊 **Monitoring & Observability**
- **Health Monitoring**: Real-time database health checks
- **Performance Tracking**: Query execution time and resource utilization
- **Error Handling**: Comprehensive error categorization and recovery
- **Metrics Collection**: Detailed operational metrics and alerting

### 🔄 **Schema Management**
- **Version Control**: Database schema versioning and migration
- **Multi-Environment**: Development, staging, and production environments
- **Rollback Support**: Safe schema rollback capabilities
- **Validation**: Schema integrity and consistency checking

## Quick Start

### 1. Service Startup
```bash
# Development mode
python main_refactored.py

# Production mode with Docker
docker run -p 8003:8003 neliti/database-service:latest
```

### 2. Health Check
```bash
curl http://localhost:8003/api/v1/database/health
```

### 3. Basic Query Example
```python
import httpx

# ClickHouse query example
response = httpx.get(
    "http://localhost:8003/api/v1/database/clickhouse/query",
    params={
        "query": "SELECT * FROM ticks WHERE symbol='EURUSD' LIMIT 10",
        "database": "trading_data"
    }
)
```

## Architecture Highlights

### **Clean Architecture Pattern**
```
┌─────────────────────────────────────┐
│           API LAYER                 │
│  ┌─────────────────────────────┐    │
│  │     Database Endpoints      │    │
│  │  - ClickHouse, PostgreSQL   │    │
│  │  - ArangoDB, Weaviate       │    │
│  │  - Cache, Schema, Health    │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│         BUSINESS LOGIC              │
│  ┌─────────────────────────────┐    │
│  │    Database Manager         │    │
│  │  - Connection Management    │    │
│  │  - Query Execution          │    │
│  │  - Health Monitoring        │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│        INFRASTRUCTURE               │
│  ┌─────────────────────────────┐    │
│  │   Connection Factory        │    │
│  │  - Pool Management          │    │
│  │  - 6 Database Types         │    │
│  └─────────────────────────────┘    │
└─────────────────────────────────────┘
```

### **Enterprise Patterns**
- **Dependency Injection**: Clean service composition
- **Factory Pattern**: Database connection creation
- **Repository Pattern**: Database operation abstraction
- **Circuit Breaker**: Fault tolerance and recovery

## Performance Benchmarks

| Operation | Database | Response Time (P95) | Throughput |
|-----------|----------|-------------------|------------|
| Tick Insert | ClickHouse | < 5ms | 50,000 ops/sec |
| Recent Ticks Query | ClickHouse | < 10ms | 10,000 queries/sec |
| User Auth | PostgreSQL | < 15ms | 5,000 ops/sec |
| Strategy Graph | ArangoDB | < 25ms | 2,000 queries/sec |
| Vector Search | Weaviate | < 50ms | 1,000 queries/sec |
| Cache Operations | DragonflyDB | < 1ms | 100,000 ops/sec |

## Support & Contributing

### Documentation Structure
- **API Documentation**: Complete endpoint documentation with examples
- **Configuration Guides**: Environment setup and connection management
- **Performance Guides**: Optimization strategies and monitoring
- **Schema Documentation**: Complete database schema reference
- **Troubleshooting**: Common issues and resolution procedures

### Getting Help
- Check the [Troubleshooting Guide](./guides/TROUBLESHOOTING.md) for common issues
- Review [API Documentation](./api/) for endpoint usage
- Examine [Examples](./examples/) for integration patterns
- Monitor service health using [Monitoring Guide](./guides/MONITORING.md)

---

**Version**: 2.0.0  
**Last Updated**: 2025-07-31  
**Service Status**: ✅ Production Ready