/**
 * API Gateway Server
 * Main entry point for JWT Authentication System
 */

require('dotenv').config();
const express = require('express');
const morgan = require('morgan');
const User = require('../models/User');
const {
  authRateLimit,
  cors,
  helmet,
  sanitizeInput,
  validateRequest,
  handleSecurityError
} = require('../middleware/security');

// Import routes
const authRoutes = require('../routes/auth');
// const userRoutes = require('../routes/users'); // Temporarily disabled for basic test

// Create Express app
const app = express();

// Security middleware
app.use(helmet);
app.use(cors);
app.use(authRateLimit);

// Request parsing middleware
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ extended: true, limit: '1mb' }));

// Request logging
app.use(morgan('combined'));

// Request sanitization and validation
app.use(sanitizeInput);
app.use(validateRequest);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    success: true,
    message: 'API Gateway is healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
  });
});

// API documentation endpoint
app.get('/api', (req, res) => {
  res.json({
    success: true,
    message: 'AI Trading Platform API Gateway',
    version: '1.0.0',
    documentation: {
      auth: {
        login: 'POST /api/auth/login',
        logout: 'POST /api/auth/logout',
        refresh: 'POST /api/auth/refresh',
        profile: 'GET /api/auth/me',
        updateProfile: 'PUT /api/auth/me',
        register: 'POST /api/auth/register (admin only)',
        sessions: 'GET /api/auth/sessions',
        changePassword: 'POST /api/auth/change-password'
      },
      users: {
        list: 'GET /api/users (admin only)',
        get: 'GET /api/users/:id',
        create: 'POST /api/users (admin only)',
        update: 'PUT /api/users/:id',
        delete: 'DELETE /api/users/:id (admin only)',
        deactivate: 'POST /api/users/:id/deactivate (admin only)',
        activate: 'POST /api/users/:id/activate (admin only)',
        stats: 'GET /api/users/stats/overview (admin only)'
      }
    },
    authentication: {
      type: 'JWT Bearer Token',
      header: 'Authorization: Bearer <token>',
      accessTokenExpiry: '15 minutes',
      refreshTokenExpiry: '7 days'
    },
    defaultCredentials: {
      admin: {
        email: 'admin@aitrading.com',
        password: 'Admin123!'
      },
      user: {
        email: 'user@aitrading.com',
        password: 'User123!'
      }
    }
  });
});

// Mount API routes
app.use('/api/auth', authRoutes);
// app.use('/api/users', userRoutes); // Temporarily disabled for basic test

// Central Hub integration endpoint
app.get('/api/integration/central-hub', (req, res) => {
  res.json({
    success: true,
    message: 'Central Hub integration ready',
    data: {
      hubUrl: process.env.CENTRAL_HUB_URL || 'http://localhost:3000',
      apiKey: process.env.CENTRAL_HUB_API_KEY ? '[CONFIGURED]' : '[NOT_CONFIGURED]',
      status: 'Phase 1 - Basic Integration Ready'
    }
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    message: 'Endpoint not found',
    code: 'ENDPOINT_NOT_FOUND',
    path: req.originalUrl,
    method: req.method
  });
});

// Security error handler
app.use(handleSecurityError);

// Global error handler
app.use((err, req, res, next) => {
  console.error('Unhandled error:', err);

  // Don't leak error details in production
  const isDevelopment = process.env.NODE_ENV === 'development';

  res.status(err.status || 500).json({
    success: false,
    message: isDevelopment ? err.message : 'Internal server error',
    code: 'INTERNAL_ERROR',
    ...(isDevelopment && { stack: err.stack })
  });
});

// Initialize default users and start server
const PORT = process.env.PORT || 3001;

async function startServer() {
  try {
    // Initialize default users
    await User.initializeDefaultUsers();

    // Start server
    app.listen(PORT, () => {
      console.log(`🚀 API Gateway server running on port ${PORT}`);
      console.log(`📋 Environment: ${process.env.NODE_ENV || 'development'}`);
      console.log(`🔒 JWT Auth System: Active`);
      console.log(`🏥 Health Check: http://localhost:${PORT}/health`);
      console.log(`📖 API Docs: http://localhost:${PORT}/api`);
      console.log(`🔑 Default Admin: admin@aitrading.com / Admin123!`);
      console.log(`👤 Default User: user@aitrading.com / User123!`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('SIGINT received, shutting down gracefully');
  process.exit(0);
});

// Start the server
startServer();

module.exports = app;