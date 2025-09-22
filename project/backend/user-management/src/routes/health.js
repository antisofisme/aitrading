const express = require('express');
const { Pool } = require('pg');
const router = express.Router();

// Database connection for health check
const pool = new Pool({
  host: process.env.POSTGRES_HOST || 'localhost',
  port: process.env.POSTGRES_PORT || 5432,
  database: process.env.POSTGRES_DB || 'aitrading',
  user: process.env.POSTGRES_USER || 'postgres',
  password: process.env.POSTGRES_PASSWORD || 'aitrading2024',
  max: 1, // Minimal pool for health checks
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// GET /health - Basic health check
router.get('/', async (req, res) => {
  const healthCheck = {
    service: 'user-management',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    dependencies: {}
  };

  try {
    // Check database connection
    const dbStart = Date.now();
    const dbResult = await pool.query('SELECT 1 as health_check');
    const dbTime = Date.now() - dbStart;

    healthCheck.dependencies.database = {
      status: 'healthy',
      responseTime: `${dbTime}ms`,
      connection: 'active'
    };

    // Check if users table exists
    try {
      await pool.query('SELECT COUNT(*) FROM users LIMIT 1');
      healthCheck.dependencies.database.usersTable = 'accessible';
    } catch (error) {
      healthCheck.dependencies.database.usersTable = 'not_accessible';
      healthCheck.dependencies.database.error = error.message;
    }

  } catch (error) {
    healthCheck.status = 'unhealthy';
    healthCheck.dependencies.database = {
      status: 'unhealthy',
      error: error.message,
      connection: 'failed'
    };
  }

  // Check environment variables
  const requiredEnvVars = ['JWT_SECRET', 'POSTGRES_HOST', 'POSTGRES_DB'];
  const missingEnvVars = requiredEnvVars.filter(envVar => !process.env[envVar]);

  if (missingEnvVars.length > 0) {
    healthCheck.status = 'unhealthy';
    healthCheck.dependencies.environment = {
      status: 'unhealthy',
      missingVariables: missingEnvVars
    };
  } else {
    healthCheck.dependencies.environment = {
      status: 'healthy',
      configuredVariables: requiredEnvVars.length
    };
  }

  // Set response status based on overall health
  const statusCode = healthCheck.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(healthCheck);
});

// GET /health/detailed - Detailed health check
router.get('/detailed', async (req, res) => {
  const detailedHealth = {
    service: 'user-management',
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    server: {
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: process.cpuUsage(),
      platform: process.platform,
      nodeVersion: process.version,
      pid: process.pid
    },
    dependencies: {},
    metrics: {}
  };

  try {
    // Database detailed check
    const dbChecks = await Promise.allSettled([
      pool.query('SELECT version()'),
      pool.query('SELECT COUNT(*) FROM users'),
      pool.query('SELECT COUNT(*) FROM users WHERE created_at > NOW() - INTERVAL \'24 hours\''),
    ]);

    const dbVersion = dbChecks[0].status === 'fulfilled' ? dbChecks[0].value.rows[0].version : 'unknown';
    const totalUsers = dbChecks[1].status === 'fulfilled' ? dbChecks[1].value.rows[0].count : 'unknown';
    const recentUsers = dbChecks[2].status === 'fulfilled' ? dbChecks[2].value.rows[0].count : 'unknown';

    detailedHealth.dependencies.database = {
      status: 'healthy',
      version: dbVersion,
      connectionPool: {
        total: pool.totalCount,
        idle: pool.idleCount,
        waiting: pool.waitingCount
      }
    };

    detailedHealth.metrics = {
      totalUsers,
      usersLast24h: recentUsers,
      lastCheck: new Date().toISOString()
    };

  } catch (error) {
    detailedHealth.status = 'unhealthy';
    detailedHealth.dependencies.database = {
      status: 'unhealthy',
      error: error.message
    };
  }

  // JWT Service check
  try {
    const jwt = require('jsonwebtoken');
    const testToken = jwt.sign({ test: true }, process.env.JWT_SECRET || 'test', { expiresIn: '1s' });
    const decoded = jwt.verify(testToken, process.env.JWT_SECRET || 'test');

    detailedHealth.dependencies.jwt = {
      status: 'healthy',
      canSignAndVerify: true
    };
  } catch (error) {
    detailedHealth.status = 'unhealthy';
    detailedHealth.dependencies.jwt = {
      status: 'unhealthy',
      error: error.message
    };
  }

  // Email service check (if configured)
  if (process.env.SMTP_HOST) {
    detailedHealth.dependencies.email = {
      status: 'configured',
      host: process.env.SMTP_HOST,
      port: process.env.SMTP_PORT
    };
  } else {
    detailedHealth.dependencies.email = {
      status: 'not_configured',
      message: 'SMTP settings not configured'
    };
  }

  const statusCode = detailedHealth.status === 'healthy' ? 200 : 503;
  res.status(statusCode).json(detailedHealth);
});

// GET /health/readiness - Kubernetes readiness probe
router.get('/readiness', async (req, res) => {
  try {
    // Quick database check
    await pool.query('SELECT 1');

    res.status(200).json({
      status: 'ready',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      status: 'not_ready',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// GET /health/liveness - Kubernetes liveness probe
router.get('/liveness', (req, res) => {
  res.status(200).json({
    status: 'alive',
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

module.exports = router;