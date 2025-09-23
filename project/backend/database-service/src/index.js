const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const winston = require('winston');
// Import the new multi-database service
const { createDatabaseService } = require('./multi-db');
const DatabaseConfig = require('./config/database'); // Legacy support
const HealthService = require('./services/HealthService');
const HubIntegration = require('./services/HubIntegration');
const createApiRoutes = require('./routes/api');

// Configure logging
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.simple()
      )
    }),
    new winston.transports.File({
      filename: 'logs/error.log',
      level: 'error'
    }),
    new winston.transports.File({
      filename: 'logs/combined.log'
    })
  ]
});

class DatabaseService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 8008;
    // Use the new multi-database service
    this.multiDb = null;
    this.db = new DatabaseConfig(); // Legacy support
    this.healthService = null;
    this.hubIntegration = new HubIntegration();
    this.server = null;
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: false // Disable for API service
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Service-Name']
    }));

    // Request parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request ID middleware
    this.app.use((req, res, next) => {
      req.id = require('uuid').v4();
      res.setHeader('X-Request-ID', req.id);
      next();
    });

    // Request logging
    this.app.use((req, res, next) => {
      const start = Date.now();

      res.on('finish', () => {
        const duration = Date.now() - start;
        logger.info('Request completed', {
          requestId: req.id,
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration,
          ip: req.ip,
          userAgent: req.get('User-Agent')
        });

        // Record metrics
        if (this.healthService) {
          this.healthService.recordQuery(duration, res.statusCode < 400);
        }
      });

      next();
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', async (req, res) => {
      try {
        const health = await this.healthService.getDetailedHealth();
        const status = health.status === 'healthy' ? 200 : 503;
        res.status(status).json(health);
      } catch (error) {
        logger.error('Health check failed:', error);
        res.status(503).json({
          service: 'database-service',
          status: 'unhealthy',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Full health report
    this.app.get('/health/full', async (req, res) => {
      try {
        const report = await this.healthService.getFullHealthReport();
        res.json(report);
      } catch (error) {
        logger.error('Full health report failed:', error);
        res.status(500).json({ error: 'Failed to generate health report' });
      }
    });

    // Service info
    this.app.get('/info', (req, res) => {
      res.json({
        service: 'database-service',
        version: process.env.npm_package_version || '1.0.0',
        description: 'Database Service for AI Trading Platform',
        capabilities: [
          'user_authentication',
          'query_execution',
          'transaction_support',
          'schema_management'
        ],
        endpoints: {
          health: '/health',
          api: '/api/*',
          users: '/api/users',
          auth: '/api/auth/*',
          query: '/api/query',
          transaction: '/api/transaction'
        }
      });
    });

    // API routes (legacy)
    this.app.use('/api', createApiRoutes(this.db));

    // Multi-database API routes
    this.app.use('/api/v2', this.createMultiDbRoutes());

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        path: req.originalUrl,
        method: req.method
      });
    });

    // Error handler
    this.app.use((error, req, res, next) => {
      logger.error('Unhandled error:', {
        error: error.message,
        stack: error.stack,
        requestId: req.id,
        url: req.url,
        method: req.method
      });

      res.status(error.status || 500).json({
        error: process.env.NODE_ENV === 'production' ?
          'Internal Server Error' : error.message,
        requestId: req.id
      });
    });
  }

  createMultiDbRoutes() {
    const router = require('express').Router();

    // Unified query endpoint
    router.post('/query', async (req, res) => {
      try {
        const result = await this.multiDb.execute(req.body);
        res.json(result);
      } catch (error) {
        logger.error('Multi-database query error:', error);
        res.status(500).json({ error: error.message });
      }
    });

    // Cross-database operations
    router.post('/cross-db', async (req, res) => {
      try {
        const result = await this.multiDb.executeCrossDatabase(req.body);
        res.json(result);
      } catch (error) {
        logger.error('Cross-database operation error:', error);
        res.status(500).json({ error: error.message });
      }
    });

    // Database-specific endpoints
    router.get('/databases', (req, res) => {
      const databases = this.multiDb.getAllDatabases();
      const databaseList = Array.from(databases.keys()).map(type => ({
        type,
        status: databases.get(type).getStatus(),
        capabilities: this.getDatabaseCapabilities(type)
      }));
      res.json({ databases: databaseList });
    });

    // Health status for all databases
    router.get('/health/all', async (req, res) => {
      try {
        const health = await this.multiDb.getHealthStatus();
        res.json(health);
      } catch (error) {
        logger.error('Multi-database health check error:', error);
        res.status(500).json({ error: error.message });
      }
    });

    return router;
  }

  getDatabaseCapabilities(type) {
    const capabilities = {
      postgresql: ['ACID_TRANSACTIONS', 'COMPLEX_QUERIES', 'REFERENTIAL_INTEGRITY'],
      clickhouse: ['TIME_SERIES', 'ANALYTICS', 'COLUMNAR_STORAGE'],
      weaviate: ['VECTOR_SEARCH', 'SIMILARITY', 'AI_INTEGRATION'],
      arangodb: ['GRAPH_TRAVERSAL', 'MULTI_MODEL', 'AQL_QUERIES'],
      dragonflydb: ['HIGH_PERFORMANCE_CACHE', 'REDIS_COMPATIBILITY', 'LOW_LATENCY'],
      redpanda: ['REAL_TIME_STREAMING', 'MESSAGE_QUEUING', 'EVENT_SOURCING']
    };
    return capabilities[type] || [];
  }

  async initialize() {
    try {
      logger.info('Initializing Database Service with Plan2 Multi-Database Architecture...');

      // Initialize new multi-database service
      this.multiDb = await createDatabaseService({
        enableHealthMonitoring: true,
        enablePoolManagement: true
      });
      logger.info('Multi-database service initialized successfully');

      // Initialize legacy database connection for backward compatibility
      await this.db.initialize();
      logger.info('Legacy database connection established');

      // Initialize health service with multi-database support
      this.healthService = new HealthService(this.db, this.multiDb);
      logger.info('Health service initialized with multi-database support');

      // Setup Express app
      this.setupMiddleware();
      this.setupRoutes();

      logger.info('Database Service initialized successfully with Plan2 architecture');

    } catch (error) {
      logger.error('Failed to initialize Database Service:', error);
      throw error;
    }
  }

  async start() {
    try {
      await this.initialize();

      this.server = this.app.listen(this.port, () => {
        logger.info(`Database Service running on port ${this.port}`);
      });

      // Register with Central Hub
      try {
        await this.hubIntegration.registerWithHub();
        this.hubIntegration.startHeartbeat(this.healthService);

        // Notify startup
        await this.hubIntegration.notifyServiceEvent('startup', {
          port: this.port,
          capabilities: [
            'user_authentication',
            'query_execution',
            'transaction_support',
            'schema_management'
          ]
        });

      } catch (error) {
        logger.warn('Failed to register with Central Hub:', error.message);
      }

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      logger.error('Failed to start Database Service:', error);
      process.exit(1);
    }
  }

  async shutdown(signal) {
    logger.info(`Received ${signal}, shutting down gracefully...`);

    try {
      // Stop accepting new requests
      if (this.server) {
        this.server.close();
      }

      // Stop heartbeat
      this.hubIntegration.stopHeartbeat();

      // Deregister from hub
      await this.hubIntegration.deregisterFromHub();

      // Close database connections
      if (this.multiDb) {
        await this.multiDb.close();
      }
      if (this.db) {
        await this.db.close();
      }

      // Notify shutdown
      await this.hubIntegration.notifyServiceEvent('shutdown', {
        signal,
        graceful: true
      });

      logger.info('Database Service shut down successfully');
      process.exit(0);

    } catch (error) {
      logger.error('Error during shutdown:', error);
      process.exit(1);
    }
  }
}

// Start service if this file is run directly
if (require.main === module) {
  const service = new DatabaseService();
  service.start();
}

module.exports = DatabaseService;