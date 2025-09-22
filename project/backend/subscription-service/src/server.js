const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
const cron = require('cron');
require('dotenv').config();

// Import routes
const subscriptionRoutes = require('./routes/subscriptions');
const usageRoutes = require('./routes/usage');
const tierRoutes = require('./routes/tiers');
const healthRoutes = require('./routes/health');

// Import middleware
const errorHandler = require('./middleware/errorHandler');
const authMiddleware = require('./middleware/auth');
const loggingMiddleware = require('./middleware/logging');

// Import services
const { initializeDatabase } = require('./database/connection');
const { processBilling } = require('./services/billingProcessor');
const { updateUsageMetrics } = require('./services/usageService');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'subscription-service' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

const app = express();
const PORT = process.env.PORT || 8022;

// Trust proxy for rate limiting behind load balancer
app.set('trust proxy', 1);

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later.',
    retryAfter: '15 minutes'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Middleware
app.use(compression());
app.use(cors({
  origin: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(',') : ['http://localhost:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-User-ID']
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined', {
    stream: { write: message => logger.info(message.trim()) }
  }));
}

app.use(loggingMiddleware);
app.use(limiter);

// Health check (no auth required)
app.use('/health', healthRoutes);

// Routes
app.use('/api/subscriptions', authMiddleware, subscriptionRoutes);
app.use('/api/usage', authMiddleware, usageRoutes);
app.use('/api/tiers', tierRoutes); // Public endpoint for tier information

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Subscription Service',
    version: '1.0.0',
    status: 'operational',
    endpoints: {
      subscriptions: '/api/subscriptions',
      usage: '/api/usage',
      tiers: '/api/tiers',
      health: '/health'
    },
    features: {
      billing: 'enabled',
      usageTracking: 'enabled',
      tierManagement: 'enabled',
      automaticBilling: 'enabled'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: `The endpoint ${req.method} ${req.originalUrl} does not exist`,
    availableEndpoints: [
      'GET /',
      'GET /health',
      'GET /api/tiers',
      'GET /api/subscriptions',
      'GET /api/usage'
    ]
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Cron jobs for automated tasks
function setupCronJobs() {
  // Daily billing processing at 2 AM
  const billingJob = new cron.CronJob('0 2 * * *', async () => {
    logger.info('Starting daily billing processing...');
    try {
      await processBilling();
      logger.info('Daily billing processing completed successfully');
    } catch (error) {
      logger.error('Daily billing processing failed:', error);
    }
  });

  // Hourly usage metrics update
  const usageJob = new cron.CronJob('0 * * * *', async () => {
    logger.info('Starting hourly usage metrics update...');
    try {
      await updateUsageMetrics();
      logger.info('Hourly usage metrics update completed successfully');
    } catch (error) {
      logger.error('Hourly usage metrics update failed:', error);
    }
  });

  // Start jobs if not in test environment
  if (process.env.NODE_ENV !== 'test') {
    billingJob.start();
    usageJob.start();
    logger.info('Cron jobs started successfully');
  }

  return { billingJob, usageJob };
}

// Initialize database and start server
async function startServer() {
  try {
    logger.info('Initializing Subscription Service...');

    // Initialize database connection
    await initializeDatabase();
    logger.info('Database connection established');

    // Setup cron jobs
    setupCronJobs();

    // Start server
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Subscription Service running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Health check: http://localhost:${PORT}/health`);
    });

    // Graceful shutdown
    process.on('SIGTERM', () => {
      logger.info('SIGTERM received, shutting down gracefully');
      server.close(() => {
        logger.info('Process terminated');
        process.exit(0);
      });
    });

    process.on('SIGINT', () => {
      logger.info('SIGINT received, shutting down gracefully');
      server.close(() => {
        logger.info('Process terminated');
        process.exit(0);
      });
    });

    return server;
  } catch (error) {
    logger.error('Failed to start Subscription Service:', error);
    process.exit(1);
  }
}

// Start server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer };