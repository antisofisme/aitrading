/**
 * Central Hub Server - Core Business Logic Coordinator
 * Enhanced with service orchestration and coordination protocols
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const winston = require('winston');
require('dotenv').config();

// Import components
const ServiceRegistry = require('./services/serviceRegistry');
const HealthMonitor = require('./health/healthMonitor');
const ErrorDNA = require('../error-dna/src/index');

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

class CentralHubServer {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 3000;
    this.serviceRegistry = new ServiceRegistry();
    this.healthMonitor = new HealthMonitor();
    this.errorDNA = new ErrorDNA();
    this.isInitialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing Central Hub Server...');

      // Initialize ErrorDNA system
      await this.errorDNA.init();

      // Setup middleware
      this.setupMiddleware();

      // Setup routes
      this.setupRoutes();

      // Initialize service registry
      await this.serviceRegistry.initialize();

      // Start health monitoring
      await this.healthMonitor.start();

      this.isInitialized = true;
      logger.info('Central Hub Server initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Central Hub Server:', error);
      throw error;
    }
  }

  setupMiddleware() {
    this.app.use(helmet());
    this.app.use(compression());
    this.app.use(cors());
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path} - ${req.ip}`);
      next();
    });

    // Error handling middleware
    this.app.use(async (err, req, res, next) => {
      // Process error through ErrorDNA
      const errorResult = await this.errorDNA.processError(err, {
        endpoint: req.path,
        method: req.method,
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });

      logger.error('Request error processed by ErrorDNA:', errorResult);

      res.status(err.status || 500).json({
        success: false,
        message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error',
        errorId: errorResult.errorId
      });
    });
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', async (req, res) => {
      try {
        const health = await this.getSystemHealth();
        res.status(health.status === 'healthy' ? 200 : 503).json(health);
      } catch (error) {
        logger.error('Health check failed:', error);
        res.status(503).json({
          status: 'unhealthy',
          error: error.message,
          timestamp: new Date().toISOString()
        });
      }
    });

    // Service registry endpoints
    this.app.post('/api/services/register', async (req, res) => {
      try {
        const service = await this.serviceRegistry.registerService(req.body);
        res.json({ success: true, data: service });
      } catch (error) {
        logger.error('Service registration failed:', error);
        res.status(400).json({ success: false, error: error.message });
      }
    });

    this.app.get('/api/services', async (req, res) => {
      try {
        const services = await this.serviceRegistry.getServices();
        res.json({ success: true, data: services });
      } catch (error) {
        logger.error('Get services failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    this.app.get('/api/services/:serviceName', async (req, res) => {
      try {
        const service = await this.serviceRegistry.getService(req.params.serviceName);
        if (!service) {
          return res.status(404).json({ success: false, error: 'Service not found' });
        }
        res.json({ success: true, data: service });
      } catch (error) {
        logger.error('Get service failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    this.app.delete('/api/services/:serviceName', async (req, res) => {
      try {
        await this.serviceRegistry.deregisterService(req.params.serviceName);
        res.json({ success: true, message: 'Service deregistered' });
      } catch (error) {
        logger.error('Service deregistration failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Service coordination endpoints
    this.app.post('/api/coordinate/task', async (req, res) => {
      try {
        const result = await this.coordinateTask(req.body);
        res.json({ success: true, data: result });
      } catch (error) {
        logger.error('Task coordination failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // System metrics endpoint
    this.app.get('/api/metrics', async (req, res) => {
      try {
        const metrics = await this.getSystemMetrics();
        res.json({ success: true, data: metrics });
      } catch (error) {
        logger.error('Get metrics failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // ErrorDNA endpoints
    this.app.get('/api/errors', async (req, res) => {
      try {
        const health = await this.errorDNA.getHealth();
        res.json({ success: true, data: health });
      } catch (error) {
        logger.error('Get ErrorDNA status failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Service info
    this.app.get('/api/info', (req, res) => {
      res.json({
        service: 'Central Hub',
        version: '1.0.0',
        port: this.port,
        status: 'running',
        initialized: this.isInitialized,
        timestamp: new Date().toISOString()
      });
    });
  }

  async coordinateTask(taskDefinition) {
    const { type, target, payload } = taskDefinition;

    logger.info(`Coordinating task: ${type} for target: ${target}`);

    switch (type) {
      case 'health-check':
        return await this.healthMonitor.checkService(target);

      case 'service-restart':
        return await this.serviceRegistry.restartService(target);

      case 'data-sync':
        return await this.coordinateDataSync(target, payload);

      case 'load-balance':
        return await this.coordinateLoadBalancing(target, payload);

      default:
        throw new Error(`Unknown task type: ${type}`);
    }
  }

  async coordinateDataSync(target, payload) {
    // Coordinate data synchronization between services
    logger.info(`Coordinating data sync for ${target}`);

    return {
      taskId: `sync_${Date.now()}`,
      target,
      status: 'initiated',
      timestamp: new Date().toISOString()
    };
  }

  async coordinateLoadBalancing(target, payload) {
    // Coordinate load balancing across services
    logger.info(`Coordinating load balancing for ${target}`);

    return {
      taskId: `balance_${Date.now()}`,
      target,
      status: 'balanced',
      timestamp: new Date().toISOString()
    };
  }

  async getSystemHealth() {
    const services = await this.serviceRegistry.getServices();
    const errorDNAHealth = await this.errorDNA.getHealth();

    const serviceHealthChecks = await Promise.all(
      services.map(async (service) => {
        try {
          const health = await this.healthMonitor.checkService(service.name);
          return { name: service.name, status: health.status };
        } catch (error) {
          return { name: service.name, status: 'unhealthy', error: error.message };
        }
      })
    );

    const unhealthyServices = serviceHealthChecks.filter(s => s.status !== 'healthy');
    const overallStatus = unhealthyServices.length === 0 ? 'healthy' : 'degraded';

    return {
      status: overallStatus,
      timestamp: new Date().toISOString(),
      services: serviceHealthChecks,
      errorDNA: {
        status: errorDNAHealth.status,
        metrics: errorDNAHealth.metrics
      },
      registry: {
        totalServices: services.length,
        healthyServices: services.length - unhealthyServices.length
      }
    };
  }

  async getSystemMetrics() {
    const services = await this.serviceRegistry.getServices();
    const errorDNAHealth = await this.errorDNA.getHealth();

    return {
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      services: {
        total: services.length,
        active: services.filter(s => s.status === 'active').length
      },
      errorDNA: errorDNAHealth.metrics,
      timestamp: new Date().toISOString()
    };
  }

  async start() {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      this.server = this.app.listen(this.port, (error) => {
        if (error) {
          reject(error);
        } else {
          logger.info(`Central Hub Server running on port ${this.port}`);
          resolve({ port: this.port });
        }
      });
    });
  }

  async stop() {
    return new Promise((resolve) => {
      if (this.server) {
        this.server.close(() => {
          logger.info('Central Hub Server stopped');
          resolve();
        });
      } else {
        resolve();
      }
    });
  }
}

// Start server if this file is run directly
if (require.main === module) {
  const server = new CentralHubServer();
  server.start().catch(error => {
    logger.error('Failed to start Central Hub Server:', error);
    process.exit(1);
  });

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    logger.info('Shutting down Central Hub Server...');
    await server.stop();
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    logger.info('Shutting down Central Hub Server...');
    await server.stop();
    process.exit(0);
  });
}

module.exports = CentralHubServer;