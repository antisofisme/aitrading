#!/usr/bin/env node

/**
 * Chain-Aware Debugging System
 * Main entry point for the comprehensive debugging architecture
 */

import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import dotenv from 'dotenv';

import logger from './utils/logger.js';
import { ChainHealthMonitor } from './core/ChainHealthMonitor.js';
import { ChainImpactAnalyzer } from './core/ChainImpactAnalyzer.js';
import { ChainRootCauseAnalyzer } from './core/ChainRootCauseAnalyzer.js';
import { ChainRecoveryOrchestrator } from './core/ChainRecoveryOrchestrator.js';
import { setupAPIRoutes } from './api/routes.js';
import { setupWebSocketHandlers } from './api/websocket.js';
import { DatabaseManager } from './utils/database.js';
import { RedisManager } from './utils/redis.js';
import { MetricsCollector } from './monitoring/MetricsCollector.js';

// Load environment variables
dotenv.config();

class ChainDebugSystem {
  constructor() {
    this.app = express();
    this.server = createServer(this.app);
    this.wss = new WebSocketServer({ server: this.server });
    this.port = process.env.PORT || 8025;

    this.components = {};
    this.isInitialized = false;
  }

  async initialize() {
    try {
      logger.info('Initializing Chain Debug System...');

      // Setup middleware
      this.setupMiddleware();

      // Initialize database connections
      await this.initializeDatabase();

      // Initialize core components
      await this.initializeComponents();

      // Setup API routes
      this.setupRoutes();

      // Setup WebSocket handlers
      this.setupWebSocket();

      // Setup error handling
      this.setupErrorHandling();

      // Start health monitoring
      await this.startMonitoring();

      this.isInitialized = true;
      logger.info('Chain Debug System initialized successfully');

    } catch (error) {
      logger.error('Failed to initialize Chain Debug System:', error);
      throw error;
    }
  }

  setupMiddleware() {
    // Security middleware
    this.app.use(helmet());
    this.app.use(cors({
      origin: process.env.CORS_ORIGIN || '*',
      credentials: true
    }));

    // Rate limiting
    const limiter = rateLimit({
      windowMs: 15 * 60 * 1000, // 15 minutes
      max: 100, // limit each IP to 100 requests per windowMs
      message: 'Too many requests from this IP'
    });
    this.app.use('/api', limiter);

    // Compression and parsing
    this.app.use(compression());
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true }));

    // Request logging
    this.app.use((req, res, next) => {
      logger.debug(`${req.method} ${req.path}`, {
        ip: req.ip,
        userAgent: req.get('User-Agent'),
        timestamp: new Date().toISOString()
      });
      next();
    });
  }

  async initializeDatabase() {
    logger.info('Initializing database connections...');

    // Initialize PostgreSQL
    this.database = new DatabaseManager();
    await this.database.connect();

    // Initialize Redis
    this.redis = new RedisManager();
    await this.redis.connect();

    logger.info('Database connections established');
  }

  async initializeComponents() {
    logger.info('Initializing core components...');

    // Initialize metrics collector
    this.components.metricsCollector = new MetricsCollector({
      database: this.database,
      redis: this.redis
    });

    // Initialize health monitor
    this.components.healthMonitor = new ChainHealthMonitor({
      database: this.database,
      redis: this.redis,
      metricsCollector: this.components.metricsCollector
    });

    // Initialize impact analyzer
    this.components.impactAnalyzer = new ChainImpactAnalyzer({
      database: this.database,
      redis: this.redis,
      metricsCollector: this.components.metricsCollector
    });

    // Initialize root cause analyzer
    this.components.rootCauseAnalyzer = new ChainRootCauseAnalyzer({
      database: this.database,
      redis: this.redis,
      metricsCollector: this.components.metricsCollector
    });

    // Initialize recovery orchestrator
    this.components.recoveryOrchestrator = new ChainRecoveryOrchestrator({
      database: this.database,
      redis: this.redis,
      metricsCollector: this.components.metricsCollector,
      impactAnalyzer: this.components.impactAnalyzer
    });

    // Initialize all components
    await Promise.all([
      this.components.metricsCollector.initialize(),
      this.components.healthMonitor.initialize(),
      this.components.impactAnalyzer.initialize(),
      this.components.rootCauseAnalyzer.initialize(),
      this.components.recoveryOrchestrator.initialize()
    ]);

    logger.info('Core components initialized successfully');
  }

  setupRoutes() {
    // Health check endpoint
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        version: process.env.npm_package_version || '1.0.0',
        components: Object.keys(this.components).reduce((acc, key) => {
          acc[key] = this.components[key].isHealthy || true;
          return acc;
        }, {})
      });
    });

    // Setup API routes
    setupAPIRoutes(this.app, this.components);

    // 404 handler
    this.app.use('*', (req, res) => {
      res.status(404).json({
        error: 'Not Found',
        message: `Route ${req.originalUrl} not found`
      });
    });
  }

  setupWebSocket() {
    setupWebSocketHandlers(this.wss, this.components);
  }

  setupErrorHandling() {
    // Global error handler
    this.app.use((error, req, res, next) => {
      logger.error('Unhandled error:', error);

      res.status(error.status || 500).json({
        error: 'Internal Server Error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong',
        timestamp: new Date().toISOString()
      });
    });

    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
      logger.error('Uncaught Exception:', error);
      this.gracefulShutdown('UNCAUGHT_EXCEPTION');
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
      logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
      this.gracefulShutdown('UNHANDLED_REJECTION');
    });

    // Handle shutdown signals
    process.on('SIGTERM', () => this.gracefulShutdown('SIGTERM'));
    process.on('SIGINT', () => this.gracefulShutdown('SIGINT'));
  }

  async startMonitoring() {
    logger.info('Starting continuous monitoring...');

    // Start health monitoring
    await this.components.healthMonitor.startMonitoring();

    logger.info('Monitoring started successfully');
  }

  async start() {
    if (!this.isInitialized) {
      await this.initialize();
    }

    return new Promise((resolve, reject) => {
      this.server.listen(this.port, (error) => {
        if (error) {
          logger.error('Failed to start server:', error);
          reject(error);
        } else {
          logger.info(`Chain Debug System listening on port ${this.port}`);
          logger.info(`Health check: http://localhost:${this.port}/health`);
          logger.info(`API documentation: http://localhost:${this.port}/api/docs`);
          resolve(this.server);
        }
      });
    });
  }

  async gracefulShutdown(signal) {
    logger.info(`Received ${signal}. Starting graceful shutdown...`);

    try {
      // Stop accepting new connections
      this.server.close(() => {
        logger.info('HTTP server closed');
      });

      // Stop monitoring
      if (this.components.healthMonitor) {
        await this.components.healthMonitor.stopMonitoring();
      }

      // Close database connections
      if (this.database) {
        await this.database.disconnect();
      }

      if (this.redis) {
        await this.redis.disconnect();
      }

      logger.info('Graceful shutdown completed');
      process.exit(0);

    } catch (error) {
      logger.error('Error during graceful shutdown:', error);
      process.exit(1);
    }
  }
}

// Start the application if this file is run directly
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const system = new ChainDebugSystem();

  system.start().catch((error) => {
    logger.error('Failed to start Chain Debug System:', error);
    process.exit(1);
  });
}

export { ChainDebugSystem };