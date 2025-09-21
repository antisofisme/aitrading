/**
 * Authentication Middleware
 * JWT token validation and user authentication
 */

const jwtService = require('../utils/jwt');
const { database } = require('../config/database');

/**
 * Authenticate JWT token middleware
 */
const authenticateToken = async (req, res, next) => {
  try {
    const authHeader = req.headers.authorization;
    const token = jwtService.extractTokenFromHeader(authHeader);

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Access token required',
        code: 'TOKEN_MISSING'
      });
    }

    const decoded = jwtService.verifyAccessToken(token);
    const user = await database.getUserById(decoded.sub);

    if (!user) {
      return res.status(401).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    if (!user.isActive) {
      return res.status(401).json({
        success: false,
        message: 'User account is deactivated',
        code: 'USER_DEACTIVATED'
      });
    }

    req.user = {
      id: user.id,
      email: user.email,
      role: user.role,
      firstName: user.firstName,
      lastName: user.lastName
    };

    req.token = {
      jti: decoded.jti,
      iat: decoded.iat,
      exp: decoded.exp
    };

    next();
  } catch (error) {
    console.error('Authentication error:', error.message);

    if (error.message.includes('expired')) {
      return res.status(401).json({
        success: false,
        message: 'Token has expired',
        code: 'TOKEN_EXPIRED'
      });
    }

    return res.status(401).json({
      success: false,
      message: 'Authentication failed',
      code: 'AUTH_FAILED'
    });
  }
};

/**
 * Role-based authorization middleware
 */
const authorize = (allowedRoles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required',
        code: 'AUTH_REQUIRED'
      });
    }

    const roles = Array.isArray(allowedRoles) ? allowedRoles : [allowedRoles];

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        message: 'Insufficient permissions',
        code: 'INSUFFICIENT_PERMISSIONS',
        required: roles,
        current: req.user.role
      });
    }

    next();
  };
};

const adminOnly = authorize(['admin']);
const userOrAdmin = authorize(['user', 'admin']);

const selfOrAdmin = (getUserIdFromParams = (req) => req.params.userId) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required',
        code: 'AUTH_REQUIRED'
      });
    }

    const targetUserId = getUserIdFromParams(req);

    if (req.user.role === 'admin' || req.user.id === targetUserId) {
      return next();
    }

    return res.status(403).json({
      success: false,
      message: 'Can only access your own resources',
      code: 'ACCESS_DENIED'
    });
  };
};

const validateRefreshToken = async (req, res, next) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({
        success: false,
        message: 'Refresh token required',
        code: 'REFRESH_TOKEN_MISSING'
      });
    }

    const decoded = jwtService.verifyRefreshToken(refreshToken);
    const user = await database.getUserById(decoded.sub);

    if (!user || !user.isActive) {
      return res.status(401).json({
        success: false,
        message: 'Invalid refresh token',
        code: 'INVALID_REFRESH_TOKEN'
      });
    }

    req.user = user;
    req.refreshTokenData = decoded;
    next();
  } catch (error) {
    console.error('Refresh token validation error:', error.message);
    return res.status(401).json({
      success: false,
      message: 'Invalid refresh token',
      code: 'INVALID_REFRESH_TOKEN'
    });
  }
};

module.exports = {
  authenticateToken,
  authorize,
  adminOnly,
  userOrAdmin,
  selfOrAdmin,
  validateRefreshToken
};