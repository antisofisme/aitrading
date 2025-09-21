/**
 * ClickHouse Database Manager
 * High-performance time-series and analytics database
 */

const { createClient } = require('@clickhouse/client');
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
    new winston.transports.File({ filename: 'logs/clickhouse.log' })
  ]
});

class ClickHouseManager extends IDatabaseManager {
  constructor(config) {
    super();
    this.config = config;
    this.client = null;
    this.isConnected = false;
    this.connectionAttempts = 0;
    this.maxConnectionAttempts = 5;
  }

  async initialize() {
    try {
      this.client = createClient({
        host: `http://${this.config.host}:${this.config.port}`,
        database: this.config.database,
        username: this.config.user,
        password: this.config.password,
        clickhouse_settings: {
          async_insert: 1,
          async_insert_max_data_size: 1000000,
          async_insert_busy_timeout_ms: 2000,
        },
        max_open_connections: this.config.max_connections || 10,
      });

      // Test connection
      await this.testConnection();

      this.isConnected = true;
      logger.info('ClickHouse connection established successfully', {
        host: this.config.host,
        port: this.config.port,
        database: this.config.database
      });

      return this.client;
    } catch (error) {
      logger.error('Failed to initialize ClickHouse connection:', error);
      this.isConnected = false;
      throw error;
    }
  }

  async testConnection() {
    let lastError;
    for (let attempt = 1; attempt <= this.maxConnectionAttempts; attempt++) {
      try {
        const result = await this.client.query({
          query: 'SELECT version() as version, now() as current_time',
        });

        const data = await result.json();
        logger.info('ClickHouse connection test successful', {
          attempt,
          version: data.data[0]?.version,
          serverTime: data.data[0]?.current_time
        });
        return;
      } catch (error) {
        lastError = error;
        logger.warn(`ClickHouse connection attempt ${attempt} failed:`, error.message);

        if (attempt < this.maxConnectionAttempts) {
          const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }
    throw lastError;
  }

  async query(queryText, params = []) {
    if (!this.isConnected) {
      throw new Error('ClickHouse not connected');
    }

    try {
      const start = Date.now();

      // Replace parameter placeholders with actual values
      let processedQuery = queryText;
      if (params.length > 0) {
        params.forEach((param, index) => {
          const placeholder = `$${index + 1}`;
          processedQuery = processedQuery.replace(
            new RegExp('\\' + placeholder, 'g'),
            typeof param === 'string' ? `'${param}'` : param
          );
        });
      }

      const result = await this.client.query({
        query: processedQuery,
        format: 'JSONEachRow',
      });

      const data = await result.json();
      const duration = Date.now() - start;

      logger.info('ClickHouse query executed', {
        duration,
        rows: data.data?.length || 0,
        query: queryText.substring(0, 100) + (queryText.length > 100 ? '...' : '')
      });

      return {
        rows: data.data || [],
        rowCount: data.data?.length || 0,
        duration,
        meta: data.meta || [],
        statistics: data.statistics || {}
      };
    } catch (error) {
      logger.error('ClickHouse query error:', {
        error: error.message,
        query: queryText.substring(0, 100),
        code: error.code
      });
      throw error;
    }
  }

  async getClient() {
    if (!this.isConnected) {
      throw new Error('ClickHouse not connected');
    }
    return this.client;
  }

  async close() {
    if (this.client) {
      await this.client.close();
      this.isConnected = false;
      logger.info('ClickHouse connection closed');
    }
  }

  getStatus() {
    return {
      type: 'clickhouse',
      connected: this.isConnected,
      config: {
        host: this.config.host,
        port: this.config.port,
        database: this.config.database,
        maxConnections: this.config.max_connections
      }
    };
  }

  async healthCheck() {
    try {
      const startTime = Date.now();
      const result = await this.client.query({
        query: 'SELECT 1 as health_check, now() as timestamp',
      });

      const data = await result.json();
      const responseTime = Date.now() - startTime;

      return {
        status: 'healthy',
        responseTime,
        timestamp: data.data[0]?.timestamp,
        details: {
          status: this.getStatus(),
          lastCheck: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('ClickHouse health check failed:', error);
      return {
        status: 'unhealthy',
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  getType() {
    return 'clickhouse';
  }

  getConfig() {
    return { ...this.config, password: '***' };
  }

  // ClickHouse doesn't support traditional transactions
  async beginTransaction() {
    throw new Error('ClickHouse does not support traditional transactions');
  }

  async commitTransaction(transaction) {
    throw new Error('ClickHouse does not support traditional transactions');
  }

  async rollbackTransaction(transaction) {
    throw new Error('ClickHouse does not support traditional transactions');
  }

  // ClickHouse-specific methods
  async insertBatch(tableName, data, options = {}) {
    const values = data.map(row =>
      Object.values(row).map(value =>
        typeof value === 'string' ? `'${value}'` : value
      ).join(', ')
    ).map(row => `(${row})`).join(', ');

    const columns = Object.keys(data[0]).join(', ');
    const query = `INSERT INTO ${tableName} (${columns}) VALUES ${values}`;

    return await this.query(query);
  }

  async createTable(tableName, schema, engine = 'MergeTree()') {
    const columns = Object.entries(schema)
      .map(([name, type]) => `${name} ${type}`)
      .join(', ');

    const query = `
      CREATE TABLE IF NOT EXISTS ${tableName} (
        ${columns}
      ) ENGINE = ${engine}
      ORDER BY tuple()
    `;

    return await this.query(query);
  }

  async optimizeTable(tableName) {
    const query = `OPTIMIZE TABLE ${tableName}`;
    return await this.query(query);
  }

  async getTableInfo(tableName) {
    const query = `
      SELECT
        name,
        type,
        default_expression,
        comment
      FROM system.columns
      WHERE table = '${tableName}' AND database = '${this.config.database}'
    `;

    return await this.query(query);
  }

  async getTableSize(tableName) {
    const query = `
      SELECT
        formatReadableSize(sum(bytes)) as size,
        sum(rows) as rows,
        count() as parts
      FROM system.parts
      WHERE table = '${tableName}' AND database = '${this.config.database}' AND active = 1
    `;

    return await this.query(query);
  }

  // Time-series specific operations
  async insertTimeSeriesData(tableName, timestamp, metrics) {
    const columns = ['timestamp', ...Object.keys(metrics)].join(', ');
    const values = [
      `'${timestamp}'`,
      ...Object.values(metrics).map(v => typeof v === 'string' ? `'${v}'` : v)
    ].join(', ');

    const query = `INSERT INTO ${tableName} (${columns}) VALUES (${values})`;
    return await this.query(query);
  }

  async queryTimeRange(tableName, startTime, endTime, aggregation = 'avg', interval = '1m') {
    const query = `
      SELECT
        toStartOfInterval(timestamp, INTERVAL ${interval}) as time_bucket,
        ${aggregation}(value) as value
      FROM ${tableName}
      WHERE timestamp >= '${startTime}' AND timestamp <= '${endTime}'
      GROUP BY time_bucket
      ORDER BY time_bucket
    `;

    return await this.query(query);
  }
}

module.exports = ClickHouseManager;