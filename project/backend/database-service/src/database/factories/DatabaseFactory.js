/**
 * Database Factory Pattern Implementation
 * Creates and manages multiple database instances
 */

const PostgreSQLManager = require('../managers/PostgreSQLManager');
const ClickHouseManager = require('../managers/ClickHouseManager');
const WeaviateManager = require('../managers/WeaviateManager');
const ArangoDBManager = require('../managers/ArangoDBManager');
const DragonflyDBManager = require('../managers/DragonflyDBManager');
const RedpandaManager = require('../managers/RedpandaManager');
const winston = require('winston');

// Logger configuration
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/database-factory.log' })
  ]
});

class DatabaseFactory {
  constructor() {
    this.databases = new Map();
    this.config = this.loadConfiguration();
    this.initialized = false;
  }

  /**
   * Load database configuration from environment
   */
  loadConfiguration() {
    return {
      postgresql: {
        type: 'postgresql',
        host: process.env.POSTGRES_HOST || 'localhost',
        port: process.env.POSTGRES_PORT || 5432,
        database: process.env.POSTGRES_DB || 'aitrading_db',
        user: process.env.POSTGRES_USER || 'postgres',
        password: process.env.POSTGRES_PASSWORD || 'postgres',
        max: parseInt(process.env.POSTGRES_POOL_MAX) || 20,
        idleTimeoutMillis: parseInt(process.env.POSTGRES_IDLE_TIMEOUT) || 30000,
        connectionTimeoutMillis: parseInt(process.env.POSTGRES_CONNECTION_TIMEOUT) || 2000,
      },
      clickhouse: {
        type: 'clickhouse',
        host: process.env.CLICKHOUSE_HOST || 'localhost',
        port: process.env.CLICKHOUSE_PORT || 8123,
        database: process.env.CLICKHOUSE_DB || 'aitrading_analytics',
        user: process.env.CLICKHOUSE_USER || 'default',
        password: process.env.CLICKHOUSE_PASSWORD || '',
        max_connections: parseInt(process.env.CLICKHOUSE_POOL_MAX) || 10,
      },
      weaviate: {
        type: 'weaviate',
        scheme: process.env.WEAVIATE_SCHEME || 'http',
        host: process.env.WEAVIATE_HOST || 'localhost',
        port: process.env.WEAVIATE_PORT || 8080,
        apiKey: process.env.WEAVIATE_API_KEY || '',
      },
      arangodb: {
        type: 'arangodb',
        url: process.env.ARANGO_URL || 'http://localhost:8529',
        database: process.env.ARANGO_DB || 'aitrading_graph',
        username: process.env.ARANGO_USER || 'root',
        password: process.env.ARANGO_PASSWORD || '',
        maxSockets: parseInt(process.env.ARANGO_POOL_MAX) || 20,
      },
      dragonflydb: {
        type: 'dragonflydb',
        host: process.env.DRAGONFLY_HOST || 'localhost',
        port: process.env.DRAGONFLY_PORT || 6379,
        password: process.env.DRAGONFLY_PASSWORD || '',
        maxRetriesPerRequest: parseInt(process.env.DRAGONFLY_MAX_RETRIES) || 3,
        retryDelayOnFailover: parseInt(process.env.DRAGONFLY_RETRY_DELAY) || 100,
      },
      redpanda: {
        type: 'redpanda',
        brokers: process.env.REDPANDA_BROKERS ? process.env.REDPANDA_BROKERS.split(',') : ['localhost:19092'],
        schemaRegistry: process.env.REDPANDA_SCHEMA_REGISTRY || 'http://localhost:8081',
        adminApi: process.env.REDPANDA_ADMIN_API || 'http://localhost:9644',
      }
    };
  }

  /**
   * Create database manager instance
   * @param {string} type - Database type
   * @returns {IDatabaseManager}
   */
  createDatabase(type) {
    const config = this.config[type];
    if (!config) {
      throw new Error(`Unsupported database type: ${type}`);
    }

    let manager;
    switch (type) {
      case 'postgresql':
        manager = new PostgreSQLManager(config);
        break;
      case 'clickhouse':
        manager = new ClickHouseManager(config);
        break;
      case 'weaviate':
        manager = new WeaviateManager(config);
        break;
      case 'arangodb':
        manager = new ArangoDBManager(config);
        break;
      case 'dragonflydb':
        manager = new DragonflyDBManager(config);
        break;
      case 'redpanda':
        manager = new RedpandaManager(config);
        break;
      default:
        throw new Error(`Unknown database type: ${type}`);
    }

    logger.info(`Created database manager for type: ${type}`, { config: { ...config, password: '***' } });
    return manager;
  }

  /**
   * Get database manager instance
   * @param {string} type - Database type
   * @returns {IDatabaseManager}
   */
  getDatabase(type) {
    if (!this.databases.has(type)) {
      const manager = this.createDatabase(type);
      this.databases.set(type, manager);
    }
    return this.databases.get(type);
  }

  /**
   * Initialize all configured databases
   * @returns {Promise<void>}
   */
  async initializeAll() {
    try {
      const initPromises = Object.keys(this.config).map(async (type) => {
        try {
          const manager = this.getDatabase(type);
          await manager.initialize();
          logger.info(`Successfully initialized ${type} database`);
          return { type, status: 'connected' };
        } catch (error) {
          logger.error(`Failed to initialize ${type} database:`, error);
          return { type, status: 'failed', error: error.message };
        }
      });

      const results = await Promise.allSettled(initPromises);
      const summary = results.map(result => result.status === 'fulfilled' ? result.value : { status: 'error' });

      this.initialized = true;
      logger.info('Database initialization completed', { summary });

      return summary;
    } catch (error) {
      logger.error('Database factory initialization failed:', error);
      throw error;
    }
  }

  /**
   * Get all database instances
   * @returns {Map<string, IDatabaseManager>}
   */
  getAllDatabases() {
    return this.databases;
  }

  /**
   * Get factory status
   * @returns {Object}
   */
  getStatus() {
    const status = {
      initialized: this.initialized,
      databases: {},
      summary: {
        total: this.databases.size,
        connected: 0,
        failed: 0
      }
    };

    this.databases.forEach((manager, type) => {
      const dbStatus = manager.getStatus();
      status.databases[type] = dbStatus;
      if (dbStatus.connected || dbStatus.status === 'connected') {
        status.summary.connected++;
      } else {
        status.summary.failed++;
      }
    });

    return status;
  }

  /**
   * Perform health check on all databases
   * @returns {Promise<Object>}
   */
  async healthCheckAll() {
    const healthChecks = {};
    const promises = [];

    this.databases.forEach((manager, type) => {
      promises.push(
        manager.healthCheck()
          .then(result => ({ type, status: 'healthy', ...result }))
          .catch(error => ({ type, status: 'unhealthy', error: error.message }))
      );
    });

    const results = await Promise.allSettled(promises);
    results.forEach(result => {
      if (result.status === 'fulfilled') {
        healthChecks[result.value.type] = result.value;
      }
    });

    return {
      timestamp: new Date().toISOString(),
      overall: Object.values(healthChecks).every(check => check.status === 'healthy') ? 'healthy' : 'degraded',
      databases: healthChecks
    };
  }

  /**
   * Close all database connections
   * @returns {Promise<void>}
   */
  async closeAll() {
    try {
      const closePromises = Array.from(this.databases.values()).map(manager =>
        manager.close().catch(error => logger.error('Error closing database:', error))
      );

      await Promise.all(closePromises);
      this.databases.clear();
      this.initialized = false;
      logger.info('All database connections closed');
    } catch (error) {
      logger.error('Error closing databases:', error);
      throw error;
    }
  }

  /**
   * Get database types
   * @returns {string[]}
   */
  getSupportedTypes() {
    return Object.keys(this.config);
  }
}

module.exports = DatabaseFactory;