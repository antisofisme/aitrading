/**
 * Multi-Database Usage Examples
 * Demonstrates how to use the new multi-database foundation
 */

const { createDatabaseService, DATABASE_TYPES } = require('../src/multi-db');

async function demonstrateMultiDatabaseUsage() {
  console.log('🚀 Multi-Database Foundation Demo');

  try {
    // Initialize the database service with all 5 databases
    console.log('\n📊 Initializing multi-database service...');
    const dbService = await createDatabaseService({
      enableHealthMonitoring: true,
      enablePoolManagement: true,
      healthCheckInterval: 30000, // 30 seconds
      poolMonitoringInterval: 60000 // 1 minute
    });

    // Check service status
    console.log('\n✅ Service Status:');
    const status = dbService.getStatus();
    console.log(`Initialized: ${status.initialized}`);
    console.log(`Databases: ${Object.keys(status.databases.databases).join(', ')}`);

    // Example 1: Store operational data in PostgreSQL
    console.log('\n💾 Example 1: Store user data (PostgreSQL)');
    const userData = {
      table: 'users',
      data: {
        email: 'demo@aitrading.com',
        name: 'Demo User',
        created_at: new Date().toISOString()
      }
    };

    try {
      const result = await dbService.store(userData, { targetDatabase: 'postgresql' });
      console.log('✅ User data stored successfully');
    } catch (error) {
      console.log('⚠️ PostgreSQL not available (expected in demo):', error.message);
    }

    // Example 2: Store time-series data in ClickHouse
    console.log('\n📈 Example 2: Store analytics data (ClickHouse)');
    const analyticsData = {
      table: 'trading_metrics',
      data: {
        timestamp: new Date().toISOString(),
        symbol: 'BTC/USD',
        price: 45000.50,
        volume: 1234.56,
        event_type: 'trade'
      }
    };

    try {
      const result = await dbService.timeSeriesQuery(analyticsData);
      console.log('✅ Analytics data processed');
    } catch (error) {
      console.log('⚠️ ClickHouse not available (expected in demo):', error.message);
    }

    // Example 3: Vector search with Weaviate
    console.log('\n🔍 Example 3: Vector similarity search (Weaviate)');
    try {
      const vectorQuery = {
        className: 'TradingStrategy',
        concepts: ['momentum trading', 'risk management'],
        limit: 5
      };

      const result = await dbService.vectorSearch(vectorQuery);
      console.log('✅ Vector search completed');
    } catch (error) {
      console.log('⚠️ Weaviate not available (expected in demo):', error.message);
    }

    // Example 4: Graph relationships with ArangoDB
    console.log('\n🕸️ Example 4: Graph query (ArangoDB)');
    try {
      const graphQuery = {
        query: `
          FOR v, e IN 1..3 OUTBOUND 'users/demo' GRAPH 'trading_network'
          RETURN { vertex: v, edge: e }
        `
      };

      const result = await dbService.graphQuery(graphQuery);
      console.log('✅ Graph query executed');
    } catch (error) {
      console.log('⚠️ ArangoDB not available (expected in demo):', error.message);
    }

    // Example 5: Cache operations with DragonflyDB
    console.log('\n⚡ Example 5: Cache operations (DragonflyDB)');
    try {
      await dbService.cache('user:session:demo', { userId: 'demo', active: true }, 3600);
      console.log('✅ Data cached successfully');
    } catch (error) {
      console.log('⚠️ DragonflyDB not available (expected in demo):', error.message);
    }

    // Example 6: Cross-database transaction
    console.log('\n🔗 Example 6: Cross-database transaction');
    try {
      const transactionId = await dbService.beginTransaction(['postgresql', 'dragonflydb']);

      // Add operations to the transaction
      await dbService.addTransactionOperation(
        transactionId,
        'postgresql',
        async (tx, db) => {
          return await db.query('INSERT INTO trades (symbol, amount) VALUES ($1, $2)', ['BTC', 100]);
        },
        async (tx, db) => {
          return await db.query('DELETE FROM trades WHERE symbol = $1', ['BTC']);
        }
      );

      await dbService.addTransactionOperation(
        transactionId,
        'dragonflydb',
        async (tx, db) => {
          return await db.set('trade:latest', JSON.stringify({ symbol: 'BTC', amount: 100 }));
        },
        async (tx, db) => {
          return await db.del('trade:latest');
        }
      );

      // Commit the transaction
      await dbService.commitTransaction(transactionId);
      console.log('✅ Cross-database transaction completed');
    } catch (error) {
      console.log('⚠️ Transaction failed (expected in demo):', error.message);
    }

    // Example 7: Health monitoring
    console.log('\n🏥 Example 7: Health monitoring');
    const healthStatus = await dbService.getHealthStatus();
    console.log(`Overall health: ${healthStatus.overall}`);
    console.log(`Active services: ${Object.keys(healthStatus.services).filter(s => healthStatus.services[s]).length}`);

    // Example 8: Performance report
    console.log('\n📊 Example 8: Performance report');
    const performanceReport = dbService.generatePerformanceReport();
    console.log(`Report generated at: ${performanceReport.timestamp}`);
    console.log(`Recommendations: ${performanceReport.recommendations.length}`);

    console.log('\n✅ Multi-database demonstration completed successfully!');
    console.log('\n🎯 Key Features Demonstrated:');
    console.log('   • Multi-database factory pattern');
    console.log('   • Unified query interface with intelligent routing');
    console.log('   • Cross-database transactions');
    console.log('   • Health monitoring and alerting');
    console.log('   • Connection pool management');
    console.log('   • Performance optimization');

    // Cleanup
    await dbService.shutdown();

  } catch (error) {
    console.error('❌ Demo failed:', error.message);
    console.error('Stack:', error.stack);
  }
}

// Configuration examples
function showConfigurationExamples() {
  console.log('\n⚙️ Configuration Examples:');

  console.log('\n📝 Environment Variables:');
  console.log(`
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=aitrading_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_POOL_MAX=20

# ClickHouse Configuration
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_DB=aitrading_analytics
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=your_password

# Weaviate Configuration
WEAVIATE_SCHEME=http
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_API_KEY=your_api_key

# ArangoDB Configuration
ARANGO_URL=http://localhost:8529
ARANGO_DB=aitrading_graph
ARANGO_USER=root
ARANGO_PASSWORD=your_password

# DragonflyDB Configuration
DRAGONFLY_HOST=localhost
DRAGONFLY_PORT=6379
DRAGONFLY_PASSWORD=your_password
  `);

  console.log('\n🔧 Programmatic Configuration:');
  console.log(`
const { createDatabaseService } = require('./src/multi-db');

const dbService = await createDatabaseService({
  enableHealthMonitoring: true,
  enablePoolManagement: true,
  healthCheckInterval: 30000,
  poolMonitoringInterval: 60000
});
  `);
}

// Integration examples
function showIntegrationExamples() {
  console.log('\n🔗 Integration Examples:');

  console.log('\n📦 Express.js Integration:');
  console.log(`
const express = require('express');
const { createDatabaseService } = require('./database-service/src/multi-db');

const app = express();
let dbService;

app.use(async (req, res, next) => {
  if (!dbService) {
    dbService = await createDatabaseService();
  }
  req.db = dbService;
  next();
});

app.post('/api/trades', async (req, res) => {
  try {
    // Store in PostgreSQL
    const trade = await req.db.store({
      table: 'trades',
      data: req.body
    });

    // Cache in DragonflyDB
    await req.db.cache(\`trade:\${trade.id}\`, trade, 3600);

    // Index in ClickHouse for analytics
    await req.db.timeSeriesQuery({
      table: 'trade_events',
      data: { ...trade, timestamp: new Date() }
    });

    res.json(trade);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
  `);

  console.log('\n🔄 Migration from Legacy:');
  console.log(`
// Before (single database)
const DatabaseConfig = require('./config/database');
const db = new DatabaseConfig();
await db.initialize();
const result = await db.query('SELECT * FROM users');

// After (multi-database)
const { createDatabaseService } = require('./multi-db');
const dbService = await createDatabaseService();
const result = await dbService.retrieve({
  table: 'users',
  targetDatabase: 'postgresql' // Optional: auto-routed if not specified
});
  `);
}

// Run demonstration
if (require.main === module) {
  console.log('🎯 AI Trading Platform - Multi-Database Foundation');
  console.log('================================================');

  showConfigurationExamples();
  showIntegrationExamples();

  console.log('\n🚀 Starting live demonstration...');
  demonstrateMultiDatabaseUsage();
}

module.exports = {
  demonstrateMultiDatabaseUsage,
  showConfigurationExamples,
  showIntegrationExamples
};