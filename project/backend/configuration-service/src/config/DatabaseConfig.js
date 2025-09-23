/**
 * Configuration Service Database Configuration
 * Uses Plan2 Multi-Database Architecture with UnifiedDatabaseInterface
 */

const path = require('path');

// Import UnifiedDatabaseInterface from database service
const UnifiedDatabaseInterface = require(path.join(
  __dirname,
  '../../../database-service/src/database/UnifiedDatabaseInterface'
));

const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/config-service-db.log' })
  ]
});

class ConfigServiceDatabaseConfig {
  constructor() {
    this.unifiedDb = new UnifiedDatabaseInterface();
    this.isConnected = false;
    this.initialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing Configuration Service database connections...');

      // Initialize the unified database interface with all databases
      await this.unifiedDb.initialize();

      this.isConnected = true;
      this.initialized = true;

      logger.info('Configuration Service database connections established successfully');

      return {
        unified: this.unifiedDb,
        postgresql: this.unifiedDb.getDatabase('postgresql'),
        dragonflydb: this.unifiedDb.getDatabase('dragonflydb'),
        clickhouse: this.unifiedDb.getDatabase('clickhouse'),
        weaviate: this.unifiedDb.getDatabase('weaviate'),
        arangodb: this.unifiedDb.getDatabase('arangodb')
      };
    } catch (error) {
      logger.error('Failed to initialize Configuration Service database connections:', error);
      this.isConnected = false;
      throw error;
    }
  }

  // Unified query interface
  async query(queryRequest) {
    if (!this.isConnected) {
      throw new Error('Database not connected');
    }
    return await this.unifiedDb.execute(queryRequest);
  }

  // Configuration-specific data operations
  async storeConfig(userId, configKey, configValue, metadata = {}) {
    const queryRequest = {
      type: 'store',
      table: 'user_configurations',
      data: {
        user_id: userId,
        config_key: configKey,
        config_value: configValue,
        metadata: metadata,
        created_at: new Date(),
        updated_at: new Date()
      },
      targetDatabase: 'postgresql'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getConfig(userId, configKey) {
    const queryRequest = {
      type: 'retrieve',
      table: 'user_configurations',
      criteria: {
        user_id: userId,
        config_key: configKey
      },
      targetDatabase: 'postgresql'
    };

    const result = await this.unifiedDb.execute(queryRequest);
    return result.data.rows[0] || null;
  }

  async updateConfig(userId, configKey, configValue, metadata = {}) {
    const queryRequest = {
      type: 'update',
      table: 'user_configurations',
      data: {
        config_value: configValue,
        metadata: metadata,
        updated_at: new Date()
      },
      criteria: {
        user_id: userId,
        config_key: configKey
      },
      targetDatabase: 'postgresql'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async deleteConfig(userId, configKey) {
    const queryRequest = {
      type: 'delete',
      table: 'user_configurations',
      criteria: {
        user_id: userId,
        config_key: configKey
      },
      targetDatabase: 'postgresql'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  // Cache operations using DragonflyDB
  async cacheConfig(userId, configKey, configData, ttl = 3600) {
    const cacheKey = `config:${userId}:${configKey}`;

    const queryRequest = {
      type: 'cache',
      key: cacheKey,
      value: configData,
      ttl: ttl,
      targetDatabase: 'dragonflydb'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getCachedConfig(userId, configKey) {
    const cacheKey = `config:${userId}:${configKey}`;

    const queryRequest = {
      type: 'retrieve',
      key: cacheKey,
      targetDatabase: 'dragonflydb'
    };

    try {
      const result = await this.unifiedDb.execute(queryRequest);
      return result.data.result;
    } catch (error) {
      logger.debug('Cache miss for config:', { userId, configKey });
      return null;
    }
  }

  // Analytics operations using ClickHouse
  async logConfigChange(userId, configKey, oldValue, newValue, timestamp = new Date()) {
    const queryRequest = {
      type: 'timeSeriesQuery',
      query: {
        table: 'config_change_log',
        data: {
          timestamp: timestamp,
          user_id: userId,
          config_key: configKey,
          old_value: oldValue,
          new_value: newValue,
          change_type: oldValue ? 'update' : 'create'
        }
      },
      targetDatabase: 'clickhouse'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getConfigAnalytics(userId, timeRange = '24h') {
    const queryRequest = {
      type: 'analyze',
      dataset: 'config_change_log',
      analysis: {
        aggregation: 'count',
        groupBy: 'config_key',
        timeRange: timeRange,
        filters: { user_id: userId }
      },
      targetDatabase: 'clickhouse'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  // Flow Registry operations (keeping existing functionality)
  async storeFlowDefinition(flowId, flowDefinition, metadata = {}) {
    const queryRequest = {
      type: 'store',
      table: 'flow_definitions',
      data: {
        flow_id: flowId,
        definition: flowDefinition,
        metadata: metadata,
        created_at: new Date(),
        updated_at: new Date()
      },
      targetDatabase: 'postgresql'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  // Get specific database instances for legacy compatibility
  getPostgreSQLClient() {
    return this.unifiedDb.getDatabase('postgresql');
  }

  getDragonflyDBClient() {
    return this.unifiedDb.getDatabase('dragonflydb');
  }

  getClickHouseClient() {
    return this.unifiedDb.getDatabase('clickhouse');
  }

  getWeaviateClient() {
    return this.unifiedDb.getDatabase('weaviate');
  }

  getArangoDBClient() {
    return this.unifiedDb.getDatabase('arangodb');
  }

  // Health and status methods
  async getHealthStatus() {
    return await this.unifiedDb.getHealthStatus();
  }

  getStatus() {
    return {
      ...this.unifiedDb.getStatus(),
      configService: {
        initialized: this.initialized,
        connected: this.isConnected
      }
    };
  }

  async close() {
    if (this.unifiedDb) {
      await this.unifiedDb.close();
      this.isConnected = false;
      this.initialized = false;
      logger.info('Configuration Service database connections closed');
    }
  }
}

module.exports = ConfigServiceDatabaseConfig;