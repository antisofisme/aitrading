/**
 * Unified Database Interface
 * Single interface for all database operations with intelligent routing
 */

const DatabaseFactory = require('./factories/DatabaseFactory');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'logs/unified-database.log' })
  ]
});

class UnifiedDatabaseInterface {
  constructor() {
    this.factory = new DatabaseFactory();
    this.queryRouter = new QueryRouter();
    this.initialized = false;
  }

  async initialize() {
    try {
      await this.factory.initializeAll();
      this.initialized = true;
      logger.info('Unified Database Interface initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Unified Database Interface:', error);
      throw error;
    }
  }

  /**
   * Execute query with automatic routing based on query type and target
   * @param {Object} queryRequest - Query request object
   * @returns {Promise<any>}
   */
  async execute(queryRequest) {
    if (!this.initialized) {
      throw new Error('Unified Database Interface not initialized');
    }

    try {
      const route = this.queryRouter.route(queryRequest);
      const database = this.factory.getDatabase(route.targetDatabase);

      const start = Date.now();
      const result = await database.query(route.query, route.params);
      const duration = Date.now() - start;

      logger.info('Query executed via unified interface', {
        targetDatabase: route.targetDatabase,
        queryType: route.queryType,
        duration,
        success: true
      });

      return {
        data: result,
        metadata: {
          targetDatabase: route.targetDatabase,
          queryType: route.queryType,
          duration,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('Query execution failed:', {
        error: error.message,
        queryRequest
      });
      throw error;
    }
  }

  /**
   * Execute cross-database operation
   * @param {Object} crossDbOperation - Cross-database operation definition
   * @returns {Promise<any>}
   */
  async executeCrossDatabase(crossDbOperation) {
    const { operations, coordinationType = 'sequential' } = crossDbOperation;

    try {
      let results = [];

      if (coordinationType === 'parallel') {
        const promises = operations.map(async (op) => {
          const database = this.factory.getDatabase(op.database);
          return await database.query(op.query, op.params);
        });

        results = await Promise.all(promises);
      } else {
        // Sequential execution
        for (const op of operations) {
          const database = this.factory.getDatabase(op.database);
          const result = await database.query(op.query, op.params);
          results.push(result);
        }
      }

      logger.info('Cross-database operation completed', {
        operationCount: operations.length,
        coordinationType,
        success: true
      });

      return {
        results,
        metadata: {
          operationCount: operations.length,
          coordinationType,
          timestamp: new Date().toISOString()
        }
      };
    } catch (error) {
      logger.error('Cross-database operation failed:', error);
      throw error;
    }
  }

  /**
   * Get specific database instance
   * @param {string} type - Database type
   * @returns {IDatabaseManager}
   */
  getDatabase(type) {
    return this.factory.getDatabase(type);
  }

  /**
   * Get all database instances
   * @returns {Map<string, IDatabaseManager>}
   */
  getAllDatabases() {
    return this.factory.getAllDatabases();
  }

  /**
   * Get unified health status
   * @returns {Promise<Object>}
   */
  async getHealthStatus() {
    return await this.factory.healthCheckAll();
  }

  /**
   * Get unified status
   * @returns {Object}
   */
  getStatus() {
    return {
      ...this.factory.getStatus(),
      unifiedInterface: {
        initialized: this.initialized,
        queryRouterActive: !!this.queryRouter
      }
    };
  }

  /**
   * Close all connections
   * @returns {Promise<void>}
   */
  async close() {
    await this.factory.closeAll();
    this.initialized = false;
    logger.info('Unified Database Interface closed');
  }

  // Convenience methods for common operations

  // Data operations
  async store(data, options = {}) {
    const queryRequest = {
      type: 'store',
      data,
      options
    };
    return await this.execute(queryRequest);
  }

  async retrieve(criteria, options = {}) {
    const queryRequest = {
      type: 'retrieve',
      criteria,
      options
    };
    return await this.execute(queryRequest);
  }

  async update(criteria, data, options = {}) {
    const queryRequest = {
      type: 'update',
      criteria,
      data,
      options
    };
    return await this.execute(queryRequest);
  }

  async delete(criteria, options = {}) {
    const queryRequest = {
      type: 'delete',
      criteria,
      options
    };
    return await this.execute(queryRequest);
  }

  // Specialized operations
  async search(query, options = {}) {
    const queryRequest = {
      type: 'search',
      query,
      options
    };
    return await this.execute(queryRequest);
  }

  async analyze(dataset, analysis, options = {}) {
    const queryRequest = {
      type: 'analyze',
      dataset,
      analysis,
      options
    };
    return await this.execute(queryRequest);
  }

  async cache(key, value, ttl = 3600) {
    const queryRequest = {
      type: 'cache',
      key,
      value,
      ttl,
      targetDatabase: 'dragonflydb'
    };
    return await this.execute(queryRequest);
  }

  async vectorSearch(vector, options = {}) {
    const queryRequest = {
      type: 'vectorSearch',
      vector,
      options,
      targetDatabase: 'weaviate'
    };
    return await this.execute(queryRequest);
  }

  async graphQuery(graphQuery, options = {}) {
    const queryRequest = {
      type: 'graphQuery',
      query: graphQuery,
      options,
      targetDatabase: 'arangodb'
    };
    return await this.execute(queryRequest);
  }

  async timeSeriesQuery(timeQuery, options = {}) {
    const queryRequest = {
      type: 'timeSeriesQuery',
      query: timeQuery,
      options,
      targetDatabase: 'clickhouse'
    };
    return await this.execute(queryRequest);
  }
}

/**
 * Query Router - Routes queries to appropriate databases
 */
class QueryRouter {
  constructor() {
    this.routingRules = this.initializeRoutingRules();
  }

  initializeRoutingRules() {
    return {
      // Operational data -> PostgreSQL
      operational: {
        patterns: ['users', 'accounts', 'transactions', 'orders', 'portfolios'],
        database: 'postgresql'
      },

      // Time-series and analytics -> ClickHouse
      analytics: {
        patterns: ['metrics', 'events', 'logs', 'time_series', 'analytics'],
        database: 'clickhouse'
      },

      // Vector and AI data -> Weaviate
      vector: {
        patterns: ['embeddings', 'vectors', 'similarity', 'recommendations'],
        database: 'weaviate'
      },

      // Graph data -> ArangoDB
      graph: {
        patterns: ['relationships', 'networks', 'graphs', 'connections'],
        database: 'arangodb'
      },

      // Cache and memory -> DragonflyDB
      cache: {
        patterns: ['cache', 'session', 'temporary', 'realtime'],
        database: 'dragonflydb'
      }
    };
  }

  route(queryRequest) {
    const { type, query, targetDatabase, options = {} } = queryRequest;

    // If target database is explicitly specified, use it
    if (targetDatabase) {
      return {
        targetDatabase,
        queryType: type,
        query: query,
        params: options.params || []
      };
    }

    // Auto-route based on query type and patterns
    let targetDb = this.determineTargetDatabase(type, query, options);

    // Transform query based on target database
    const transformedQuery = this.transformQuery(query, targetDb, type);

    return {
      targetDatabase: targetDb,
      queryType: type,
      query: transformedQuery,
      params: options.params || []
    };
  }

  determineTargetDatabase(type, query, options) {
    // Route based on operation type
    switch (type) {
      case 'cache':
        return 'dragonflydb';
      case 'vectorSearch':
      case 'similarity':
        return 'weaviate';
      case 'graphQuery':
      case 'traverse':
        return 'arangodb';
      case 'timeSeriesQuery':
      case 'analyze':
        return 'clickhouse';
      case 'store':
      case 'retrieve':
      case 'update':
      case 'delete':
      default:
        return this.routeByContent(query, options);
    }
  }

  routeByContent(query, options) {
    const queryString = typeof query === 'string' ? query.toLowerCase() : JSON.stringify(query).toLowerCase();

    // Check routing rules
    for (const [category, rule] of Object.entries(this.routingRules)) {
      for (const pattern of rule.patterns) {
        if (queryString.includes(pattern)) {
          return rule.database;
        }
      }
    }

    // Default to PostgreSQL for operational data
    return 'postgresql';
  }

  transformQuery(query, targetDatabase, type) {
    // Transform query format based on target database
    switch (targetDatabase) {
      case 'postgresql':
        return this.transformToSQL(query, type);
      case 'clickhouse':
        return this.transformToClickHouseSQL(query, type);
      case 'weaviate':
        return this.transformToWeaviateQuery(query, type);
      case 'arangodb':
        return this.transformToAQL(query, type);
      case 'dragonflydb':
        return this.transformToRedisCommand(query, type);
      default:
        return query;
    }
  }

  transformToSQL(query, type) {
    if (typeof query === 'object') {
      // Transform object query to SQL
      switch (type) {
        case 'store':
          return this.buildInsertSQL(query);
        case 'retrieve':
          return this.buildSelectSQL(query);
        case 'update':
          return this.buildUpdateSQL(query);
        case 'delete':
          return this.buildDeleteSQL(query);
        default:
          return query;
      }
    }
    return query;
  }

  transformToClickHouseSQL(query, type) {
    // Similar to PostgreSQL but with ClickHouse-specific optimizations
    return this.transformToSQL(query, type);
  }

  transformToWeaviateQuery(query, type) {
    if (typeof query === 'object') {
      return {
        type: type,
        ...query
      };
    }
    return query;
  }

  transformToAQL(query, type) {
    if (typeof query === 'object') {
      // Transform to ArangoDB AQL
      return query;
    }
    return query;
  }

  transformToRedisCommand(query, type) {
    // Redis commands are typically handled differently
    return query;
  }

  // SQL builders (simplified versions)
  buildInsertSQL(query) {
    const { table, data } = query;
    const columns = Object.keys(data).join(', ');
    const values = Object.keys(data).map((_, i) => `$${i + 1}`).join(', ');
    return `INSERT INTO ${table} (${columns}) VALUES (${values})`;
  }

  buildSelectSQL(query) {
    const { table, columns = '*', where = {}, limit, offset } = query;
    let sql = `SELECT ${Array.isArray(columns) ? columns.join(', ') : columns} FROM ${table}`;

    if (Object.keys(where).length > 0) {
      const conditions = Object.keys(where).map((key, i) => `${key} = $${i + 1}`);
      sql += ` WHERE ${conditions.join(' AND ')}`;
    }

    if (limit) sql += ` LIMIT ${limit}`;
    if (offset) sql += ` OFFSET ${offset}`;

    return sql;
  }

  buildUpdateSQL(query) {
    const { table, data, where = {} } = query;
    const setClause = Object.keys(data).map((key, i) => `${key} = $${i + 1}`).join(', ');
    let sql = `UPDATE ${table} SET ${setClause}`;

    if (Object.keys(where).length > 0) {
      const whereStart = Object.keys(data).length;
      const conditions = Object.keys(where).map((key, i) => `${key} = $${whereStart + i + 1}`);
      sql += ` WHERE ${conditions.join(' AND ')}`;
    }

    return sql;
  }

  buildDeleteSQL(query) {
    const { table, where = {} } = query;
    let sql = `DELETE FROM ${table}`;

    if (Object.keys(where).length > 0) {
      const conditions = Object.keys(where).map((key, i) => `${key} = $${i + 1}`);
      sql += ` WHERE ${conditions.join(' AND ')}`;
    }

    return sql;
  }
}

module.exports = UnifiedDatabaseInterface;