import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { config } from '@/config';
import { JWTPayload, RefreshTokenPayload, User, SubscriptionTier } from '@/types';
import { logger } from '@/logging';

export class JWTManager {
  private static instance: JWTManager;
  private refreshTokens: Set<string> = new Set();

  private constructor() {}

  public static getInstance(): JWTManager {
    if (!JWTManager.instance) {
      JWTManager.instance = new JWTManager();
    }
    return JWTManager.instance;
  }

  /**
   * Generate access token for authenticated user
   */
  public generateAccessToken(user: User): string {
    const payload: JWTPayload = {
      user_id: user.id,
      email: user.email,
      subscription_tier: user.subscription_tier,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + this.parseExpirationTime(config.jwt.expiresIn),
      jti: uuidv4()
    };

    return jwt.sign(payload, config.jwt.secret, {
      algorithm: 'HS256'
    });
  }

  /**
   * Generate refresh token for user session
   */
  public generateRefreshToken(userId: string): string {
    const tokenId = uuidv4();
    const payload: RefreshTokenPayload = {
      user_id: userId,
      token_id: tokenId,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + this.parseExpirationTime(config.jwt.refreshExpiresIn)
    };

    const token = jwt.sign(payload, config.jwt.refreshSecret, {
      algorithm: 'HS256'
    });

    // Store refresh token in memory (in production, use Redis)
    this.refreshTokens.add(tokenId);

    logger.info('Refresh token generated', {
      user_id: userId,
      token_id: tokenId,
      expires_in: config.jwt.refreshExpiresIn
    });

    return token;
  }

  /**
   * Verify and decode access token
   */
  public verifyAccessToken(token: string): JWTPayload | null {
    try {
      const decoded = jwt.verify(token, config.jwt.secret) as JWTPayload;

      // Additional validation
      if (!decoded.user_id || !decoded.email || !decoded.subscription_tier) {
        logger.warn('Invalid JWT payload structure', { decoded });
        return null;
      }

      // Check token expiration
      if (decoded.exp < Math.floor(Date.now() / 1000)) {
        logger.warn('JWT token expired', {
          user_id: decoded.user_id,
          exp: decoded.exp,
          current_time: Math.floor(Date.now() / 1000)
        });
        return null;
      }

      return decoded;
    } catch (error) {
      logger.warn('JWT verification failed', {
        error: error instanceof Error ? error.message : 'Unknown error',
        token: token.substring(0, 20) + '...'
      });
      return null;
    }
  }

  /**
   * Verify and decode refresh token
   */
  public verifyRefreshToken(token: string): RefreshTokenPayload | null {
    try {
      const decoded = jwt.verify(token, config.jwt.refreshSecret) as RefreshTokenPayload;

      // Check if refresh token is still valid (not revoked)
      if (!this.refreshTokens.has(decoded.token_id)) {
        logger.warn('Refresh token revoked or invalid', {
          user_id: decoded.user_id,
          token_id: decoded.token_id
        });
        return null;
      }

      // Check token expiration
      if (decoded.exp < Math.floor(Date.now() / 1000)) {
        this.revokeRefreshToken(decoded.token_id);
        logger.warn('Refresh token expired', {
          user_id: decoded.user_id,
          token_id: decoded.token_id
        });
        return null;
      }

      return decoded;
    } catch (error) {
      logger.warn('Refresh token verification failed', {
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      return null;
    }
  }

  /**
   * Revoke refresh token
   */
  public revokeRefreshToken(tokenId: string): void {
    this.refreshTokens.delete(tokenId);
    logger.info('Refresh token revoked', { token_id: tokenId });
  }

  /**
   * Revoke all refresh tokens for a user
   */
  public revokeAllUserTokens(userId: string): void {
    // In production, this would query Redis/database for user's tokens
    // For now, we'll clear all tokens (simplified implementation)
    const revokedCount = this.refreshTokens.size;
    this.refreshTokens.clear();

    logger.info('All user tokens revoked', {
      user_id: userId,
      revoked_count: revokedCount
    });
  }

  /**
   * Check if user has required subscription tier for feature access
   */
  public hasSubscriptionAccess(userTier: SubscriptionTier, requiredTier: SubscriptionTier): boolean {
    const tierHierarchy = {
      [SubscriptionTier.FREE]: 0,
      [SubscriptionTier.BASIC]: 1,
      [SubscriptionTier.PRO]: 2,
      [SubscriptionTier.ENTERPRISE]: 3
    };

    return tierHierarchy[userTier] >= tierHierarchy[requiredTier];
  }

  /**
   * Parse expiration time string to seconds
   */
  private parseExpirationTime(expirationString: string): number {
    const unit = expirationString.slice(-1);
    const value = parseInt(expirationString.slice(0, -1), 10);

    switch (unit) {
      case 's': return value;
      case 'm': return value * 60;
      case 'h': return value * 60 * 60;
      case 'd': return value * 60 * 60 * 24;
      default: return parseInt(expirationString, 10) || 900; // Default 15 minutes
    }
  }

  /**
   * Generate token pair (access + refresh)
   */
  public generateTokenPair(user: User): { accessToken: string; refreshToken: string } {
    const accessToken = this.generateAccessToken(user);
    const refreshToken = this.generateRefreshToken(user.id);

    logger.info('Token pair generated', {
      user_id: user.id,
      email: user.email,
      subscription_tier: user.subscription_tier
    });

    return { accessToken, refreshToken };
  }

  /**
   * Refresh access token using valid refresh token
   */
  public async refreshAccessToken(refreshToken: string, userProvider: (userId: string) => Promise<User | null>): Promise<{ accessToken: string; refreshToken: string } | null> {
    const refreshPayload = this.verifyRefreshToken(refreshToken);
    if (!refreshPayload) {
      return null;
    }

    // Get updated user data
    const user = await userProvider(refreshPayload.user_id);
    if (!user || !user.is_active) {
      this.revokeRefreshToken(refreshPayload.token_id);
      logger.warn('User not found or inactive during token refresh', {
        user_id: refreshPayload.user_id
      });
      return null;
    }

    // Revoke old refresh token
    this.revokeRefreshToken(refreshPayload.token_id);

    // Generate new token pair
    return this.generateTokenPair(user);
  }

  /**
   * Validate token format without verification (for logging/debugging)
   */
  public isValidTokenFormat(token: string): boolean {
    const parts = token.split('.');
    return parts.length === 3;
  }

  /**
   * Get token payload without verification (for debugging)
   */
  public decodeTokenUnsafe(token: string): any {
    try {
      return jwt.decode(token);
    } catch {
      return null;
    }
  }

  /**
   * Check if user is authorized for multi-tenant resource access
   */
  public isAuthorizedForResource(userPayload: JWTPayload, resourceUserId: string): boolean {
    // Users can only access their own resources unless they're enterprise tier with special permissions
    if (userPayload.user_id === resourceUserId) {
      return true;
    }

    // Enterprise tier users might have cross-account access (implement based on business rules)
    if (userPayload.subscription_tier === SubscriptionTier.ENTERPRISE) {
      // Implement enterprise-specific authorization logic here
      return false; // For now, even enterprise users can only access their own resources
    }

    return false;
  }

  /**
   * Get active refresh tokens count (for monitoring)
   */
  public getActiveTokensCount(): number {
    return this.refreshTokens.size;
  }

  /**
   * Cleanup expired tokens (should be called periodically)
   */
  public cleanupExpiredTokens(): number {
    // In production, this would be handled by Redis TTL or database cleanup job
    // For memory storage, we need to manually track and clean up
    let cleanedCount = 0;

    // This is a simplified cleanup - in production, store tokens with expiration timestamps
    // For now, we'll implement proper token storage in the database layer

    logger.info('Token cleanup completed', { cleaned_count: cleanedCount });
    return cleanedCount;
  }
}

// Export singleton instance
export const jwtManager = JWTManager.getInstance();