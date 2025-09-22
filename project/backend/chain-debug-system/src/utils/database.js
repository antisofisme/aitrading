/**
 * Database Manager
 * PostgreSQL connection and query management
 */

import pkg from 'pg';
const { Pool } = pkg;
import logger from './logger.js';

export class DatabaseManager {
  constructor(config = {}) {
    this.config = {
      connectionString: config.connectionString || process.env.DATABASE_URL,
      host: config.host || process.env.DB_HOST || 'localhost',
      port: config.port || process.env.DB_PORT || 5432,
      database: config.database || process.env.DB_NAME || 'aitrading_db',
      user: config.user || process.env.DB_USER || 'postgres',
      password: config.password || process.env.DB_PASSWORD || 'password',
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
      max: 20, // Maximum number of clients in the pool
      idleTimeoutMillis: 30000, // How long a client is allowed to remain idle
      connectionTimeoutMillis: 2000, // How long to wait for a connection
    };

    this.pool = null;
    this.isConnected = false;
  }

  async connect() {
    try {
      logger.info('Connecting to PostgreSQL database...');

      // Use connection string if provided, otherwise use individual parameters
      if (this.config.connectionString) {
        this.pool = new Pool({
          connectionString: this.config.connectionString,
          ssl: this.config.ssl,
          max: this.config.max,
          idleTimeoutMillis: this.config.idleTimeoutMillis,
          connectionTimeoutMillis: this.config.connectionTimeoutMillis
        });
      } else {
        this.pool = new Pool(this.config);
      }

      // Test connection
      const client = await this.pool.connect();
      await client.query('SELECT NOW()');
      client.release();

      this.isConnected = true;

      // Setup error handling
      this.pool.on('error', (err) => {
        logger.error('Unexpected database error:', err);
        this.isConnected = false;
      });

      logger.info('Database connected successfully');

      // Initialize database schema if needed
      await this.initializeSchema();

    } catch (error) {
      logger.error('Failed to connect to database:', error);
      throw error;
    }
  }

  async disconnect() {
    try {
      if (this.pool) {
        await this.pool.end();
        this.isConnected = false;
        logger.info('Database disconnected');
      }
    } catch (error) {
      logger.error('Error disconnecting from database:', error);
    }
  }

  async query(text, params = []) {
    if (!this.isConnected) {
      throw new Error('Database not connected');
    }

    const startTime = Date.now();

    try {
      const result = await this.pool.query(text, params);

      const duration = Date.now() - startTime;

      if (duration > 1000) { // Log slow queries
        logger.warn('Slow query detected', {
          query: text.substring(0, 100),
          duration,
          rowCount: result.rowCount
        });
      }

      return result;

    } catch (error) {
      const duration = Date.now() - startTime;

      logger.error('Database query failed', {
        query: text.substring(0, 100),
        error: error.message,
        duration,
        params: params.length
      });

      throw error;
    }
  }

  async transaction(queries) {
    const client = await this.pool.connect();

    try {
      await client.query('BEGIN');

      const results = [];
      for (const { text, params } of queries) {
        const result = await client.query(text, params);
        results.push(result);
      }

      await client.query('COMMIT');
      return results;

    } catch (error) {
      await client.query('ROLLBACK');
      logger.error('Transaction failed:', error);
      throw error;

    } finally {
      client.release();
    }
  }

  async initializeSchema() {
    try {
      logger.info('Initializing database schema...');

      // Create tables if they don't exist
      await this.createTables();

      // Create indexes
      await this.createIndexes();

      logger.info('Database schema initialized');

    } catch (error) {
      logger.error('Failed to initialize schema:', error);
      throw error;
    }
  }

  async createTables() {
    const tables = [
      // Chain Events Table
      {
        name: 'chain_events',
        sql: `
          CREATE TABLE IF NOT EXISTS chain_events (
            id BIGSERIAL PRIMARY KEY,
            chain_id VARCHAR(255) NOT NULL,
            service_name VARCHAR(255) NOT NULL,
            event_type VARCHAR(100) NOT NULL,
            status VARCHAR(50),
            duration_ms INTEGER,
            error_message TEXT,
            http_status INTEGER,
            user_id VARCHAR(255),
            dependencies JSONB,
            metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
          )
        `
      },

      // Chain Health Metrics Table
      {
        name: 'chain_health_metrics',
        sql: `
          CREATE TABLE IF NOT EXISTS chain_health_metrics (
            id BIGSERIAL PRIMARY KEY,
            chain_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            total_requests INTEGER DEFAULT 0,
            avg_duration INTEGER DEFAULT 0,
            p50_duration INTEGER DEFAULT 0,
            p95_duration INTEGER DEFAULT 0,
            p99_duration INTEGER DEFAULT 0,
            error_rate DECIMAL(5,4) DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            dependency_failure_rate DECIMAL(5,4) DEFAULT 0,
            bottleneck_services JSONB,
            health_score INTEGER DEFAULT 100,
            raw_data JSONB
          )
        `
      },

      // Chain Anomalies Table
      {
        name: 'chain_anomalies',
        sql: `
          CREATE TABLE IF NOT EXISTS chain_anomalies (
            id BIGSERIAL PRIMARY KEY,
            chain_id VARCHAR(255) NOT NULL,
            type VARCHAR(100) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            description TEXT,
            affected_metric VARCHAR(100),
            current_value DECIMAL(15,6),
            baseline_value DECIMAL(15,6),
            confidence DECIMAL(4,3),
            detection_method VARCHAR(50),
            affected_services JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            raw_data JSONB
          )
        `
      },

      // Impact Assessments Table
      {
        name: 'impact_assessments',
        sql: `
          CREATE TABLE IF NOT EXISTS impact_assessments (
            id BIGSERIAL PRIMARY KEY,
            chain_id VARCHAR(255) NOT NULL,
            affected_services JSONB,
            user_impact JSONB,
            business_impact JSONB,
            cascade_risk JSONB,
            priority_level VARCHAR(20) NOT NULL,
            estimated_recovery_time INTEGER,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            raw_data JSONB
          )
        `
      },

      // Root Cause Analyses Table
      {
        name: 'root_cause_analyses',
        sql: `
          CREATE TABLE IF NOT EXISTS root_cause_analyses (
            id BIGSERIAL PRIMARY KEY,
            chain_id VARCHAR(255) NOT NULL,
            root_cause_type VARCHAR(100),
            root_cause_description TEXT,
            confidence_score DECIMAL(4,3),
            contributing_factors JSONB,
            evidence JSONB,
            recommended_actions JSONB,
            analysis_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            raw_data JSONB
          )
        `
      },

      // Recovery Results Table
      {
        name: 'recovery_results',
        sql: `
          CREATE TABLE IF NOT EXISTS recovery_results (
            id BIGSERIAL PRIMARY KEY,
            chain_id VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL,
            start_time TIMESTAMP WITH TIME ZONE,
            end_time TIMESTAMP WITH TIME ZONE,
            total_duration INTEGER,
            actions_executed JSONB,
            verification_result JSONB,
            raw_data JSONB
          )
        `
      },

      // Chain Baselines Table
      {
        name: 'chain_baselines',
        sql: `
          CREATE TABLE IF NOT EXISTS chain_baselines (
            chain_id VARCHAR(255) PRIMARY KEY,
            baseline_data JSONB NOT NULL,
            calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            data_points INTEGER,
            version VARCHAR(10)
          )
        `
      },

      // ML Models Table
      {
        name: 'ml_models',
        sql: `
          CREATE TABLE IF NOT EXISTS ml_models (
            id BIGSERIAL PRIMARY KEY,
            model_type VARCHAR(50) NOT NULL,
            chain_type VARCHAR(50) NOT NULL,
            model_data JSONB NOT NULL,
            accuracy DECIMAL(4,3),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(model_type, chain_type)
          )
        `
      },

      // Service Recovery Configs Table
      {
        name: 'service_recovery_configs',
        sql: `
          CREATE TABLE IF NOT EXISTS service_recovery_configs (
            service_name VARCHAR(255) PRIMARY KEY,
            preferred_recovery_method VARCHAR(50),
            restart_duration INTEGER,
            scale_duration INTEGER,
            shutdown_timeout INTEGER,
            scale_multiplier DECIMAL(3,1),
            max_instances INTEGER,
            config_data JSONB,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
          )
        `
      },

      // System Metrics Table
      {
        name: 'system_metrics',
        sql: `
          CREATE TABLE IF NOT EXISTS system_metrics (
            id BIGSERIAL PRIMARY KEY,
            metric_name VARCHAR(100) NOT NULL,
            value DECIMAL(15,6) NOT NULL,
            service_name VARCHAR(255),
            tags JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
          )
        `
      },

      // Application Logs Table
      {
        name: 'application_logs',
        sql: `
          CREATE TABLE IF NOT EXISTS application_logs (
            id BIGSERIAL PRIMARY KEY,
            service_name VARCHAR(255),
            level VARCHAR(20),
            message TEXT,
            stack_trace TEXT,
            metadata JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
          )
        `
      }
    ];

    for (const table of tables) {
      try {
        await this.query(table.sql);
        logger.debug(`Table ${table.name} created/verified`);
      } catch (error) {
        logger.error(`Failed to create table ${table.name}:`, error);
        throw error;
      }
    }
  }

  async createIndexes() {
    const indexes = [
      // Chain Events Indexes
      'CREATE INDEX IF NOT EXISTS idx_chain_events_chain_id ON chain_events(chain_id)',
      'CREATE INDEX IF NOT EXISTS idx_chain_events_created_at ON chain_events(created_at)',
      'CREATE INDEX IF NOT EXISTS idx_chain_events_service_name ON chain_events(service_name)',
      'CREATE INDEX IF NOT EXISTS idx_chain_events_event_type ON chain_events(event_type)',

      // Chain Health Metrics Indexes
      'CREATE INDEX IF NOT EXISTS idx_chain_health_metrics_chain_id ON chain_health_metrics(chain_id)',
      'CREATE INDEX IF NOT EXISTS idx_chain_health_metrics_timestamp ON chain_health_metrics(timestamp)',
      'CREATE INDEX IF NOT EXISTS idx_chain_health_metrics_health_score ON chain_health_metrics(health_score)',

      // Chain Anomalies Indexes
      'CREATE INDEX IF NOT EXISTS idx_chain_anomalies_chain_id ON chain_anomalies(chain_id)',
      'CREATE INDEX IF NOT EXISTS idx_chain_anomalies_timestamp ON chain_anomalies(timestamp)',
      'CREATE INDEX IF NOT EXISTS idx_chain_anomalies_severity ON chain_anomalies(severity)',
      'CREATE INDEX IF NOT EXISTS idx_chain_anomalies_type ON chain_anomalies(type)',

      // Impact Assessments Indexes
      'CREATE INDEX IF NOT EXISTS idx_impact_assessments_chain_id ON impact_assessments(chain_id)',
      'CREATE INDEX IF NOT EXISTS idx_impact_assessments_timestamp ON impact_assessments(timestamp)',
      'CREATE INDEX IF NOT EXISTS idx_impact_assessments_priority ON impact_assessments(priority_level)',

      // System Metrics Indexes
      'CREATE INDEX IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics(metric_name)',
      'CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)',
      'CREATE INDEX IF NOT EXISTS idx_system_metrics_service_name ON system_metrics(service_name)',

      // Composite Indexes
      'CREATE INDEX IF NOT EXISTS idx_chain_events_chain_created ON chain_events(chain_id, created_at)',
      'CREATE INDEX IF NOT EXISTS idx_chain_anomalies_chain_timestamp ON chain_anomalies(chain_id, timestamp)',
      'CREATE INDEX IF NOT EXISTS idx_system_metrics_name_service_time ON system_metrics(metric_name, service_name, timestamp)'
    ];

    for (const indexSql of indexes) {
      try {
        await this.query(indexSql);
      } catch (error) {
        logger.error(`Failed to create index: ${indexSql}`, error);
        // Continue with other indexes
      }
    }

    logger.debug('Database indexes created/verified');
  }

  // Utility methods
  async healthCheck() {
    try {
      const result = await this.query('SELECT NOW() as current_time, version() as postgres_version');
      return {
        connected: true,
        currentTime: result.rows[0].current_time,
        version: result.rows[0].postgres_version
      };
    } catch (error) {
      return {
        connected: false,
        error: error.message
      };
    }
  }

  async getConnectionInfo() {
    return {
      totalCount: this.pool?.totalCount || 0,
      idleCount: this.pool?.idleCount || 0,
      waitingCount: this.pool?.waitingCount || 0,
      isConnected: this.isConnected
    };
  }

  // Helper method for building WHERE clauses
  buildWhereClause(conditions) {
    const whereConditions = [];
    const params = [];
    let paramIndex = 1;

    for (const [field, value] of Object.entries(conditions)) {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          whereConditions.push(`${field} = ANY($${paramIndex})`);
          params.push(value);
        } else {
          whereConditions.push(`${field} = $${paramIndex}`);
          params.push(value);
        }
        paramIndex++;
      }
    }

    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

    return { whereClause, params };
  }

  // Helper method for pagination
  buildPaginationClause(limit, offset) {
    const pagination = [];
    const params = [];
    let paramIndex = 1;

    if (limit) {
      pagination.push(`LIMIT $${paramIndex++}`);
      params.push(limit);
    }

    if (offset) {
      pagination.push(`OFFSET $${paramIndex++}`);
      params.push(offset);
    }

    return {
      paginationClause: pagination.join(' '),
      params,
      nextParamIndex: paramIndex
    };
  }
}