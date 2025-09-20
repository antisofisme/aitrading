# Database Service

## Overview
Centralized data persistence and management for all 6 databases.

## Responsibilities
- 6 database connections (ClickHouse, PostgreSQL, ArangoDB, Weaviate, DragonflyDB, Redpanda)
- Connection pooling
- Query optimization
- Data consistency
- Backup management

## Dependencies
- Database drivers for all 6 databases
- Connection pooling libraries
- Query optimization tools

## Resources
- CPU: 2 cores
- Memory: 4GB RAM
- Port: 8007

## API Endpoints
```
GET  /health           - Health check
POST /clickhouse       - ClickHouse operations
POST /postgres         - PostgreSQL operations
POST /arangodb         - ArangoDB operations
POST /weaviate         - Weaviate operations
POST /dragonfly        - DragonflyDB operations
POST /redpanda         - Redpanda operations
```