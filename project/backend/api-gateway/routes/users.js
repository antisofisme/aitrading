/**
 * User Management Routes
 * Admin endpoints for user management
 */

const express = require('express');
const router = express.Router();
const User = require('../models/User');
const { database } = require('../config/database');
const {
  authenticateToken,
  adminOnly,
  selfOrAdmin
} = require('../middleware/auth');

/**
 * GET /users
 * Get all users (admin only)
 */
router.get('/', authenticateToken, adminOnly, async (req, res) => {
  try {
    const {
      role,
      isActive,
      search,
      page = 1,
      limit = 20,
      sortBy = 'createdAt',
      sortOrder = 'desc'
    } = req.query;

    // Build filters
    const filters = {};
    if (role) filters.role = role;
    if (isActive !== undefined) filters.isActive = isActive === 'true';
    if (search) filters.search = search;

    // Get users
    let users = await User.findAll(filters);

    // Sort users
    users.sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];

      if (sortOrder === 'desc') {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      } else {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      }
    });

    // Pagination
    const pageNum = parseInt(page);
    const limitNum = parseInt(limit);
    const startIndex = (pageNum - 1) * limitNum;
    const endIndex = startIndex + limitNum;

    const paginatedUsers = users.slice(startIndex, endIndex);

    res.json({
      success: true,
      message: 'Users retrieved successfully',
      data: {
        users: paginatedUsers,
        pagination: {
          currentPage: pageNum,
          totalPages: Math.ceil(users.length / limitNum),
          totalUsers: users.length,
          hasNextPage: endIndex < users.length,
          hasPrevPage: pageNum > 1
        }
      }
    });

  } catch (error) {
    console.error('Get users error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to retrieve users',
      code: 'USERS_RETRIEVAL_FAILED'
    });
  }
});

/**
 * GET /users/:userId
 * Get specific user by ID
 */
router.get('/:userId', authenticateToken, selfOrAdmin(), async (req, res) => {
  try {
    const { userId } = req.params;

    const user = await User.findById(userId);

    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    res.json({
      success: true,
      message: 'User retrieved successfully',
      data: {
        user: User.sanitize(user)
      }
    });

  } catch (error) {
    console.error('Get user error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to retrieve user',
      code: 'USER_RETRIEVAL_FAILED'
    });
  }
});

/**
 * POST /users
 * Create new user (admin only)
 */
router.post('/', authenticateToken, adminOnly, async (req, res) => {
  try {
    const { email, password, firstName, lastName, role = 'user' } = req.body;

    // Create user
    const user = await User.create({
      email: email?.toLowerCase(),
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
    console.error('Create user error:', error.message);

    res.status(400).json({
      success: false,
      message: error.message || 'Failed to create user',
      code: 'USER_CREATION_FAILED'
    });
  }
});

/**
 * PUT /users/:userId
 * Update user (admin or self)
 */
router.put('/:userId', authenticateToken, selfOrAdmin(), async (req, res) => {
  try {
    const { userId } = req.params;
    const { firstName, lastName, role, isActive, emailVerified } = req.body;

    // Check if user exists
    const existingUser = await User.findById(userId);
    if (!existingUser) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    // Build update data
    const updateData = {};
    if (firstName !== undefined) updateData.firstName = firstName;
    if (lastName !== undefined) updateData.lastName = lastName;

    // Only admin can update role, isActive, and emailVerified
    if (req.user.role === 'admin') {
      if (role !== undefined) updateData.role = role;
      if (isActive !== undefined) updateData.isActive = isActive;
      if (emailVerified !== undefined) updateData.emailVerified = emailVerified;
    } else {
      // Users can't change their own role or account status
      if (role !== undefined || isActive !== undefined || emailVerified !== undefined) {
        return res.status(403).json({
          success: false,
          message: 'Cannot modify role, active status, or email verification',
          code: 'INSUFFICIENT_PERMISSIONS'
        });
      }
    }

    // Update user
    const updatedUser = await User.update(userId, updateData);

    // Log admin actions
    if (req.user.role === 'admin' && req.user.id !== userId) {
      console.log(`User ${userId} updated by admin ${req.user.email}`);
    }

    res.json({
      success: true,
      message: 'User updated successfully',
      data: {
        user: User.sanitize(updatedUser)
      }
    });

  } catch (error) {
    console.error('Update user error:', error.message);

    res.status(400).json({
      success: false,
      message: error.message || 'Failed to update user',
      code: 'USER_UPDATE_FAILED'
    });
  }
});

/**
 * DELETE /users/:userId
 * Delete user (admin only)
 */
router.delete('/:userId', authenticateToken, adminOnly, async (req, res) => {
  try {
    const { userId } = req.params;

    // Check if user exists
    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    // Prevent admin from deleting themselves
    if (req.user.id === userId) {
      return res.status(400).json({
        success: false,
        message: 'Cannot delete your own account',
        code: 'CANNOT_DELETE_SELF'
      });
    }

    // Delete user
    await User.delete(userId);

    // Delete user's sessions
    await database.deleteUserSessions(userId);

    console.log(`User ${user.email} deleted by admin ${req.user.email}`);

    res.json({
      success: true,
      message: 'User deleted successfully',
      data: {}
    });

  } catch (error) {
    console.error('Delete user error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to delete user',
      code: 'USER_DELETION_FAILED'
    });
  }
});

/**
 * POST /users/:userId/deactivate
 * Deactivate user account (admin only)
 */
router.post('/:userId/deactivate', authenticateToken, adminOnly, async (req, res) => {
  try {
    const { userId } = req.params;

    // Check if user exists
    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    // Prevent admin from deactivating themselves
    if (req.user.id === userId) {
      return res.status(400).json({
        success: false,
        message: 'Cannot deactivate your own account',
        code: 'CANNOT_DEACTIVATE_SELF'
      });
    }

    // Deactivate user
    const updatedUser = await User.update(userId, {
      isActive: false,
      updatedAt: new Date()
    });

    // Delete user's active sessions
    await database.deleteUserSessions(userId);

    console.log(`User ${user.email} deactivated by admin ${req.user.email}`);

    res.json({
      success: true,
      message: 'User deactivated successfully',
      data: {
        user: User.sanitize(updatedUser)
      }
    });

  } catch (error) {
    console.error('Deactivate user error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to deactivate user',
      code: 'USER_DEACTIVATION_FAILED'
    });
  }
});

/**
 * POST /users/:userId/activate
 * Activate user account (admin only)
 */
router.post('/:userId/activate', authenticateToken, adminOnly, async (req, res) => {
  try {
    const { userId } = req.params;

    // Check if user exists
    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({
        success: false,
        message: 'User not found',
        code: 'USER_NOT_FOUND'
      });
    }

    // Activate user
    const updatedUser = await User.update(userId, {
      isActive: true,
      updatedAt: new Date()
    });

    console.log(`User ${user.email} activated by admin ${req.user.email}`);

    res.json({
      success: true,
      message: 'User activated successfully',
      data: {
        user: User.sanitize(updatedUser)
      }
    });

  } catch (error) {
    console.error('Activate user error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to activate user',
      code: 'USER_ACTIVATION_FAILED'
    });
  }
});

/**
 * GET /users/stats/overview
 * Get user statistics (admin only)
 */
router.get('/stats/overview', authenticateToken, adminOnly, async (req, res) => {
  try {
    const users = await User.findAll();

    const stats = {
      totalUsers: users.length,
      activeUsers: users.filter(u => u.isActive).length,
      inactiveUsers: users.filter(u => !u.isActive).length,
      adminUsers: users.filter(u => u.role === 'admin').length,
      regularUsers: users.filter(u => u.role === 'user').length,
      verifiedEmails: users.filter(u => u.emailVerified).length,
      unverifiedEmails: users.filter(u => !u.emailVerified).length,
      recentRegistrations: users.filter(u => {
        const dayAgo = new Date();
        dayAgo.setDate(dayAgo.getDate() - 1);
        return new Date(u.createdAt) > dayAgo;
      }).length
    };

    res.json({
      success: true,
      message: 'User statistics retrieved successfully',
      data: {
        stats
      }
    });

  } catch (error) {
    console.error('Get user stats error:', error.message);

    res.status(500).json({
      success: false,
      message: 'Failed to retrieve user statistics',
      code: 'STATS_RETRIEVAL_FAILED'
    });
  }
});

module.exports = router;