/**
 * Multi-Database Manager
 * Manages connections to multiple database types as specified in plan2 Level 1
 */

const { Pool } = require('pg');
const { createClient } = require('redis');
const { MongoClient } = require('mongodb');
const winston = require('winston');

// Logger
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class MultiDbManager {
  constructor() {
    this.connections = new Map();
    this.healthStatus = new Map();
    this.isInitialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing Multi-Database Manager...');

      // Initialize PostgreSQL (Primary relational database)
      await this.initializePostgreSQL();

      // Initialize Redis (Cache and sessions)
      await this.initializeRedis();

      // Initialize MongoDB (Document storage for logs and configurations)
      await this.initializeMongoDB();

      // Initialize mock connections for other databases mentioned in plan2
      await this.initializeMockDatabases();

      // Start health monitoring
      this.startHealthMonitoring();

      this.isInitialized = true;
      logger.info('Multi-Database Manager initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Multi-Database Manager:', error);
      throw error;
    }
  }

  async initializePostgreSQL() {
    try {
      const pgPool = new Pool({
        host: process.env.POSTGRES_HOST || 'localhost',
        port: process.env.POSTGRES_PORT || 5432,
        database: process.env.POSTGRES_DB || 'aitrading',
        user: process.env.POSTGRES_USER || 'postgres',
        password: process.env.POSTGRES_PASSWORD || 'aitrading2024',
        max: 20,
        idleTimeoutMillis: 30000,
        connectionTimeoutMillis: 2000,
      });

      // Test connection
      const client = await pgPool.connect();
      await client.query('SELECT NOW()');
      client.release();

      this.connections.set('postgresql', pgPool);
      this.healthStatus.set('postgresql', { status: 'healthy', lastCheck: new Date() });

      logger.info('PostgreSQL connection established');
    } catch (error) {
      logger.error('PostgreSQL connection failed:', error);
      this.healthStatus.set('postgresql', { status: 'unhealthy', error: error.message });
      throw error;
    }
  }

  async initializeRedis() {
    try {
      const redisClient = createClient({
        host: process.env.REDIS_HOST || 'localhost',
        port: process.env.REDIS_PORT || 6379,
        password: process.env.REDIS_PASSWORD,
        retry_unfulfilled_commands: true,
        retry_delay_on_failover: 100,
        enable_offline_queue: false
      });

      redisClient.on('error', (err) => {
        logger.error('Redis error:', err);
        this.healthStatus.set('redis', { status: 'unhealthy', error: err.message });
      });

      redisClient.on('connect', () => {
        logger.info('Redis connected');
        this.healthStatus.set('redis', { status: 'healthy', lastCheck: new Date() });
      });

      await redisClient.connect();

      // Test connection
      await redisClient.ping();

      this.connections.set('redis', redisClient);
      this.healthStatus.set('redis', { status: 'healthy', lastCheck: new Date() });

      logger.info('Redis connection established');
    } catch (error) {
      logger.error('Redis connection failed:', error);
      this.healthStatus.set('redis', { status: 'unhealthy', error: error.message });
      // Don't throw error for Redis as it's not critical for basic functionality
    }
  }

  async initializeMongoDB() {
    try {
      const mongoUri = `mongodb://${process.env.MONGO_USERNAME || 'admin'}:${process.env.MONGO_PASSWORD || 'aitrading2024'}@${process.env.MONGODB_HOST || 'localhost'}:${process.env.MONGODB_PORT || 27017}/${process.env.MONGO_DATABASE || 'aitrading_logs'}?authSource=admin`;

      const mongoClient = new MongoClient(mongoUri, {
        maxPoolSize: 10,
        serverSelectionTimeoutMS: 5000,
        socketTimeoutMS: 45000,
      });

      await mongoClient.connect();

      // Test connection
      await mongoClient.db().admin().ping();

      this.connections.set('mongodb', mongoClient);
      this.healthStatus.set('mongodb', { status: 'healthy', lastCheck: new Date() });

      logger.info('MongoDB connection established');
    } catch (error) {
      logger.error('MongoDB connection failed:', error);
      this.healthStatus.set('mongodb', { status: 'unhealthy', error: error.message });
      // Don't throw error for MongoDB as it's not critical for basic functionality
    }
  }

  async initializeMockDatabases() {
    // Mock implementations for databases mentioned in plan2 but not yet implemented

    // ClickHouse (Analytics database)
    this.connections.set('clickhouse', {
      query: async (sql) => {
        logger.info(`Mock ClickHouse query: ${sql}`);
        return { rows: [] };
      },
      ping: async () => true
    });
    this.healthStatus.set('clickhouse', { status: 'mock', lastCheck: new Date() });

    // Weaviate (Vector database)
    this.connections.set('weaviate', {
      query: async (query) => {
        logger.info(`Mock Weaviate query: ${JSON.stringify(query)}`);
        return { data: [] };
      },
      ping: async () => true
    });
    this.healthStatus.set('weaviate', { status: 'mock', lastCheck: new Date() });

    // ArangoDB (Graph database)
    this.connections.set('arangodb', {
      query: async (aql) => {
        logger.info(`Mock ArangoDB query: ${aql}`);
        return { cursor: { all: async () => [] } };
      },
      ping: async () => true
    });
    this.healthStatus.set('arangodb', { status: 'mock', lastCheck: new Date() });

    // DragonflyDB (Redis alternative)
    this.connections.set('dragonflydb', {
      get: async (key) => {
        logger.info(`Mock DragonflyDB GET: ${key}`);
        return null;
      },
      set: async (key, value) => {
        logger.info(`Mock DragonflyDB SET: ${key} = ${value}`);
        return 'OK';
      },
      ping: async () => 'PONG'
    });
    this.healthStatus.set('dragonflydb', { status: 'mock', lastCheck: new Date() });

    logger.info('Mock database connections initialized');
  }

  async getConnection(database) {
    if (!this.connections.has(database)) {
      throw new Error(`Database connection not found: ${database}`);
    }
    return this.connections.get(database);
  }

  async executeQuery(database, query, params = []) {
    const connection = await this.getConnection(database);

    switch (database) {
      case 'postgresql':
        const result = await connection.query(query, params);
        return result.rows;

      case 'redis':
        // Handle Redis operations
        if (query.type === 'GET') {
          return await connection.get(query.key);
        } else if (query.type === 'SET') {
          return await connection.set(query.key, query.value);
        }
        throw new Error(`Unsupported Redis operation: ${query.type}`);

      case 'mongodb':
        const db = connection.db();
        const collection = db.collection(query.collection);

        switch (query.operation) {
          case 'find':
            return await collection.find(query.filter || {}).toArray();
          case 'insertOne':
            return await collection.insertOne(query.document);
          case 'updateOne':
            return await collection.updateOne(query.filter, query.update);
          case 'deleteOne':
            return await collection.deleteOne(query.filter);
          default:
            throw new Error(`Unsupported MongoDB operation: ${query.operation}`);
        }

      case 'clickhouse':
      case 'weaviate':
      case 'arangodb':
      case 'dragonflydb':
        // Mock implementations
        return await connection.query(query);

      default:
        throw new Error(`Unsupported database: ${database}`);
    }
  }

  async healthCheck(database) {
    try {
      const connection = await this.getConnection(database);

      switch (database) {
        case 'postgresql':
          await connection.query('SELECT 1');
          break;
        case 'redis':
          await connection.ping();
          break;
        case 'mongodb':
          await connection.db().admin().ping();
          break;
        default:
          await connection.ping();
      }

      this.healthStatus.set(database, { status: 'healthy', lastCheck: new Date() });
      return { status: 'healthy' };
    } catch (error) {
      this.healthStatus.set(database, { status: 'unhealthy', error: error.message, lastCheck: new Date() });
      return { status: 'unhealthy', error: error.message };
    }
  }

  async healthCheckAll() {
    const results = {};
    const databases = Array.from(this.connections.keys());

    for (const database of databases) {
      results[database] = await this.healthCheck(database);
    }

    return results;
  }

  startHealthMonitoring() {
    setInterval(async () => {
      try {
        await this.healthCheckAll();
      } catch (error) {
        logger.error('Health monitoring error:', error);
      }
    }, 30000); // Check every 30 seconds
  }

  getHealthStatus() {
    const status = {};
    for (const [database, health] of this.healthStatus.entries()) {
      status[database] = health;
    }
    return status;
  }

  getConnectionCount() {
    return {
      total: this.connections.size,
      healthy: Array.from(this.healthStatus.values()).filter(h => h.status === 'healthy').length,
      unhealthy: Array.from(this.healthStatus.values()).filter(h => h.status === 'unhealthy').length,
      mock: Array.from(this.healthStatus.values()).filter(h => h.status === 'mock').length
    };
  }

  async disconnect() {
    logger.info('Disconnecting from all databases...');

    for (const [database, connection] of this.connections.entries()) {
      try {
        switch (database) {
          case 'postgresql':
            await connection.end();
            break;
          case 'redis':
            await connection.quit();
            break;
          case 'mongodb':
            await connection.close();
            break;
          default:
            // Mock connections don't need cleanup
            break;
        }
        logger.info(`Disconnected from ${database}`);
      } catch (error) {
        logger.error(`Error disconnecting from ${database}:`, error);
      }
    }

    this.connections.clear();
    this.healthStatus.clear();
    this.isInitialized = false;
  }
}

module.exports = MultiDbManager;