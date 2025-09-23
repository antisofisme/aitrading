/**
 * Database Manager - Multi-Database Connection Handler
 *
 * Manages connections to the 6-database architecture:
 * - PostgreSQL (Primary transactional data)
 * - DragonflyDB (High-performance cache)
 * - ClickHouse (Analytics data)
 * - Weaviate (Vector/AI data)
 * - ArangoDB (Graph data)
 * - Redis (Legacy cache support)
 */

const { Pool } = require('pg');
const { createClient } = require('redis');
const { Client } = require('@clickhouse/client');
const weaviate = require('weaviate-ts-client');
const { Database } = require('arangojs');
const winston = require('winston');

class DatabaseManager {
  constructor(logger = null) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console(),
        new winston.transports.File({ filename: 'logs/database-manager.log' })
      ]
    });

    this.connections = {
      postgres: null,
      dragonflydb: null,
      clickhouse: null,
      weaviate: null,
      arangodb: null,
      redis: null
    };

    this.connectionStatus = {
      postgres: false,
      dragonflydb: false,
      clickhouse: false,
      weaviate: false,
      arangodb: false,
      redis: false
    };

    this.isInitialized = false;
  }

  /**
   * Initialize all database connections
   */
  async initialize() {
    try {
      this.logger.info('Initializing database connections...');

      // Initialize connections in parallel
      const connectionPromises = [
        this.initializePostgreSQL(),
        this.initializeDragonflyDB(),
        this.initializeClickHouse(),
        this.initializeWeaviate(),
        this.initializeArangoDB(),
        this.initializeRedis()
      ];

      await Promise.allSettled(connectionPromises);

      this.isInitialized = true;
      this.logger.info('Database Manager initialized', {
        connectionStatus: this.connectionStatus
      });

      return this.connectionStatus;
    } catch (error) {
      this.logger.error('Failed to initialize DatabaseManager', { error: error.message });
      throw error;
    }
  }

  /**
   * Initialize PostgreSQL connection
   */
  async initializePostgreSQL() {
    try {
      const config = {
        host: process.env.POSTGRES_HOST || 'postgres',
        port: parseInt(process.env.POSTGRES_PORT) || 5432,
        database: process.env.POSTGRES_DB || 'ai_trading',
        user: process.env.POSTGRES_USER || 'ai_trading_user',
        password: process.env.POSTGRES_PASSWORD || 'secure_password_123',
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
        ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
      };

      this.connections.postgres = new Pool(config);

      // Test connection
      const client = await this.connections.postgres.connect();
      await client.query('SELECT 1');
      client.release();

      this.connectionStatus.postgres = true;
      this.logger.info('PostgreSQL connection established');
    } catch (error) {
      this.logger.error('Failed to connect to PostgreSQL', { error: error.message });
      this.connectionStatus.postgres = false;
    }
  }

  /**
   * Initialize DragonflyDB connection
   */
  async initializeDragonflyDB() {
    try {
      const config = {
        socket: {
          host: process.env.DRAGONFLY_HOST || 'dragonflydb',
          port: parseInt(process.env.DRAGONFLY_PORT) || 6379
        },
        password: process.env.DRAGONFLY_PASSWORD || undefined,
        database: 0
      };

      this.connections.dragonflydb = createClient(config);

      this.connections.dragonflydb.on('error', (err) => {
        this.logger.error('DragonflyDB error', { error: err.message });
        this.connectionStatus.dragonflydb = false;
      });

      this.connections.dragonflydb.on('connect', () => {
        this.logger.info('DragonflyDB connected');
        this.connectionStatus.dragonflydb = true;
      });

      await this.connections.dragonflydb.connect();
      await this.connections.dragonflydb.ping();

      this.connectionStatus.dragonflydb = true;
      this.logger.info('DragonflyDB connection established');
    } catch (error) {
      this.logger.error('Failed to connect to DragonflyDB', { error: error.message });
      this.connectionStatus.dragonflydb = false;
    }
  }

  /**
   * Initialize ClickHouse connection
   */
  async initializeClickHouse() {
    try {
      this.connections.clickhouse = new Client({
        host: process.env.CLICKHOUSE_HOST || 'clickhouse',
        port: parseInt(process.env.CLICKHOUSE_PORT) || 8123,
        username: process.env.CLICKHOUSE_USER || 'default',
        password: process.env.CLICKHOUSE_PASSWORD || 'secure_password_456',
        database: process.env.CLICKHOUSE_DB || 'aitrading_analytics'
      });

      // Test connection
      await this.connections.clickhouse.query({ query: 'SELECT 1' });

      this.connectionStatus.clickhouse = true;
      this.logger.info('ClickHouse connection established');
    } catch (error) {
      this.logger.error('Failed to connect to ClickHouse', { error: error.message });
      this.connectionStatus.clickhouse = false;
    }
  }

  /**
   * Initialize Weaviate connection
   */
  async initializeWeaviate() {
    try {
      this.connections.weaviate = weaviate.client({
        scheme: 'http',
        host: `${process.env.WEAVIATE_HOST || 'weaviate'}:${process.env.WEAVIATE_PORT || 8080}`
      });

      // Test connection
      await this.connections.weaviate.misc.readyChecker().do();

      this.connectionStatus.weaviate = true;
      this.logger.info('Weaviate connection established');
    } catch (error) {
      this.logger.error('Failed to connect to Weaviate', { error: error.message });
      this.connectionStatus.weaviate = false;
    }
  }

  /**
   * Initialize ArangoDB connection
   */
  async initializeArangoDB() {
    try {
      this.connections.arangodb = new Database({
        url: process.env.ARANGO_URL || 'http://arangodb:8529',
        databaseName: process.env.ARANGO_DB || 'aitrading_graph',
        auth: {
          username: 'root',
          password: process.env.ARANGO_PASSWORD || 'secure_password_789'
        }
      });

      // Test connection
      await this.connections.arangodb.version();

      this.connectionStatus.arangodb = true;
      this.logger.info('ArangoDB connection established');
    } catch (error) {
      this.logger.error('Failed to connect to ArangoDB', { error: error.message });
      this.connectionStatus.arangodb = false;
    }
  }

  /**
   * Initialize Redis connection (legacy support)
   */
  async initializeRedis() {
    try {
      this.connections.redis = createClient({
        socket: {
          host: process.env.REDIS_HOST || 'redis',
          port: parseInt(process.env.REDIS_PORT) || 6380
        }
      });

      this.connections.redis.on('error', (err) => {
        this.logger.error('Redis error', { error: err.message });
        this.connectionStatus.redis = false;
      });

      await this.connections.redis.connect();
      await this.connections.redis.ping();

      this.connectionStatus.redis = true;
      this.logger.info('Redis connection established');
    } catch (error) {
      this.logger.error('Failed to connect to Redis', { error: error.message });
      this.connectionStatus.redis = false;
    }
  }

  /**
   * Get specific database connection
   */
  getConnection(database) {
    if (!this.connections[database]) {
      throw new Error(`Database connection '${database}' not found`);
    }
    return this.connections[database];
  }

  /**
   * Check if specific database is connected
   */
  isConnected(database) {
    return this.connectionStatus[database] || false;
  }

  /**
   * Get all connection statuses
   */
  getConnectionStatus() {
    return { ...this.connectionStatus };
  }

  /**
   * Health check for all databases
   */
  async healthCheck() {
    const healthChecks = {};

    // PostgreSQL health check
    try {
      if (this.connections.postgres) {
        const client = await this.connections.postgres.connect();
        await client.query('SELECT 1');
        client.release();
        healthChecks.postgres = { status: 'healthy', timestamp: new Date() };
      } else {
        healthChecks.postgres = { status: 'disconnected', timestamp: new Date() };
      }
    } catch (error) {
      healthChecks.postgres = { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }

    // DragonflyDB health check
    try {
      if (this.connections.dragonflydb && this.connectionStatus.dragonflydb) {
        await this.connections.dragonflydb.ping();
        healthChecks.dragonflydb = { status: 'healthy', timestamp: new Date() };
      } else {
        healthChecks.dragonflydb = { status: 'disconnected', timestamp: new Date() };
      }
    } catch (error) {
      healthChecks.dragonflydb = { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }

    // ClickHouse health check
    try {
      if (this.connections.clickhouse && this.connectionStatus.clickhouse) {
        await this.connections.clickhouse.query({ query: 'SELECT 1' });
        healthChecks.clickhouse = { status: 'healthy', timestamp: new Date() };
      } else {
        healthChecks.clickhouse = { status: 'disconnected', timestamp: new Date() };
      }
    } catch (error) {
      healthChecks.clickhouse = { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }

    // Weaviate health check
    try {
      if (this.connections.weaviate && this.connectionStatus.weaviate) {
        await this.connections.weaviate.misc.readyChecker().do();
        healthChecks.weaviate = { status: 'healthy', timestamp: new Date() };
      } else {
        healthChecks.weaviate = { status: 'disconnected', timestamp: new Date() };
      }
    } catch (error) {
      healthChecks.weaviate = { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }

    // ArangoDB health check
    try {
      if (this.connections.arangodb && this.connectionStatus.arangodb) {
        await this.connections.arangodb.version();
        healthChecks.arangodb = { status: 'healthy', timestamp: new Date() };
      } else {
        healthChecks.arangodb = { status: 'disconnected', timestamp: new Date() };
      }
    } catch (error) {
      healthChecks.arangodb = { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }

    // Redis health check
    try {
      if (this.connections.redis && this.connectionStatus.redis) {
        await this.connections.redis.ping();
        healthChecks.redis = { status: 'healthy', timestamp: new Date() };
      } else {
        healthChecks.redis = { status: 'disconnected', timestamp: new Date() };
      }
    } catch (error) {
      healthChecks.redis = { status: 'unhealthy', error: error.message, timestamp: new Date() };
    }

    return healthChecks;
  }

  /**
   * Close all database connections
   */
  async close() {
    try {
      const closePromises = [];

      if (this.connections.postgres) {
        closePromises.push(this.connections.postgres.end());
      }

      if (this.connections.dragonflydb && this.connectionStatus.dragonflydb) {
        closePromises.push(this.connections.dragonflydb.quit());
      }

      if (this.connections.clickhouse) {
        closePromises.push(this.connections.clickhouse.close());
      }

      if (this.connections.redis && this.connectionStatus.redis) {
        closePromises.push(this.connections.redis.quit());
      }

      await Promise.allSettled(closePromises);

      this.logger.info('All database connections closed');
    } catch (error) {
      this.logger.error('Error closing database connections', { error: error.message });
    }
  }
}

module.exports = DatabaseManager;