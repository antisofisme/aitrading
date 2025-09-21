import express, { Application, Request, Response, NextFunction } from 'express';
import cors from 'cors';
import compression from 'compression';
import { config, validateConfig } from '@/config';
import { DatabaseService } from '@/database';
import { SecurityService, createSecurityMiddleware } from '@/security';
import { MT5ConnectionManager } from '@/mt5';
import { logger, loggerService } from '@/logging';
import { errorDnaService } from '@/utils/errorDna';
import { createAuthRoutes } from '@/api/auth.routes';
import { createTradingRoutes } from '@/api/trading.routes';
import { ApiResponse, HealthStatus, HealthCheck } from '@/types';

class AITradingServer {
  private app: Application;
  private databaseService: DatabaseService;
  private securityService: SecurityService;
  private mt5ConnectionManager: MT5ConnectionManager;
  private server: any;

  constructor() {
    this.app = express();
    this.databaseService = new DatabaseService();
    this.securityService = new SecurityService(this.databaseService);
    this.mt5ConnectionManager = new MT5ConnectionManager(this.databaseService);

    this.initializeServer();
  }

  /**
   * Initialize Express server with all middleware and routes
   */
  private initializeServer(): void {
    // Validate configuration
    validateConfig();

    // Trust proxy (important for proper IP detection behind load balancers)
    this.app.set('trust proxy', 1);

    // Initialize security middleware
    const security = createSecurityMiddleware(this.databaseService);

    // Core middleware (order matters for performance)
    this.app.use(security.addRequestId);
    this.app.use(security.securityHeaders);
    this.app.use(compression());
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use(express.urlencoded({ extended: true, limit: '10mb' }));

    // CORS configuration
    this.app.use(cors({
      origin: config.cors.origin,
      credentials: config.cors.credentials,
      methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID', 'X-Refresh-Token'],
      exposedHeaders: ['X-Request-ID', 'X-RateLimit-Limit', 'X-RateLimit-Remaining']
    }));

    // Audit logging middleware
    this.app.use(security.auditLogger);

    // Health check endpoint (no authentication required)
    this.app.get('/health', this.healthCheckHandler.bind(this));
    this.app.get('/health/detailed', this.detailedHealthCheckHandler.bind(this));

    // API routes with versioning
    const apiV1Router = express.Router();

    // Authentication routes
    apiV1Router.use('/auth', createAuthRoutes(this.databaseService, this.securityService));

    // Trading routes
    apiV1Router.use('/trading', createTradingRoutes(this.databaseService, this.mt5ConnectionManager));

    // User management routes
    apiV1Router.use('/users', this.createUserManagementRoutes());

    // System monitoring routes (admin only)
    apiV1Router.use('/system', this.createSystemRoutes());

    // Mount API routes
    this.app.use(`/api/${config.apiVersion}`, apiV1Router);

    // Default route
    this.app.get('/', (req: Request, res: Response) => {
      const response: ApiResponse = {
        success: true,
        data: {
          service: 'AI Trading Platform Backend API',
          version: config.apiVersion,
          environment: config.nodeEnv,
          timestamp: new Date()
        },
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] as string || 'unknown'
      };

      res.json(response);
    });

    // 404 handler
    this.app.use('*', (req: Request, res: Response) => {
      const response: ApiResponse = {
        success: false,
        error: 'Endpoint not found',
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] as string || 'unknown'
      };

      res.status(404).json(response);
    });

    // Global error handler (must be last)
    this.app.use(security.errorHandler);

    logger.info('Express server initialized successfully', {
      port: config.port,
      environment: config.nodeEnv,
      api_version: config.apiVersion
    });
  }

  /**
   * Health check endpoint
   */
  private async healthCheckHandler(req: Request, res: Response): Promise<void> {
    try {
      const health = await this.databaseService.healthCheck();
      const mt5Health = await this.mt5ConnectionManager.healthCheck();
      const loggingHealth = loggerService.healthCheck();

      const overallHealth = health.postgres && health.redis && loggingHealth.status === 'healthy';

      const response: ApiResponse<HealthStatus> = {
        success: overallHealth,
        data: {
          service: 'ai-trading-backend',
          status: overallHealth ? 'healthy' : 'unhealthy',
          checks: [
            {
              name: 'PostgreSQL',
              status: health.postgres ? 'pass' : 'fail',
              duration_ms: 0
            },
            {
              name: 'Redis',
              status: health.redis ? 'pass' : 'fail',
              duration_ms: 0
            },
            {
              name: 'ClickHouse',
              status: health.clickhouse ? 'pass' : 'fail',
              duration_ms: 0
            },
            {
              name: 'MT5 Connections',
              status: mt5Health.errors === 0 ? 'pass' : 'warn',
              duration_ms: 0,
              details: mt5Health
            },
            {
              name: 'Logging System',
              status: loggingHealth.status === 'healthy' ? 'pass' : 'fail',
              duration_ms: 0,
              details: loggingHealth.details
            }
          ],
          timestamp: new Date()
        },
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] as string || 'unknown'
      };

      res.status(overallHealth ? 200 : 503).json(response);

    } catch (error) {
      const response: ApiResponse = {
        success: false,
        error: 'Health check failed',
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] as string || 'unknown'
      };

      res.status(503).json(response);
    }
  }

  /**
   * Detailed health check with performance metrics
   */
  private async detailedHealthCheckHandler(req: Request, res: Response): Promise<void> {
    try {
      const startTime = process.hrtime.bigint();

      const [
        dbHealth,
        mt5Health,
        loggingHealth
      ] = await Promise.all([
        this.databaseService.healthCheck(),
        this.mt5ConnectionManager.healthCheck(),
        Promise.resolve(loggerService.healthCheck())
      ]);

      const duration = Number(process.hrtime.bigint() - startTime) / 1000000; // Convert to ms
      const errorAnalytics = errorDnaService.getErrorAnalytics();
      const costAnalytics = loggerService.getCostAnalytics();

      const response: ApiResponse = {
        success: true,
        data: {
          service: 'ai-trading-backend',
          status: 'healthy',
          uptime: process.uptime(),
          memory_usage: process.memoryUsage(),
          check_duration_ms: duration,
          database: dbHealth,
          mt5_connections: mt5Health,
          logging: loggingHealth,
          error_analytics: errorAnalytics,
          cost_analytics: costAnalytics,
          performance: {
            active_connections: mt5Health.connected,
            error_rate: errorAnalytics.criticalErrorCount,
            average_response_time: duration
          }
        },
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] as string || 'unknown'
      };

      res.json(response);

    } catch (error) {
      const response: ApiResponse = {
        success: false,
        error: 'Detailed health check failed',
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] as string || 'unknown'
      };

      res.status(503).json(response);
    }
  }

  /**
   * Create user management routes
   */
  private createUserManagementRoutes(): express.Router {
    const router = express.Router();
    const security = createSecurityMiddleware(this.databaseService);

    // Get subscription information
    router.get('/subscription', [
      security.authenticate,
      security.rateLimiter
    ], async (req: any, res: Response) => {
      try {
        const subscription = req.subscription;

        const response: ApiResponse = {
          success: true,
          data: subscription,
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] as string || 'unknown'
        };

        res.json(response);

      } catch (error) {
        const errorResult = await errorDnaService.handleError(error as Error, {
          operation: 'get_subscription',
          userId: req.user?.id,
          requestId: req.headers['x-request-id'] as string
        });

        const response: ApiResponse = {
          success: false,
          error: errorResult.classification.userMessage,
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] as string || 'unknown'
        };

        res.status(500).json(response);
      }
    });

    return router;
  }

  /**
   * Create system monitoring routes
   */
  private createSystemRoutes(): express.Router {
    const router = express.Router();
    const security = createSecurityMiddleware(this.databaseService);

    // System metrics (enterprise tier required)
    router.get('/metrics', [
      security.authenticate,
      security.requireEnterprise,
      security.rateLimiter
    ], async (req: Request, res: Response) => {
      try {
        const metrics = {
          error_analytics: errorDnaService.getErrorAnalytics(),
          cost_analytics: loggerService.getCostAnalytics(),
          mt5_connections: this.mt5ConnectionManager.getConnectionStats(),
          memory_usage: process.memoryUsage(),
          uptime: process.uptime()
        };

        const response: ApiResponse = {
          success: true,
          data: metrics,
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] as string || 'unknown'
        };

        res.json(response);

      } catch (error) {
        const response: ApiResponse = {
          success: false,
          error: 'Failed to retrieve system metrics',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] as string || 'unknown'
        };

        res.status(500).json(response);
      }
    });

    return router;
  }

  /**
   * Start the server
   */
  public async start(): Promise<void> {
    try {
      // Wait for database to be ready
      while (!this.databaseService.isReady()) {
        logger.info('Waiting for database connections...');
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // Start HTTP server
      this.server = this.app.listen(config.port, () => {
        logger.info('AI Trading Backend API started successfully', {
          port: config.port,
          environment: config.nodeEnv,
          api_version: config.apiVersion,
          pid: process.pid
        });
      });

      // Graceful shutdown handling
      this.setupGracefulShutdown();

    } catch (error) {
      logger.error('Failed to start server', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      process.exit(1);
    }
  }

  /**
   * Stop the server gracefully
   */
  public async stop(): Promise<void> {
    try {
      logger.info('Shutting down AI Trading Backend API...');

      // Close HTTP server
      if (this.server) {
        await new Promise<void>((resolve, reject) => {
          this.server.close((error: any) => {
            if (error) reject(error);
            else resolve();
          });
        });
      }

      // Close database connections
      await this.databaseService.close();

      // Cleanup MT5 connections
      await this.mt5ConnectionManager.cleanupInactiveConnections();

      logger.info('AI Trading Backend API stopped successfully');

    } catch (error) {
      logger.error('Error during server shutdown', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  }

  /**
   * Setup graceful shutdown handlers
   */
  private setupGracefulShutdown(): void {
    const shutdown = async (signal: string) => {
      logger.info(`Received ${signal}, starting graceful shutdown...`);
      await this.stop();
      process.exit(0);
    };

    process.on('SIGTERM', () => shutdown('SIGTERM'));
    process.on('SIGINT', () => shutdown('SIGINT'));

    // Handle uncaught exceptions
    process.on('uncaughtException', (error: Error) => {
      logger.error('Uncaught Exception', {
        error: error.message,
        stack: error.stack
      });
      process.exit(1);
    });

    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason: any, promise: Promise<any>) => {
      logger.error('Unhandled Rejection', {
        reason: reason instanceof Error ? reason.message : reason,
        stack: reason instanceof Error ? reason.stack : undefined
      });
      process.exit(1);
    });
  }

  /**
   * Get Express application instance
   */
  public getApp(): Application {
    return this.app;
  }
}

// Create and export server instance
const server = new AITradingServer();

// Start server if this file is run directly
if (require.main === module) {
  server.start().catch((error) => {
    logger.error('Server startup failed', {
      error: error instanceof Error ? error.message : 'Unknown error'
    });
    process.exit(1);
  });
}

export default server;
export { AITradingServer };