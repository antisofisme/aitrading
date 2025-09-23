const userConfigService = require('../services/userConfigService');
const logger = require('../utils/logger');
const { ApiError } = require('../utils/apiError');

class UserConfigController {
  async getUserConfig(req, res, next) {
    try {
      const { userId } = req.params;
      const { configType, isActive } = req.query;

      const config = await userConfigService.getUserConfig(userId, { configType, isActive });

      res.json({
        success: true,
        data: config,
        message: 'User configuration retrieved successfully'
      });
    } catch (error) {
      logger.error('Error getting user config:', error);
      next(error);
    }
  }

  async getUserConfigByKey(req, res, next) {
    try {
      const { userId, configKey } = req.params;

      const config = await userConfigService.getUserConfigByKey(userId, configKey);

      if (!config) {
        throw new ApiError(404, `Configuration not found for key: ${configKey}`);
      }

      res.json({
        success: true,
        data: config,
        message: 'User configuration retrieved successfully'
      });
    } catch (error) {
      logger.error('Error getting user config by key:', error);
      next(error);
    }
  }

  async createUserConfig(req, res, next) {
    try {
      const {
        userId,
        configKey,
        configValue,
        configType = 'user',
        isEncrypted = false,
        metadata = {}
      } = req.body;

      const config = await userConfigService.createUserConfig({
        userId,
        configKey,
        configValue,
        configType,
        isEncrypted,
        metadata
      });

      res.status(201).json({
        success: true,
        data: config,
        message: 'User configuration created successfully'
      });
    } catch (error) {
      logger.error('Error creating user config:', error);
      next(error);
    }
  }

  async updateUserConfig(req, res, next) {
    try {
      const { id } = req.params;
      const updateData = req.body;

      const config = await userConfigService.updateUserConfig(id, updateData);

      res.json({
        success: true,
        data: config,
        message: 'User configuration updated successfully'
      });
    } catch (error) {
      logger.error('Error updating user config:', error);
      next(error);
    }
  }

  async deleteUserConfig(req, res, next) {
    try {
      const { id } = req.params;

      await userConfigService.deleteUserConfig(id);

      res.json({
        success: true,
        message: 'User configuration deleted successfully'
      });
    } catch (error) {
      logger.error('Error deleting user config:', error);
      next(error);
    }
  }

  async bulkUpdateUserConfig(req, res, next) {
    try {
      const { userId } = req.params;
      const { configurations } = req.body;

      const result = await userConfigService.bulkUpdateUserConfig(userId, configurations);

      res.json({
        success: true,
        data: result,
        message: 'User configurations updated successfully'
      });
    } catch (error) {
      logger.error('Error bulk updating user config:', error);
      next(error);
    }
  }

  async getUserConfigHistory(req, res, next) {
    try {
      const { userId, configKey } = req.params;
      const { limit = 50, offset = 0 } = req.query;

      const history = await userConfigService.getUserConfigHistory(userId, configKey, {
        limit: parseInt(limit),
        offset: parseInt(offset)
      });

      res.json({
        success: true,
        data: history,
        message: 'User configuration history retrieved successfully'
      });
    } catch (error) {
      logger.error('Error getting user config history:', error);
      next(error);
    }
  }

  async resetUserConfigToDefault(req, res, next) {
    try {
      const { userId, configKey } = req.params;

      const config = await userConfigService.resetUserConfigToDefault(userId, configKey);

      res.json({
        success: true,
        data: config,
        message: 'User configuration reset to default successfully'
      });
    } catch (error) {
      logger.error('Error resetting user config to default:', error);
      next(error);
    }
  }

  async exportUserConfig(req, res, next) {
    try {
      const { userId } = req.params;
      const { format = 'json' } = req.query;

      const exportData = await userConfigService.exportUserConfig(userId, format);

      res.setHeader('Content-Disposition', `attachment; filename=user-config-${userId}.${format}`);
      res.setHeader('Content-Type', format === 'json' ? 'application/json' : 'text/plain');

      res.send(exportData);
    } catch (error) {
      logger.error('Error exporting user config:', error);
      next(error);
    }
  }

  async importUserConfig(req, res, next) {
    try {
      const { userId } = req.params;
      const { configData, overwrite = false } = req.body;

      const result = await userConfigService.importUserConfig(userId, configData, overwrite);

      res.json({
        success: true,
        data: result,
        message: 'User configuration imported successfully'
      });
    } catch (error) {
      logger.error('Error importing user config:', error);
      next(error);
    }
  }
}

module.exports = new UserConfigController();