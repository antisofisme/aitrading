const { Pool } = require('pg');
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
    new winston.transports.File({ filename: 'logs/database.log' })
  ]
});

class DatabaseConfig {
  constructor() {
    this.config = {
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'aitrading_db',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'postgres',
      max: parseInt(process.env.DB_POOL_MAX) || 20,
      idleTimeoutMillis: parseInt(process.env.DB_IDLE_TIMEOUT) || 30000,
      connectionTimeoutMillis: parseInt(process.env.DB_CONNECTION_TIMEOUT) || 2000,
    };

    this.pool = null;
    this.isConnected = false;
  }

  async initialize() {
    try {
      this.pool = new Pool(this.config);

      // Test connection
      const client = await this.pool.connect();
      await client.query('SELECT NOW()');
      client.release();

      this.isConnected = true;
      logger.info('Database connection established successfully');

      // Set up error handling
      this.pool.on('error', (err) => {
        logger.error('Database pool error:', err);
        this.isConnected = false;
      });

      return this.pool;
    } catch (error) {
      logger.error('Failed to initialize database connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async query(text, params) {
    if (!this.isConnected) {
      throw new Error('Database not connected');
    }

    try {
      const start = Date.now();
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;

      logger.info('Query executed', {
        duration,
        rows: result.rowCount,
        query: text.substring(0, 100)
      });

      return result;
    } catch (error) {
      logger.error('Query error:', { error: error.message, query: text });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected) {
      throw new Error('Database not connected');
    }
    return await this.pool.connect();
  }

  async close() {
    if (this.pool) {
      await this.pool.end();
      this.isConnected = false;
      logger.info('Database connection closed');
    }
  }

  getStatus() {
    return {
      connected: this.isConnected,
      totalCount: this.pool?.totalCount || 0,
      idleCount: this.pool?.idleCount || 0,
      waitingCount: this.pool?.waitingCount || 0
    };
  }
}

module.exports = DatabaseConfig;