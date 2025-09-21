const jwt = require('jsonwebtoken');
const Redis = require('redis');
const logger = require('../utils/logger');
const config = require('../config/gateway.config');

class AuthMiddleware {
  constructor() {
    this.redis = null;
    this.initRedis();
  }

  async initRedis() {
    try {
      this.redis = Redis.createClient({
        host: config.redis.host,
        port: config.redis.port,
        password: config.redis.password,
        db: config.redis.db
      });

      await this.redis.connect();
      logger.info('Connected to Redis for auth middleware');
    } catch (error) {
      logger.error('Failed to connect to Redis:', error);
      // Continue without Redis (fallback mode)
    }
  }

  // JWT token authentication
  authenticate = async (req, res, next) => {
    try {
      const authHeader = req.headers.authorization;
      const apiKey = req.headers['x-api-key'];

      // Check for API key authentication
      if (apiKey) {
        const isValidApiKey = await this.validateApiKey(apiKey);
        if (isValidApiKey) {
          req.auth = { type: 'api-key', apiKey };
          return next();
        }
      }

      // Check for JWT authentication
      if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({
          error: 'Authentication required',
          message: 'No valid authentication token provided',
          code: 'AUTH_REQUIRED'
        });
      }

      const token = authHeader.substring(7);

      // Check if token is blacklisted
      if (await this.isTokenBlacklisted(token)) {
        return res.status(401).json({
          error: 'Token invalid',
          message: 'Token has been revoked',
          code: 'TOKEN_REVOKED'
        });
      }

      // Verify JWT token
      const decoded = jwt.verify(token, config.jwt.secret, {
        issuer: config.jwt.issuer,
        audience: config.jwt.audience
      });

      // Add user info to request
      req.auth = {
        type: 'jwt',
        token,
        user: {
          id: decoded.sub,
          email: decoded.email,
          roles: decoded.roles || [],
          permissions: decoded.permissions || [],
          sessionId: decoded.sessionId
        }
      };

      // Update last activity
      await this.updateLastActivity(decoded.sub);

      next();
    } catch (error) {
      logger.warn(`Authentication failed: ${error.message}`);

      if (error.name === 'TokenExpiredError') {
        return res.status(401).json({
          error: 'Token expired',
          message: 'Your session has expired. Please login again.',
          code: 'TOKEN_EXPIRED'
        });
      }

      if (error.name === 'JsonWebTokenError') {
        return res.status(401).json({
          error: 'Invalid token',
          message: 'The provided token is invalid',
          code: 'TOKEN_INVALID'
        });
      }

      res.status(401).json({
        error: 'Authentication failed',
        message: 'Unable to authenticate request',
        code: 'AUTH_FAILED'
      });
    }
  };

  // Role-based authorization
  authorize = (requiredRoles = []) => {
    return (req, res, next) => {
      try {
        if (!req.auth || !req.auth.user) {
          return res.status(401).json({
            error: 'Authentication required',
            code: 'AUTH_REQUIRED'
          });
        }

        const userRoles = req.auth.user.roles || [];

        // Check if user has any of the required roles
        const hasRequiredRole = requiredRoles.length === 0 ||
          requiredRoles.some(role => userRoles.includes(role));

        if (!hasRequiredRole) {
          logger.warn(`Authorization failed for user ${req.auth.user.id}. Required: ${requiredRoles}, Has: ${userRoles}`);
          return res.status(403).json({
            error: 'Insufficient permissions',
            message: 'You do not have permission to access this resource',
            code: 'INSUFFICIENT_PERMISSIONS',
            requiredRoles,
            userRoles
          });
        }

        next();
      } catch (error) {
        logger.error('Authorization error:', error);
        res.status(500).json({
          error: 'Authorization error',
          code: 'AUTH_ERROR'
        });
      }
    };
  };

  // Permission-based authorization
  requirePermission = (permission) => {
    return (req, res, next) => {
      try {
        if (!req.auth || !req.auth.user) {
          return res.status(401).json({
            error: 'Authentication required',
            code: 'AUTH_REQUIRED'
          });
        }

        const userPermissions = req.auth.user.permissions || [];

        if (!userPermissions.includes(permission)) {
          logger.warn(`Permission denied for user ${req.auth.user.id}. Required: ${permission}`);
          return res.status(403).json({
            error: 'Permission denied',
            message: `Required permission: ${permission}`,
            code: 'PERMISSION_DENIED'
          });
        }

        next();
      } catch (error) {
        logger.error('Permission check error:', error);
        res.status(500).json({
          error: 'Permission check error',
          code: 'PERMISSION_ERROR'
        });
      }
    };
  };

  // Optional authentication (user info if available)
  optionalAuth = async (req, res, next) => {
    try {
      await this.authenticate(req, res, () => {
        // Authentication succeeded
        next();
      });
    } catch (error) {
      // Authentication failed, but continue without user info
      req.auth = null;
      next();
    }
  };

  // Validate API key
  async validateApiKey(apiKey) {
    try {
      if (!this.redis) return false;

      const keyData = await this.redis.get(`api_key:${apiKey}`);
      if (!keyData) return false;

      const keyInfo = JSON.parse(keyData);
      return keyInfo.active && (!keyInfo.expiresAt || keyInfo.expiresAt > Date.now());
    } catch (error) {
      logger.error('API key validation error:', error);
      return false;
    }
  }

  // Check if token is blacklisted
  async isTokenBlacklisted(token) {
    try {
      if (!this.redis) return false;

      const isBlacklisted = await this.redis.get(`blacklist:${token}`);
      return !!isBlacklisted;
    } catch (error) {
      logger.error('Token blacklist check error:', error);
      return false;
    }
  }

  // Update user's last activity
  async updateLastActivity(userId) {
    try {
      if (!this.redis) return;

      await this.redis.set(`last_activity:${userId}`, Date.now(), 'EX', 3600);
    } catch (error) {
      logger.error('Failed to update last activity:', error);
    }
  }

  // Blacklist token
  async blacklistToken(token) {
    try {
      if (!this.redis) return false;

      const decoded = jwt.decode(token);
      const expiresIn = decoded.exp - Math.floor(Date.now() / 1000);

      if (expiresIn > 0) {
        await this.redis.set(`blacklist:${token}`, '1', 'EX', expiresIn);
      }

      return true;
    } catch (error) {
      logger.error('Failed to blacklist token:', error);
      return false;
    }
  }

  // Admin only middleware
  adminOnly = this.authorize(['admin']);

  // Trader or admin middleware
  traderOrAdmin = this.authorize(['trader', 'admin']);

  // Premium user middleware
  premiumUser = this.authorize(['premium', 'trader', 'admin']);
}

module.exports = new AuthMiddleware();