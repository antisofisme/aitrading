const jwt = require('jsonwebtoken');
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'user-management-tokenService' }
});

const JWT_SECRET = process.env.JWT_SECRET || 'fallback-secret-change-in-production';
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET || 'fallback-refresh-secret-change-in-production';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '1h';
const JWT_REFRESH_EXPIRES_IN = process.env.JWT_REFRESH_EXPIRES_IN || '7d';

/**
 * Generate access and refresh tokens
 */
function generateTokens(user) {
  try {
    const payload = {
      userId: user.id,
      email: user.email,
      subscription: user.subscription,
      isActive: user.isActive,
      emailVerified: user.emailVerified
    };

    // Generate access token (short-lived)
    const accessToken = jwt.sign(payload, JWT_SECRET, {
      expiresIn: JWT_EXPIRES_IN,
      issuer: 'aitrading-user-management',
      audience: 'aitrading-services'
    });

    // Generate refresh token (long-lived)
    const refreshToken = jwt.sign(
      { userId: user.id, type: 'refresh' },
      JWT_REFRESH_SECRET,
      {
        expiresIn: JWT_REFRESH_EXPIRES_IN,
        issuer: 'aitrading-user-management',
        audience: 'aitrading-services'
      }
    );

    return {
      accessToken,
      refreshToken,
      expiresIn: JWT_EXPIRES_IN
    };

  } catch (error) {
    logger.error('Error generating tokens:', error);
    throw error;
  }
}

/**
 * Verify access token
 */
function verifyAccessToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET, {
      issuer: 'aitrading-user-management',
      audience: 'aitrading-services'
    });
  } catch (error) {
    logger.warn('Access token verification failed:', error.message);
    return null;
  }
}

/**
 * Verify refresh token
 */
function verifyRefreshToken(token) {
  try {
    const decoded = jwt.verify(token, JWT_REFRESH_SECRET, {
      issuer: 'aitrading-user-management',
      audience: 'aitrading-services'
    });

    if (decoded.type !== 'refresh') {
      throw new Error('Invalid token type');
    }

    return decoded;
  } catch (error) {
    logger.warn('Refresh token verification failed:', error.message);
    return null;
  }
}

/**
 * Generate password reset token
 */
function generatePasswordResetToken(userId) {
  try {
    return jwt.sign(
      { userId, type: 'password_reset' },
      JWT_SECRET,
      {
        expiresIn: '1h', // Short expiry for security
        issuer: 'aitrading-user-management',
        audience: 'aitrading-services'
      }
    );
  } catch (error) {
    logger.error('Error generating password reset token:', error);
    throw error;
  }
}

/**
 * Verify password reset token
 */
function verifyPasswordResetToken(token) {
  try {
    const decoded = jwt.verify(token, JWT_SECRET, {
      issuer: 'aitrading-user-management',
      audience: 'aitrading-services'
    });

    if (decoded.type !== 'password_reset') {
      throw new Error('Invalid token type');
    }

    return decoded;
  } catch (error) {
    logger.warn('Password reset token verification failed:', error.message);
    return null;
  }
}

/**
 * Generate email verification token
 */
function generateEmailVerificationToken(userId) {
  try {
    return jwt.sign(
      { userId, type: 'email_verification' },
      JWT_SECRET,
      {
        expiresIn: '24h',
        issuer: 'aitrading-user-management',
        audience: 'aitrading-services'
      }
    );
  } catch (error) {
    logger.error('Error generating email verification token:', error);
    throw error;
  }
}

/**
 * Verify email verification token
 */
function verifyEmailVerificationToken(token) {
  try {
    const decoded = jwt.verify(token, JWT_SECRET, {
      issuer: 'aitrading-user-management',
      audience: 'aitrading-services'
    });

    if (decoded.type !== 'email_verification') {
      throw new Error('Invalid token type');
    }

    return decoded;
  } catch (error) {
    logger.warn('Email verification token verification failed:', error.message);
    return null;
  }
}

/**
 * Decode token without verification (for expired token info)
 */
function decodeToken(token) {
  try {
    return jwt.decode(token);
  } catch (error) {
    logger.warn('Token decode failed:', error.message);
    return null;
  }
}

/**
 * Get token expiry time
 */
function getTokenExpiry(token) {
  try {
    const decoded = jwt.decode(token);
    if (decoded && decoded.exp) {
      return new Date(decoded.exp * 1000);
    }
    return null;
  } catch (error) {
    logger.warn('Error getting token expiry:', error.message);
    return null;
  }
}

/**
 * Check if token is expired
 */
function isTokenExpired(token) {
  try {
    const expiry = getTokenExpiry(token);
    if (!expiry) return true;
    return expiry < new Date();
  } catch (error) {
    logger.warn('Error checking token expiry:', error.message);
    return true;
  }
}

module.exports = {
  generateTokens,
  verifyAccessToken,
  verifyRefreshToken,
  generatePasswordResetToken,
  verifyPasswordResetToken,
  generateEmailVerificationToken,
  verifyEmailVerificationToken,
  decodeToken,
  getTokenExpiry,
  isTokenExpired
};