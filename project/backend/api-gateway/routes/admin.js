const express = require('express');
const { requireAdmin } = require('../middleware/auth');
const { UserStore } = require('../models/User');

const router = express.Router();

/**
 * @route   GET /api/admin/users
 * @desc    Get all users (admin only)
 * @access  Private (Admin)
 */
router.get('/users', requireAdmin, (req, res) => {
  try {
    const users = UserStore.getAllUsers();

    res.json({
      success: true,
      data: {
        users,
        total: users.length
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Failed to fetch users',
      error: error.message
    });
  }
});

/**
 * @route   GET /api/admin/stats
 * @desc    Get system statistics (admin only)
 * @access  Private (Admin)
 */
router.get('/stats', requireAdmin, (req, res) => {
  try {
    const totalUsers = UserStore.users.size;
    const activeUsers = Array.from(UserStore.users.values())
      .filter(user => user.isActive).length;
    const adminUsers = Array.from(UserStore.users.values())
      .filter(user => user.role === 'admin').length;

    res.json({
      success: true,
      data: {
        totalUsers,
        activeUsers,
        adminUsers,
        inactiveUsers: totalUsers - activeUsers
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      message: 'Failed to fetch statistics',
      error: error.message
    });
  }
});

module.exports = router;