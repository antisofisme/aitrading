/**
 * Health Check Routes for AI Orchestrator
 * Provides health, readiness, and status endpoints
 */

const express = require('express');
const router = express.Router();

// Health check endpoint
router.get('/', async (req, res) => {
  try {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'ai-orchestrator',
      port: process.env.PORT || 8020,
      environment: process.env.NODE_ENV || 'development',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: '1.0.0',
      level: 'level4-intelligence'
    };

    // Add database health if available
    if (global.dbPool) {
      try {
        const dbHealth = await global.dbPool.healthCheck();
        health.database = dbHealth;
      } catch (error) {
        health.database = { healthy: false, error: error.message };
        health.status = 'degraded';
      }
    }

    // Add DragonflyDB/Redis health if available
    if (global.redisClient) {
      try {
        await global.redisClient.ping();
        health.dragonfly = { healthy: true };
      } catch (error) {
        health.dragonfly = { healthy: false, error: error.message };
        health.status = 'degraded';
      }
    }

    // Add Configuration Service connectivity
    if (process.env.CONFIG_SERVICE_ENABLED === 'true') {
      health.configService = {
        url: process.env.CONFIG_SERVICE_URL,
        enabled: true
      };
    }

    res.json(health);
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Readiness check
router.get('/ready', async (req, res) => {
  try {
    const readiness = {
      ready: true,
      timestamp: new Date().toISOString(),
      checks: []
    };

    // Database readiness
    if (global.dbPool) {
      try {
        await global.dbPool.healthCheck();
        readiness.checks.push({ name: 'database', ready: true });
      } catch (error) {
        readiness.checks.push({ name: 'database', ready: false, error: error.message });
        readiness.ready = false;
      }
    }

    // DragonflyDB readiness
    if (global.redisClient) {
      try {
        await global.redisClient.ping();
        readiness.checks.push({ name: 'dragonfly', ready: true });
      } catch (error) {
        readiness.checks.push({ name: 'dragonfly', ready: false, error: error.message });
        readiness.ready = false;
      }
    }

    const statusCode = readiness.ready ? 200 : 503;
    res.status(statusCode).json(readiness);
  } catch (error) {
    res.status(503).json({
      ready: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Liveness check
router.get('/live', (req, res) => {
  res.json({
    alive: true,
    timestamp: new Date().toISOString(),
    service: 'ai-orchestrator'
  });
});

module.exports = router;