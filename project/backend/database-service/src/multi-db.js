/**
 * Multi-Database Service Entry Point
 * Advanced multi-database foundation for AI Trading Platform
 */

const DatabaseService = require('./database/DatabaseService');
const DatabaseFactory = require('./database/factories/DatabaseFactory');
const UnifiedDatabaseInterface = require('./database/UnifiedDatabaseInterface');

// Individual database managers
const PostgreSQLManager = require('./database/managers/PostgreSQLManager');
const ClickHouseManager = require('./database/managers/ClickHouseManager');
const WeaviateManager = require('./database/managers/WeaviateManager');
const ArangoDBManager = require('./database/managers/ArangoDBManager');
const DragonflyDBManager = require('./database/managers/DragonflyDBManager');

// Utilities
const HealthMonitor = require('./database/health/HealthMonitor');
const ConnectionPoolManager = require('./database/utils/ConnectionPoolManager');
const TransactionCoordinator = require('./database/utils/TransactionCoordinator');

module.exports = {
  // Main service
  DatabaseService,

  // Core components
  DatabaseFactory,
  UnifiedDatabaseInterface,

  // Database managers
  PostgreSQLManager,
  ClickHouseManager,
  WeaviateManager,
  ArangoDBManager,
  DragonflyDBManager,

  // Utilities
  HealthMonitor,
  ConnectionPoolManager,
  TransactionCoordinator,

  // Factory function for easy initialization
  createDatabaseService: async (options = {}) => {
    const service = new DatabaseService();
    await service.initialize(options);
    return service;
  },

  // Quick access to specific database types
  createPostgreSQLManager: (config) => new PostgreSQLManager(config),
  createClickHouseManager: (config) => new ClickHouseManager(config),
  createWeaviateManager: (config) => new WeaviateManager(config),
  createArangoDBManager: (config) => new ArangoDBManager(config),
  createDragonflyDBManager: (config) => new DragonflyDBManager(config),

  // Database types constant
  DATABASE_TYPES: {
    POSTGRESQL: 'postgresql',
    CLICKHOUSE: 'clickhouse',
    WEAVIATE: 'weaviate',
    ARANGODB: 'arangodb',
    DRAGONFLYDB: 'dragonflydb'
  }
};