# Multi-Database Architecture Documentation

## Overview

The AI Trading Platform now implements a comprehensive multi-database foundation supporting 5 specialized database types, each optimized for specific data patterns and use cases.

## Supported Databases

### 1. PostgreSQL (Operational Data)
- **Purpose**: Primary operational data, ACID transactions
- **Use Cases**: User accounts, trading orders, portfolios, configurations
- **Features**: Full ACID compliance, complex queries, referential integrity
- **Port**: 5432

### 2. ClickHouse (Time-Series Analytics)
- **Purpose**: High-performance analytics and time-series data
- **Use Cases**: Trading metrics, market data, performance analytics, logs
- **Features**: Columnar storage, real-time analytics, high throughput
- **Port**: 8123

### 3. Weaviate (Vector/AI Data)
- **Purpose**: Vector storage and similarity search
- **Use Cases**: AI embeddings, recommendation systems, semantic search
- **Features**: Vector indexing, GraphQL API, ML integration
- **Port**: 8080

### 4. ArangoDB (Graph Data)
- **Purpose**: Multi-model database for graph relationships
- **Use Cases**: Social networks, risk analysis, relationship mapping
- **Features**: Graph traversal, document storage, AQL queries
- **Port**: 8529

### 5. DragonflyDB (Cache/Memory)
- **Purpose**: High-performance in-memory caching
- **Use Cases**: Session storage, real-time data, temporary calculations
- **Features**: Redis compatibility, ultra-low latency, high concurrency
- **Port**: 6379

## Architecture Components

### Database Factory Pattern
- **Purpose**: Centralized database instance creation and management
- **Features**: Configuration management, connection pooling, lifecycle management
- **Location**: `src/database/factories/DatabaseFactory.js`

### Unified Database Interface
- **Purpose**: Single API for all database operations with intelligent routing
- **Features**: Query routing, cross-database operations, unified responses
- **Location**: `src/database/UnifiedDatabaseInterface.js`

### Database Managers
Individual managers for each database type implementing the `IDatabaseManager` interface:
- `PostgreSQLManager.js` - Enhanced PostgreSQL operations
- `ClickHouseManager.js` - Time-series and analytics queries
- `WeaviateManager.js` - Vector operations and similarity search
- `ArangoDBManager.js` - Graph queries and document operations
- `DragonflyDBManager.js` - High-performance caching operations

### Health Monitoring
- **Purpose**: Real-time health monitoring for all databases
- **Features**: Automated health checks, alerting, performance metrics
- **Location**: `src/database/health/HealthMonitor.js`

### Connection Pool Management
- **Purpose**: Optimized connection pooling for each database type
- **Features**: Dynamic pool sizing, performance optimization, monitoring
- **Location**: `src/database/utils/ConnectionPoolManager.js`

### Transaction Coordinator
- **Purpose**: Distributed transactions across multiple databases
- **Features**: Two-phase commit, compensation patterns, rollback support
- **Location**: `src/database/utils/TransactionCoordinator.js`

## Usage Examples

### Basic Initialization
```javascript
const { createDatabaseService } = require('./src/multi-db');

const dbService = await createDatabaseService({
  enableHealthMonitoring: true,
  enablePoolManagement: true
});
```

### Operational Data (PostgreSQL)
```javascript
// Store user data
const user = await dbService.store({
  table: 'users',
  data: { email: 'user@example.com', name: 'John Doe' }
});

// Query with auto-routing
const users = await dbService.retrieve({
  table: 'users',
  criteria: { active: true }
});
```

### Analytics Data (ClickHouse)
```javascript
// Store time-series data
await dbService.timeSeriesQuery({
  table: 'trading_metrics',
  data: {
    timestamp: new Date(),
    symbol: 'BTC/USD',
    price: 45000,
    volume: 1000
  }
});

// Aggregate analytics
const metrics = await dbService.analyze({
  table: 'trading_metrics',
  aggregation: 'avg',
  timeRange: '24h'
});
```

### Vector Search (Weaviate)
```javascript
// Similarity search
const similar = await dbService.vectorSearch({
  className: 'TradingStrategy',
  concepts: ['momentum', 'risk management'],
  limit: 10
});

// Store vector data
await dbService.store({
  className: 'Document',
  data: { content: 'Trading analysis...', category: 'research' },
  targetDatabase: 'weaviate'
});
```

### Graph Operations (ArangoDB)
```javascript
// Graph traversal
const network = await dbService.graphQuery({
  query: `
    FOR v, e IN 1..3 OUTBOUND 'users/john' GRAPH 'trading_network'
    RETURN { user: v, relationship: e }
  `
});

// Create relationships
await dbService.store({
  collection: 'follows',
  data: { _from: 'users/john', _to: 'users/jane', type: 'mentor' },
  targetDatabase: 'arangodb'
});
```

### Caching (DragonflyDB)
```javascript
// Cache data
await dbService.cache('user:session:123', {
  userId: 123,
  permissions: ['read', 'write'],
  expires: Date.now() + 3600000
}, 3600);

// Real-time operations
await dbService.query({
  type: 'lpush',
  key: 'live:prices:BTC',
  value: JSON.stringify({ price: 45000, timestamp: Date.now() }),
  targetDatabase: 'dragonflydb'
});
```

### Cross-Database Transactions
```javascript
// Begin distributed transaction
const transactionId = await dbService.beginTransaction(['postgresql', 'dragonflydb']);

// Add operations
await dbService.addTransactionOperation(
  transactionId,
  'postgresql',
  async (tx, db) => {
    return await db.query('INSERT INTO trades (...) VALUES (...)', params);
  },
  async (tx, db) => {
    return await db.query('DELETE FROM trades WHERE id = ?', [tradeId]);
  }
);

await dbService.addTransactionOperation(
  transactionId,
  'dragonflydb',
  async (tx, db) => {
    return await db.set('trade:latest', tradeData);
  },
  async (tx, db) => {
    return await db.del('trade:latest');
  }
);

// Commit or rollback
await dbService.commitTransaction(transactionId);
// OR
await dbService.rollbackTransaction(transactionId);
```

## Configuration

### Environment Variables
```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=aitrading_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_POOL_MAX=20

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=aitrading_analytics
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_password

# Weaviate
WEAVIATE_SCHEME=http
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your_api_key

# ArangoDB
ARANGO_URL=http://localhost:8529
ARANGO_DB=aitrading_graph
ARANGO_USER=root
ARANGO_PASSWORD=your_password

# DragonflyDB
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=your_password
```

### Service Configuration
```javascript
const dbService = await createDatabaseService({
  // Health monitoring
  enableHealthMonitoring: true,
  healthCheckInterval: 30000, // 30 seconds

  // Connection pool management
  enablePoolManagement: true,
  poolMonitoringInterval: 60000, // 1 minute

  // Transaction settings
  transactionTimeout: 300000, // 5 minutes
  maxRetries: 3
});
```

## Monitoring and Health

### Health Status
```javascript
const health = await dbService.getHealthStatus();
console.log(`Overall: ${health.overall}`);
console.log(`Databases: ${Object.keys(health.databases).length}`);
```

### Performance Metrics
```javascript
const report = dbService.generatePerformanceReport();
console.log(`Uptime: ${report.health.summary.uptime}%`);
console.log(`Pool efficiency: ${report.pools.summary.efficiency}%`);
```

### Alerts and Monitoring
- Automatic health checks every 30 seconds
- Pool performance monitoring
- Connection failure detection
- Response time alerts
- Memory usage monitoring

## Query Routing

The system automatically routes queries to appropriate databases based on:

1. **Explicit targeting**: `targetDatabase` parameter
2. **Content analysis**: Table/collection names, query patterns
3. **Operation type**: CRUD, analytics, vector, graph, cache operations

### Routing Rules
- `users`, `accounts`, `transactions` → PostgreSQL
- `metrics`, `events`, `time_series` → ClickHouse
- `embeddings`, `vectors`, `similarity` → Weaviate
- `relationships`, `networks`, `graphs` → ArangoDB
- `cache`, `session`, `temporary` → DragonflyDB

## Performance Optimization

### Connection Pooling
- Database-specific pool configurations
- Dynamic pool sizing based on load
- Connection health monitoring
- Automatic pool optimization

### Query Optimization
- Database-specific query transformations
- Caching of frequently accessed data
- Connection reuse and management
- Batch operation support

### Monitoring
- Real-time performance metrics
- Bottleneck detection
- Resource utilization tracking
- Performance recommendations

## Error Handling

### Graceful Degradation
- Automatic failover for non-critical operations
- Circuit breaker patterns
- Retry logic with exponential backoff
- Fallback to alternative databases when possible

### Transaction Safety
- ACID compliance where supported
- Compensation patterns for non-transactional databases
- Automatic rollback on failures
- Distributed transaction coordination

## Migration Guide

### From Single Database
1. Replace `DatabaseConfig` imports with `createDatabaseService`
2. Update query calls to use unified interface
3. Configure additional databases as needed
4. Test cross-database operations

### Legacy Compatibility
The system maintains backward compatibility through the enhanced `DatabaseConfig` class that wraps the new multi-database service.

## Best Practices

### Database Selection
- Use PostgreSQL for ACID-compliant operational data
- Use ClickHouse for analytics and time-series data
- Use Weaviate for AI/ML vector operations
- Use ArangoDB for complex relationships and graph data
- Use DragonflyDB for high-performance caching

### Performance
- Use appropriate database for each data type
- Implement proper indexing strategies
- Monitor connection pool utilization
- Use transactions only when necessary
- Cache frequently accessed data

### Security
- Use environment variables for credentials
- Implement proper access controls
- Monitor for unusual activity
- Regular security audits
- Encrypted connections where possible

## Troubleshooting

### Common Issues
1. **Connection failures**: Check database availability and credentials
2. **Performance issues**: Monitor pool utilization and query performance
3. **Transaction failures**: Check cross-database compatibility
4. **Memory issues**: Monitor connection pool sizes and cache usage

### Debugging
- Enable detailed logging
- Monitor health endpoints
- Check performance reports
- Review connection pool metrics
- Analyze transaction logs

## Future Enhancements

### Planned Features
- Automatic database sharding
- Read/write replicas support
- Advanced caching strategies
- Machine learning-based query optimization
- Real-time data synchronization
- Enhanced monitoring and alerting

### Extensibility
The architecture is designed to easily accommodate additional database types and features through the plugin-based factory pattern.