const { User, UserStore } = require('../models/User');
const JWTUtils = require('../utils/jwt');
const Joi = require('joi');

/**
 * Validation schemas
 */
const loginSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().required()
});

const registerSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).required(),
  role: Joi.string().valid('admin', 'user').optional()
});

const refreshTokenSchema = Joi.object({
  refreshToken: Joi.string().required()
});

class AuthController {
  /**
   * User registration
   */
  static async register(req, res) {
    try {
      const { error, value } = registerSchema.validate(req.body);
      if (error) {
        return res.status(400).json({
          success: false,
          message: 'Validation error',
          errors: error.details.map(detail => detail.message)
        });
      }

      const { email, password, role } = value;

      // Check if user already exists
      const existingUser = User.findByEmail(email);
      if (existingUser) {
        return res.status(409).json({
          success: false,
          message: 'User already exists with this email'
        });
      }

      // Create new user
      const user = await User.create({ email, password, role });

      // Generate tokens
      const tokens = JWTUtils.generateTokenPair(user);

      // Store refresh token
      UserStore.storeRefreshToken(user.id, tokens.refreshToken);

      res.status(201).json({
        success: true,
        message: 'User registered successfully',
        data: {
          user: user.toJSON(),
          ...tokens
        }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Registration failed',
        error: error.message
      });
    }
  }

  /**
   * User login
   */
  static async login(req, res) {
    try {
      const { error, value } = loginSchema.validate(req.body);
      if (error) {
        return res.status(400).json({
          success: false,
          message: 'Validation error',
          errors: error.details.map(detail => detail.message)
        });
      }

      const { email, password } = value;

      // Find user by email
      const user = User.findByEmail(email);
      if (!user) {
        return res.status(401).json({
          success: false,
          message: 'Invalid credentials'
        });
      }

      // Check if user is active
      if (!user.isActive) {
        return res.status(401).json({
          success: false,
          message: 'Account is disabled'
        });
      }

      // Verify password
      const isPasswordValid = await user.verifyPassword(password);
      if (!isPasswordValid) {
        return res.status(401).json({
          success: false,
          message: 'Invalid credentials'
        });
      }

      // Generate tokens
      const tokens = JWTUtils.generateTokenPair(user);

      // Store refresh token
      UserStore.storeRefreshToken(user.id, tokens.refreshToken);

      res.json({
        success: true,
        message: 'Login successful',
        data: {
          user: user.toJSON(),
          ...tokens
        }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Login failed',
        error: error.message
      });
    }
  }

  /**
   * Token refresh
   */
  static async refreshToken(req, res) {
    try {
      const { error, value } = refreshTokenSchema.validate(req.body);
      if (error) {
        return res.status(400).json({
          success: false,
          message: 'Validation error',
          errors: error.details.map(detail => detail.message)
        });
      }

      const { refreshToken } = value;

      // Verify refresh token
      const decoded = JWTUtils.verifyRefreshToken(refreshToken);
      const userId = decoded.userId;

      // Check if refresh token exists in store
      const storedRefreshToken = UserStore.getRefreshToken(userId);
      if (!storedRefreshToken || storedRefreshToken !== refreshToken) {
        return res.status(401).json({
          success: false,
          message: 'Invalid refresh token'
        });
      }

      // Find user
      const user = User.findById(userId);
      if (!user || !user.isActive) {
        return res.status(401).json({
          success: false,
          message: 'User not found or inactive'
        });
      }

      // Generate new tokens
      const tokens = JWTUtils.generateTokenPair(user);

      // Update stored refresh token
      UserStore.storeRefreshToken(user.id, tokens.refreshToken);

      res.json({
        success: true,
        message: 'Token refreshed successfully',
        data: tokens
      });
    } catch (error) {
      res.status(401).json({
        success: false,
        message: 'Token refresh failed',
        error: error.message
      });
    }
  }

  /**
   * User logout
   */
  static async logout(req, res) {
    try {
      const userId = req.user.userId;

      // Remove refresh token
      UserStore.removeRefreshToken(userId);

      res.json({
        success: true,
        message: 'Logged out successfully'
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Logout failed',
        error: error.message
      });
    }
  }

  /**
   * Get current user profile
   */
  static async getProfile(req, res) {
    try {
      const userId = req.user.userId;
      const user = User.findById(userId);

      if (!user) {
        return res.status(404).json({
          success: false,
          message: 'User not found'
        });
      }

      res.json({
        success: true,
        data: {
          user: user.toJSON()
        }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Failed to get profile',
        error: error.message
      });
    }
  }

  /**
   * Verify token endpoint
   */
  static async verifyToken(req, res) {
    try {
      // If we reach here, token is valid (middleware already verified it)
      res.json({
        success: true,
        message: 'Token is valid',
        data: {
          user: req.user
        }
      });
    } catch (error) {
      res.status(500).json({
        success: false,
        message: 'Token verification failed',
        error: error.message
      });
    }
  }
}

module.exports = AuthController;