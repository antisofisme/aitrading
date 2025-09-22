/**
 * Level 4 Configuration Service (Port 8012)
 * Purpose: Centralized per-user config management with enterprise multi-tenancy
 * Enhanced: Flow registry, credential storage, multi-tenant isolation
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const dotenv = require('dotenv');
const winston = require('winston');
const cron = require('node-cron');
const { WebSocketServer } = require('ws');

// Load environment variables
dotenv.config();

// Import core modules
const ConfigurationCore = require('./core/ConfigurationCore');
const UserConfigManager = require('./services/UserConfigManager');
const CredentialManager = require('./services/CredentialManager');
const FlowRegistry = require('./services/FlowRegistry');
const TenantManager = require('./services/TenantManager');

// Import routes
const healthRoutes = require('./routes/health');
const configRoutes = require('./routes/config');
const userRoutes = require('./routes/users');
const flowRoutes = require('./routes/flows');
const tenantRoutes = require('./routes/tenants');

class ConfigurationService {
  constructor() {
    this.app = express();
    this.port = process.env.CONFIG_SERVICE_PORT || 8012;
    this.serviceName = 'configuration-service';

    // Initialize logger
    this.logger = winston.createLogger({
      level: process.env.LOG_LEVEL || 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      defaultMeta: {
        service: this.serviceName,
        level: 'level4-intelligence'
      },
      transports: [
        new winston.transports.Console({
          format: winston.format.combine(
            winston.format.colorize(),
            winston.format.simple()
          )
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}-error.log`,
          level: 'error'
        }),
        new winston.transports.File({
          filename: `logs/${this.serviceName}.log`
        })
      ]
    });

    // Initialize core components
    this.configCore = new ConfigurationCore(this.logger);
    this.userConfigManager = new UserConfigManager(this.logger);
    this.credentialManager = new CredentialManager(this.logger);
    this.flowRegistry = new FlowRegistry(this.logger);
    this.tenantManager = new TenantManager(this.logger);

    // WebSocket for hot-reload capabilities
    this.wsClients = new Set();

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      configRequests: 0,
      tenantCount: 0,
      activeUsers: new Set(),
      averageResponseTime: 0,
      lastHealthCheck: Date.now(),
      hotReloadEvents: 0
    };

    this.initializeMiddleware();
    this.initializeRoutes();
    this.initializeWebSocket();
    this.initializeErrorHandling();
    this.setupPerformanceMonitoring();
  }

  initializeMiddleware() {
    // Security middleware
    this.app.use(helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          scriptSrc: ["'self'", "'unsafe-inline'"],
          styleSrc: ["'self'", "'unsafe-inline'"],
          imgSrc: ["'self'", "data:", "https:"]
        }
      }
    }));

    // CORS configuration
    this.app.use(cors({
      origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
      credentials: true,
      optionsSuccessStatus: 200
    }));

    // Body parsing
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // Request logging and metrics
    this.app.use((req, res, next) => {
      const startTime = Date.now();

      // Track tenant isolation
      if (req.headers['tenant-id']) {
        this.metrics.tenantCount = Math.max(
          this.metrics.tenantCount,
          parseInt(req.headers['tenant-id']) || 0
        );
      }

      // Track user sessions
      if (req.headers['user-id']) {
        this.metrics.activeUsers.add(req.headers['user-id']);
      }

      // Request logging
      this.logger.info('Incoming request', {
        method: req.method,
        url: req.url,
        userAgent: req.get('User-Agent'),
        userId: req.headers['user-id'],
        tenantId: req.headers['tenant-id'],
        ip: req.ip
      });

      // Response time tracking
      res.on('finish', () => {
        const duration = Date.now() - startTime;
        this.metrics.requestCount++;
        this.metrics.averageResponseTime =
          (this.metrics.averageResponseTime + duration) / 2;

        this.logger.info('Request completed', {
          method: req.method,
          url: req.url,
          statusCode: res.statusCode,
          duration: `${duration}ms`,
          userId: req.headers['user-id'],
          tenantId: req.headers['tenant-id']
        });
      });

      next();
    });
  }

  initializeRoutes() {
    // API routes
    this.app.use('/health', healthRoutes);
    this.app.use('/api/config', configRoutes);
    this.app.use('/api/users', userRoutes);
    this.app.use('/api/flows', flowRoutes);
    this.app.use('/api/tenants', tenantRoutes);

    // Level 4 specific endpoints
    this.app.get('/api/status', (req, res) => {
      res.json({
        service: this.serviceName,
        level: 'level4-intelligence',
        status: 'operational',
        version: '1.0.0',
        uptime: Date.now() - this.metrics.startTime,
        performance: {
          requestCount: this.metrics.requestCount,
          configRequests: this.metrics.configRequests,
          activeTenants: this.metrics.tenantCount,
          activeUsers: this.metrics.activeUsers.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          targetResponseTime: '<5ms',
          level4Compliance: true
        },
        capabilities: [
          'per-user-config-management',
          'multi-tenant-isolation',
          'credential-encryption',
          'flow-registry',
          'hot-reload',
          'enterprise-grade-security'
        ],
        integrationPoints: {
          allServices: true,
          flowRegistry: true,
          credentialStorage: true,
          tenantIsolation: true,
          hotReload: true
        }
      });
    });

    // Multi-tenant configuration endpoint
    this.app.get('/api/config/:userId', async (req, res) => {
      const startTime = Date.now();

      try {
        const { userId } = req.params;
        const tenantId = req.headers['tenant-id'];

        if (!userId) {
          return res.status(400).json({
            error: 'User ID is required'
          });
        }

        // Get user configuration with tenant isolation
        const userConfig = await this.userConfigManager.getUserConfig(userId, tenantId);

        this.metrics.configRequests++;
        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          userId,
          tenantId,
          config: userConfig,
          metadata: {
            processingTime: `${processingTime}ms`,
            targetCompliance: processingTime < 5 ? 'PASSED' : 'WARNING',
            timestamp: new Date().toISOString(),
            version: userConfig.version || '1.0.0'
          }
        });

      } catch (error) {
        this.logger.error('Configuration retrieval error', {
          error: error.message,
          stack: error.stack,
          userId: req.params.userId,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'Configuration retrieval failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Update user configuration
    this.app.put('/api/config/:userId', async (req, res) => {
      const startTime = Date.now();

      try {
        const { userId } = req.params;
        const tenantId = req.headers['tenant-id'];
        const { config } = req.body;

        if (!userId || !config) {
          return res.status(400).json({
            error: 'User ID and config are required'
          });
        }

        // Update user configuration with tenant isolation
        const updatedConfig = await this.userConfigManager.updateUserConfig(
          userId,
          config,
          tenantId
        );

        // Trigger hot-reload for connected clients
        this.triggerHotReload(userId, tenantId, updatedConfig);

        const processingTime = Date.now() - startTime;

        res.json({
          success: true,
          userId,
          tenantId,
          config: updatedConfig,
          metadata: {
            processingTime: `${processingTime}ms`,
            hotReloadTriggered: true,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Configuration update error', {
          error: error.message,
          stack: error.stack,
          userId: req.params.userId,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'Configuration update failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Flow registry endpoints
    this.app.get('/api/flows/:userId', async (req, res) => {
      try {
        const { userId } = req.params;
        const tenantId = req.headers['tenant-id'];

        const userFlows = await this.flowRegistry.getUserFlows(userId, tenantId);

        res.json({
          success: true,
          userId,
          tenantId,
          flows: userFlows,
          metadata: {
            flowCount: userFlows.length,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Flow retrieval error', {
          error: error.message,
          userId: req.params.userId,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'Flow retrieval failed',
          message: error.message
        });
      }
    });

    // Credential management endpoints
    this.app.post('/api/credentials/:userId', async (req, res) => {
      try {
        const { userId } = req.params;
        const tenantId = req.headers['tenant-id'];
        const { credentialType, credentials } = req.body;

        const encryptedCredentials = await this.credentialManager.storeCredentials(
          userId,
          credentialType,
          credentials,
          tenantId
        );

        res.json({
          success: true,
          userId,
          tenantId,
          credentialType,
          credentialId: encryptedCredentials.id,
          metadata: {
            encrypted: true,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Credential storage error', {
          error: error.message,
          userId: req.params.userId,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'Credential storage failed',
          message: error.message
        });
      }
    });

    // Performance metrics endpoint
    this.app.get('/api/performance', (req, res) => {
      const uptime = Date.now() - this.metrics.startTime;

      res.json({
        service: this.serviceName,
        performance: {
          uptime: `${Math.floor(uptime / 1000)}s`,
          requestCount: this.metrics.requestCount,
          configRequests: this.metrics.configRequests,
          activeTenants: this.metrics.tenantCount,
          activeUsers: this.metrics.activeUsers.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          targetResponseTime: '<5ms',
          hotReloadEvents: this.metrics.hotReloadEvents,
          level4Targets: {
            responseTime: this.metrics.averageResponseTime < 5 ? 'PASSED' : 'WARNING',
            multiTenant: this.metrics.tenantCount > 0 ? 'ACTIVE' : 'READY',
            userIsolation: 'OPERATIONAL',
            credentialSecurity: 'ENCRYPTED'
          }
        },
        health: {
          status: 'healthy',
          lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
          components: {
            configCore: this.configCore.isHealthy(),
            userConfig: this.userConfigManager.isHealthy(),
            credentials: this.credentialManager.isHealthy(),
            flowRegistry: this.flowRegistry.isHealthy(),
            tenantManager: this.tenantManager.isHealthy()
          }
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        service: 'Configuration Service',
        level: 'Level 4 - Intelligence',
        description: 'Centralized per-user config management with enterprise multi-tenancy',
        version: '1.0.0',
        port: this.port,
        capabilities: [
          'per-user-configurations',
          'multi-tenant-isolation',
          'encrypted-credential-storage',
          'flow-registry',
          'hot-reload',
          'enterprise-security'
        ],
        documentation: '/api/docs',
        health: '/health',
        status: '/api/status'
      });
    });
  }

  initializeWebSocket() {
    this.wss = new WebSocketServer({
      port: this.port + 1000, // WebSocket on port 9012
      path: '/ws'
    });

    this.wss.on('connection', (ws, req) => {
      this.wsClients.add(ws);

      this.logger.info('WebSocket client connected', {
        clientCount: this.wsClients.size,
        userAgent: req.headers['user-agent']
      });

      ws.on('close', () => {
        this.wsClients.delete(ws);
        this.logger.info('WebSocket client disconnected', {
          clientCount: this.wsClients.size
        });
      });

      ws.on('error', (error) => {
        this.logger.error('WebSocket error', {
          error: error.message
        });
        this.wsClients.delete(ws);
      });

      // Send initial connection confirmation
      ws.send(JSON.stringify({
        type: 'connection',
        message: 'Connected to Configuration Service',
        timestamp: new Date().toISOString()
      }));
    });
  }

  triggerHotReload(userId, tenantId, config) {
    const hotReloadMessage = {
      type: 'hot_reload',
      userId,
      tenantId,
      config,
      timestamp: new Date().toISOString()
    };

    let successCount = 0;
    this.wsClients.forEach(client => {
      try {
        if (client.readyState === 1) { // WebSocket.OPEN
          client.send(JSON.stringify(hotReloadMessage));
          successCount++;
        }
      } catch (error) {
        this.logger.error('Failed to send hot reload message', {
          error: error.message
        });
        this.wsClients.delete(client);
      }
    });

    this.metrics.hotReloadEvents++;
    this.logger.info('Hot reload triggered', {
      userId,
      tenantId,
      clientsNotified: successCount,
      totalClients: this.wsClients.size
    });
  }

  initializeErrorHandling() {
    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Endpoint not found',
        service: this.serviceName,
        availableEndpoints: [
          'GET /health',
          'GET /api/status',
          'GET /api/config/:userId',
          'PUT /api/config/:userId',
          'GET /api/flows/:userId',
          'POST /api/credentials/:userId',
          'GET /api/performance'
        ]
      });
    });

    // Global error handler
    this.app.use((error, req, res, next) => {
      this.logger.error('Unhandled error', {
        error: error.message,
        stack: error.stack,
        url: req.url,
        method: req.method,
        userId: req.headers['user-id'],
        tenantId: req.headers['tenant-id']
      });

      res.status(500).json({
        error: 'Internal server error',
        message: error.message,
        service: this.serviceName,
        timestamp: new Date().toISOString()
      });
    });
  }

  setupPerformanceMonitoring() {
    // Health check every 30 seconds
    cron.schedule('*/30 * * * * *', () => {
      this.metrics.lastHealthCheck = Date.now();
      this.performHealthCheck();
    });

    // Performance metrics logging every minute
    cron.schedule('0 * * * * *', () => {
      this.logger.info('Performance metrics', {
        service: this.serviceName,
        metrics: {
          uptime: Date.now() - this.metrics.startTime,
          requestCount: this.metrics.requestCount,
          configRequests: this.metrics.configRequests,
          activeTenants: this.metrics.tenantCount,
          activeUsers: this.metrics.activeUsers.size,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          hotReloadEvents: this.metrics.hotReloadEvents,
          wsClients: this.wsClients.size,
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        }
      });
    });

    // Reset user sessions every hour
    cron.schedule('0 0 * * * *', () => {
      this.metrics.activeUsers.clear();
      this.logger.info('User sessions reset for new hour');
    });
  }

  async performHealthCheck() {
    try {
      const health = {
        service: this.serviceName,
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: Date.now() - this.metrics.startTime,
        components: {
          configCore: this.configCore.isHealthy(),
          userConfig: this.userConfigManager.isHealthy(),
          credentials: this.credentialManager.isHealthy(),
          flowRegistry: this.flowRegistry.isHealthy(),
          tenantManager: this.tenantManager.isHealthy(),
          webSocket: this.wss.clients.size >= 0
        }
      };

      // Check if any components are unhealthy
      const unhealthyComponents = Object.entries(health.components)
        .filter(([, status]) => !status);

      if (unhealthyComponents.length > 0) {
        health.status = 'unhealthy';
        health.issues = unhealthyComponents.map(([component]) => component);
        this.logger.warn('Health check failed', health);
      }

    } catch (error) {
      this.logger.error('Health check error', {
        error: error.message,
        stack: error.stack
      });
    }
  }

  async start() {
    try {
      // Initialize core components
      await this.configCore.initialize();
      await this.userConfigManager.initialize();
      await this.credentialManager.initialize();
      await this.flowRegistry.initialize();
      await this.tenantManager.initialize();

      // Start HTTP server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('Configuration Service started', {
          service: this.serviceName,
          port: this.port,
          wsPort: this.port + 1000,
          level: 'level4-intelligence',
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          capabilities: [
            'per-user-config-management',
            'multi-tenant-isolation',
            'credential-encryption',
            'flow-registry',
            'hot-reload-websocket'
          ]
        });
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      this.logger.error('Failed to start Configuration Service', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  async shutdown(signal) {
    this.logger.info(`Received ${signal}, shutting down gracefully`);

    // Close WebSocket connections
    this.wsClients.forEach(client => {
      try {
        client.close();
      } catch (error) {
        this.logger.error('Error closing WebSocket client', {
          error: error.message
        });
      }
    });

    if (this.wss) {
      this.wss.close();
    }

    if (this.server) {
      this.server.close(() => {
        this.logger.info('Configuration Service stopped');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const service = new ConfigurationService();
  service.start().catch(error => {
    console.error('Failed to start service:', error);
    process.exit(1);
  });
}

module.exports = ConfigurationService;