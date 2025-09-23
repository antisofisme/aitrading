const express = require('express');
const router = express.Router();
const userConfigController = require('../controllers/userConfigController');
const { authenticate, authorize } = require('../middleware/authMiddleware');
const { validateUserConfig, validateConfigUpdate } = require('../middleware/validationMiddleware');

// Get user configuration
router.get('/:userId', authenticate, userConfigController.getUserConfig);

// Get specific user configuration by key
router.get('/:userId/:configKey', authenticate, userConfigController.getUserConfigByKey);

// Create user configuration
router.post('/', authenticate, validateUserConfig, userConfigController.createUserConfig);

// Update user configuration
router.put('/:id', authenticate, validateConfigUpdate, userConfigController.updateUserConfig);

// Delete user configuration
router.delete('/:id', authenticate, authorize(['admin', 'user']), userConfigController.deleteUserConfig);

// Bulk update user configurations
router.put('/bulk/:userId', authenticate, userConfigController.bulkUpdateUserConfig);

// Get user configuration history
router.get('/:userId/history/:configKey', authenticate, userConfigController.getUserConfigHistory);

// Reset user configuration to default
router.post('/:userId/reset/:configKey', authenticate, userConfigController.resetUserConfigToDefault);

// Export user configuration
router.get('/:userId/export', authenticate, userConfigController.exportUserConfig);

// Import user configuration
router.post('/:userId/import', authenticate, userConfigController.importUserConfig);

module.exports = router;