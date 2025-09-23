const { Pool } = require('pg');
const { createClient } = require('redis');
const logger = require('../utils/logger');

// PostgreSQL connection
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'aitrading_config',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'password',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Redis connection
const redisClient = createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379',
  retry_strategy: (options) => {
    if (options.error && options.error.code === 'ECONNREFUSED') {
      logger.error('Redis server connection refused');
      return new Error('Redis server connection refused');
    }
    if (options.total_retry_time > 1000 * 60 * 60) {
      logger.error('Redis retry time exhausted');
      return new Error('Retry time exhausted');
    }
    if (options.attempt > 10) {
      logger.error('Redis connection attempts exceeded');
      return undefined;
    }
    return Math.min(options.attempt * 100, 3000);
  }
});

async function connectDatabase() {
  try {
    // Test PostgreSQL connection
    const client = await pool.connect();
    await client.query('SELECT NOW()');
    client.release();
    logger.info('PostgreSQL connected successfully');

    // Create tables if they don't exist
    await createTables();

  } catch (error) {
    logger.error('PostgreSQL connection failed:', error);
    throw error;
  }
}

async function connectRedis() {
  try {
    await redisClient.connect();
    logger.info('Redis connected successfully');

    redisClient.on('error', (err) => {
      logger.error('Redis Client Error:', err);
    });

    redisClient.on('reconnecting', () => {
      logger.info('Redis Client Reconnecting');
    });

  } catch (error) {
    logger.error('Redis connection failed:', error);
    throw error;
  }
}

async function createTables() {
  const client = await pool.connect();
  try {
    // User configurations table
    await client.query(`
      CREATE TABLE IF NOT EXISTS user_configurations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        config_key VARCHAR(255) NOT NULL,
        config_value JSONB NOT NULL,
        config_type VARCHAR(100) NOT NULL DEFAULT 'user',
        is_encrypted BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        version INTEGER DEFAULT 1,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, config_key)
      )
    `);

    // System configurations table
    await client.query(`
      CREATE TABLE IF NOT EXISTS system_configurations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        config_key VARCHAR(255) UNIQUE NOT NULL,
        config_value JSONB NOT NULL,
        config_type VARCHAR(100) NOT NULL DEFAULT 'system',
        is_encrypted BOOLEAN DEFAULT FALSE,
        is_active BOOLEAN DEFAULT TRUE,
        version INTEGER DEFAULT 1,
        metadata JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Configuration templates table
    await client.query(`
      CREATE TABLE IF NOT EXISTS configuration_templates (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        template_name VARCHAR(255) UNIQUE NOT NULL,
        template_config JSONB NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Configuration audit log
    await client.query(`
      CREATE TABLE IF NOT EXISTS configuration_audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID,
        config_id UUID,
        action VARCHAR(50) NOT NULL,
        old_value JSONB,
        new_value JSONB,
        ip_address INET,
        user_agent TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
      )
    `);

    // Create indexes
    await client.query(`CREATE INDEX IF NOT EXISTS idx_user_config_user_id ON user_configurations(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_user_config_key ON user_configurations(config_key)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_configurations(config_key)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON configuration_audit_log(user_id)`);
    await client.query(`CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON configuration_audit_log(created_at)`);

    logger.info('Database tables created successfully');
  } finally {
    client.release();
  }
}

module.exports = {
  pool,
  redisClient,
  connectDatabase,
  connectRedis
};