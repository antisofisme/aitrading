const { verifyAccessToken } = require('../services/tokenService');
const { getUserById } = require('../services/userService');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'user-management-auth-middleware' }
});

/**
 * Authentication middleware
 * Verifies JWT token and attaches user to request
 */
async function authMiddleware(req, res, next) {
  try {
    // Get token from Authorization header
    const authHeader = req.headers.authorization;
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        error: 'Access denied',
        message: 'No token provided or invalid format. Use "Bearer <token>"'
      });
    }

    const token = authHeader.slice(7); // Remove 'Bearer ' prefix

    // Verify token
    const decoded = verifyAccessToken(token);
    if (!decoded) {
      return res.status(401).json({
        success: false,
        error: 'Invalid token',
        message: 'Token is invalid or expired'
      });
    }

    // Get user from database to ensure they still exist and are active
    const user = await getUserById(decoded.userId);
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'User not found',
        message: 'User associated with token no longer exists'
      });
    }

    if (!user.isActive) {
      return res.status(403).json({
        success: false,
        error: 'Account disabled',
        message: 'Your account has been disabled. Please contact support.'
      });
    }

    // Attach user to request object (without password)
    req.user = {
      id: user.id,
      email: user.email,
      firstName: user.firstName,
      lastName: user.lastName,
      subscription: user.subscription,
      emailVerified: user.emailVerified,
      isActive: user.isActive
    };

    // Attach token info
    req.token = {
      userId: decoded.userId,
      email: decoded.email,
      subscription: decoded.subscription,
      iat: decoded.iat,
      exp: decoded.exp
    };

    next();

  } catch (error) {
    logger.error('Authentication middleware error:', error);
    res.status(500).json({
      success: false,
      error: 'Authentication failed',
      message: 'An error occurred during authentication'
    });
  }
}

/**
 * Optional authentication middleware
 * Attaches user if token is valid, but doesn't require authentication
 */
async function optionalAuthMiddleware(req, res, next) {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      // No token provided, continue without user
      return next();
    }

    const token = authHeader.slice(7);
    const decoded = verifyAccessToken(token);

    if (decoded) {
      const user = await getUserById(decoded.userId);
      if (user && user.isActive) {
        req.user = {
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          subscription: user.subscription,
          emailVerified: user.emailVerified,
          isActive: user.isActive
        };
      }
    }

    next();

  } catch (error) {
    // Log error but continue without user
    logger.warn('Optional authentication failed:', error.message);
    next();
  }
}

/**
 * Subscription tier middleware
 * Requires specific subscription tier or higher
 */
function requireSubscription(requiredTier) {
  const tierLevels = {
    'FREE': 0,
    'BASIC': 1,
    'PREMIUM': 2,
    'ENTERPRISE': 3
  };

  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        message: 'This endpoint requires authentication'
      });
    }

    const userTierLevel = tierLevels[req.user.subscription] || 0;
    const requiredTierLevel = tierLevels[requiredTier] || 0;

    if (userTierLevel < requiredTierLevel) {
      return res.status(403).json({
        success: false,
        error: 'Insufficient subscription',
        message: `This feature requires ${requiredTier} subscription or higher. Your current tier: ${req.user.subscription}`,
        requiredTier,
        currentTier: req.user.subscription
      });
    }

    next();
  };
}

/**
 * Email verification middleware
 * Requires verified email address
 */
function requireEmailVerification(req, res, next) {
  if (!req.user) {
    return res.status(401).json({
      success: false,
      error: 'Authentication required',
      message: 'This endpoint requires authentication'
    });
  }

  if (!req.user.emailVerified) {
    return res.status(403).json({
      success: false,
      error: 'Email verification required',
      message: 'Please verify your email address to access this feature'
    });
  }

  next();
}

/**
 * Admin middleware
 * Checks if user has admin role (for future use)
 */
function requireAdmin(req, res, next) {
  if (!req.user) {
    return res.status(401).json({
      success: false,
      error: 'Authentication required',
      message: 'This endpoint requires authentication'
    });
  }

  // For now, check if user has ENTERPRISE subscription as admin proxy
  // In future, implement proper role-based access control
  if (req.user.subscription !== 'ENTERPRISE') {
    return res.status(403).json({
      success: false,
      error: 'Admin access required',
      message: 'This endpoint requires admin privileges'
    });
  }

  next();
}

/**
 * Rate limiting middleware per user
 * Implements per-user rate limiting based on subscription tier
 */
function createUserRateLimit(redis) {
  const tierLimits = {
    'FREE': { windowMs: 15 * 60 * 1000, max: 10 }, // 10 requests per 15 minutes
    'BASIC': { windowMs: 15 * 60 * 1000, max: 50 }, // 50 requests per 15 minutes
    'PREMIUM': { windowMs: 15 * 60 * 1000, max: 200 }, // 200 requests per 15 minutes
    'ENTERPRISE': { windowMs: 15 * 60 * 1000, max: 1000 } // 1000 requests per 15 minutes
  };

  return async (req, res, next) => {
    try {
      if (!req.user) {
        return next(); // Let authMiddleware handle it
      }

      const userTier = req.user.subscription || 'FREE';
      const limits = tierLimits[userTier] || tierLimits['FREE'];

      const key = `rate_limit:${req.user.id}:${Math.floor(Date.now() / limits.windowMs)}`;

      // Get current count
      const currentCount = await redis.get(key) || 0;

      if (parseInt(currentCount) >= limits.max) {
        return res.status(429).json({
          success: false,
          error: 'Rate limit exceeded',
          message: `Rate limit exceeded for ${userTier} tier. Limit: ${limits.max} requests per ${limits.windowMs / 60000} minutes`,
          retryAfter: Math.ceil(limits.windowMs / 1000)
        });
      }

      // Increment count
      await redis.incr(key);
      await redis.expire(key, Math.ceil(limits.windowMs / 1000));

      // Add rate limit headers
      res.set({
        'X-RateLimit-Limit': limits.max,
        'X-RateLimit-Remaining': Math.max(0, limits.max - parseInt(currentCount) - 1),
        'X-RateLimit-Reset': new Date(Date.now() + limits.windowMs).toISOString()
      });

      next();

    } catch (error) {
      logger.error('User rate limiting error:', error);
      // Continue without rate limiting on error
      next();
    }
  };
}

module.exports = {
  authMiddleware,
  optionalAuthMiddleware,
  requireSubscription,
  requireEmailVerification,
  requireAdmin,
  createUserRateLimit
};