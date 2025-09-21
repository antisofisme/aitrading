/**
 * Authentication Routes
 * Login, logout, refresh token, and user management endpoints
 */

const express = require('express');
const router = express.Router();
const User = require('../models/User');
const jwtService = require('../utils/jwt');
const passwordService = require('../utils/password');
const { database } = require('../config/database');
const {
  authenticateToken,
  validateRefreshToken,
  adminOnly
} = require('../middleware/auth');
const { strictAuthRateLimit } = require('../middleware/security');

/**
 * POST /auth/login
 */
router.post('/login', strictAuthRateLimit, async (req, res) => {
  try {
    const { email, password, rememberMe = false } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Email and password are required',
        code: 'MISSING_CREDENTIALS'
      });
    }

    const user = await User.authenticate(email.toLowerCase(), password);
    const tokenPair = jwtService.generateTokenPair(user);

    const session = await database.createSession(user.id, {
      rememberMe,
      userAgent: req.headers['user-agent'],
      ipAddress: req.ip,
      refreshTokenJti: jwtService.decodeToken(tokenPair.refreshToken).payload.jti
    });

    console.log(`User ${user.email} logged in successfully from ${req.ip}`);

    res.json({
      success: true,
      message: 'Login successful',
      data: {
        user: User.sanitize(user),
        tokens: tokenPair,
        sessionId: session.id
      }
    });

  } catch (error) {
    console.error('Login error:', error.message);

    res.status(401).json({
      success: false,
      message: error.message === 'Invalid credentials' ? 'Invalid email or password' : 'Login failed',
      code: 'LOGIN_FAILED'
    });
  }
});

/**
 * POST /auth/logout
 */
router.post('/logout', authenticateToken, async (req, res) => {
  try {
    const { sessionId } = req.body;

    if (sessionId) {
      await database.deleteSession(sessionId);
    } else {
      await database.deleteUserSessions(req.user.id);
    }

    console.log(`User ${req.user.email} logged out successfully`);

    res.json({
      success: true,
      message: 'Logout successful',
      data: {}
    });

  } catch (error) {
    console.error('Logout error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Logout failed',
      code: 'LOGOUT_FAILED'
    });
  }
});

/**
 * POST /auth/refresh
 */
router.post('/refresh', validateRefreshToken, async (req, res) => {
  try {
    const user = req.user;
    const tokenPair = jwtService.generateTokenPair(user);

    res.json({
      success: true,
      message: 'Token refreshed successfully',
      data: {
        tokens: tokenPair
      }
    });

  } catch (error) {
    console.error('Token refresh error:', error.message);

    res.status(401).json({
      success: false,
      message: 'Token refresh failed',
      code: 'REFRESH_FAILED'
    });
  }
});

/**
 * GET /auth/me
 */
router.get('/me', authenticateToken, async (req, res) => {
  try {
    const user = await User.findById(req.user.id);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    res.json({
      success: true,
      message: 'User profile retrieved successfully',
      data: {
        user: User.sanitize(user)
      }
    });

  } catch (error) {
    console.error('Get profile error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to retrieve user profile',
      code: 'PROFILE_RETRIEVAL_FAILED'
    });
  }
});

/**
 * POST /auth/register (admin only)
 */
router.post('/register', authenticateToken, adminOnly, async (req, res) => {
  try {
    const { email, password, firstName, lastName, role = 'user' } = req.body;

    const user = await User.create({
      email: email.toLowerCase(),
      password,
      firstName,
      lastName,
      role,
      emailVerified: true
    });

    console.log(`User ${user.email} created by admin ${req.user.email}`);

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      data: {
        user: User.sanitize(user)
      }
    });

  } catch (error) {
    console.error('User registration error:', error.message);

    res.status(400).json({
      success: false,
      message: error.message || 'User registration failed',
      code: 'REGISTRATION_FAILED'
    });
  }
});

module.exports = router;