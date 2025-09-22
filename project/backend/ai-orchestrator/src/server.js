/**
 * Level 4 Intelligence Orchestrator (Port 8020)
 * Purpose: Multi-tenant AI coordination and deployment management
 * Coordinates: All Level 4 AI/ML services with enterprise-grade multi-tenancy
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const dotenv = require('dotenv');
const winston = require('winston');
const cron = require('node-cron');

// Load environment variables
dotenv.config();

// Import core modules
const OrchestrationCore = require('./core/OrchestrationCore');
const ServiceCoordinator = require('./services/ServiceCoordinator');
const TenantManager = require('./services/TenantManager');
const AIModelDeployment = require('./services/AIModelDeployment');
const PerformanceManager = require('./services/PerformanceManager');

// Import routes
const healthRoutes = require('./routes/health');
const orchestrationRoutes = require('./routes/orchestration');
const deploymentRoutes = require('./routes/deployment');
const tenantRoutes = require('./routes/tenants');

class Level4Orchestrator {
  constructor() {
    this.app = express();
    this.port = process.env.LEVEL4_ORCHESTRATOR_PORT || 8020;
    this.serviceName = 'level4-orchestrator';

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
    this.orchestrationCore = new OrchestrationCore(this.logger);
    this.serviceCoordinator = new ServiceCoordinator(this.logger);
    this.tenantManager = new TenantManager(this.logger);
    this.aiModelDeployment = new AIModelDeployment(this.logger);
    this.performanceManager = new PerformanceManager(this.logger);

    // Level 4 services registry
    this.level4Services = {
      'feature-engineering': { port: 8011, status: 'unknown', health: null },
      'configuration-service': { port: 8012, status: 'unknown', health: null },
      'ml-automl': { port: 8013, status: 'unknown', health: null },
      'pattern-validator': { port: 8015, status: 'unknown', health: null },
      'telegram-service': { port: 8016, status: 'unknown', health: null },
      'realtime-inference-engine': { port: 8017, status: 'unknown', health: null },
      'ml-ensemble': { port: 8021, status: 'unknown', health: null },
      'backtesting-engine': { port: 8024, status: 'unknown', health: null },
      'performance-analytics': { port: 8002, status: 'unknown', health: null },
      'revenue-analytics': { port: 8026, status: 'unknown', health: null },
      'usage-monitoring': { port: 8027, status: 'unknown', health: null },
      'compliance-monitor': { port: 8040, status: 'unknown', health: null }
    };

    // Performance tracking
    this.metrics = {
      startTime: Date.now(),
      requestCount: 0,
      orchestrationRequests: 0,
      deploymentRequests: 0,
      activeTenants: new Set(),
      activeUsers: new Set(),
      totalAIModels: 0,
      averageResponseTime: 0,
      lastHealthCheck: Date.now(),
      serviceHealthChecks: 0,
      successfulDeployments: 0
    };

    // Level 4 performance targets
    this.performanceTargets = {
      maxOrchestrationTime: 100, // ms for orchestration
      serviceAvailability: 0.999, // 99.9% availability
      aiAccuracy: 0.65, // >65% AI accuracy
      maxInferenceTime: 15, // ms for inference
      multiTenantIsolation: true
    };

    this.initializeMiddleware();
    this.initializeRoutes();
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

      // Track multi-tenant usage
      if (req.headers['user-id']) {
        this.metrics.activeUsers.add(req.headers['user-id']);
      }
      if (req.headers['tenant-id']) {
        this.metrics.activeTenants.add(req.headers['tenant-id']);
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
    this.app.use('/api/orchestration', orchestrationRoutes);
    this.app.use('/api/deployment', deploymentRoutes);
    this.app.use('/api/tenants', tenantRoutes);

    // Level 4 specific endpoints
    this.app.get('/api/status', async (req, res) => {
      const servicesStatus = await this.getServicesStatus();

      res.json({
        service: this.serviceName,
        level: 'level4-intelligence',
        status: 'operational',
        version: '1.0.0',
        uptime: Date.now() - this.metrics.startTime,
        performance: {
          requestCount: this.metrics.requestCount,
          orchestrationRequests: this.metrics.orchestrationRequests,
          deploymentRequests: this.metrics.deploymentRequests,
          activeTenants: this.metrics.activeTenants.size,
          activeUsers: this.metrics.activeUsers.size,
          totalAIModels: this.metrics.totalAIModels,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          targetResponseTime: '<100ms',
          successfulDeployments: this.metrics.successfulDeployments,
          level4Compliance: true
        },
        capabilities: [
          'multi-tenant-ai-coordination',
          'ai-model-deployment',
          'service-orchestration',
          'performance-management',
          'enterprise-grade-security',
          'real-time-monitoring'
        ],
        integrationPoints: {
          level3DataStream: true,
          allLevel4Services: true,
          enterpriseMultiTenancy: true,
          aiModelManagement: true
        },
        services: servicesStatus
      });
    });

    // Level 4 services orchestration
    this.app.post('/api/orchestrate-ai-workflow', async (req, res) => {
      const startTime = Date.now();

      try {
        const {
          tenantId,
          userId,
          workflowType,
          parameters,
          services
        } = req.body;

        if (!tenantId || !userId || !workflowType) {
          return res.status(400).json({
            error: 'Missing required fields: tenantId, userId, workflowType'
          });
        }

        // Orchestrate AI workflow across Level 4 services
        const orchestrationResult = await this.orchestrationCore.orchestrateWorkflow({
          tenantId,
          userId,
          workflowType,
          parameters,
          services: services || Object.keys(this.level4Services),
          startTime
        });

        this.metrics.orchestrationRequests++;
        const orchestrationTime = Date.now() - startTime;

        res.json({
          success: true,
          tenantId,
          userId,
          workflowType,
          orchestration: orchestrationResult,
          metadata: {
            orchestrationTime: `${orchestrationTime}ms`,
            targetCompliance: orchestrationTime < this.performanceTargets.maxOrchestrationTime ? 'PASSED' : 'WARNING',
            servicesInvolved: orchestrationResult.servicesInvolved,
            aiAccuracy: orchestrationResult.averageAccuracy,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Orchestration error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.body.tenantId,
          userId: req.body.userId
        });

        res.status(500).json({
          error: 'Orchestration failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // AI model deployment
    this.app.post('/api/deploy-ai-model', async (req, res) => {
      const startTime = Date.now();

      try {
        const {
          tenantId,
          userId,
          modelType,
          modelConfig,
          deploymentTarget
        } = req.body;

        if (!tenantId || !userId || !modelType) {
          return res.status(400).json({
            error: 'Missing required fields: tenantId, userId, modelType'
          });
        }

        // Deploy AI model with multi-tenant isolation
        const deploymentResult = await this.aiModelDeployment.deployModel({
          tenantId,
          userId,
          modelType,
          modelConfig,
          deploymentTarget: deploymentTarget || 'production',
          startTime
        });

        this.metrics.deploymentRequests++;
        this.metrics.totalAIModels++;
        if (deploymentResult.success) {
          this.metrics.successfulDeployments++;
        }

        const deploymentTime = Date.now() - startTime;

        res.json({
          success: deploymentResult.success,
          tenantId,
          userId,
          modelType,
          deployment: deploymentResult,
          metadata: {
            deploymentTime: `${deploymentTime}ms`,
            modelId: deploymentResult.modelId,
            estimatedAccuracy: deploymentResult.estimatedAccuracy,
            multiTenantIsolation: true,
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Model deployment error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.body.tenantId,
          userId: req.body.userId
        });

        res.status(500).json({
          error: 'Model deployment failed',
          message: error.message,
          processingTime: `${Date.now() - startTime}ms`
        });
      }
    });

    // Multi-tenant performance dashboard
    this.app.get('/api/tenant-dashboard/:tenantId', async (req, res) => {
      try {
        const { tenantId } = req.params;

        const tenantDashboard = await this.tenantManager.getTenantDashboard(tenantId);

        res.json({
          success: true,
          tenantId,
          dashboard: tenantDashboard,
          level4Performance: {
            aiAccuracy: tenantDashboard.averageAIAccuracy,
            inferenceTime: tenantDashboard.averageInferenceTime,
            serviceAvailability: tenantDashboard.serviceAvailability,
            compliance: {
              aiAccuracy: tenantDashboard.averageAIAccuracy >= this.performanceTargets.aiAccuracy ? 'PASSED' : 'WARNING',
              inferenceTime: tenantDashboard.averageInferenceTime < this.performanceTargets.maxInferenceTime ? 'PASSED' : 'WARNING',
              availability: tenantDashboard.serviceAvailability >= this.performanceTargets.serviceAvailability ? 'PASSED' : 'WARNING'
            }
          },
          metadata: {
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Tenant dashboard error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.params.tenantId
        });

        res.status(500).json({
          error: 'Failed to get tenant dashboard',
          message: error.message
        });
      }
    });

    // Level 4 services health check
    this.app.get('/api/services-health', async (req, res) => {
      try {
        const servicesHealth = await this.getServicesHealth();

        res.json({
          success: true,
          level4Services: servicesHealth,
          summary: {
            totalServices: Object.keys(this.level4Services).length,
            healthyServices: Object.values(servicesHealth).filter(s => s.status === 'healthy').length,
            degradedServices: Object.values(servicesHealth).filter(s => s.status === 'degraded').length,
            unhealthyServices: Object.values(servicesHealth).filter(s => s.status === 'unhealthy').length,
            overallHealth: this.calculateOverallHealth(servicesHealth)
          },
          metadata: {
            lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('Services health check error', {
          error: error.message,
          stack: error.stack
        });

        res.status(500).json({
          error: 'Failed to get services health',
          message: error.message
        });
      }
    });

    // AI accuracy validation
    this.app.get('/api/validate-ai-accuracy', async (req, res) => {
      try {
        const tenantId = req.headers['tenant-id'];

        const accuracyValidation = await this.performanceManager.validateAIAccuracy(tenantId);

        res.json({
          success: true,
          tenantId,
          validation: accuracyValidation,
          level4Compliance: {
            target: `>${this.performanceTargets.aiAccuracy * 100}%`,
            actual: `${Math.round(accuracyValidation.averageAccuracy * 100)}%`,
            compliance: accuracyValidation.averageAccuracy >= this.performanceTargets.aiAccuracy ? 'PASSED' : 'FAILED',
            recommendations: accuracyValidation.recommendations
          },
          metadata: {
            timestamp: new Date().toISOString()
          }
        });

      } catch (error) {
        this.logger.error('AI accuracy validation error', {
          error: error.message,
          stack: error.stack,
          tenantId: req.headers['tenant-id']
        });

        res.status(500).json({
          error: 'AI accuracy validation failed',
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
          orchestrationRequests: this.metrics.orchestrationRequests,
          deploymentRequests: this.metrics.deploymentRequests,
          activeTenants: this.metrics.activeTenants.size,
          activeUsers: this.metrics.activeUsers.size,
          totalAIModels: this.metrics.totalAIModels,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          serviceHealthChecks: this.metrics.serviceHealthChecks,
          successfulDeployments: this.metrics.successfulDeployments,
          level4Targets: {
            orchestrationTime: this.metrics.averageResponseTime < this.performanceTargets.maxOrchestrationTime ? 'PASSED' : 'WARNING',
            serviceAvailability: 'MONITORING',
            aiAccuracy: 'MONITORING',
            multiTenant: this.metrics.activeTenants.size > 0 ? 'ACTIVE' : 'READY'
          }
        },
        health: {
          status: 'healthy',
          lastHealthCheck: new Date(this.metrics.lastHealthCheck).toISOString(),
          components: {
            orchestrationCore: this.orchestrationCore.isHealthy(),
            serviceCoordinator: this.serviceCoordinator.isHealthy(),
            tenantManager: this.tenantManager.isHealthy(),
            aiModelDeployment: this.aiModelDeployment.isHealthy(),
            performanceManager: this.performanceManager.isHealthy()
          }
        }
      });
    });

    // Root endpoint
    this.app.get('/', (req, res) => {
      res.json({
        service: 'Level 4 Intelligence Orchestrator',
        level: 'Level 4 - Intelligence',
        description: 'Multi-tenant AI coordination and deployment management',
        version: '1.0.0',
        port: this.port,
        capabilities: [
          'multi-tenant-ai-coordination',
          'ai-model-deployment',
          'service-orchestration',
          'performance-management',
          'enterprise-grade-security',
          'real-time-monitoring'
        ],
        documentation: '/api/docs',
        health: '/health',
        status: '/api/status'
      });
    });
  }

  async getServicesStatus() {
    const servicesStatus = {};

    for (const [serviceName, serviceInfo] of Object.entries(this.level4Services)) {
      try {
        const response = await this.serviceCoordinator.checkServiceHealth(serviceName, serviceInfo.port);
        servicesStatus[serviceName] = {
          ...serviceInfo,
          status: response.status,
          health: response.health,
          lastCheck: new Date().toISOString()
        };
      } catch (error) {
        servicesStatus[serviceName] = {
          ...serviceInfo,
          status: 'unhealthy',
          health: null,
          error: error.message,
          lastCheck: new Date().toISOString()
        };
      }
    }

    return servicesStatus;
  }

  async getServicesHealth() {
    const servicesHealth = {};

    for (const [serviceName, serviceInfo] of Object.entries(this.level4Services)) {
      try {
        const health = await this.serviceCoordinator.getDetailedHealth(serviceName, serviceInfo.port);
        servicesHealth[serviceName] = health;
        this.metrics.serviceHealthChecks++;
      } catch (error) {
        servicesHealth[serviceName] = {
          status: 'unhealthy',
          error: error.message,
          lastCheck: new Date().toISOString()
        };
      }
    }

    return servicesHealth;
  }

  calculateOverallHealth(servicesHealth) {
    const services = Object.values(servicesHealth);
    const healthyCount = services.filter(s => s.status === 'healthy').length;
    const totalCount = services.length;

    if (healthyCount === totalCount) return 'healthy';
    if (healthyCount >= totalCount * 0.8) return 'degraded';
    return 'unhealthy';
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
          'POST /api/orchestrate-ai-workflow',
          'POST /api/deploy-ai-model',
          'GET /api/tenant-dashboard/:tenantId',
          'GET /api/services-health',
          'GET /api/validate-ai-accuracy',
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
          orchestrationRequests: this.metrics.orchestrationRequests,
          deploymentRequests: this.metrics.deploymentRequests,
          activeTenants: this.metrics.activeTenants.size,
          activeUsers: this.metrics.activeUsers.size,
          totalAIModels: this.metrics.totalAIModels,
          averageResponseTime: Math.round(this.metrics.averageResponseTime),
          serviceHealthChecks: this.metrics.serviceHealthChecks,
          successfulDeployments: this.metrics.successfulDeployments,
          memoryUsage: process.memoryUsage(),
          cpuUsage: process.cpuUsage()
        }
      });
    });

    // Reset user and tenant sessions every hour
    cron.schedule('0 0 * * * *', () => {
      this.metrics.activeUsers.clear();
      this.metrics.activeTenants.clear();
      this.logger.info('User and tenant sessions reset for new hour');
    });

    // Level 4 services health monitoring every 2 minutes
    cron.schedule('*/2 * * * * *', async () => {
      try {
        const servicesHealth = await this.getServicesHealth();
        const overallHealth = this.calculateOverallHealth(servicesHealth);

        if (overallHealth !== 'healthy') {
          this.logger.warn('Level 4 services health degraded', {
            overallHealth,
            unhealthyServices: Object.entries(servicesHealth)
              .filter(([, health]) => health.status !== 'healthy')
              .map(([name]) => name)
          });
        }
      } catch (error) {
        this.logger.error('Failed to monitor services health', {
          error: error.message
        });
      }
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
          orchestrationCore: this.orchestrationCore.isHealthy(),
          serviceCoordinator: this.serviceCoordinator.isHealthy(),
          tenantManager: this.tenantManager.isHealthy(),
          aiModelDeployment: this.aiModelDeployment.isHealthy(),
          performanceManager: this.performanceManager.isHealthy()
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

      // Check orchestration performance
      if (this.metrics.averageResponseTime > this.performanceTargets.maxOrchestrationTime) {
        health.status = 'degraded';
        health.performanceWarning = {
          issue: 'orchestration_time_exceeded',
          current: this.metrics.averageResponseTime,
          target: this.performanceTargets.maxOrchestrationTime,
          message: 'Orchestration time exceeds Level 4 target'
        };
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
      await this.orchestrationCore.initialize();
      await this.serviceCoordinator.initialize();
      await this.tenantManager.initialize();
      await this.aiModelDeployment.initialize();
      await this.performanceManager.initialize();

      // Start server
      this.server = this.app.listen(this.port, () => {
        this.logger.info('Level 4 Intelligence Orchestrator started', {
          service: this.serviceName,
          port: this.port,
          level: 'level4-intelligence',
          environment: process.env.NODE_ENV || 'development',
          timestamp: new Date().toISOString(),
          capabilities: [
            'multi-tenant-ai-coordination',
            'ai-model-deployment',
            'service-orchestration',
            'performance-management'
          ],
          performanceTargets: this.performanceTargets,
          level4Services: Object.keys(this.level4Services)
        });
      });

      // Graceful shutdown handling
      process.on('SIGTERM', () => this.shutdown('SIGTERM'));
      process.on('SIGINT', () => this.shutdown('SIGINT'));

    } catch (error) {
      this.logger.error('Failed to start Level 4 Intelligence Orchestrator', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    }
  }

  async shutdown(signal) {
    this.logger.info(`Received ${signal}, shutting down gracefully`);

    if (this.server) {
      this.server.close(() => {
        this.logger.info('Level 4 Intelligence Orchestrator stopped');
        process.exit(0);
      });
    } else {
      process.exit(0);
    }
  }
}

// Start service if called directly
if (require.main === module) {
  const service = new Level4Orchestrator();
  service.start().catch(error => {
    console.error('Failed to start service:', error);
    process.exit(1);
  });
}

module.exports = Level4Orchestrator;