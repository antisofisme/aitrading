/**
 * Enhanced API Gateway Server with 6-Database Architecture
 *
 * Features:
 * - Multi-database architecture integration (PostgreSQL, DragonflyDB, ClickHouse, Weaviate, ArangoDB, Redis)
 * - Configuration Service integration with Flow Registry
 * - Flow-Aware Error Handling
 * - Advanced service discovery
 * - Comprehensive health monitoring
 */

require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const winston = require('winston');
const { v4: uuidv4 } = require('uuid');

// Import custom components
const DatabaseManager = require('./config/DatabaseManager');
const FlowAwareErrorHandler = require('./middleware/FlowAwareErrorHandler');
const ConfigurationServiceClient = require('./services/ConfigurationServiceClient');

// Import existing routes
const authRoutes = require('../routes/auth');
const businessRoutes = require('../routes/business');

class EnhancedAPIGateway {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3001;
    this.environment = process.env.NODE_ENV || 'development';

    // Initialize logger
    this.logger = winston.createLogger({
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
          filename: 'logs/api-gateway.log',
          maxsize: 5242880, // 5MB
          maxFiles: 5
        })
      ]
    });

    // Initialize components
    this.databaseManager = new DatabaseManager(this.logger);
    this.configServiceClient = new ConfigurationServiceClient({
      logger: this.logger
    });
    this.flowAwareErrorHandler = new FlowAwareErrorHandler({
      logger: this.logger
    });

    this.isInitialized = false;
    this.startTime = new Date();
  }

  /**
   * Initialize all components
   */
  async initialize() {
    try {
      this.logger.info('🚀 Initializing Enhanced API Gateway...');

      // Initialize database connections
      this.logger.info('📊 Initializing database connections...');
      await this.databaseManager.initialize();

      // Initialize Configuration Service client
      this.logger.info('⚙️ Initializing Configuration Service client...');
      await this.configServiceClient.initialize();

      // Register with Configuration Service
      await this.configServiceClient.registerService();

      // Setup Express app
      this.setupMiddleware();
      this.setupRoutes();
      this.setupErrorHandling();

      this.isInitialized = true;
      this.logger.info('✅ Enhanced API Gateway initialized successfully');

      return true;
    } catch (error) {
      this.logger.error('❌ Failed to initialize Enhanced API Gateway', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  /**
   * Setup Express middleware
   */
  setupMiddleware() {
    // Request ID middleware
    this.app.use((req, res, next) => {
      req.requestId = req.headers['x-request-id'] || uuidv4();
      res.locals.requestId = req.requestId;
      res.set('X-Request-ID', req.requestId);
      next();
    });

    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          scriptSrc: ["'self'"],
          imgSrc: ["'self'", "data:", "https:"]
        }
      }
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID', 'X-Tenant-ID']
    }));

    // Compression
    this.app.use(compression());

    // Rate limiting with DragonflyDB backend
    const rateLimiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 1000, // Limit each IP to 1000 requests per windowMs
      message: {
        success: false,
        message: 'Too many requests from this IP, please try again later',
        code: 'RATE_LIMIT_EXCEEDED'
      },
      standardHeaders: true,
      legacyHeaders: false,
      skip: (req) => {
        // Skip rate limiting for health checks
        return req.path === '/health';
      }
    });

    this.app.use('/api/', rateLimiter);

    // Body parsing
    this.app.use(express.json({
      limit: '10mb',
      verify: (req, res, buf) => {
        req.rawBody = buf;
      }
    }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Logging with request context
    this.app.use(morgan('combined', {
      stream: {
        write: (message) => {
          this.logger.info(message.trim());
        }
      }
    }));

    // Database and service injection middleware
    this.app.use((req, res, next) => {
      req.databases = this.databaseManager;
      req.configService = this.configServiceClient;
      req.logger = this.logger.child({ requestId: req.requestId });
      next();
    });
  }

  /**
   * Setup application routes
   */
  setupRoutes() {
    // Health check endpoint with comprehensive status
    this.app.get('/health', async (req, res) => {
      try {
        const healthData = {
          status: 'healthy',
          timestamp: new Date(),
          uptime: Math.floor((Date.now() - this.startTime.getTime()) / 1000),
          version: '1.0.0',
          environment: this.environment,
          requestId: req.requestId,
          services: {
            apiGateway: {
              status: 'healthy',
              initialized: this.isInitialized
            }
          }
        };

        // Check database health
        try {
          const dbHealth = await this.databaseManager.healthCheck();
          healthData.services.databases = dbHealth;
        } catch (dbError) {
          healthData.services.databases = { error: dbError.message };
          healthData.status = 'degraded';
        }

        // Check Configuration Service health
        try {
          const configServiceStatus = this.configServiceClient.getConnectionStatus();
          healthData.services.configurationService = {
            status: configServiceStatus.isConnected ? 'healthy' : 'unhealthy',
            ...configServiceStatus
          };
        } catch (configError) {
          healthData.services.configurationService = {
            status: 'unhealthy',
            error: configError.message
          };
          healthData.status = 'degraded';
        }

        const statusCode = healthData.status === 'healthy' ? 200 : 503;
        res.status(statusCode).json({
          success: true,
          data: healthData
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          message: 'Health check failed',
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    // Database status endpoint
    this.app.get('/api/v1/status/databases', async (req, res) => {
      try {
        const dbStatus = await this.databaseManager.healthCheck();
        const connectionStatus = this.databaseManager.getConnectionStatus();

        res.json({
          success: true,
          data: {
            connections: connectionStatus,
            health: dbStatus,
            timestamp: new Date()
          }
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          message: 'Failed to get database status',
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    // Configuration Service integration endpoints
    this.app.get('/api/v1/config/:key', async (req, res) => {
      try {
        const { key } = req.params;
        const { environment, tenantId, userId } = req.query;

        const config = await this.configServiceClient.getConfiguration(key, {
          environment,
          tenantId,
          userId
        });

        if (!config) {
          return res.status(404).json({
            success: false,
            message: `Configuration '${key}' not found`,
            requestId: req.requestId
          });
        }

        res.json({
          success: true,
          data: config
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          message: 'Failed to get configuration',
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    // Service discovery endpoint
    this.app.get('/api/v1/services', async (req, res) => {
      try {
        const services = await this.configServiceClient.listServices();
        res.json({
          success: true,
          data: services
        });
      } catch (error) {
        res.status(500).json({
          success: false,
          message: 'Failed to list services',
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    this.app.get('/api/v1/services/discover/:serviceName', async (req, res) => {
      try {
        const { serviceName } = req.params;
        const serviceInfo = await this.configServiceClient.discoverService(serviceName);

        res.json({
          success: true,
          data: serviceInfo
        });
      } catch (error) {
        res.status(404).json({
          success: false,
          message: `Service '${req.params.serviceName}' not found`,
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    // Flow Registry integration
    this.app.post('/api/v1/flows', async (req, res) => {
      try {
        const flowDefinition = req.body;
        const result = await this.configServiceClient.registerFlow(flowDefinition);

        res.status(201).json({
          success: true,
          data: result
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          message: 'Failed to register flow',
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    this.app.get('/api/v1/flows/:flowId', async (req, res) => {
      try {
        const { flowId } = req.params;
        const flow = await this.configServiceClient.getFlow(flowId);

        res.json({
          success: true,
          data: flow
        });
      } catch (error) {
        res.status(404).json({
          success: false,
          message: `Flow '${req.params.flowId}' not found`,
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    this.app.post('/api/v1/flows/:flowId/execute', async (req, res) => {
      try {
        const { flowId } = req.params;
        const parameters = req.body;

        const result = await this.configServiceClient.executeFlow(flowId, parameters);

        res.json({
          success: true,
          data: result
        });
      } catch (error) {
        res.status(400).json({
          success: false,
          message: 'Failed to execute flow',
          error: error.message,
          requestId: req.requestId
        });
      }
    });

    // API documentation endpoint
    this.app.get('/api', (req, res) => {
      res.json({
        success: true,
        message: 'Enhanced AI Trading Platform API Gateway',
        version: '1.0.0',
        features: [
          'Multi-database architecture (PostgreSQL, DragonflyDB, ClickHouse, Weaviate, ArangoDB, Redis)',
          'Configuration Service integration',
          'Flow Registry support',
          'Flow-Aware Error Handling',
          'Advanced service discovery',
          'Comprehensive health monitoring'
        ],
        endpoints: {
          health: 'GET /health',
          databases: 'GET /api/v1/status/databases',
          configuration: 'GET /api/v1/config/:key',
          services: 'GET /api/v1/services',
          serviceDiscovery: 'GET /api/v1/services/discover/:serviceName',
          flows: {
            register: 'POST /api/v1/flows',
            get: 'GET /api/v1/flows/:flowId',
            execute: 'POST /api/v1/flows/:flowId/execute'
          },
          auth: {
            login: 'POST /api/auth/login',
            logout: 'POST /api/auth/logout',
            refresh: 'POST /api/auth/refresh',
            profile: 'GET /api/auth/me'
          }
        }
      });
    });

    // Mount existing routes with database context
    this.app.use('/api/auth', (req, res, next) => {
      // Add database connections to request for auth routes
      req.db = this.databaseManager.getConnection('postgres');
      req.cache = this.databaseManager.getConnection('dragonflydb');
      next();
    }, authRoutes);

    this.app.use('/api/business', (req, res, next) => {
      // Add database connections to request for business routes
      req.db = this.databaseManager.getConnection('postgres');
      req.cache = this.databaseManager.getConnection('dragonflydb');
      req.analytics = this.databaseManager.getConnection('clickhouse');
      next();
    }, businessRoutes);

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        success: false,
        message: 'Endpoint not found',
        code: 'ENDPOINT_NOT_FOUND',
        path: req.originalUrl,
        method: req.method,
        requestId: req.requestId
      });
    });
  }

  /**
   * Setup error handling
   */
  setupErrorHandling() {
    // Flow-Aware Error Handler
    this.app.use(this.flowAwareErrorHandler.handleError());

    // Global error handler (fallback)
    this.app.use((err, req, res, next) => {
      this.logger.error('Unhandled error in API Gateway', {
        error: err.message,
        stack: err.stack,
        requestId: req.requestId,
        method: req.method,
        path: req.path
      });

      if (res.headersSent) {
        return next(err);
      }

      const isDevelopment = this.environment === 'development';

      res.status(err.status || 500).json({
        success: false,
        message: isDevelopment ? err.message : 'Internal server error',
        code: 'INTERNAL_ERROR',
        requestId: req.requestId,
        timestamp: new Date(),
        ...(isDevelopment && { stack: err.stack })
      });
    });
  }

  /**
   * Start the server
   */
  async start() {
    try {
      if (!this.isInitialized) {
        await this.initialize();
      }

      const server = this.app.listen(this.port, () => {
        this.logger.info('🚀 Enhanced API Gateway started', {
          port: this.port,
          environment: this.environment,
          pid: process.pid,
          features: {
            multiDatabase: true,
            configurationService: this.configServiceClient.isConnected,
            flowRegistry: true,
            errorHandling: true
          }
        });

        console.log(`
╔══════════════════════════════════════════════════════════════╗
║             🚀 ENHANCED API GATEWAY STARTED 🚀              ║
╠══════════════════════════════════════════════════════════════╣
║ Port:                ${this.port.toString().padEnd(42)} ║
║ Environment:         ${this.environment.padEnd(42)} ║
║ Health Check:        http://localhost:${this.port}/health${' '.repeat(18)} ║
║ API Docs:            http://localhost:${this.port}/api${' '.repeat(21)} ║
║ Database Status:     http://localhost:${this.port}/api/v1/status/databases ║
╠══════════════════════════════════════════════════════════════╣
║ Features:                                                    ║
║ ✅ Multi-Database Architecture                              ║
║ ✅ Configuration Service Integration                        ║
║ ✅ Flow Registry Support                                    ║
║ ✅ Flow-Aware Error Handling                               ║
║ ✅ Advanced Service Discovery                              ║
║ ✅ Comprehensive Health Monitoring                         ║
╚══════════════════════════════════════════════════════════════╝
        `);
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.gracefulShutdown(server));
      process.on('SIGINT', () => this.gracefulShutdown(server));

      return server;
    } catch (error) {
      this.logger.error('Failed to start Enhanced API Gateway', {
        error: error.message,
        stack: error.stack
      });
      throw error;
    }
  }

  /**
   * Graceful shutdown
   */
  async gracefulShutdown(server) {
    this.logger.info('🛑 Graceful shutdown initiated...');

    // Stop accepting new connections
    server.close(async () => {
      this.logger.info('✅ HTTP server closed');

      try {
        // Close database connections
        await this.databaseManager.close();
        this.logger.info('✅ Database connections closed');

        // Close Configuration Service client
        this.configServiceClient.close();
        this.logger.info('✅ Configuration Service client closed');

        // Close error handler
        await this.flowAwareErrorHandler.close();
        this.logger.info('✅ Flow-Aware Error Handler closed');

        this.logger.info('✅ Graceful shutdown completed');
        process.exit(0);
      } catch (error) {
        this.logger.error('❌ Error during graceful shutdown', {
          error: error.message
        });
        process.exit(1);
      }
    });

    // Force exit after 30 seconds
    setTimeout(() => {
      this.logger.error('❌ Graceful shutdown timeout, forcing exit');
      process.exit(1);
    }, 30000);
  }
}

// Start the Enhanced API Gateway if this file is run directly
if (require.main === module) {
  const gateway = new EnhancedAPIGateway();

  gateway.start().catch((error) => {
    console.error('❌ Failed to start Enhanced API Gateway:', error);
    process.exit(1);
  });
}

module.exports = EnhancedAPIGateway;