import { Request, Response, NextFunction } from 'express';
import rateLimit from 'express-rate-limit';
import slowDown from 'express-slow-down';
import helmet from 'helmet';
import { jwtManager } from '@/auth/jwt';
import { config } from '@/config';
import { logger } from '@/logging';
import { AuthenticatedRequest, SecurityEvent, SubscriptionTier } from '@/types';
import { DatabaseService } from '@/database';

export class SecurityService {
  private databaseService: DatabaseService;

  constructor(databaseService: DatabaseService) {
    this.databaseService = databaseService;
  }

  /**
   * JWT Authentication Middleware
   */
  public authenticateToken = async (req: AuthenticatedRequest, res: Response, next: NextFunction): Promise<void> => {
    try {
      const authHeader = req.headers['authorization'];
      const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

      if (!token) {
        res.status(401).json({
          success: false,
          error: 'Access token is required',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      // Verify JWT token
      const payload = jwtManager.verifyAccessToken(token);
      if (!payload) {
        res.status(401).json({
          success: false,
          error: 'Invalid or expired token',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      // Get user from database to ensure they're still active
      const user = await this.databaseService.findUserById(payload.user_id);
      if (!user || !user.is_active) {
        res.status(401).json({
          success: false,
          error: 'User account is inactive',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      // Get user subscription
      const subscription = await this.databaseService.getUserSubscription(user.id);

      // Attach user and subscription to request
      req.user = user;
      req.subscription = subscription;

      next();

    } catch (error) {
      logger.error('Authentication middleware error', {
        error: error instanceof Error ? error.message : 'Unknown error',
        ip: req.ip,
        user_agent: req.get('User-Agent')
      });

      res.status(500).json({
        success: false,
        error: 'Authentication error',
        timestamp: new Date(),
        request_id: req.headers['x-request-id'] || 'unknown'
      });
    }
  };

  /**
   * Subscription Tier Authorization Middleware
   */
  public requireSubscription = (requiredTier: SubscriptionTier) => {
    return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
      if (!req.user || !req.subscription) {
        res.status(401).json({
          success: false,
          error: 'Authentication required',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      const hasAccess = jwtManager.hasSubscriptionAccess(req.user.subscription_tier, requiredTier);
      if (!hasAccess) {
        res.status(403).json({
          success: false,
          error: `Subscription tier '${requiredTier}' or higher required`,
          current_tier: req.user.subscription_tier,
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      next();
    };
  };

  /**
   * Resource Authorization Middleware (Multi-tenant)
   */
  public authorizeResourceAccess = (resourceUserIdParam: string = 'userId') => {
    return (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
      if (!req.user) {
        res.status(401).json({
          success: false,
          error: 'Authentication required',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      const resourceUserId = req.params[resourceUserIdParam] || req.body[resourceUserIdParam];
      if (!resourceUserId) {
        res.status(400).json({
          success: false,
          error: 'Resource user ID is required',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      // Check if user can access this resource
      const payload = {
        user_id: req.user.id,
        email: req.user.email,
        subscription_tier: req.user.subscription_tier,
        iat: 0,
        exp: 0,
        jti: ''
      };

      if (!jwtManager.isAuthorizedForResource(payload, resourceUserId)) {
        res.status(403).json({
          success: false,
          error: 'Access denied to this resource',
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      next();
    };
  };

  /**
   * Rate Limiting Middleware
   */
  public createRateLimiter = (options?: Partial<typeof config.security.rateLimiting>) => {
    const rateLimitConfig = { ...config.security.rateLimiting, ...options };

    return rateLimit({
      windowMs: rateLimitConfig.windowMs,
      max: rateLimitConfig.max,
      message: {
        success: false,
        error: rateLimitConfig.message,
        timestamp: new Date()
      },
      standardHeaders: true,
      legacyHeaders: false,
      skipSuccessfulRequests: rateLimitConfig.skipSuccessfulRequests,
      keyGenerator: (req: Request) => {
        // Use user ID if authenticated, otherwise IP
        const authReq = req as AuthenticatedRequest;
        return authReq.user?.id || req.ip;
      },
      onLimitReached: (req: Request) => {
        logger.warn('Rate limit exceeded', {
          ip: req.ip,
          user_agent: req.get('User-Agent'),
          path: req.path,
          user_id: (req as AuthenticatedRequest).user?.id
        });
      }
    });
  };

  /**
   * Slow Down Middleware (Progressive delay)
   */
  public createSlowDown = (options?: any) => {
    return slowDown({
      windowMs: 15 * 60 * 1000, // 15 minutes
      delayAfter: 5, // allow 5 requests per windowMs without delay
      delayMs: 500, // add 500ms delay per request after delayAfter
      maxDelayMs: 20000, // max delay of 20 seconds
      ...options,
      keyGenerator: (req: Request) => {
        const authReq = req as AuthenticatedRequest;
        return authReq.user?.id || req.ip;
      },
      onLimitReached: (req: Request) => {
        logger.warn('Slow down limit reached', {
          ip: req.ip,
          user_agent: req.get('User-Agent'),
          path: req.path,
          user_id: (req as AuthenticatedRequest).user?.id
        });
      }
    });
  };

  /**
   * Security Headers Middleware
   */
  public securityHeaders = helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"],
      },
    },
    crossOriginEmbedderPolicy: false,
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true
    }
  });

  /**
   * Request ID Middleware
   */
  public addRequestId = (req: Request, res: Response, next: NextFunction): void => {
    const requestId = req.headers['x-request-id'] as string || this.generateRequestId();
    req.headers['x-request-id'] = requestId;
    res.setHeader('X-Request-ID', requestId);
    next();
  };

  /**
   * Audit Logging Middleware
   */
  public auditLogger = (req: AuthenticatedRequest, res: Response, next: NextFunction): void => {
    const start = Date.now();

    // Log request
    logger.info('API Request', {
      request_id: req.headers['x-request-id'],
      method: req.method,
      url: req.url,
      ip: req.ip,
      user_agent: req.get('User-Agent'),
      user_id: req.user?.id,
      subscription_tier: req.user?.subscription_tier
    });

    // Override res.json to log response
    const originalJson = res.json;
    res.json = function(body: any) {
      const duration = Date.now() - start;

      logger.info('API Response', {
        request_id: req.headers['x-request-id'],
        method: req.method,
        url: req.url,
        status_code: res.statusCode,
        duration,
        user_id: req.user?.id,
        success: body?.success !== false
      });

      return originalJson.call(this, body);
    };

    next();
  };

  /**
   * Error Handler Middleware
   */
  public errorHandler = (err: Error, req: Request, res: Response, next: NextFunction): void => {
    logger.error('Unhandled error', {
      error: err.message,
      stack: err.stack,
      request_id: req.headers['x-request-id'],
      method: req.method,
      url: req.url,
      ip: req.ip,
      user_agent: req.get('User-Agent'),
      user_id: (req as AuthenticatedRequest).user?.id
    });

    res.status(500).json({
      success: false,
      error: 'Internal server error',
      timestamp: new Date(),
      request_id: req.headers['x-request-id'] || 'unknown'
    });
  };

  /**
   * Input Validation Middleware
   */
  public validateInput = (schema: any) => {
    return (req: Request, res: Response, next: NextFunction): void => {
      const { error } = schema.validate(req.body, { abortEarly: false });

      if (error) {
        const validationErrors = error.details.map((detail: any) => ({
          field: detail.path.join('.'),
          message: detail.message,
          value: detail.context?.value
        }));

        res.status(400).json({
          success: false,
          error: 'Validation failed',
          validation_errors: validationErrors,
          timestamp: new Date(),
          request_id: req.headers['x-request-id'] || 'unknown'
        });
        return;
      }

      next();
    };
  };

  /**
   * Log security event
   */
  public async logSecurityEvent(event: SecurityEvent): Promise<void> {
    try {
      await this.databaseService.logSecurityEvent(event);

      // If high risk, trigger additional alerts
      if (event.risk_score >= 7) {
        logger.warn('High risk security event detected', {
          event_type: event.event_type,
          user_id: event.user_id,
          ip_address: event.ip_address,
          risk_score: event.risk_score,
          details: event.details
        });
      }

    } catch (error) {
      logger.error('Failed to log security event', {
        error: error instanceof Error ? error.message : 'Unknown error',
        event
      });
    }
  }

  /**
   * Suspicious Activity Detection
   */
  public async detectSuspiciousActivity(req: AuthenticatedRequest): Promise<boolean> {
    try {
      // Implement suspicious activity detection logic
      // For example: too many failed requests, unusual access patterns, etc.

      const recentEvents = await this.getRecentSecurityEvents(
        req.user?.id,
        req.ip,
        15 * 60 * 1000 // 15 minutes
      );

      const failedAttempts = recentEvents.filter(event =>
        event.event_type === 'failed_login' && event.risk_score >= 5
      ).length;

      if (failedAttempts >= 5) {
        logger.warn('Suspicious activity detected', {
          user_id: req.user?.id,
          ip: req.ip,
          failed_attempts: failedAttempts
        });
        return true;
      }

      return false;

    } catch (error) {
      logger.error('Error detecting suspicious activity', {
        error: error instanceof Error ? error.message : 'Unknown error',
        user_id: req.user?.id,
        ip: req.ip
      });
      return false;
    }
  }

  // Private helper methods

  private generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async getRecentSecurityEvents(
    userId?: string,
    ipAddress?: string,
    timeWindowMs: number = 15 * 60 * 1000
  ): Promise<SecurityEvent[]> {
    // Implementation would query database for recent security events
    // This is a simplified version
    return [];
  }
}

// Export middleware factory functions for easy use
export const createSecurityMiddleware = (databaseService: DatabaseService) => {
  const securityService = new SecurityService(databaseService);

  return {
    // Authentication & Authorization
    authenticate: securityService.authenticateToken,
    requireBasic: securityService.requireSubscription(SubscriptionTier.BASIC),
    requirePro: securityService.requireSubscription(SubscriptionTier.PRO),
    requireEnterprise: securityService.requireSubscription(SubscriptionTier.ENTERPRISE),
    authorizeResource: securityService.authorizeResourceAccess,

    // Rate Limiting & Protection
    rateLimiter: securityService.createRateLimiter(),
    strictRateLimiter: securityService.createRateLimiter({ max: 50, windowMs: 15 * 60 * 1000 }),
    slowDown: securityService.createSlowDown(),

    // Security & Monitoring
    securityHeaders: securityService.securityHeaders,
    addRequestId: securityService.addRequestId,
    auditLogger: securityService.auditLogger,
    errorHandler: securityService.errorHandler,
    validateInput: securityService.validateInput,

    // Service instance for manual use
    securityService
  };
};