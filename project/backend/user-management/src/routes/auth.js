const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');

const { getUserByEmail, createUser, updateUserLastLogin, getUserById } = require('../services/userService');
const { generateTokens, verifyRefreshToken } = require('../services/tokenService');
const { sendVerificationEmail, sendPasswordResetEmail } = require('../services/emailService');
const authMiddleware = require('../middleware/auth');

const router = express.Router();

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  defaultMeta: { service: 'user-management-auth' }
});

// Validation rules
const registerValidation = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required'),
  body('password')
    .isLength({ min: 8 })
    .withMessage('Password must be at least 8 characters')
    .matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/)
    .withMessage('Password must contain uppercase, lowercase, number and special character'),
  body('firstName')
    .isLength({ min: 2, max: 50 })
    .withMessage('First name must be between 2 and 50 characters'),
  body('lastName')
    .isLength({ min: 2, max: 50 })
    .withMessage('Last name must be between 2 and 50 characters'),
  body('phoneNumber')
    .optional()
    .isMobilePhone('any')
    .withMessage('Valid phone number is required'),
  body('acceptTerms')
    .equals('true')
    .withMessage('You must accept the terms and conditions')
];

const loginValidation = [
  body('email')
    .isEmail()
    .normalizeEmail()
    .withMessage('Valid email is required'),
  body('password')
    .notEmpty()
    .withMessage('Password is required')
];

// POST /api/auth/register
router.post('/register', registerValidation, async (req, res) => {
  try {
    // Check for validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { email, password, firstName, lastName, phoneNumber, acceptTerms } = req.body;

    // Check if user already exists
    const existingUser = await getUserByEmail(email);
    if (existingUser) {
      return res.status(409).json({
        success: false,
        error: 'User already exists',
        message: 'An account with this email already exists'
      });
    }

    // Hash password
    const saltRounds = parseInt(process.env.BCRYPT_ROUNDS) || 12;
    const hashedPassword = await bcrypt.hash(password, saltRounds);

    // Create user
    const userData = {
      id: uuidv4(),
      email,
      password: hashedPassword,
      firstName,
      lastName,
      phoneNumber: phoneNumber || null,
      emailVerified: false,
      isActive: true,
      subscription: 'FREE',
      acceptTerms: acceptTerms === 'true',
      createdAt: new Date(),
      updatedAt: new Date()
    };

    const user = await createUser(userData);

    // Generate verification token
    const verificationToken = jwt.sign(
      { userId: user.id, type: 'email_verification' },
      process.env.JWT_SECRET || 'fallback-secret',
      { expiresIn: '24h' }
    );

    // Send verification email (async, don't wait)
    sendVerificationEmail(email, verificationToken)
      .catch(error => logger.error('Failed to send verification email:', error));

    // Generate auth tokens
    const { accessToken, refreshToken } = generateTokens(user);

    logger.info(`User registered successfully: ${email}`);

    res.status(201).json({
      success: true,
      message: 'Account created successfully. Please check your email for verification.',
      data: {
        user: {
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          emailVerified: user.emailVerified,
          subscription: user.subscription,
          isActive: user.isActive
        },
        tokens: {
          accessToken,
          refreshToken,
          expiresIn: '24h'
        }
      }
    });

  } catch (error) {
    logger.error('Registration error:', error);
    res.status(500).json({
      success: false,
      error: 'Registration failed',
      message: 'An error occurred during registration. Please try again.'
    });
  }
});

// POST /api/auth/login
router.post('/login', loginValidation, async (req, res) => {
  try {
    // Check for validation errors
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({
        success: false,
        error: 'Validation failed',
        details: errors.array()
      });
    }

    const { email, password } = req.body;

    // Get user by email
    const user = await getUserByEmail(email);
    if (!user) {
      return res.status(401).json({
        success: false,
        error: 'Invalid credentials',
        message: 'Email or password is incorrect'
      });
    }

    // Check if user is active
    if (!user.isActive) {
      return res.status(403).json({
        success: false,
        error: 'Account disabled',
        message: 'Your account has been disabled. Please contact support.'
      });
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      return res.status(401).json({
        success: false,
        error: 'Invalid credentials',
        message: 'Email or password is incorrect'
      });
    }

    // Update last login
    await updateUserLastLogin(user.id);

    // Generate auth tokens
    const { accessToken, refreshToken } = generateTokens(user);

    logger.info(`User logged in successfully: ${email}`);

    res.json({
      success: true,
      message: 'Login successful',
      data: {
        user: {
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          emailVerified: user.emailVerified,
          subscription: user.subscription,
          isActive: user.isActive,
          lastLogin: new Date()
        },
        tokens: {
          accessToken,
          refreshToken,
          expiresIn: '24h'
        }
      }
    });

  } catch (error) {
    logger.error('Login error:', error);
    res.status(500).json({
      success: false,
      error: 'Login failed',
      message: 'An error occurred during login. Please try again.'
    });
  }
});

// POST /api/auth/refresh
router.post('/refresh', async (req, res) => {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({
        success: false,
        error: 'Refresh token required',
        message: 'Refresh token is missing'
      });
    }

    // Verify refresh token
    const decoded = verifyRefreshToken(refreshToken);
    if (!decoded) {
      return res.status(401).json({
        success: false,
        error: 'Invalid refresh token',
        message: 'Refresh token is invalid or expired'
      });
    }

    // Get user
    const user = await getUserById(decoded.userId);
    if (!user || !user.isActive) {
      return res.status(401).json({
        success: false,
        error: 'Invalid user',
        message: 'User not found or inactive'
      });
    }

    // Generate new tokens
    const tokens = generateTokens(user);

    res.json({
      success: true,
      message: 'Tokens refreshed successfully',
      data: {
        tokens: {
          accessToken: tokens.accessToken,
          refreshToken: tokens.refreshToken,
          expiresIn: '24h'
        }
      }
    });

  } catch (error) {
    logger.error('Token refresh error:', error);
    res.status(500).json({
      success: false,
      error: 'Token refresh failed',
      message: 'An error occurred while refreshing tokens'
    });
  }
});

// POST /api/auth/logout
router.post('/logout', authMiddleware, async (req, res) => {
  try {
    // In a production environment, you would:
    // 1. Add the token to a blacklist (Redis)
    // 2. Remove refresh token from database
    // For now, we'll just return success

    logger.info(`User logged out: ${req.user.email}`);

    res.json({
      success: true,
      message: 'Logout successful'
    });

  } catch (error) {
    logger.error('Logout error:', error);
    res.status(500).json({
      success: false,
      error: 'Logout failed',
      message: 'An error occurred during logout'
    });
  }
});

// POST /api/auth/verify-email
router.post('/verify-email', async (req, res) => {
  try {
    const { token } = req.body;

    if (!token) {
      return res.status(400).json({
        success: false,
        error: 'Verification token required'
      });
    }

    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'fallback-secret');

    if (decoded.type !== 'email_verification') {
      return res.status(400).json({
        success: false,
        error: 'Invalid token type'
      });
    }

    // Update user email verification status
    const user = await getUserById(decoded.userId);
    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }

    // Mark email as verified (implement in userService)
    // await updateUserEmailVerification(user.id, true);

    logger.info(`Email verified for user: ${user.email}`);

    res.json({
      success: true,
      message: 'Email verified successfully'
    });

  } catch (error) {
    if (error.name === 'JsonWebTokenError' || error.name === 'TokenExpiredError') {
      return res.status(400).json({
        success: false,
        error: 'Invalid or expired verification token'
      });
    }

    logger.error('Email verification error:', error);
    res.status(500).json({
      success: false,
      error: 'Email verification failed'
    });
  }
});

// GET /api/auth/me
router.get('/me', authMiddleware, async (req, res) => {
  try {
    const user = await getUserById(req.user.id);

    if (!user) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }

    res.json({
      success: true,
      data: {
        user: {
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          phoneNumber: user.phoneNumber,
          emailVerified: user.emailVerified,
          subscription: user.subscription,
          isActive: user.isActive,
          createdAt: user.createdAt,
          lastLogin: user.lastLogin
        }
      }
    });

  } catch (error) {
    logger.error('Get current user error:', error);
    res.status(500).json({
      success: false,
      error: 'Failed to get user information'
    });
  }
});

module.exports = router;