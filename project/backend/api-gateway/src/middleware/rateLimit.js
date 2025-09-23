/**
 * Rate Limiting Middleware for API Gateway
 * Implements multiple rate limiting strategies with DragonflyDB backend
 */

const rateLimit = require('express-rate-limit');
const slowDown = require('express-slow-down');
const Redis = require('ioredis');
const winston = require('winston');

class RateLimitMiddleware {
  constructor(logger) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [new winston.transports.Console()]
    });

    // Initialize DragonflyDB (Redis-compatible) connection
    this.redis = new Redis({
      host: process.env.DRAGONFLY_HOST || 'localhost',
      port: process.env.DRAGONFLY_PORT || 6379,
      password: process.env.DRAGONFLY_PASSWORD || 'dragonfly_secure_pass_2024',
      maxRetriesPerRequest: 3,
      retryDelayOnFailover: 100,
      enableReadyCheck: false,
      maxRetriesPerRequest: null
    });

    // Rate limiting configuration from environment
    this.config = {
      windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 900000, // 15 minutes
      maxRequests: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
      skipSuccessfulRequests: false,
      skipFailedRequests: false,
      keyGenerator: this.defaultKeyGenerator.bind(this)
    };

    this.setupRedisEventHandlers();
  }

  /**
   * Setup Redis event handlers
   */
  setupRedisEventHandlers() {
    this.redis.on('connect', () => {
      this.logger.info('DragonflyDB connected for rate limiting');
    });

    this.redis.on('error', (error) => {
      this.logger.error('DragonflyDB error', {
        error: error.message,
        component: 'rate-limiting'
      });
    });

    this.redis.on('close', () => {
      this.logger.warn('DragonflyDB connection closed');
    });
  }

  /**
   * Default key generator for rate limiting
   */
  defaultKeyGenerator(req) {
    // Use user ID if authenticated, otherwise IP
    const userId = req.user?.id || req.headers['user-id'];
    const tenantId = req.user?.tenantId || req.headers['tenant-id'];

    if (userId && tenantId) {
      return `rate_limit:user:${tenantId}:${userId}`;
    }

    // Fallback to IP-based limiting
    return `rate_limit:ip:${req.ip}`;
  }

  /**
   * Create Redis store for rate limiting
   */
  createRedisStore() {
    return {
      incr: async (key, cb) => {
        try {
          const multi = this.redis.multi();
          multi.incr(key);
          multi.expire(key, Math.ceil(this.config.windowMs / 1000));
          const results = await multi.exec();

          const count = results[0][1];
          cb(null, count, new Date(Date.now() + this.config.windowMs));
        } catch (error) {
          this.logger.error('Redis incr error', {
            error: error.message,
            key
          });
          cb(error);
        }
      },

      decrement: async (key) => {
        try {
          await this.redis.decr(key);
        } catch (error) {
          this.logger.error('Redis decr error', {
            error: error.message,
            key
          });
        }
      },

      resetKey: async (key) => {
        try {
          await this.redis.del(key);
        } catch (error) {
          this.logger.error('Redis resetKey error', {
            error: error.message,
            key
          });
        }
      }
    };
  }

  /**
   * General rate limiting middleware
   */
  general = () => {
    return rateLimit({
      windowMs: this.config.windowMs,
      max: this.config.maxRequests,
      keyGenerator: this.config.keyGenerator,
      store: this.createRedisStore(),
      handler: (req, res) => {
        const userId = req.user?.id || 'anonymous';
        const tenantId = req.user?.tenantId || 'none';

        this.logger.warn('Rate limit exceeded', {
          userId,
          tenantId,
          ip: req.ip,
          path: req.path,
          userAgent: req.get('User-Agent'),
          requestId: req.requestId
        });

        res.status(429).json({
          error: 'Too many requests',
          message: `Rate limit exceeded. Try again in ${Math.ceil(this.config.windowMs / 1000)} seconds.`,
          code: 'RATE_LIMIT_EXCEEDED',
          retryAfter: Math.ceil(this.config.windowMs / 1000),
          timestamp: new Date().toISOString()
        });
      },
      skip: (req) => {
        // Skip rate limiting for health checks
        return req.path === '/health' || req.path === '/api/status';
      }
    });
  };

  /**
   * Strict rate limiting for authentication endpoints
   */
  auth = () => {
    return rateLimit({
      windowMs: 900000, // 15 minutes
      max: 5, // 5 attempts per 15 minutes
      keyGenerator: (req) => `auth_limit:${req.ip}`,
      store: this.createRedisStore(),
      handler: (req, res) => {
        this.logger.warn('Auth rate limit exceeded', {
          ip: req.ip,
          path: req.path,
          userAgent: req.get('User-Agent'),
          requestId: req.requestId
        });

        res.status(429).json({
          error: 'Too many authentication attempts',
          message: 'Please wait 15 minutes before trying again.',
          code: 'AUTH_RATE_LIMIT_EXCEEDED',
          retryAfter: 900,
          timestamp: new Date().toISOString()
        });
      }
    });
  };

  /**
   * Trading-specific rate limiting (more restrictive)
   */
  trading = () => {
    return rateLimit({
      windowMs: 60000, // 1 minute
      max: 10, // 10 trading requests per minute
      keyGenerator: (req) => {
        const userId = req.user?.id || req.headers['user-id'];
        const tenantId = req.user?.tenantId || req.headers['tenant-id'];
        return `trading_limit:${tenantId}:${userId}`;
      },
      store: this.createRedisStore(),
      handler: (req, res) => {
        const userId = req.user?.id || 'anonymous';
        const tenantId = req.user?.tenantId || 'none';

        this.logger.warn('Trading rate limit exceeded', {
          userId,
          tenantId,
          ip: req.ip,
          path: req.path,
          requestId: req.requestId
        });

        res.status(429).json({
          error: 'Trading rate limit exceeded',
          message: 'Too many trading requests. Please slow down.',
          code: 'TRADING_RATE_LIMIT_EXCEEDED',
          retryAfter: 60,
          timestamp: new Date().toISOString()
        });
      }
    });
  };

  /**
   * AI/ML endpoints rate limiting (resource intensive)
   */
  aiMl = () => {
    return rateLimit({
      windowMs: 300000, // 5 minutes
      max: 20, // 20 AI requests per 5 minutes
      keyGenerator: (req) => {
        const userId = req.user?.id || req.headers['user-id'];
        const tenantId = req.user?.tenantId || req.headers['tenant-id'];
        return `ai_limit:${tenantId}:${userId}`;
      },
      store: this.createRedisStore(),
      handler: (req, res) => {
        const userId = req.user?.id || 'anonymous';
        const tenantId = req.user?.tenantId || 'none';

        this.logger.warn('AI/ML rate limit exceeded', {
          userId,
          tenantId,
          ip: req.ip,
          path: req.path,
          requestId: req.requestId
        });

        res.status(429).json({
          error: 'AI/ML rate limit exceeded',
          message: 'AI requests are resource intensive. Please wait before making more requests.',
          code: 'AI_RATE_LIMIT_EXCEEDED',
          retryAfter: 300,
          timestamp: new Date().toISOString()
        });
      }
    });
  };

  /**
   * Slow down middleware (gradually increases delay)
   */
  slowDown = () => {
    return slowDown({
      windowMs: this.config.windowMs,
      delayAfter: Math.floor(this.config.maxRequests * 0.7), // Start slowing down after 70% of limit
      delayMs: 500, // Add 500ms delay per request
      maxDelayMs: 20000, // Maximum delay of 20 seconds
      keyGenerator: this.config.keyGenerator,
      skip: (req) => {
        return req.path === '/health' || req.path === '/api/status';
      },
      onLimitReached: (req, res, options) => {
        const userId = req.user?.id || 'anonymous';
        const tenantId = req.user?.tenantId || 'none';

        this.logger.info('Slow down limit reached', {
          userId,
          tenantId,
          ip: req.ip,
          path: req.path,
          delay: options.delay,
          requestId: req.requestId
        });
      }
    });
  };

  /**
   * Get rate limit stats for monitoring
   */
  async getStats() {
    try {
      const keys = await this.redis.keys('rate_limit:*');
      const stats = {
        totalKeys: keys.length,
        activeUsers: 0,
        activeIPs: 0,
        keysByType: {}
      };

      for (const key of keys) {
        const parts = key.split(':');
        const type = parts[2]; // user or ip

        if (!stats.keysByType[type]) {
          stats.keysByType[type] = 0;
        }
        stats.keysByType[type]++;

        if (type === 'user') stats.activeUsers++;
        if (type === 'ip') stats.activeIPs++;
      }

      return stats;
    } catch (error) {
      this.logger.error('Failed to get rate limit stats', {
        error: error.message
      });
      return { error: 'Failed to retrieve stats' };
    }
  }

  /**
   * Clear rate limits for a specific user (admin function)
   */
  async clearUserLimits(userId, tenantId) {
    try {
      const patterns = [
        `rate_limit:user:${tenantId}:${userId}`,
        `auth_limit:user:${tenantId}:${userId}`,
        `trading_limit:${tenantId}:${userId}`,
        `ai_limit:${tenantId}:${userId}`
      ];

      for (const pattern of patterns) {
        await this.redis.del(pattern);
      }

      this.logger.info('Cleared rate limits for user', {
        userId,
        tenantId
      });

      return { success: true, message: 'Rate limits cleared' };
    } catch (error) {
      this.logger.error('Failed to clear user rate limits', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Check current rate limit status for a user
   */
  async checkUserLimits(userId, tenantId) {
    try {
      const keys = [
        `rate_limit:user:${tenantId}:${userId}`,
        `trading_limit:${tenantId}:${userId}`,
        `ai_limit:${tenantId}:${userId}`
      ];

      const limits = {};
      for (const key of keys) {
        const count = await this.redis.get(key);
        const ttl = await this.redis.ttl(key);

        limits[key] = {
          count: parseInt(count) || 0,
          ttl: ttl > 0 ? ttl : null
        };
      }

      return limits;
    } catch (error) {
      this.logger.error('Failed to check user limits', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Cleanup expired keys (called periodically)
   */
  async cleanup() {
    try {
      const keys = await this.redis.keys('rate_limit:*');
      let cleanedCount = 0;

      for (const key of keys) {
        const ttl = await this.redis.ttl(key);
        if (ttl === -1) { // Key exists but has no expiry
          await this.redis.expire(key, Math.ceil(this.config.windowMs / 1000));
        } else if (ttl === -2) { // Key doesn't exist
          cleanedCount++;
        }
      }

      this.logger.info('Rate limit cleanup completed', {
        totalKeys: keys.length,
        cleanedKeys: cleanedCount
      });

      return { totalKeys: keys.length, cleanedKeys: cleanedCount };
    } catch (error) {
      this.logger.error('Rate limit cleanup failed', {
        error: error.message
      });
      throw error;
    }
  }
}

module.exports = RateLimitMiddleware;