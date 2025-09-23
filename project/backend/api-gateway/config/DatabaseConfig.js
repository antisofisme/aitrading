/**
 * API Gateway Database Configuration
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
    new winston.transports.File({ filename: 'logs/api-gateway-db.log' })
  ]
});

class ApiGatewayDatabaseConfig {
  constructor() {
    this.unifiedDb = new UnifiedDatabaseInterface();
    this.isConnected = false;
    this.initialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing API Gateway database connections...');

      // Initialize the unified database interface with all databases
      await this.unifiedDb.initialize();

      this.isConnected = true;
      this.initialized = true;

      logger.info('API Gateway database connections established successfully');

      return {
        unified: this.unifiedDb,
        postgresql: this.unifiedDb.getDatabase('postgresql'),
        dragonflydb: this.unifiedDb.getDatabase('dragonflydb'),
        clickhouse: this.unifiedDb.getDatabase('clickhouse'),
        weaviate: this.unifiedDb.getDatabase('weaviate'),
        arangodb: this.unifiedDb.getDatabase('arangodb')
      };
    } catch (error) {
      logger.error('Failed to initialize API Gateway database connections:', error);
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

  // API Gateway specific operations

  // Session management using DragonflyDB
  async storeSession(sessionId, sessionData, ttl = 3600) {
    const sessionKey = `session:${sessionId}`;

    const queryRequest = {
      type: 'cache',
      key: sessionKey,
      value: sessionData,
      ttl: ttl,
      targetDatabase: 'dragonflydb'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getSession(sessionId) {
    const sessionKey = `session:${sessionId}`;

    const queryRequest = {
      type: 'retrieve',
      key: sessionKey,
      targetDatabase: 'dragonflydb'
    };

    try {
      const result = await this.unifiedDb.execute(queryRequest);
      return result.data.result;
    } catch (error) {
      logger.debug('Session not found:', { sessionId });
      return null;
    }
  }

  async deleteSession(sessionId) {
    const sessionKey = `session:${sessionId}`;

    const queryRequest = {
      type: 'delete',
      key: sessionKey,
      targetDatabase: 'dragonflydb'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  // Rate limiting using DragonflyDB
  async checkRateLimit(clientId, windowMs, maxRequests) {
    const rateLimitKey = `rate_limit:${clientId}`;
    const currentTime = Date.now();
    const windowStart = currentTime - windowMs;

    // Remove old entries and count current requests
    const multi = await this.unifiedDb.getDatabase('dragonflydb').beginTransaction();

    try {
      // Remove entries older than the window
      await multi.zremrangebyscore(rateLimitKey, '-inf', windowStart);

      // Count current requests in window
      const requestCount = await multi.zcard(rateLimitKey);

      if (requestCount >= maxRequests) {
        await this.unifiedDb.getDatabase('dragonflydb').commitTransaction(multi);
        return { allowed: false, remaining: 0, resetTime: windowStart + windowMs };
      }

      // Add current request
      await multi.zadd(rateLimitKey, currentTime, `${currentTime}-${Math.random()}`);
      await multi.expire(rateLimitKey, Math.ceil(windowMs / 1000));

      await this.unifiedDb.getDatabase('dragonflydb').commitTransaction(multi);

      return {
        allowed: true,
        remaining: maxRequests - requestCount - 1,
        resetTime: windowStart + windowMs
      };
    } catch (error) {
      await this.unifiedDb.getDatabase('dragonflydb').rollbackTransaction(multi);
      throw error;
    }
  }

  // API Gateway analytics using ClickHouse
  async logApiRequest(requestData) {
    const queryRequest = {
      type: 'timeSeriesQuery',
      query: {
        table: 'api_requests',
        data: {
          timestamp: new Date(),
          request_id: requestData.requestId,
          method: requestData.method,
          endpoint: requestData.endpoint,
          status_code: requestData.statusCode,
          duration_ms: requestData.duration,
          client_ip: requestData.clientIp,
          user_agent: requestData.userAgent,
          service_route: requestData.serviceRoute,
          error_message: requestData.errorMessage || null
        }
      },
      targetDatabase: 'clickhouse'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getApiAnalytics(timeRange = '24h', filters = {}) {
    const queryRequest = {
      type: 'analyze',
      dataset: 'api_requests',
      analysis: {
        aggregation: ['count', 'avg(duration_ms)', 'sum(status_code >= 400)'],
        groupBy: ['endpoint', 'method'],
        timeRange: timeRange,
        filters: filters
      },
      targetDatabase: 'clickhouse'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  // Service registry using PostgreSQL
  async registerService(serviceInfo) {
    const queryRequest = {
      type: 'store',
      table: 'service_registry',
      data: {
        service_id: serviceInfo.serviceId,
        service_name: serviceInfo.serviceName,
        service_url: serviceInfo.serviceUrl,
        health_check_url: serviceInfo.healthCheckUrl,
        status: 'active',
        metadata: serviceInfo.metadata || {},
        registered_at: new Date(),
        last_heartbeat: new Date()
      },
      targetDatabase: 'postgresql'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async updateServiceHeartbeat(serviceId) {
    const queryRequest = {
      type: 'update',
      table: 'service_registry',
      data: {
        last_heartbeat: new Date(),
        status: 'active'
      },
      criteria: {
        service_id: serviceId
      },
      targetDatabase: 'postgresql'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getActiveServices() {
    const queryRequest = {
      type: 'retrieve',
      table: 'service_registry',
      criteria: {
        status: 'active'
      },
      targetDatabase: 'postgresql'
    };

    const result = await this.unifiedDb.execute(queryRequest);
    return result.data.rows;
  }

  // Cache commonly accessed data
  async cacheServiceRoutes(routes, ttl = 3600) {
    const queryRequest = {
      type: 'cache',
      key: 'service_routes',
      value: routes,
      ttl: ttl,
      targetDatabase: 'dragonflydb'
    };

    return await this.unifiedDb.execute(queryRequest);
  }

  async getCachedServiceRoutes() {
    const queryRequest = {
      type: 'retrieve',
      key: 'service_routes',
      targetDatabase: 'dragonflydb'
    };

    try {
      const result = await this.unifiedDb.execute(queryRequest);
      return result.data.result;
    } catch (error) {
      logger.debug('Service routes cache miss');
      return null;
    }
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
      apiGateway: {
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
      logger.info('API Gateway database connections closed');
    }
  }
}

module.exports = ApiGatewayDatabaseConfig;