const { Pool } = require('pg');
const winston = require('winston');

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

class DatabaseConnection {
  constructor() {
    this.pool = null;
    this.config = {
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'aitrading',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'password',
      max: parseInt(process.env.DB_POOL_MAX) || 20,
      idleTimeoutMillis: parseInt(process.env.DB_IDLE_TIMEOUT) || 30000,
      connectionTimeoutMillis: parseInt(process.env.DB_CONNECTION_TIMEOUT) || 10000,
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
    };
  }

  async connect() {
    try {
      this.pool = new Pool(this.config);

      // Test connection
      const client = await this.pool.connect();
      await client.query('SELECT NOW()');
      client.release();

      logger.info('PostgreSQL connection established successfully');

      // Handle pool errors
      this.pool.on('error', (err) => {
        logger.error('Unexpected error on idle client:', err);
      });

      return this.pool;
    } catch (error) {
      logger.error('Failed to connect to PostgreSQL:', error);
      throw error;
    }
  }

  async disconnect() {
    if (this.pool) {
      await this.pool.end();
      logger.info('PostgreSQL connection closed');
    }
  }

  async query(text, params = []) {
    const start = Date.now();
    try {
      const result = await this.pool.query(text, params);
      const duration = Date.now() - start;
      logger.info(`Query executed in ${duration}ms`);
      return result;
    } catch (error) {
      logger.error('Query error:', error);
      throw error;
    }
  }

  async transaction(callback) {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  getPool() {
    return this.pool;
  }

  async healthCheck() {
    try {
      const result = await this.query('SELECT 1 as health');
      return {
        status: 'healthy',
        connection: 'active',
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }
}

module.exports = DatabaseConnection;