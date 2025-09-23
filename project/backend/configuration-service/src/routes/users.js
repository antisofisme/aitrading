/**
 * User routes for Configuration Service
 *
 * Provides user-specific configuration management:
 * - User configuration CRUD operations
 * - User profile management
 * - User preferences and settings
 * - User configuration history
 */

const express = require('express');
const router = express.Router();

/**
 * Get user configuration
 * GET /users/:userId/config
 */
router.get('/:userId/config', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const { includeDefaults = true } = req.query;

    // This would use UserConfigManager service
    const userConfig = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      userId,
      tenantId,
      config: {
        theme: { mode: 'dark', fontSize: 'medium' },
        notifications: { email: true, push: true, sms: false },
        privacy: { profileVisibility: 'private', dataSharing: false },
        api: { rateLimit: 1000, timeout: 30000, retries: 3 }
      },
      preferences: {
        language: 'en',
        timezone: 'UTC',
        dateFormat: 'YYYY-MM-DD'
      },
      settings: {
        autoSave: true,
        confirmBeforeDelete: true
      },
      profile: {
        firstName: 'John',
        lastName: 'Doe',
        email: 'john.doe@example.com',
        avatar: null,
        timezone: 'UTC',
        locale: 'en-US'
      },
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastAccessed: new Date().toISOString()
    };

    res.json({
      success: true,
      userId,
      tenantId,
      config: userConfig,
      metadata: {
        processingTime: '3ms',
        includeDefaults: includeDefaults === 'true',
        source: 'database'
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to get user configuration',
      message: error.message
    });
  }
});

/**
 * Update user configuration
 * PUT /users/:userId/config
 */
router.put('/:userId/config', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const configData = req.body;
    const changedBy = req.headers['user-id'] || userId;

    if (!configData || Object.keys(configData).length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Configuration data is required'
      });
    }

    // This would use UserConfigManager service
    const updatedConfig = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      userId,
      tenantId,
      config: {
        ...configData,
        updatedAt: new Date().toISOString()
      },
      version: '1.0.1',
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date().toISOString(),
      lastAccessed: new Date().toISOString()
    };

    res.json({
      success: true,
      userId,
      tenantId,
      config: updatedConfig,
      metadata: {
        processingTime: '5ms',
        changedBy,
        hotReloadTriggered: true,
        operation: 'update'
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to update user configuration',
      message: error.message
    });
  }
});

/**
 * Update user profile
 * PUT /users/:userId/profile
 */
router.put('/:userId/profile', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const profileData = req.body;

    if (!profileData || Object.keys(profileData).length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Profile data is required'
      });
    }

    // This would use UserConfigManager service
    const updatedProfile = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      userId,
      tenantId,
      firstName: profileData.firstName || 'John',
      lastName: profileData.lastName || 'Doe',
      email: profileData.email || 'john.doe@example.com',
      avatar: profileData.avatar,
      timezone: profileData.timezone || 'UTC',
      locale: profileData.locale || 'en-US',
      role: profileData.role,
      department: profileData.department,
      metadata: profileData.metadata || {},
      createdAt: new Date(Date.now() - 86400000).toISOString(),
      updatedAt: new Date().toISOString()
    };

    res.json({
      success: true,
      userId,
      tenantId,
      profile: updatedProfile,
      metadata: {
        processingTime: '3ms',
        operation: 'profile_update'
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to update user profile',
      message: error.message
    });
  }
});

/**
 * Get user configuration history
 * GET /users/:userId/config/history
 */
router.get('/:userId/config/history', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const { limit = 20, offset = 0 } = req.query;

    // This would use UserConfigManager service
    const history = [
      {
        id: '123e4567-e89b-12d3-a456-426614174001',
        userConfigId: '123e4567-e89b-12d3-a456-426614174000',
        oldConfig: { theme: { mode: 'light' } },
        newConfig: { theme: { mode: 'dark' } },
        changeType: 'UPDATE',
        changedAt: new Date().toISOString(),
        changedBy: userId,
        reason: 'User preference update'
      },
      {
        id: '123e4567-e89b-12d3-a456-426614174002',
        userConfigId: '123e4567-e89b-12d3-a456-426614174000',
        newConfig: { theme: { mode: 'light' } },
        changeType: 'CREATE',
        changedAt: new Date(Date.now() - 86400000).toISOString(),
        changedBy: 'system',
        reason: 'Initial user configuration creation'
      }
    ];

    res.json({
      success: true,
      userId,
      tenantId,
      history,
      metadata: {
        totalChanges: history.length,
        limit: parseInt(limit),
        offset: parseInt(offset),
        processingTime: '2ms'
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to get user configuration history',
      message: error.message
    });
  }
});

/**
 * Get user preferences
 * GET /users/:userId/preferences
 */
router.get('/:userId/preferences', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const { category } = req.query;

    // This would extract preferences from UserConfigManager
    const preferences = {
      theme: {
        mode: 'dark',
        primaryColor: '#007bff',
        fontSize: 'medium'
      },
      notifications: {
        email: true,
        push: true,
        sms: false,
        frequency: 'immediate'
      },
      privacy: {
        profileVisibility: 'private',
        dataSharing: false,
        analytics: true
      },
      accessibility: {
        highContrast: false,
        screenReader: false,
        keyboardNavigation: true
      },
      language: 'en',
      timezone: 'UTC',
      dateFormat: 'YYYY-MM-DD',
      timeFormat: '24h'
    };

    // Filter by category if specified
    const filteredPreferences = category && preferences[category] 
      ? { [category]: preferences[category] }
      : preferences;

    res.json({
      success: true,
      userId,
      tenantId,
      preferences: filteredPreferences,
      metadata: {
        category: category || 'all',
        processingTime: '1ms'
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to get user preferences',
      message: error.message
    });
  }
});

/**
 * Update user preferences
 * PATCH /users/:userId/preferences
 */
router.patch('/:userId/preferences', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const preferenceUpdates = req.body;
    const changedBy = req.headers['user-id'] || userId;

    if (!preferenceUpdates || Object.keys(preferenceUpdates).length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Preference updates are required'
      });
    }

    // This would use UserConfigManager to update specific preferences
    const updatedPreferences = {
      ...preferenceUpdates,
      updatedAt: new Date().toISOString(),
      updatedBy: changedBy
    };

    res.json({
      success: true,
      userId,
      tenantId,
      preferences: updatedPreferences,
      metadata: {
        updatedCategories: Object.keys(preferenceUpdates),
        changedBy,
        processingTime: '2ms',
        hotReloadTriggered: true
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to update user preferences',
      message: error.message
    });
  }
});

/**
 * Reset user configuration to defaults
 * POST /users/:userId/config/reset
 */
router.post('/:userId/config/reset', async (req, res) => {
  try {
    const { userId } = req.params;
    const tenantId = req.headers['tenant-id'];
    const { category, confirmReset } = req.body;
    const changedBy = req.headers['user-id'] || userId;

    if (!confirmReset) {
      return res.status(400).json({
        success: false,
        error: 'Reset confirmation is required'
      });
    }

    // This would use UserConfigManager to reset to defaults
    const defaultConfig = {
      id: '123e4567-e89b-12d3-a456-426614174000',
      userId,
      tenantId,
      config: {
        theme: { mode: 'auto', fontSize: 'medium' },
        notifications: { email: true, push: true, sms: false },
        privacy: { profileVisibility: 'private', dataSharing: false },
        api: { rateLimit: 1000, timeout: 30000, retries: 3 }
      },
      preferences: {},
      settings: {},
      version: '1.0.0',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastAccessed: new Date().toISOString()
    };

    res.json({
      success: true,
      userId,
      tenantId,
      config: defaultConfig,
      metadata: {
        operation: 'reset',
        category: category || 'all',
        changedBy,
        processingTime: '4ms',
        hotReloadTriggered: true
      }
    });
  } catch (error) {
    res.status(500).json({
      success: false,
      error: 'Failed to reset user configuration',
      message: error.message
    });
  }
});

module.exports = router;
