import { Router, Request, Response } from 'express';
import Joi from 'joi';
import { AuthService } from '@/auth/auth.service';
import { DatabaseService } from '@/database';
import { SecurityService, createSecurityMiddleware } from '@/security';
import { logger } from '@/logging';
import { handleError } from '@/utils/errorDna';
import { ApiResponse, SubscriptionTier } from '@/types';

const router = Router();

// Validation schemas
const registerSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).pattern(new RegExp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])')).required()
    .messages({
      'string.pattern.base': 'Password must contain at least one lowercase letter, one uppercase letter, one number, and one special character'
    }),
  firstName: Joi.string().min(1).max(50).required(),
  lastName: Joi.string().min(1).max(50).required(),
  subscriptionTier: Joi.string().valid(...Object.values(SubscriptionTier)).optional()
});

const loginSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().required()
});

const refreshTokenSchema = Joi.object({
  refreshToken: Joi.string().required()
});

const changePasswordSchema = Joi.object({
  currentPassword: Joi.string().required(),
  newPassword: Joi.string().min(8).pattern(new RegExp('^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%\^&\*])')).required()
    .messages({
      'string.pattern.base': 'Password must contain at least one lowercase letter, one uppercase letter, one number, and one special character'
    })
});

// Initialize services
export const createAuthRoutes = (
  databaseService: DatabaseService,
  securityService: SecurityService
): Router => {
  const authService = new AuthService(databaseService, securityService);
  const security = createSecurityMiddleware(databaseService);

  /**
   * Register new user
   * POST /api/v1/auth/register
   */
  router.post('/register', [
    security.rateLimiter,
    security.validateInput(registerSchema)
  ], async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const { email, password, firstName, lastName, subscriptionTier } = req.body;
      const ipAddress = req.ip;
      const userAgent = req.get('User-Agent') || 'Unknown';

      const result = await authService.register(
        {
          email,
          password,
          firstName,
          lastName,
          subscriptionTier
        },
        ipAddress,
        userAgent
      );

      if (!result.success) {
        const response: ApiResponse = {
          success: false,
          error: result.error,
          timestamp: new Date(),
          request_id: requestId
        };

        return res.status(400).json(response);
      }

      const response: ApiResponse = {
        success: true,
        data: {
          user: result.user,
          access_token: result.accessToken,
          refresh_token: result.refreshToken,
          token_type: 'Bearer',
          expires_in: '15m'
        },
        message: 'Registration successful',
        timestamp: new Date(),
        request_id: requestId
      };

      logger.info('User registration successful', {
        user_id: result.user?.id,
        email: result.user?.email,
        subscription_tier: result.user?.subscription_tier,
        request_id: requestId
      });

      res.status(201).json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'user_registration',
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * User login
   * POST /api/v1/auth/login
   */
  router.post('/login', [
    security.rateLimiter,
    security.validateInput(loginSchema)
  ], async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const { email, password } = req.body;
      const ipAddress = req.ip;
      const userAgent = req.get('User-Agent') || 'Unknown';

      const result = await authService.login(
        { email, password },
        ipAddress,
        userAgent
      );

      if (!result.success) {
        const response: ApiResponse = {
          success: false,
          error: result.error,
          timestamp: new Date(),
          request_id: requestId
        };

        return res.status(401).json(response);
      }

      const response: ApiResponse = {
        success: true,
        data: {
          user: result.user,
          access_token: result.accessToken,
          refresh_token: result.refreshToken,
          token_type: 'Bearer',
          expires_in: '15m'
        },
        message: 'Login successful',
        timestamp: new Date(),
        request_id: requestId
      };

      logger.info('User login successful', {
        user_id: result.user?.id,
        email: result.user?.email,
        request_id: requestId
      });

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'user_login',
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Refresh access token
   * POST /api/v1/auth/refresh
   */
  router.post('/refresh', [
    security.rateLimiter,
    security.validateInput(refreshTokenSchema)
  ], async (req: Request, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const { refreshToken } = req.body;

      const result = await authService.refreshToken(refreshToken);

      if (!result.success) {
        const response: ApiResponse = {
          success: false,
          error: result.error,
          timestamp: new Date(),
          request_id: requestId
        };

        return res.status(401).json(response);
      }

      const response: ApiResponse = {
        success: true,
        data: {
          user: result.user,
          access_token: result.accessToken,
          refresh_token: result.refreshToken,
          token_type: 'Bearer',
          expires_in: '15m'
        },
        message: 'Token refreshed successfully',
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'token_refresh',
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * User logout
   * POST /api/v1/auth/logout
   */
  router.post('/logout', [
    security.authenticate,
    security.rateLimiter
  ], async (req: any, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user.id;
      const refreshToken = req.body.refreshToken || req.headers['x-refresh-token'];
      const ipAddress = req.ip;
      const userAgent = req.get('User-Agent') || 'Unknown';

      const success = await authService.logout(userId, refreshToken, ipAddress, userAgent);

      const response: ApiResponse = {
        success,
        message: success ? 'Logout successful' : 'Logout failed',
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'user_logout',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Change password
   * POST /api/v1/auth/change-password
   */
  router.post('/change-password', [
    security.authenticate,
    security.rateLimiter,
    security.validateInput(changePasswordSchema)
  ], async (req: any, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const userId = req.user.id;
      const { currentPassword, newPassword } = req.body;

      const success = await authService.changePassword(userId, currentPassword, newPassword);

      if (!success) {
        const response: ApiResponse = {
          success: false,
          error: 'Current password is incorrect',
          timestamp: new Date(),
          request_id: requestId
        };

        return res.status(400).json(response);
      }

      const response: ApiResponse = {
        success: true,
        message: 'Password changed successfully. Please log in with your new password.',
        timestamp: new Date(),
        request_id: requestId
      };

      logger.info('Password changed successfully', {
        user_id: userId,
        request_id: requestId
      });

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'change_password',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Get current user profile
   * GET /api/v1/auth/profile
   */
  router.get('/profile', [
    security.authenticate,
    security.rateLimiter
  ], async (req: any, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const user = req.user;
      const subscription = req.subscription;

      const response: ApiResponse = {
        success: true,
        data: {
          user: {
            id: user.id,
            email: user.email,
            first_name: user.first_name,
            last_name: user.last_name,
            subscription_tier: user.subscription_tier,
            subscription_status: user.subscription_status,
            created_at: user.created_at,
            last_login: user.last_login,
            email_verified: user.email_verified
          },
          subscription: subscription ? {
            tier: subscription.tier,
            status: subscription.status,
            features: subscription.features,
            ends_at: subscription.ends_at,
            auto_renew: subscription.auto_renew
          } : null
        },
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'get_profile',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  /**
   * Validate subscription access
   * GET /api/v1/auth/validate-subscription/:tier
   */
  router.get('/validate-subscription/:tier', [
    security.authenticate,
    security.rateLimiter
  ], async (req: any, res: Response) => {
    const requestId = req.headers['x-request-id'] as string;

    try {
      const requiredTier = req.params.tier as SubscriptionTier;
      const userId = req.user.id;

      if (!Object.values(SubscriptionTier).includes(requiredTier)) {
        const response: ApiResponse = {
          success: false,
          error: 'Invalid subscription tier',
          timestamp: new Date(),
          request_id: requestId
        };

        return res.status(400).json(response);
      }

      const hasAccess = await authService.validateSubscriptionAccess(userId, requiredTier);

      const response: ApiResponse = {
        success: true,
        data: {
          has_access: hasAccess,
          current_tier: req.user.subscription_tier,
          required_tier: requiredTier
        },
        timestamp: new Date(),
        request_id: requestId
      };

      res.json(response);

    } catch (error) {
      const errorResult = await handleError(error as Error, {
        operation: 'validate_subscription',
        userId: req.user?.id,
        requestId
      });

      const response: ApiResponse = {
        success: false,
        error: errorResult.classification.userMessage,
        timestamp: new Date(),
        request_id: requestId
      };

      res.status(500).json(response);
    }
  });

  return router;
};

export default router;