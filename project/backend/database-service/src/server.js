const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const { Pool } = require('pg');
const winston = require('winston');
require('dotenv').config();

const DatabaseConnection = require('./database/connection');
const MultiDbManager = require('./database/multiDbManager');
const UserService = require('./services/userService');
const QueryInterface = require('./database/queryInterface');
const HealthMonitor = require('./health/monitor');
const CentralHubClient = require('./integration/centralHubClient');

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

class DatabaseService {
  constructor() {
    this.app = express();
    this.port = process.env.PORT || 8008;
    this.db = null;
    this.multiDbManager = null;
    this.userService = null;
    this.queryInterface = null;
    this.healthMonitor = null;
    this.centralHubClient = null;
  }

  async initialize() {
    try {
      // Initialize database connection
      this.db = new DatabaseConnection();
      await this.db.connect();
      logger.info('Database connected successfully');

      // Initialize multi-database manager
      this.multiDbManager = new MultiDbManager();
      await this.multiDbManager.initialize();
      logger.info('Multi-Database Manager initialized successfully');

      // Initialize services
      this.userService = new UserService(this.db);
      this.queryInterface = new QueryInterface(this.db);
      this.healthMonitor = new HealthMonitor(this.db);
      this.centralHubClient = new CentralHubClient();

      // Setup middleware
      this.setupMiddleware();

      // Setup routes
      this.setupRoutes();

      // Register with Central Hub
      await this.registerWithCentralHub();

      logger.info('Database Service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize Database Service:', error);
      process.exit(1);
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
  }

  setupRoutes() {
    // Health check
    this.app.get('/health', async (req, res) => {
      try {
        const health = await this.healthMonitor.checkHealth();
        const multiDbHealth = await this.multiDbManager.healthCheckAll();

        const combinedHealth = {
          ...health,
          databases: multiDbHealth,
          multiDbStatus: this.multiDbManager.getConnectionCount()
        };

        const isHealthy = health.status === 'healthy' &&
          Object.values(multiDbHealth).every(db => db.status === 'healthy' || db.status === 'mock');

        res.status(isHealthy ? 200 : 503).json(combinedHealth);
      } catch (error) {
        logger.error('Health check failed:', error);
        res.status(503).json({ status: 'unhealthy', error: error.message });
      }
    });

    // User management routes
    this.app.post('/api/users', async (req, res) => {
      try {
        const user = await this.userService.createUser(req.body);
        res.status(201).json({ success: true, data: user });
      } catch (error) {
        logger.error('Create user failed:', error);
        res.status(400).json({ success: false, error: error.message });
      }
    });

    this.app.get('/api/users/:id', async (req, res) => {
      try {
        const user = await this.userService.getUserById(req.params.id);
        if (!user) {
          return res.status(404).json({ success: false, error: 'User not found' });
        }
        res.json({ success: true, data: user });
      } catch (error) {
        logger.error('Get user failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    this.app.post('/api/users/authenticate', async (req, res) => {
      try {
        const result = await this.userService.authenticateUser(req.body.email, req.body.password);
        res.json({ success: true, data: result });
      } catch (error) {
        logger.error('Authentication failed:', error);
        res.status(401).json({ success: false, error: error.message });
      }
    });

    // Query interface routes
    this.app.post('/api/query', async (req, res) => {
      try {
        const result = await this.queryInterface.executeQuery(req.body.query, req.body.params);
        res.json({ success: true, data: result });
      } catch (error) {
        logger.error('Query execution failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Multi-database query endpoint
    this.app.post('/api/multi-db/query', async (req, res) => {
      try {
        const { database, query, params } = req.body;
        const result = await this.multiDbManager.executeQuery(database, query, params);
        res.json({ success: true, data: result });
      } catch (error) {
        logger.error('Multi-DB query execution failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Database status endpoint
    this.app.get('/api/databases/status', async (req, res) => {
      try {
        const status = this.multiDbManager.getHealthStatus();
        const connections = this.multiDbManager.getConnectionCount();
        res.json({ success: true, data: { status, connections } });
      } catch (error) {
        logger.error('Get database status failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Migration routes
    this.app.post('/api/migrate', async (req, res) => {
      try {
        const result = await this.queryInterface.runMigrations();
        res.json({ success: true, data: result });
      } catch (error) {
        logger.error('Migration failed:', error);
        res.status(500).json({ success: false, error: error.message });
      }
    });

    // Service info
    this.app.get('/api/info', (req, res) => {
      res.json({
        service: 'Database Service',
        version: '1.0.0',
        port: this.port,
        status: 'running',
        timestamp: new Date().toISOString()
      });
    });
  }

  async registerWithCentralHub() {
    try {
      await this.centralHubClient.registerService({
        name: 'database-service',
        port: this.port,
        health: `http://localhost:${this.port}/health`,
        endpoints: [
          '/api/users',
          '/api/query',
          '/api/migrate'
        ]
      });
      logger.info('Registered with Central Hub successfully');
    } catch (error) {
      logger.warn('Failed to register with Central Hub:', error.message);
    }
  }

  async start() {
    await this.initialize();

    this.app.listen(this.port, () => {
      logger.info(`Database Service running on port ${this.port}`);
    });

    // Graceful shutdown
    process.on('SIGTERM', async () => {
      logger.info('Shutting down Database Service...');
      if (this.db) {
        await this.db.disconnect();
      }
      process.exit(0);
    });
  }
}

// Start service
if (require.main === module) {
  const service = new DatabaseService();
  service.start().catch(error => {
    logger.error('Failed to start Database Service:', error);
    process.exit(1);
  });
}

module.exports = DatabaseService;