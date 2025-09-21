import bcrypt from 'bcrypt';
import { v4 as uuidv4 } from 'uuid';
import { config } from '@/config';
import { jwtManager } from './jwt';
import { User, SubscriptionTier, SubscriptionStatus, SecurityEvent } from '@/types';
import { logger } from '@/logging';
import { DatabaseService } from '@/database';
import { SecurityService } from '@/security';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  subscriptionTier?: SubscriptionTier;
}

export interface AuthResponse {
  success: boolean;
  user?: Omit<User, 'password_hash'>;
  accessToken?: string;
  refreshToken?: string;
  error?: string;
}

export class AuthService {
  private databaseService: DatabaseService;
  private securityService: SecurityService;

  constructor(databaseService: DatabaseService, securityService: SecurityService) {
    this.databaseService = databaseService;
    this.securityService = securityService;
  }

  /**
   * Register new user with multi-tenant support
   */
  public async register(data: RegisterData, ipAddress: string, userAgent: string): Promise<AuthResponse> {
    try {
      // Validate email uniqueness
      const existingUser = await this.findUserByEmail(data.email);
      if (existingUser) {
        await this.logSecurityEvent({
          event_type: 'failed_login',
          ip_address: ipAddress,
          user_agent: userAgent,
          details: { reason: 'email_already_exists', email: data.email },
          risk_score: 3
        });

        return {
          success: false,
          error: 'Email already registered'
        };
      }

      // Hash password
      const passwordHash = await this.hashPassword(data.password);

      // Create user
      const userId = uuidv4();
      const user: User = {
        id: userId,
        email: data.email.toLowerCase(),
        password_hash: passwordHash,
        first_name: data.firstName,
        last_name: data.lastName,
        subscription_tier: data.subscriptionTier || SubscriptionTier.FREE,
        subscription_status: SubscriptionStatus.ACTIVE,
        created_at: new Date(),
        updated_at: new Date(),
        last_login: null,
        is_active: true,
        email_verified: false
      };

      // Save user to database
      await this.saveUser(user);

      // Create default subscription
      await this.createDefaultSubscription(userId, user.subscription_tier);

      // Generate tokens
      const { accessToken, refreshToken } = jwtManager.generateTokenPair(user);

      // Log successful registration
      await this.logSecurityEvent({
        user_id: userId,
        event_type: 'login',
        ip_address: ipAddress,
        user_agent: userAgent,
        details: { action: 'registration', subscription_tier: user.subscription_tier },
        risk_score: 1
      });

      logger.info('User registered successfully', {
        user_id: userId,
        email: data.email,
        subscription_tier: user.subscription_tier
      });

      return {
        success: true,
        user: this.sanitizeUser(user),
        accessToken,
        refreshToken
      };

    } catch (error) {
      logger.error('Registration failed', {
        email: data.email,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      return {
        success: false,
        error: 'Registration failed'
      };
    }
  }

  /**
   * Authenticate user login
   */
  public async login(credentials: LoginCredentials, ipAddress: string, userAgent: string): Promise<AuthResponse> {
    try {
      // Find user by email
      const user = await this.findUserByEmail(credentials.email);
      if (!user) {
        await this.logSecurityEvent({
          event_type: 'failed_login',
          ip_address: ipAddress,
          user_agent: userAgent,
          details: { reason: 'user_not_found', email: credentials.email },
          risk_score: 5
        });

        return {
          success: false,
          error: 'Invalid credentials'
        };
      }

      // Check if user is active
      if (!user.is_active) {
        await this.logSecurityEvent({
          user_id: user.id,
          event_type: 'failed_login',
          ip_address: ipAddress,
          user_agent: userAgent,
          details: { reason: 'account_inactive' },
          risk_score: 4
        });

        return {
          success: false,
          error: 'Account is inactive'
        };
      }

      // Verify password
      const isPasswordValid = await this.verifyPassword(credentials.password, user.password_hash);
      if (!isPasswordValid) {
        await this.logSecurityEvent({
          user_id: user.id,
          event_type: 'failed_login',
          ip_address: ipAddress,
          user_agent: userAgent,
          details: { reason: 'invalid_password' },
          risk_score: 7
        });

        return {
          success: false,
          error: 'Invalid credentials'
        };
      }

      // Update last login
      await this.updateLastLogin(user.id);

      // Generate tokens
      const { accessToken, refreshToken } = jwtManager.generateTokenPair(user);

      // Log successful login
      await this.logSecurityEvent({
        user_id: user.id,
        event_type: 'login',
        ip_address: ipAddress,
        user_agent: userAgent,
        details: { action: 'login_success' },
        risk_score: 1
      });

      logger.info('User logged in successfully', {
        user_id: user.id,
        email: user.email
      });

      return {
        success: true,
        user: this.sanitizeUser(user),
        accessToken,
        refreshToken
      };

    } catch (error) {
      logger.error('Login failed', {
        email: credentials.email,
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      return {
        success: false,
        error: 'Login failed'
      };
    }
  }

  /**
   * Refresh access token
   */
  public async refreshToken(refreshToken: string): Promise<AuthResponse> {
    try {
      const result = await jwtManager.refreshAccessToken(
        refreshToken,
        async (userId: string) => await this.findUserById(userId)
      );

      if (!result) {
        return {
          success: false,
          error: 'Invalid refresh token'
        };
      }

      const user = await this.findUserById(result.accessToken);
      if (!user) {
        return {
          success: false,
          error: 'User not found'
        };
      }

      logger.info('Token refreshed successfully', {
        user_id: user.id
      });

      return {
        success: true,
        user: this.sanitizeUser(user),
        accessToken: result.accessToken,
        refreshToken: result.refreshToken
      };

    } catch (error) {
      logger.error('Token refresh failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });

      return {
        success: false,
        error: 'Token refresh failed'
      };
    }
  }

  /**
   * Logout user and revoke tokens
   */
  public async logout(userId: string, refreshToken: string, ipAddress: string, userAgent: string): Promise<boolean> {
    try {
      // Verify and get refresh token payload
      const refreshPayload = jwtManager.verifyRefreshToken(refreshToken);
      if (refreshPayload) {
        jwtManager.revokeRefreshToken(refreshPayload.token_id);
      }

      // Log logout event
      await this.logSecurityEvent({
        user_id: userId,
        event_type: 'logout',
        ip_address: ipAddress,
        user_agent: userAgent,
        details: { action: 'logout' },
        risk_score: 1
      });

      logger.info('User logged out successfully', { user_id: userId });
      return true;

    } catch (error) {
      logger.error('Logout failed', {
        user_id: userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return false;
    }
  }

  /**
   * Change user password
   */
  public async changePassword(userId: string, currentPassword: string, newPassword: string): Promise<boolean> {
    try {
      const user = await this.findUserById(userId);
      if (!user) {
        return false;
      }

      // Verify current password
      const isCurrentPasswordValid = await this.verifyPassword(currentPassword, user.password_hash);
      if (!isCurrentPasswordValid) {
        return false;
      }

      // Hash new password
      const newPasswordHash = await this.hashPassword(newPassword);

      // Update password in database
      await this.updateUserPassword(userId, newPasswordHash);

      // Revoke all existing tokens for security
      jwtManager.revokeAllUserTokens(userId);

      logger.info('Password changed successfully', { user_id: userId });
      return true;

    } catch (error) {
      logger.error('Password change failed', {
        user_id: userId,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return false;
    }
  }

  /**
   * Validate user subscription access
   */
  public async validateSubscriptionAccess(userId: string, requiredTier: SubscriptionTier): Promise<boolean> {
    try {
      const user = await this.findUserById(userId);
      if (!user) {
        return false;
      }

      return jwtManager.hasSubscriptionAccess(user.subscription_tier, requiredTier);

    } catch (error) {
      logger.error('Subscription validation failed', {
        user_id: userId,
        required_tier: requiredTier,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return false;
    }
  }

  // Private helper methods

  private async hashPassword(password: string): Promise<string> {
    return bcrypt.hash(password, config.security.bcryptRounds);
  }

  private async verifyPassword(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }

  private sanitizeUser(user: User): Omit<User, 'password_hash'> {
    const { password_hash, ...sanitizedUser } = user;
    return sanitizedUser;
  }

  private async findUserByEmail(email: string): Promise<User | null> {
    // Implementation depends on DatabaseService
    return this.databaseService.findUserByEmail(email.toLowerCase());
  }

  private async findUserById(id: string): Promise<User | null> {
    return this.databaseService.findUserById(id);
  }

  private async saveUser(user: User): Promise<void> {
    return this.databaseService.createUser(user);
  }

  private async updateLastLogin(userId: string): Promise<void> {
    return this.databaseService.updateUserLastLogin(userId, new Date());
  }

  private async updateUserPassword(userId: string, passwordHash: string): Promise<void> {
    return this.databaseService.updateUserPassword(userId, passwordHash);
  }

  private async createDefaultSubscription(userId: string, tier: SubscriptionTier): Promise<void> {
    // Create default subscription based on tier
    return this.databaseService.createSubscription({
      id: uuidv4(),
      user_id: userId,
      tier,
      status: SubscriptionStatus.ACTIVE,
      price: this.getTierPrice(tier),
      currency: 'USD',
      billing_cycle: 'monthly',
      features: this.getTierFeatures(tier),
      starts_at: new Date(),
      ends_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
      auto_renew: true,
      created_at: new Date(),
      updated_at: new Date()
    });
  }

  private getTierPrice(tier: SubscriptionTier): number {
    const prices = {
      [SubscriptionTier.FREE]: 0,
      [SubscriptionTier.BASIC]: 49,
      [SubscriptionTier.PRO]: 199,
      [SubscriptionTier.ENTERPRISE]: 999
    };
    return prices[tier];
  }

  private getTierFeatures(tier: SubscriptionTier): string[] {
    const features = {
      [SubscriptionTier.FREE]: ['basic_access'],
      [SubscriptionTier.BASIC]: ['basic_signals', 'email_support'],
      [SubscriptionTier.PRO]: ['advanced_signals', 'priority_support', 'api_access'],
      [SubscriptionTier.ENTERPRISE]: ['all_features', 'dedicated_support', 'custom_integration']
    };
    return features[tier];
  }

  private async logSecurityEvent(event: Omit<SecurityEvent, 'id' | 'created_at'>): Promise<void> {
    const securityEvent: SecurityEvent = {
      id: uuidv4(),
      ...event,
      created_at: new Date()
    };

    await this.securityService.logSecurityEvent(securityEvent);
  }
}