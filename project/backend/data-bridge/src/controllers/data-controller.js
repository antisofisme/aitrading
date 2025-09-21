const logger = require('../utils/logger');
const { checkRateLimit } = require('../middleware/validation');
const config = require('../../config/config');

class DataController {
  constructor() {
    this.mt5Service = null;
  }

  // Set MT5 service reference
  setMT5Service(mt5Service) {
    this.mt5Service = mt5Service;
  }

  async getStatus(req, res) {
    try {
      const clientIP = req.ip;

      // Rate limiting
      if (!checkRateLimit(clientIP, config.security.rateLimitWindow, config.security.rateLimitMax)) {
        logger.warn(`Rate limit exceeded for IP: ${clientIP}`);
        return res.status(429).json({
          error: 'Rate limit exceeded',
          message: 'Too many requests. Please try again later.'
        });
      }

      const status = {
        service: 'data-bridge',
        version: process.env.npm_package_version || '1.0.0',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        environment: config.server.environment,
        mt5: this.mt5Service ? this.mt5Service.getConnectionStatus() : {
          connected: false,
          error: 'MT5 service not initialized'
        },
        websocket: {
          maxConnections: config.websocket.maxConnections,
          compression: config.websocket.compression
        },
        memory: {
          used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
          total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
          external: Math.round(process.memoryUsage().external / 1024 / 1024)
        },
        system: {
          platform: process.platform,
          nodeVersion: process.version,
          pid: process.pid
        }
      };

      logger.info('Status request processed', { ip: clientIP });
      res.json(status);

    } catch (error) {
      logger.error('Error getting status:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: 'Failed to get service status'
      });
    }
  }

  async getSymbols(req, res) {
    try {
      const clientIP = req.ip;

      // Rate limiting
      if (!checkRateLimit(clientIP, config.security.rateLimitWindow, config.security.rateLimitMax)) {
        logger.warn(`Rate limit exceeded for IP: ${clientIP}`);
        return res.status(429).json({
          error: 'Rate limit exceeded',
          message: 'Too many requests. Please try again later.'
        });
      }

      if (!this.mt5Service || !this.mt5Service.isConnected()) {
        return res.status(503).json({
          error: 'Service unavailable',
          message: 'MT5 connection not available'
        });
      }

      const symbols = await this.mt5Service.getSymbols();

      logger.info('Symbols request processed', {
        ip: clientIP,
        symbolCount: symbols.length
      });

      res.json({
        symbols,
        timestamp: new Date().toISOString(),
        count: symbols.length
      });

    } catch (error) {
      logger.error('Error getting symbols:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: 'Failed to get symbols list'
      });
    }
  }

  async getMarketData(req, res) {
    try {
      const clientIP = req.ip;
      const { symbol } = req.params;
      const { from, to, limit = 100 } = req.query;

      // Rate limiting
      if (!checkRateLimit(clientIP, config.security.rateLimitWindow, config.security.rateLimitMax)) {
        logger.warn(`Rate limit exceeded for IP: ${clientIP}`);
        return res.status(429).json({
          error: 'Rate limit exceeded',
          message: 'Too many requests. Please try again later.'
        });
      }

      // Validate symbol format
      if (!symbol || !/^[A-Z]{6}$/.test(symbol)) {
        return res.status(400).json({
          error: 'Invalid symbol',
          message: 'Symbol must be 6 uppercase letters (e.g., EURUSD)'
        });
      }

      // Validate limit
      const parsedLimit = parseInt(limit);
      if (isNaN(parsedLimit) || parsedLimit < 1 || parsedLimit > 10000) {
        return res.status(400).json({
          error: 'Invalid limit',
          message: 'Limit must be between 1 and 10000'
        });
      }

      // Validate date range
      let fromDate = null;
      let toDate = null;

      if (from) {
        fromDate = new Date(from);
        if (isNaN(fromDate.getTime())) {
          return res.status(400).json({
            error: 'Invalid from date',
            message: 'From date must be a valid ISO date string'
          });
        }
      }

      if (to) {
        toDate = new Date(to);
        if (isNaN(toDate.getTime())) {
          return res.status(400).json({
            error: 'Invalid to date',
            message: 'To date must be a valid ISO date string'
          });
        }
      }

      if (fromDate && toDate && fromDate >= toDate) {
        return res.status(400).json({
          error: 'Invalid date range',
          message: 'From date must be before to date'
        });
      }

      if (!this.mt5Service || !this.mt5Service.isConnected()) {
        return res.status(503).json({
          error: 'Service unavailable',
          message: 'MT5 connection not available'
        });
      }

      const startTime = Date.now();
      const marketData = await this.mt5Service.getMarketData(
        symbol,
        fromDate,
        toDate,
        parsedLimit
      );
      const duration = Date.now() - startTime;

      logger.performance.latency('getMarketData', duration, {
        symbol,
        dataPoints: marketData.length,
        ip: clientIP
      });

      logger.info('Market data request processed', {
        ip: clientIP,
        symbol,
        dataPoints: marketData.length,
        duration
      });

      res.json({
        symbol,
        data: marketData,
        metadata: {
          count: marketData.length,
          from: fromDate ? fromDate.toISOString() : null,
          to: toDate ? toDate.toISOString() : null,
          requestedAt: new Date().toISOString(),
          processingTime: `${duration}ms`
        }
      });

    } catch (error) {
      logger.error('Error getting market data:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: 'Failed to get market data'
      });
    }
  }

  async getHealth(req, res) {
    try {
      const health = {
        status: 'healthy',
        timestamp: new Date().toISOString(),
        checks: {
          mt5Connection: this.mt5Service ? this.mt5Service.isConnected() : false,
          memory: this.checkMemoryHealth(),
          uptime: process.uptime() > 0
        }
      };

      // Determine overall health
      const allChecksPass = Object.values(health.checks).every(check => check === true);
      health.status = allChecksPass ? 'healthy' : 'unhealthy';

      const statusCode = allChecksPass ? 200 : 503;
      res.status(statusCode).json(health);

    } catch (error) {
      logger.error('Error during health check:', error);
      res.status(500).json({
        status: 'error',
        timestamp: new Date().toISOString(),
        error: 'Health check failed'
      });
    }
  }

  checkMemoryHealth() {
    const memUsage = process.memoryUsage();
    const heapUsedMB = memUsage.heapUsed / 1024 / 1024;
    const heapTotalMB = memUsage.heapTotal / 1024 / 1024;

    // Consider unhealthy if using more than 80% of allocated heap
    const memoryUtilization = heapUsedMB / heapTotalMB;
    return memoryUtilization < 0.8;
  }

  // Metrics endpoint for monitoring
  async getMetrics(req, res) {
    try {
      const memUsage = process.memoryUsage();
      const cpuUsage = process.cpuUsage();

      const metrics = {
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        memory: {
          heapUsed: Math.round(memUsage.heapUsed / 1024 / 1024),
          heapTotal: Math.round(memUsage.heapTotal / 1024 / 1024),
          external: Math.round(memUsage.external / 1024 / 1024),
          rss: Math.round(memUsage.rss / 1024 / 1024)
        },
        cpu: {
          user: cpuUsage.user,
          system: cpuUsage.system
        },
        mt5: this.mt5Service ? {
          connected: this.mt5Service.isConnected(),
          subscriptions: this.mt5Service.subscriptions ? this.mt5Service.subscriptions.size : 0
        } : null,
        process: {
          pid: process.pid,
          version: process.version,
          platform: process.platform
        }
      };

      res.json(metrics);

    } catch (error) {
      logger.error('Error getting metrics:', error);
      res.status(500).json({
        error: 'Internal server error',
        message: 'Failed to get metrics'
      });
    }
  }
}

module.exports = DataController;