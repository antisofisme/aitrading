/**
 * PostgreSQL Database Manager
 * Enhanced version of existing PostgreSQL implementation
 */

const { Pool } = require('pg');
const IDatabaseManager = require('../interfaces/IDatabaseManager');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/postgresql.log' })
  ]
});

class PostgreSQLManager extends IDatabaseManager {
  constructor(config) {
    super();
    this.config = config;
    this.pool = null;
    this.isConnected = false;
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 5;
  }

  async initialize() {
    try {
      this.pool = new Pool(this.config);

      // Test connection with retry logic
      await this.testConnection();

      this.isConnected = true;
      logger.info('PostgreSQL connection established successfully', {
        host: this.config.host,
        port: this.config.port,
        database: this.config.database
      });

      // Set up error handling
      this.pool.on('error', (err) => {
        logger.error('PostgreSQL pool error:', err);
        this.isConnected = false;
      });

      this.pool.on('connect', () => {
        logger.debug('New PostgreSQL client connected');
      });

      this.pool.on('remove', () => {
        logger.debug('PostgreSQL client removed from pool');
      });

      return this.pool;
    } catch (error) {
      logger.error('Failed to initialize PostgreSQL connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async testConnection() {
    let lastError;
    for (let attempt = 1; attempt <= this.maxConnectionAttempts; attempt++) {
      try {
        const client = await this.pool.connect();
        const result = await client.query('SELECT NOW() as current_time, version() as version');
        client.release();

        logger.info('PostgreSQL connection test successful', {
          attempt,
          serverTime: result.rows[0].current_time,
          version: result.rows[0].version.split(' ')[0]
        });
        return;
      } catch (error) {
        lastError = error;
        logger.warn(`PostgreSQL connection attempt ${attempt} failed:`, error.message);

        if (attempt < this.maxConnectionAttempts) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    throw lastError;
  }

  async query(text, params = []) {
    if (!this.isConnected) {
      throw new Error('PostgreSQL not connected');
    }

    try {
      const start = Date.now();
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;

      logger.info('PostgreSQL query executed', {
        duration,
        rows: result.rowCount,
        query: text.substring(0, 100) + (text.length > 100 ? '...' : '')
      });

      return {
        rows: result.rows,
        rowCount: result.rowCount,
        fields: result.fields,
        command: result.command,
        oid: result.oid,
        duration
      };
    } catch (error) {
      logger.error('PostgreSQL query error:', {
        error: error.message,
        query: text.substring(0, 100),
        code: error.code,
        detail: error.detail
      });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected) {
      throw new Error('PostgreSQL not connected');
    }
    return await this.pool.connect();
  }

  async close() {
    if (this.pool) {
      await this.pool.end();
      this.isConnected = false;
      logger.info('PostgreSQL connection closed');
    }
  }

  getStatus() {
    return {
      type: 'postgresql',
      connected: this.isConnected,
      totalCount: this.pool?.totalCount || 0,
      idleCount: this.pool?.idleCount || 0,
      waitingCount: this.pool?.waitingCount || 0,
      config: {
        host: this.config.host,
        port: this.config.port,
        database: this.config.database,
        maxConnections: this.config.max
      }
    };
  }

  async healthCheck() {
    try {
      const client = await this.getClient();
      const startTime = Date.now();

      const result = await client.query('SELECT 1 as health_check, NOW() as timestamp');
      client.release();

      const responseTime = Date.now() - startTime;

      return {
        status: 'healthy',
        responseTime,
        timestamp: result.rows[0].timestamp,
        details: {
          poolStatus: this.getStatus(),
          lastCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('PostgreSQL health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  getType() {
    return 'postgresql';
  }

  getConfig() {
    return { ...this.config, password: '***' };
  }

  async beginTransaction() {
    const client = await this.getClient();
    await client.query('BEGIN');
    return client;
  }

  async commitTransaction(client) {
    try {
      await client.query('COMMIT');
    } finally {
      client.release();
    }
  }

  async rollbackTransaction(client) {
    try {
      await client.query('ROLLBACK');
    } finally {
      client.release();
    }
  }

  // PostgreSQL-specific methods
  async executeInTransaction(queries) {
    const client = await this.beginTransaction();
    try {
      const results = [];
      for (const { query, params } of queries) {
        const result = await client.query(query, params);
        results.push(result);
      }
      await this.commitTransaction(client);
      return results;
    } catch (error) {
      await this.rollbackTransaction(client);
      throw error;
    }
  }

  async createIndex(tableName, columns, options = {}) {
    const indexName = options.name || `idx_${tableName}_${columns.join('_')}`;
    const indexType = options.type || 'btree';
    const unique = options.unique ? 'UNIQUE' : '';

    const query = `
      CREATE ${unique} INDEX IF NOT EXISTS ${indexName}
      ON ${tableName} USING ${indexType} (${columns.join(', ')})
    `;

    return await this.query(query);
  }

  async getTableStats(tableName) {
    const query = `
      SELECT
        schemaname,
        tablename,
        attname,
        n_distinct,
        correlation
      FROM pg_stats
      WHERE tablename = $1
    `;

    return await this.query(query, [tableName]);
  }
}

module.exports = PostgreSQLManager;