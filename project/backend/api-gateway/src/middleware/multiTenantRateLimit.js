const winston = require('winston');
const { getUserTierLimits } = require('./multiTenantAuth');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'api-gateway-rate-limit' }
});

// In-memory fallback for when Redis is not available
const memoryStore = new Map();
const MEMORY_CLEANUP_INTERVAL = 5 * 60 * 1000; // 5 minutes

// Clean up expired entries from memory store
setInterval(() => {
  const now = Date.now();
  for (const [key, data] of memoryStore.entries()) {
    if (data.resetTime < now) {
      memoryStore.delete(key);
    }
  }
}, MEMORY_CLEANUP_INTERVAL);

/**
 * Multi-tenant rate limiting middleware
 * Implements per-user rate limiting based on subscription tier
 */
function multiTenantRateLimit(redisClient) {
  return async (req, res, next) => {
    try {
      // Skip rate limiting for health checks and public endpoints
      const skipEndpoints = ['/health', '/', '/api/auth/login'];
      if (skipEndpoints.includes(req.path)) {
        return next();
      }

      // Get user information from auth middleware
      const user = req.user;
      if (!user) {
        // Apply anonymous rate limiting
        return applyAnonymousRateLimit(req, res, next, redisClient);
      }

      // Get user tier limits
      const tierLimits = getUserTierLimits(user.subscription);

      // Apply rate limiting based on subscription tier
      const rateLimitResult = await applyUserRateLimit(
        user,
        tierLimits,
        req,
        redisClient
      );

      if (rateLimitResult.limited) {
        return res.status(429).json({
          success: false,
          error: 'Rate limit exceeded',
          message: `Rate limit exceeded for ${user.subscription} tier`,
          details: {
            tier: user.subscription,
            limit: rateLimitResult.limit,
            remaining: rateLimitResult.remaining,
            resetTime: rateLimitResult.resetTime,
            retryAfter: rateLimitResult.retryAfter
          },
          upgradeInfo: user.subscription !== 'ENTERPRISE' ? {
            message: 'Upgrade your subscription for higher rate limits',
            upgradeUrl: '/api/subscriptions'
          } : null
        });
      }

      // Add rate limit headers
      res.set({
        'X-RateLimit-Limit': rateLimitResult.limit,
        'X-RateLimit-Remaining': rateLimitResult.remaining,
        'X-RateLimit-Reset': rateLimitResult.resetTime,
        'X-RateLimit-Tier': user.subscription
      });

      next();

    } catch (error) {
      logger.error('Rate limiting error:', error);
      // Continue without rate limiting on error
      next();
    }
  };
}

/**
 * Apply rate limiting for authenticated users based on their subscription tier
 */
async function applyUserRateLimit(user, tierLimits, req, redisClient) {
  const now = Date.now();
  const windows = [
    { name: 'minute', duration: 60 * 1000, limit: tierLimits.requestsPerMinute },
    { name: 'hour', duration: 60 * 60 * 1000, limit: tierLimits.requestsPerHour },
    { name: 'day', duration: 24 * 60 * 60 * 1000, limit: tierLimits.requestsPerDay }
  ];

  // Check each time window
  for (const window of windows) {
    if (window.limit === 'unlimited') continue;

    const key = `rate_limit:${user.id}:${window.name}:${Math.floor(now / window.duration)}`;
    const count = await getAndIncrementCounter(key, window.duration, redisClient);

    if (count > window.limit) {
      const resetTime = Math.ceil(now / window.duration) * window.duration;
      return {
        limited: true,
        limit: window.limit,
        remaining: 0,
        resetTime: new Date(resetTime).toISOString(),
        retryAfter: Math.ceil((resetTime - now) / 1000),
        window: window.name
      };
    }

    // If this is the most restrictive window that applies, use it for headers
    if (window.name === 'minute') {
      const resetTime = Math.ceil(now / window.duration) * window.duration;
      return {
        limited: false,
        limit: window.limit,
        remaining: Math.max(0, window.limit - count),
        resetTime: new Date(resetTime).toISOString(),
        retryAfter: 0,
        window: window.name
      };
    }
  }

  // Default response (should not reach here)
  return {
    limited: false,
    limit: tierLimits.requestsPerMinute,
    remaining: tierLimits.requestsPerMinute,
    resetTime: new Date(now + 60 * 1000).toISOString(),
    retryAfter: 0,
    window: 'minute'
  };
}

/**
 * Apply rate limiting for anonymous users (more restrictive)
 */
async function applyAnonymousRateLimit(req, res, next, redisClient) {
  const now = Date.now();
  const ip = req.ip || req.connection.remoteAddress;
  const limit = 20; // 20 requests per minute for anonymous users
  const windowDuration = 60 * 1000; // 1 minute

  const key = `rate_limit:anonymous:${ip}:${Math.floor(now / windowDuration)}`;
  const count = await getAndIncrementCounter(key, windowDuration, redisClient);

  if (count > limit) {
    const resetTime = Math.ceil(now / windowDuration) * windowDuration;
    return res.status(429).json({
      success: false,
      error: 'Rate limit exceeded',
      message: 'Rate limit exceeded for anonymous users',
      details: {
        limit,
        remaining: 0,
        resetTime: new Date(resetTime).toISOString(),
        retryAfter: Math.ceil((resetTime - now) / 1000)
      },
      authInfo: {
        message: 'Sign in for higher rate limits',
        loginUrl: '/api/auth/login'
      }
    });
  }

  // Add rate limit headers
  const resetTime = Math.ceil(now / windowDuration) * windowDuration;
  res.set({
    'X-RateLimit-Limit': limit,
    'X-RateLimit-Remaining': Math.max(0, limit - count),
    'X-RateLimit-Reset': new Date(resetTime).toISOString(),
    'X-RateLimit-Tier': 'anonymous'
  });

  next();
}

/**
 * Get and increment counter using Redis or memory fallback
 */
async function getAndIncrementCounter(key, ttl, redisClient) {
  try {
    // Try Redis first
    if (redisClient && redisClient.connected) {
      const count = await redisIncrement(redisClient, key, ttl);
      return count;
    }
  } catch (error) {
    logger.warn('Redis operation failed, falling back to memory store:', error.message);
  }

  // Fallback to memory store
  return memoryIncrement(key, ttl);
}

/**
 * Redis increment operation
 */
async function redisIncrement(redisClient, key, ttl) {
  return new Promise((resolve, reject) => {
    redisClient.multi()
      .incr(key)
      .expire(key, Math.ceil(ttl / 1000))
      .exec((err, results) => {
        if (err) {
          reject(err);
        } else {
          resolve(results[0][1]); // Get the result of INCR command
        }
      });
  });
}

/**
 * Memory store increment operation
 */
function memoryIncrement(key, ttl) {
  const now = Date.now();
  const resetTime = now + ttl;

  if (memoryStore.has(key)) {
    const data = memoryStore.get(key);
    if (data.resetTime > now) {
      data.count++;
      return data.count;
    }
  }

  // Create new entry
  memoryStore.set(key, {
    count: 1,
    resetTime
  });

  return 1;
}

/**
 * Get current rate limit status for a user
 */
async function getRateLimitStatus(userId, subscription, redisClient) {
  const tierLimits = getUserTierLimits(subscription);
  const now = Date.now();

  const status = {
    tier: subscription,
    limits: tierLimits,
    windows: {}
  };

  const windows = [
    { name: 'minute', duration: 60 * 1000, limit: tierLimits.requestsPerMinute },
    { name: 'hour', duration: 60 * 60 * 1000, limit: tierLimits.requestsPerHour },
    { name: 'day', duration: 24 * 60 * 60 * 1000, limit: tierLimits.requestsPerDay }
  ];

  for (const window of windows) {
    if (window.limit === 'unlimited') {
      status.windows[window.name] = {
        limit: 'unlimited',
        remaining: 'unlimited',
        resetTime: null
      };
      continue;
    }

    const key = `rate_limit:${userId}:${window.name}:${Math.floor(now / window.duration)}`;
    let count = 0;

    try {
      if (redisClient && redisClient.connected) {
        count = await new Promise((resolve, reject) => {
          redisClient.get(key, (err, result) => {
            if (err) reject(err);
            else resolve(parseInt(result) || 0);
          });
        });
      } else {
        const data = memoryStore.get(key);
        count = data ? data.count : 0;
      }
    } catch (error) {
      logger.warn(`Error getting rate limit status for ${key}:`, error.message);
    }

    const resetTime = Math.ceil(now / window.duration) * window.duration;
    status.windows[window.name] = {
      limit: window.limit,
      used: count,
      remaining: Math.max(0, window.limit - count),
      resetTime: new Date(resetTime).toISOString()
    };
  }

  return status;
}

/**
 * Reset rate limits for a user (admin function)
 */
async function resetUserRateLimit(userId, redisClient) {
  const patterns = [
    `rate_limit:${userId}:minute:*`,
    `rate_limit:${userId}:hour:*`,
    `rate_limit:${userId}:day:*`
  ];

  try {
    if (redisClient && redisClient.connected) {
      for (const pattern of patterns) {
        const keys = await new Promise((resolve, reject) => {
          redisClient.keys(pattern, (err, result) => {
            if (err) reject(err);
            else resolve(result);
          });
        });

        if (keys.length > 0) {
          await new Promise((resolve, reject) => {
            redisClient.del(keys, (err, result) => {
              if (err) reject(err);
              else resolve(result);
            });
          });
        }
      }
    }

    // Also clear from memory store
    for (const key of memoryStore.keys()) {
      if (key.includes(`rate_limit:${userId}:`)) {
        memoryStore.delete(key);
      }
    }

    logger.info(`Rate limits reset for user: ${userId}`);
    return true;

  } catch (error) {
    logger.error(`Error resetting rate limits for user ${userId}:`, error);
    return false;
  }
}

module.exports = {
  multiTenantRateLimit,
  getRateLimitStatus,
  resetUserRateLimit
};