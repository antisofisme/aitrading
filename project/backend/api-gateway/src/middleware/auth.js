/**
 * JWT Authentication Middleware for API Gateway
 * Integrates with Configuration Service for user validation
 */

const jwt = require('jsonwebtoken');
const axios = require('axios');
const winston = require('winston');

class AuthMiddleware {
  constructor(logger) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.json(),
      transports: [new winston.transports.Console()]
    });

    this.jwtSecret = process.env.JWT_SECRET || 'ai_trading_jwt_super_secret_key_change_in_production_2024';
    this.configServiceUrl = process.env.CONFIG_SERVICE_URL || 'http://localhost:8012';

    // Cache for user validation (30 second TTL)
    this.userCache = new Map();
    this.cacheTimeout = 30000; // 30 seconds
  }

  /**
   * JWT Authentication middleware
   */
  authenticate = (options = {}) => {
    const { required = true, skipPaths = [] } = options;

    return async (req, res, next) => {
      const startTime = Date.now();

      try {
        // Skip authentication for certain paths
        if (skipPaths.some(path => req.path.startsWith(path))) {
          return next();
        }

        const token = this.extractToken(req);

        if (!token) {
          if (!required) {
            return next();
          }

          return res.status(401).json({
            error: 'Authentication required',
            message: 'No token provided',
            code: 'NO_TOKEN',
            timestamp: new Date().toISOString()
          });
        }

        // Verify JWT token
        const decoded = await this.verifyToken(token);

        if (!decoded) {
          return res.status(401).json({
            error: 'Invalid token',
            message: 'Token verification failed',
            code: 'INVALID_TOKEN',
            timestamp: new Date().toISOString()
          });
        }

        // Validate user with Configuration Service
        const user = await this.validateUser(decoded.userId, decoded.tenantId);

        if (!user) {
          return res.status(401).json({
            error: 'User validation failed',
            message: 'User not found or inactive',
            code: 'USER_VALIDATION_FAILED',
            timestamp: new Date().toISOString()
          });
        }

        // Attach user info to request
        req.user = {
          id: decoded.userId,
          tenantId: decoded.tenantId,
          role: user.role || 'user',
          permissions: user.permissions || [],
          tokenIssuedAt: decoded.iat,
          tokenExpiresAt: decoded.exp
        };

        // Add auth headers for downstream services
        req.headers['user-id'] = decoded.userId;
        req.headers['tenant-id'] = decoded.tenantId;
        req.headers['user-role'] = user.role || 'user';

        const processingTime = Date.now() - startTime;

        this.logger.info('Authentication successful', {
          userId: decoded.userId,
          tenantId: decoded.tenantId,
          role: user.role,
          processingTime: `${processingTime}ms`,
          requestId: req.requestId,
          path: req.path
        });

        next();

      } catch (error) {
        const processingTime = Date.now() - startTime;

        this.logger.error('Authentication error', {
          error: error.message,
          stack: error.stack,
          processingTime: `${processingTime}ms`,
          requestId: req.requestId,
          path: req.path
        });

        if (error.name === 'TokenExpiredError') {
          return res.status(401).json({
            error: 'Token expired',
            message: 'Please login again',
            code: 'TOKEN_EXPIRED',
            timestamp: new Date().toISOString()
          });
        }

        if (error.name === 'JsonWebTokenError') {
          return res.status(401).json({
            error: 'Invalid token',
            message: 'Token is malformed',
            code: 'MALFORMED_TOKEN',
            timestamp: new Date().toISOString()
          });
        }

        res.status(500).json({
          error: 'Authentication service error',
          message: 'Internal authentication error',
          code: 'AUTH_SERVICE_ERROR',
          timestamp: new Date().toISOString()
        });
      }
    };
  };

  /**
   * Authorization middleware (checks permissions)
   */
  authorize = (requiredPermissions = []) => {
    return (req, res, next) => {
      if (!req.user) {
        return res.status(401).json({
          error: 'Authentication required',
          message: 'User not authenticated',
          code: 'NOT_AUTHENTICATED',
          timestamp: new Date().toISOString()
        });
      }

      // Check if user has required permissions
      const userPermissions = req.user.permissions || [];
      const hasPermission = requiredPermissions.every(permission =>
        userPermissions.includes(permission) || userPermissions.includes('admin')
      );

      if (!hasPermission) {
        this.logger.warn('Authorization failed', {
          userId: req.user.id,
          tenantId: req.user.tenantId,
          requiredPermissions,
          userPermissions,
          requestId: req.requestId,
          path: req.path
        });

        return res.status(403).json({
          error: 'Insufficient permissions',
          message: 'You do not have permission to access this resource',
          code: 'INSUFFICIENT_PERMISSIONS',
          requiredPermissions,
          timestamp: new Date().toISOString()
        });
      }

      this.logger.info('Authorization successful', {
        userId: req.user.id,
        tenantId: req.user.tenantId,
        requiredPermissions,
        requestId: req.requestId,
        path: req.path
      });

      next();
    };
  };

  /**
   * Extract JWT token from request headers
   */
  extractToken(req) {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }

    // Also check for token in cookies
    if (req.cookies && req.cookies.token) {
      return req.cookies.token;
    }

    return null;
  }

  /**
   * Verify JWT token
   */
  async verifyToken(token) {
    try {
      const decoded = jwt.verify(token, this.jwtSecret);
      return decoded;
    } catch (error) {
      this.logger.error('Token verification failed', {
        error: error.message,
        tokenLength: token.length
      });
      throw error;
    }
  }

  /**
   * Validate user with Configuration Service (with caching)
   */
  async validateUser(userId, tenantId) {
    const cacheKey = `${userId}:${tenantId}`;

    // Check cache first
    if (this.userCache.has(cacheKey)) {
      const cached = this.userCache.get(cacheKey);
      if (Date.now() - cached.timestamp < this.cacheTimeout) {
        return cached.user;
      }
      // Remove expired cache entry
      this.userCache.delete(cacheKey);
    }

    try {
      // Query Configuration Service for user validation
      const response = await axios.get(
        `${this.configServiceUrl}/api/config/${userId}`,
        {
          headers: {
            'tenant-id': tenantId,
            'Content-Type': 'application/json'
          },
          timeout: 5000
        }
      );

      const user = {
        id: userId,
        tenantId: tenantId,
        role: response.data.config?.role || 'user',
        permissions: response.data.config?.permissions || [],
        active: response.data.config?.active !== false,
        lastLogin: response.data.config?.lastLogin
      };

      // Cache the user data
      this.userCache.set(cacheKey, {
        user,
        timestamp: Date.now()
      });

      return user.active ? user : null;

    } catch (error) {
      this.logger.error('User validation failed', {
        userId,
        tenantId,
        error: error.message,
        configServiceUrl: this.configServiceUrl
      });

      // If configuration service is down, allow access for critical operations
      // but with limited permissions
      if (error.code === 'ECONNREFUSED' || error.code === 'ETIMEDOUT') {
        this.logger.warn('Configuration service unavailable, using fallback', {
          userId,
          tenantId
        });

        return {
          id: userId,
          tenantId: tenantId,
          role: 'user',
          permissions: ['read'],
          active: true,
          fallback: true
        };
      }

      return null;
    }
  }

  /**
   * Clear user cache (useful for logout or user updates)
   */
  clearUserCache(userId, tenantId) {
    const cacheKey = `${userId}:${tenantId}`;
    this.userCache.delete(cacheKey);
  }

  /**
   * Get cache statistics
   */
  getCacheStats() {
    return {
      size: this.userCache.size,
      timeout: this.cacheTimeout,
      entries: Array.from(this.userCache.keys())
    };
  }
}

module.exports = AuthMiddleware;