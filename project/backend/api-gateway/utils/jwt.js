/**
 * JWT Utility Functions
 * Token generation, validation, and management
 */

const jwt = require('jsonwebtoken');
const { v4: uuidv4 } = require('uuid');
const jwtConfig = require('../config/jwt');

class JWTService {
  /**
   * Generate access token
   */
  generateAccessToken(payload) {
    const tokenPayload = {
      sub: payload.id,
      email: payload.email,
      role: payload.role,
      jti: uuidv4(),
      iat: Math.floor(Date.now() / 1000),
      type: 'access'
    };

    return jwt.sign(
      tokenPayload,
      jwtConfig.accessTokenSecret,
      {
        expiresIn: jwtConfig.accessTokenExpiry,
        issuer: jwtConfig.accessTokenOptions.issuer,
        audience: jwtConfig.accessTokenOptions.audience,
        algorithm: jwtConfig.accessTokenOptions.algorithm
      }
    );
  }

  /**
   * Generate refresh token
   */
  generateRefreshToken(payload) {
    const tokenPayload = {
      sub: payload.id,
      email: payload.email,
      jti: uuidv4(),
      iat: Math.floor(Date.now() / 1000),
      type: 'refresh'
    };

    return jwt.sign(
      tokenPayload,
      jwtConfig.refreshTokenSecret,
      {
        expiresIn: jwtConfig.refreshTokenExpiry,
        issuer: jwtConfig.refreshTokenOptions.issuer,
        audience: jwtConfig.refreshTokenOptions.audience,
        algorithm: jwtConfig.refreshTokenOptions.algorithm
      }
    );
  }

  /**
   * Generate token pair
   */
  generateTokenPair(user) {
    const payload = {
      id: user.id,
      email: user.email,
      role: user.role
    };

    const accessToken = this.generateAccessToken(payload);
    const refreshToken = this.generateRefreshToken(payload);

    return {
      accessToken,
      refreshToken,
      tokenType: 'Bearer',
      expiresIn: this.getExpirySeconds(jwtConfig.accessTokenExpiry)
    };
  }

  /**
   * Verify access token
   */
  verifyAccessToken(token) {
    try {
      const decoded = jwt.verify(token, jwtConfig.accessTokenSecret, {
        issuer: jwtConfig.accessTokenOptions.issuer,
        audience: jwtConfig.accessTokenOptions.audience,
        algorithms: [jwtConfig.accessTokenOptions.algorithm]
      });

      if (decoded.type !== 'access') {
        throw new Error('Invalid token type');
      }

      return decoded;
    } catch (error) {
      throw new Error(`Access token verification failed: ${error.message}`);
    }
  }

  /**
   * Verify refresh token
   */
  verifyRefreshToken(token) {
    try {
      const decoded = jwt.verify(token, jwtConfig.refreshTokenSecret, {
        issuer: jwtConfig.refreshTokenOptions.issuer,
        audience: jwtConfig.refreshTokenOptions.audience,
        algorithms: [jwtConfig.refreshTokenOptions.algorithm]
      });

      if (decoded.type !== 'refresh') {
        throw new Error('Invalid token type');
      }

      return decoded;
    } catch (error) {
      throw new Error(`Refresh token verification failed: ${error.message}`);
    }
  }

  /**
   * Extract token from Authorization header
   */
  extractTokenFromHeader(authHeader) {
    if (!authHeader) return null;

    const parts = authHeader.split(' ');
    if (parts.length !== 2 || parts[0] !== 'Bearer') {
      return null;
    }

    return parts[1];
  }

  /**
   * Convert expiry string to seconds
   */
  getExpirySeconds(expiry) {
    const units = { s: 1, m: 60, h: 3600, d: 86400 };
    const match = expiry.match(/^(\d+)([smhd])$/);
    if (!match) return 900; // Default 15 minutes

    const value = parseInt(match[1]);
    const unit = match[2];
    return value * (units[unit] || 900);
  }

  /**
   * Decode token without verification
   */
  decodeToken(token) {
    try {
      return jwt.decode(token, { complete: true });
    } catch (error) {
      throw new Error(`Token decode failed: ${error.message}`);
    }
  }
}

module.exports = new JWTService();