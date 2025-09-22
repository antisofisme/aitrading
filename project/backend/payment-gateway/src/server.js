const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const morgan = require('morgan');
const rateLimit = require('express-rate-limit');
const winston = require('winston');
require('dotenv').config();

// Import routes
const paymentRoutes = require('./routes/payments');
const webhookRoutes = require('./routes/webhooks');
const methodRoutes = require('./routes/methods');
const healthRoutes = require('./routes/health');

// Import middleware
const errorHandler = require('./middleware/errorHandler');
const authMiddleware = require('./middleware/auth');
const loggingMiddleware = require('./middleware/logging');
const webhookVerification = require('./middleware/webhookVerification');

// Import services
const { initializeDatabase } = require('./database/connection');
const { initializeMidtrans } = require('./services/midtransService');

// Configure logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'payment-gateway' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

const app = express();
const PORT = process.env.PORT || 8023;

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

// Rate limiting (more restrictive for payment service)
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 50, // Limit each IP to 50 requests per windowMs (lower for payments)
  message: {
    error: 'Too many payment requests from this IP, please try again later.',
    retryAfter: '15 minutes'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Stricter rate limiting for payment creation
const paymentLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 5, // Only 5 payment attempts per 5 minutes
  message: {
    error: 'Too many payment attempts, please try again later.',
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
  allowedHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-User-ID', 'X-Signature']
}));

// Body parsing - special handling for webhooks
app.use('/api/webhooks', express.raw({ type: 'application/json' }));
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

// Webhook routes (no auth required, but signature verification)
app.use('/api/webhooks', webhookVerification, webhookRoutes);

// Apply rate limiting
app.use('/api/payments', paymentLimiter);
app.use(limiter);

// Routes with authentication
app.use('/api/payments', authMiddleware, paymentRoutes);
app.use('/api/methods', authMiddleware, methodRoutes);

// Root endpoint
app.get('/', (req, res) => {
  res.json({
    service: 'Payment Gateway Service',
    version: '1.0.0',
    status: 'operational',
    endpoints: {
      payments: '/api/payments',
      webhooks: '/api/webhooks',
      methods: '/api/methods',
      health: '/health'
    },
    features: {
      midtransIntegration: 'enabled',
      indonesianPayments: 'enabled',
      webhookProcessing: 'enabled',
      securePayments: 'enabled'
    },
    supportedMethods: [
      'credit_card',
      'bank_transfer',
      'e_wallet',
      'virtual_account',
      'convenience_store'
    ]
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
      'POST /api/payments/create',
      'GET /api/payments',
      'GET /api/methods'
    ]
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Initialize services and start server
async function startServer() {
  try {
    logger.info('Initializing Payment Gateway Service...');

    // Initialize database connection
    await initializeDatabase();
    logger.info('Database connection established');

    // Initialize Midtrans service
    await initializeMidtrans();
    logger.info('Midtrans service initialized');

    // Start server
    const server = app.listen(PORT, '0.0.0.0', () => {
      logger.info(`Payment Gateway Service running on port ${PORT}`);
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
    logger.error('Failed to start Payment Gateway Service:', error);
    process.exit(1);
  }
}

// Start server if this file is run directly
if (require.main === module) {
  startServer();
}

module.exports = { app, startServer };