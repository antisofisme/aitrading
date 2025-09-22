const jwt = require('jsonwebtoken');
const winston = require('winston');
const axios = require('axios');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'api-gateway-multi-tenant-auth' }
});

// Subscription tier limits
const TIER_LIMITS = {
  'FREE': {
    requestsPerMinute: 10,
    requestsPerHour: 100,
    requestsPerDay: 1000,
    maxRequestSize: '1mb',
    allowedEndpoints: ['/api/auth', '/api/subscriptions', '/health']
  },
  'BASIC': {
    requestsPerMinute: 50,
    requestsPerHour: 1000,
    requestsPerDay: 10000,
    maxRequestSize: '5mb',
    allowedEndpoints: ['*'] // All endpoints except admin
  },
  'PREMIUM': {
    requestsPerMinute: 200,
    requestsPerHour: 5000,
    requestsPerDay: 50000,
    maxRequestSize: '10mb',
    allowedEndpoints: ['*']
  },
  'ENTERPRISE': {
    requestsPerMinute: 1000,
    requestsPerHour: 25000,
    requestsPerDay: 'unlimited',
    maxRequestSize: '50mb',
    allowedEndpoints: ['*', '/api/database', '/metrics'] // Includes admin endpoints
  }
};

/**
 * Multi-tenant authentication middleware
 * Extracts user information and subscription tier from JWT token
 */
async function multiTenantAuth(req, res, next) {
  try {
    // Skip authentication for public endpoints
    const publicEndpoints = ['/health', '/', '/api/auth/login', '/api/auth/register'];
    const isPublicEndpoint = publicEndpoints.some(endpoint =>
      req.path === endpoint || req.path.startsWith('/health')
    );

    if (isPublicEndpoint) {
      return next();
    }

    // Get token from Authorization header
    const authHeader = req.headers.authorization;
    const apiKey = req.headers['x-api-key'];

    let user = null;
    let authMethod = 'none';

    // Try JWT authentication first
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.slice(7);

      try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'fallback-secret');

        // Validate token structure
        if (decoded.userId && decoded.email && decoded.subscription) {
          user = {
            id: decoded.userId,
            email: decoded.email,
            subscription: decoded.subscription,
            emailVerified: decoded.emailVerified,
            isActive: decoded.isActive,
            role: decoded.role || 'user'
          };
          authMethod = 'jwt';

          // Add tenant information (for future multi-tenant support)
          user.tenantId = decoded.tenantId || 'default';

          logger.info(`User authenticated via JWT: ${user.email} (${user.subscription})`);
        }
      } catch (jwtError) {
        // JWT verification failed, try API key authentication
        logger.warn(`JWT verification failed: ${jwtError.message}`);
      }
    }

    // Try API key authentication if JWT failed
    if (!user && apiKey) {
      try {
        const userInfo = await authenticateApiKey(apiKey);
        if (userInfo) {
          user = userInfo;
          authMethod = 'api_key';
          logger.info(`User authenticated via API key: ${user.email} (${user.subscription})`);
        }
      } catch (apiError) {
        logger.warn(`API key authentication failed: ${apiError.message}`);
      }
    }

    // Check if authentication is required for this endpoint
    const protectedEndpoints = [
      '/api/users', '/api/subscriptions', '/api/payments',
      '/api/notifications', '/api/billing', '/api/data',
      '/api/hub', '/api/database', '/metrics'
    ];

    const requiresAuth = protectedEndpoints.some(endpoint =>
      req.path.startsWith(endpoint)
    );

    if (requiresAuth && !user) {
      return res.status(401).json({
        success: false,
        error: 'Authentication required',
        message: 'Please provide a valid JWT token or API key',
        authMethods: ['Bearer token', 'X-API-Key header']
      });
    }

    // Add user information to request
    if (user) {
      req.user = user;
      req.authMethod = authMethod;

      // Check subscription tier access
      const hasAccess = checkTierAccess(user.subscription, req.path, req.method);
      if (!hasAccess) {
        return res.status(403).json({
          success: false,
          error: 'Insufficient subscription tier',
          message: `Your ${user.subscription} subscription does not have access to this endpoint`,
          currentTier: user.subscription,
          requiredTier: getRequiredTier(req.path),
          upgradeUrl: '/api/subscriptions'
        });
      }

      // Add rate limiting context
      req.rateLimitKey = `user:${user.id}`;
      req.tierLimits = TIER_LIMITS[user.subscription] || TIER_LIMITS['FREE'];

      // Add request tracking headers
      res.set({
        'X-User-ID': user.id,
        'X-User-Tier': user.subscription,
        'X-Auth-Method': authMethod,
        'X-Rate-Limit-Tier': user.subscription
      });
    }

    next();

  } catch (error) {
    logger.error('Multi-tenant authentication error:', error);
    res.status(500).json({
      success: false,
      error: 'Authentication service error',
      message: 'An error occurred during authentication'
    });
  }
}

/**
 * Authenticate using API key
 */
async function authenticateApiKey(apiKey) {
  try {
    // In production, this would call the user management service
    // For now, we'll validate against a simple format and mock response

    if (!apiKey.startsWith('ak_')) {
      return null;
    }

    // Mock API key validation (replace with actual service call)
    const mockUserResponse = {
      id: 'api-user-' + apiKey.slice(-8),
      email: 'api@aitrading.com',
      subscription: 'PREMIUM',
      emailVerified: true,
      isActive: true,
      role: 'api_user',
      tenantId: 'default'
    };

    // In production, make actual service call:
    // const response = await axios.get(`${USER_MANAGEMENT_URL}/api/users/by-api-key`, {
    //   headers: { 'X-API-Key': apiKey }
    // });
    // return response.data.user;

    return mockUserResponse;

  } catch (error) {
    logger.error('API key authentication error:', error);
    return null;
  }
}

/**
 * Check if user's subscription tier has access to the requested endpoint
 */
function checkTierAccess(subscription, path, method) {
  const tierConfig = TIER_LIMITS[subscription] || TIER_LIMITS['FREE'];
  const allowedEndpoints = tierConfig.allowedEndpoints;

  // If tier allows all endpoints
  if (allowedEndpoints.includes('*')) {
    // Check for admin-only endpoints
    const adminEndpoints = ['/api/database', '/metrics'];
    if (adminEndpoints.some(endpoint => path.startsWith(endpoint))) {
      return subscription === 'ENTERPRISE';
    }
    return true;
  }

  // Check specific allowed endpoints
  return allowedEndpoints.some(endpoint =>
    path.startsWith(endpoint) || path === endpoint
  );
}

/**
 * Get required tier for endpoint
 */
function getRequiredTier(path) {
  if (path.startsWith('/api/database') || path.startsWith('/metrics')) {
    return 'ENTERPRISE';
  }

  if (path.startsWith('/api/payments') || path.startsWith('/api/billing')) {
    return 'BASIC';
  }

  return 'FREE';
}

/**
 * Service-to-service authentication middleware
 */
function serviceAuth(req, res, next) {
  const serviceToken = req.headers['x-service-token'];

  if (!serviceToken) {
    return res.status(401).json({
      success: false,
      error: 'Service authentication required',
      message: 'Missing X-Service-Token header'
    });
  }

  try {
    const decoded = jwt.verify(serviceToken, process.env.SERVICE_SECRET || 'service-secret-key');

    if (decoded.type !== 'service') {
      return res.status(401).json({
        success: false,
        error: 'Invalid service token',
        message: 'Token is not a service token'
      });
    }

    req.service = {
      name: decoded.iss,
      target: decoded.aud,
      isValid: true
    };

    next();

  } catch (error) {
    logger.error('Service authentication error:', error);
    res.status(401).json({
      success: false,
      error: 'Invalid service token',
      message: 'Service token verification failed'
    });
  }
}

/**
 * Get user tier limits for rate limiting
 */
function getUserTierLimits(subscription) {
  return TIER_LIMITS[subscription] || TIER_LIMITS['FREE'];
}

module.exports = {
  multiTenantAuth,
  serviceAuth,
  getUserTierLimits,
  TIER_LIMITS
};