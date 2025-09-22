const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
const Bull = require('bull');
require('dotenv').config();

// Import routes
const notificationRoutes = require('./routes/notifications');
const telegramRoutes = require('./routes/telegram');
const subscriptionRoutes = require('./routes/subscriptions');
const healthRoutes = require('./routes/health');

// Import middleware
const errorHandler = require('./middleware/errorHandler');
const authMiddleware = require('./middleware/auth');
const loggingMiddleware = require('./middleware/logging');
const telegramWebhook = require('./middleware/telegramWebhook');

// Import services
const { initializeDatabase } = require('./database/connection');
const { initializeTelegramBot } = require('./services/telegramService');
const { initializeEmailService } = require('./services/emailService');
const { processNotificationQueue } = require('./services/queueProcessor');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'notification-service' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

const app = express();
const PORT = process.env.PORT || 8024;

// Initialize Redis connection for queues
const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

// Initialize notification queue
const notificationQueue = new Bull('notification processing', REDIS_URL, {
  defaultJobOptions: {
    removeOnComplete: 100,
    removeOnFail: 50,
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
  },
});

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

// Stricter rate limiting for notification sending
const notificationLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 20, // Only 20 notification requests per 5 minutes per IP
  message: {
    error: 'Too many notification requests, please try again later.',
    retryAfter: '5 minutes'
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
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-User-ID', 'X-Telegram-Bot-Api-Secret-Token']
}));

// Body parsing - special handling for Telegram webhooks
app.use('/api/telegram/webhook', express.json({ limit: '1mb' }));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Logging
if (process.env.NODE_ENV !== 'test') {
  app.use(morgan('combined', {
    stream: { write: message => logger.info(message.trim()) }
  }));
}

app.use(loggingMiddleware);

// Health check (no auth required)
app.use('/health', healthRoutes);

// Telegram webhook (no auth required, but token verification)
app.use('/api/telegram/webhook', telegramWebhook, telegramRoutes);

// Apply rate limiting
app.use('/api/notifications', notificationLimiter);
app.use(limiter);

// Routes with authentication
app.use('/api/notifications', authMiddleware, notificationRoutes);
app.use('/api/telegram', authMiddleware, telegramRoutes);
app.use('/api/subscriptions', authMiddleware, subscriptionRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Notification Service',
    version: '1.0.0',
    status: 'operational',
    endpoints: {
      notifications: '/api/notifications',
      telegram: '/api/telegram',
      subscriptions: '/api/subscriptions',
      health: '/health'
    },
    features: {
      telegramBot: 'enabled',
      emailNotifications: 'enabled',
      smsNotifications: 'enabled',
      queueProcessing: 'enabled',
      multiUserSupport: 'enabled'
    },
    supportedChannels: [
      'telegram',
      'email',
      'sms',
      'push_notification',
      'webhook'
    ]
  });
});

// Queue dashboard (for monitoring - dev only)
if (process.env.NODE_ENV === 'development') {
  const arena = require('bull-arena');
  const arenaConfig = arena({
    Bull,
    queues: [
      {
        name: 'notification processing',
        hostId: 'Notification Queue',
        redis: { port: 6379, host: 'localhost' },
      },
    ],
  });
  app.use('/admin/queues', arenaConfig);
}

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    message: `The endpoint ${req.method} ${req.originalUrl} does not exist`,
    availableEndpoints: [
      'GET /',
      'GET /health',
      'POST /api/notifications/send',
      'GET /api/telegram/status',
      'POST /api/subscriptions/telegram'
    ]
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Initialize services and start server
async function startServer() {
  try {
    logger.info('Initializing Notification Service...');

    // Initialize database connection
    await initializeDatabase();
    logger.info('Database connection established');

    // Initialize Telegram bot
    await initializeTelegramBot();
    logger.info('Telegram bot initialized');

    // Initialize email service
    await initializeEmailService();
    logger.info('Email service initialized');

    // Start queue processor
    processNotificationQueue(notificationQueue);
    logger.info('Notification queue processor started');

    // Start server
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Notification Service running on port ${PORT}`);
      logger.info(`Environment: ${process.env.NODE_ENV || 'development'}`);
      logger.info(`Health check: http://localhost:${PORT}/health`);

      if (process.env.NODE_ENV === 'development') {
        logger.info(`Queue dashboard: http://localhost:${PORT}/admin/queues`);
      }
    });

    // Graceful shutdown
    const gracefulShutdown = () => {
      logger.info('Received shutdown signal, closing server...');

      server.close(() => {
        logger.info('HTTP server closed');

        // Close queue
        notificationQueue.close().then(() => {
          logger.info('Queue closed');
          process.exit(0);
        });
      });
    };

    process.on('SIGTERM', gracefulShutdown);
    process.on('SIGINT', gracefulShutdown);

    // Make queue available to routes
    app.locals.notificationQueue = notificationQueue;

    return server;
  } catch (error) {
    logger.error('Failed to start Notification Service:', error);
    process.exit(1);
  }
}

// Start server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer, notificationQueue };