/**
 * UserConfigManager - Per-user configuration management service
 *
 * Provides user-specific configuration management with:
 * - Individual user configuration profiles
 * - Configuration inheritance from global settings
 * - User preference management
 * - Configuration validation
 * - Multi-tenant user isolation
 */

const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');

class UserConfigManager {
  constructor(logger = null, dbConfig = null) {
    this.logger = logger || winston.createLogger({
      level: 'info',
      format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
      ),
      transports: [
        new winston.transports.Console(),
        new winston.transports.File({
          filename: 'logs/user-config-manager.log',
          maxsize: 5242880, // 5MB
          maxFiles: 5
        })
      ]
    });

    this.dbConfig = dbConfig || {
      host: process.env.DB_HOST || 'localhost',
      port: process.env.DB_PORT || 5432,
      database: process.env.DB_NAME || 'configuration_service',
      user: process.env.DB_USER || 'config_user',
      password: process.env.DB_PASSWORD || 'config_password',
      ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
      max: 20,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000
    };

    this.pool = new Pool(this.dbConfig);
    this.userConfigCache = new Map();
    this.isInitialized = false;
    this.healthStatus = true;

    this.initializeValidationSchemas();
  }

  /**
   * Initialize validation schemas
   */
  initializeValidationSchemas() {
    // User configuration schema
    this.userConfigSchema = Joi.object({
      userId: Joi.string().required(),
      tenantId: Joi.string().optional(),
      preferences: Joi.object().optional(),
      settings: Joi.object().optional(),
      theme: Joi.object({
        mode: Joi.string().valid('light', 'dark', 'auto').default('auto'),
        primaryColor: Joi.string().optional(),
        fontSize: Joi.string().valid('small', 'medium', 'large').default('medium')
      }).optional(),
      notifications: Joi.object({
        email: Joi.boolean().default(true),
        push: Joi.boolean().default(true),
        sms: Joi.boolean().default(false),
        frequency: Joi.string().valid('immediate', 'hourly', 'daily').default('immediate')
      }).optional(),
      privacy: Joi.object({
        profileVisibility: Joi.string().valid('public', 'private', 'contacts').default('private'),
        dataSharing: Joi.boolean().default(false),
        analytics: Joi.boolean().default(true)
      }).optional(),
      api: Joi.object({
        rateLimit: Joi.number().min(10).max(10000).default(1000),
        timeout: Joi.number().min(1000).max(60000).default(30000),
        retries: Joi.number().min(0).max(10).default(3)
      }).optional(),
      features: Joi.object().optional(),
      metadata: Joi.object().optional()
    });

    // User profile schema
    this.userProfileSchema = Joi.object({
      userId: Joi.string().required(),
      tenantId: Joi.string().optional(),
      firstName: Joi.string().optional(),
      lastName: Joi.string().optional(),
      email: Joi.string().email().optional(),
      avatar: Joi.string().uri().optional(),
      timezone: Joi.string().optional(),
      locale: Joi.string().optional(),
      role: Joi.string().optional(),
      department: Joi.string().optional(),
      metadata: Joi.object().optional()
    });
  }

  /**
   * Initialize the user config manager
   */
  async initialize() {
    try {
      await this.initializeDatabase();
      this.isInitialized = true;
      this.healthStatus = true;

      this.logger.info('UserConfigManager initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize UserConfigManager', {
        error: error.message,
        stack: error.stack
      });
      this.healthStatus = false;
      throw error;
    }
  }

  /**
   * Initialize database tables
   */
  async initializeDatabase() {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');

      // Create user configurations table
      await client.query(`
        CREATE TABLE IF NOT EXISTS user_configurations (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id VARCHAR(100) NOT NULL,
          tenant_id VARCHAR(100),
          config_json JSONB NOT NULL DEFAULT '{}',
          preferences_json JSONB DEFAULT '{}',
          settings_json JSONB DEFAULT '{}',
          theme_json JSONB DEFAULT '{}',
          notifications_json JSONB DEFAULT '{}',
          privacy_json JSONB DEFAULT '{}',
          api_json JSONB DEFAULT '{}',
          features_json JSONB DEFAULT '{}',
          metadata_json JSONB DEFAULT '{}',
          version VARCHAR(20) DEFAULT '1.0.0',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id, tenant_id)
        );
      `);

      // Create user profiles table
      await client.query(`
        CREATE TABLE IF NOT EXISTS user_profiles (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id VARCHAR(100) NOT NULL,
          tenant_id VARCHAR(100),
          first_name VARCHAR(100),
          last_name VARCHAR(100),
          email VARCHAR(255),
          avatar VARCHAR(500),
          timezone VARCHAR(50),
          locale VARCHAR(10),
          role VARCHAR(100),
          department VARCHAR(100),
          metadata_json JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          UNIQUE(user_id, tenant_id)
        );
      `);

      // Create user configuration history table
      await client.query(`
        CREATE TABLE IF NOT EXISTS user_config_history (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_config_id UUID REFERENCES user_configurations(id) ON DELETE CASCADE,
          old_config_json JSONB,
          new_config_json JSONB,
          change_type VARCHAR(50) NOT NULL,
          changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          changed_by VARCHAR(100),
          reason TEXT
        );
      `);

      // Create indexes
      await client.query(`
        CREATE INDEX IF NOT EXISTS idx_user_configurations_user_id ON user_configurations(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_configurations_tenant_id ON user_configurations(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_user_configurations_last_accessed ON user_configurations(last_accessed);
        CREATE INDEX IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_profiles_tenant_id ON user_profiles(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
        CREATE INDEX IF NOT EXISTS idx_user_config_history_config_id ON user_config_history(user_config_id);
      `);

      await client.query('COMMIT');
      this.logger.info('UserConfigManager database tables initialized successfully');
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Failed to initialize UserConfigManager database tables', {
        error: error.message
      });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Get user configuration
   */
  async getUserConfig(userId, tenantId = null, options = {}) {
    try {
      const { useCache = true, includeDefaults = true } = options;

      const cacheKey = `${userId}:${tenantId || 'null'}`;

      // Check cache first
      if (useCache && this.userConfigCache.has(cacheKey)) {
        const cached = this.userConfigCache.get(cacheKey);
        // Update last accessed
        this.updateLastAccessed(cached.id);
        return cached;
      }

      // Query database
      const result = await this.pool.query(
        `SELECT uc.*, up.first_name, up.last_name, up.email, up.avatar, up.timezone, up.locale, up.role, up.department
         FROM user_configurations uc
         LEFT JOIN user_profiles up ON uc.user_id = up.user_id AND (uc.tenant_id = up.tenant_id OR (uc.tenant_id IS NULL AND up.tenant_id IS NULL))
         WHERE uc.user_id = $1 AND (uc.tenant_id = $2 OR (uc.tenant_id IS NULL AND $2 IS NULL))
         ORDER BY uc.tenant_id NULLS LAST
         LIMIT 1`,
        [userId, tenantId]
      );

      let userConfig;
      if (result.rows.length === 0) {
        if (includeDefaults) {
          // Create default configuration
          userConfig = await this.createDefaultUserConfig(userId, tenantId);
        } else {
          return null;
        }
      } else {
        userConfig = this.formatUserConfigResponse(result.rows[0]);
        // Update last accessed
        this.updateLastAccessed(userConfig.id);
      }

      // Update cache
      if (useCache) {
        this.userConfigCache.set(cacheKey, userConfig);
      }

      return userConfig;
    } catch (error) {
      this.logger.error('Failed to get user configuration', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Update user configuration
   */
  async updateUserConfig(userId, configData, tenantId = null, options = {}) {
    try {
      const { changedBy = 'user', reason = 'User configuration update' } = options;

      // Validate configuration data
      const { error, value } = this.userConfigSchema.validate({
        userId,
        tenantId,
        ...configData
      });
      if (error) {
        throw new Error(`User configuration validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const validatedConfig = value;

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Get existing configuration
        const existingResult = await client.query(
          `SELECT * FROM user_configurations 
           WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL))`,
          [userId, tenantId]
        );

        let configResult;
        if (existingResult.rows.length > 0) {
          // Update existing configuration
          const existingConfig = existingResult.rows[0];

          // Store history
          await client.query(
            `INSERT INTO user_config_history 
             (user_config_id, old_config_json, new_config_json, change_type, changed_by, reason)
             VALUES ($1, $2, $3, $4, $5, $6)`,
            [
              existingConfig.id,
              existingConfig.config_json,
              JSON.stringify(validatedConfig),
              'UPDATE',
              changedBy,
              reason
            ]
          );

          // Update configuration
          configResult = await client.query(
            `UPDATE user_configurations 
             SET config_json = $1, preferences_json = $2, settings_json = $3,
                 theme_json = $4, notifications_json = $5, privacy_json = $6,
                 api_json = $7, features_json = $8, metadata_json = $9,
                 updated_at = CURRENT_TIMESTAMP, last_accessed = CURRENT_TIMESTAMP
             WHERE id = $10
             RETURNING *`,
            [
              JSON.stringify(validatedConfig),
              JSON.stringify(validatedConfig.preferences || {}),
              JSON.stringify(validatedConfig.settings || {}),
              JSON.stringify(validatedConfig.theme || {}),
              JSON.stringify(validatedConfig.notifications || {}),
              JSON.stringify(validatedConfig.privacy || {}),
              JSON.stringify(validatedConfig.api || {}),
              JSON.stringify(validatedConfig.features || {}),
              JSON.stringify(validatedConfig.metadata || {}),
              existingConfig.id
            ]
          );
        } else {
          // Insert new configuration
          configResult = await client.query(
            `INSERT INTO user_configurations 
             (user_id, tenant_id, config_json, preferences_json, settings_json,
              theme_json, notifications_json, privacy_json, api_json, features_json, metadata_json)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
             RETURNING *`,
            [
              userId,
              tenantId,
              JSON.stringify(validatedConfig),
              JSON.stringify(validatedConfig.preferences || {}),
              JSON.stringify(validatedConfig.settings || {}),
              JSON.stringify(validatedConfig.theme || {}),
              JSON.stringify(validatedConfig.notifications || {}),
              JSON.stringify(validatedConfig.privacy || {}),
              JSON.stringify(validatedConfig.api || {}),
              JSON.stringify(validatedConfig.features || {}),
              JSON.stringify(validatedConfig.metadata || {})
            ]
          );

          // Store creation history
          await client.query(
            `INSERT INTO user_config_history 
             (user_config_id, new_config_json, change_type, changed_by, reason)
             VALUES ($1, $2, $3, $4, $5)`,
            [
              configResult.rows[0].id,
              JSON.stringify(validatedConfig),
              'CREATE',
              changedBy,
              reason
            ]
          );
        }

        await client.query('COMMIT');

        const updatedConfig = this.formatUserConfigResponse(configResult.rows[0]);

        // Update cache
        const cacheKey = `${userId}:${tenantId || 'null'}`;
        this.userConfigCache.set(cacheKey, updatedConfig);

        this.logger.info('User configuration updated successfully', {
          userId,
          tenantId,
          changedBy
        });

        return updatedConfig;
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to update user configuration', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Create default user configuration
   */
  async createDefaultUserConfig(userId, tenantId = null) {
    const defaultConfig = {
      userId,
      tenantId,
      preferences: {},
      settings: {},
      theme: {
        mode: 'auto',
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
      api: {
        rateLimit: 1000,
        timeout: 30000,
        retries: 3
      },
      features: {},
      metadata: {}
    };

    return await this.updateUserConfig(userId, defaultConfig, tenantId, {
      changedBy: 'system',
      reason: 'Default user configuration creation'
    });
  }

  /**
   * Update user profile
   */
  async updateUserProfile(userId, profileData, tenantId = null) {
    try {
      // Validate profile data
      const { error, value } = this.userProfileSchema.validate({
        userId,
        tenantId,
        ...profileData
      });
      if (error) {
        throw new Error(`User profile validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const validatedProfile = value;

      const result = await this.pool.query(
        `INSERT INTO user_profiles 
         (user_id, tenant_id, first_name, last_name, email, avatar, timezone, locale, role, department, metadata_json)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
         ON CONFLICT (user_id, tenant_id) DO UPDATE SET
           first_name = EXCLUDED.first_name,
           last_name = EXCLUDED.last_name,
           email = EXCLUDED.email,
           avatar = EXCLUDED.avatar,
           timezone = EXCLUDED.timezone,
           locale = EXCLUDED.locale,
           role = EXCLUDED.role,
           department = EXCLUDED.department,
           metadata_json = EXCLUDED.metadata_json,
           updated_at = CURRENT_TIMESTAMP
         RETURNING *`,
        [
          userId,
          tenantId,
          validatedProfile.firstName,
          validatedProfile.lastName,
          validatedProfile.email,
          validatedProfile.avatar,
          validatedProfile.timezone,
          validatedProfile.locale,
          validatedProfile.role,
          validatedProfile.department,
          JSON.stringify(validatedProfile.metadata || {})
        ]
      );

      // Clear cache to force refresh
      const cacheKey = `${userId}:${tenantId || 'null'}`;
      this.userConfigCache.delete(cacheKey);

      this.logger.info('User profile updated successfully', {
        userId,
        tenantId
      });

      return this.formatUserProfileResponse(result.rows[0]);
    } catch (error) {
      this.logger.error('Failed to update user profile', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Get user configuration history
   */
  async getUserConfigHistory(userId, tenantId = null, options = {}) {
    try {
      const { limit = 20, offset = 0 } = options;

      // First get the user config ID
      const configResult = await this.pool.query(
        `SELECT id FROM user_configurations 
         WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL))`,
        [userId, tenantId]
      );

      if (configResult.rows.length === 0) {
        return [];
      }

      const configId = configResult.rows[0].id;

      const result = await this.pool.query(
        `SELECT * FROM user_config_history
         WHERE user_config_id = $1
         ORDER BY changed_at DESC
         LIMIT $2 OFFSET $3`,
        [configId, limit, offset]
      );

      return result.rows.map(history => ({
        id: history.id,
        userConfigId: history.user_config_id,
        oldConfig: history.old_config_json ? JSON.parse(history.old_config_json) : null,
        newConfig: history.new_config_json ? JSON.parse(history.new_config_json) : null,
        changeType: history.change_type,
        changedAt: history.changed_at,
        changedBy: history.changed_by,
        reason: history.reason
      }));
    } catch (error) {
      this.logger.error('Failed to get user configuration history', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Update last accessed timestamp
   * @private
   */
  async updateLastAccessed(configId) {
    try {
      await this.pool.query(
        'UPDATE user_configurations SET last_accessed = CURRENT_TIMESTAMP WHERE id = $1',
        [configId]
      );
    } catch (error) {
      // Log but don't throw - this is not critical
      this.logger.warn('Failed to update last accessed timestamp', {
        error: error.message,
        configId
      });
    }
  }

  /**
   * Check if the service is healthy
   */
  isHealthy() {
    return this.isInitialized && this.healthStatus;
  }

  /**
   * Format user configuration response
   * @private
   */
  formatUserConfigResponse(config) {
    return {
      id: config.id,
      userId: config.user_id,
      tenantId: config.tenant_id,
      config: typeof config.config_json === 'string'
        ? JSON.parse(config.config_json)
        : config.config_json || {},
      preferences: typeof config.preferences_json === 'string'
        ? JSON.parse(config.preferences_json)
        : config.preferences_json || {},
      settings: typeof config.settings_json === 'string'
        ? JSON.parse(config.settings_json)
        : config.settings_json || {},
      theme: typeof config.theme_json === 'string'
        ? JSON.parse(config.theme_json)
        : config.theme_json || {},
      notifications: typeof config.notifications_json === 'string'
        ? JSON.parse(config.notifications_json)
        : config.notifications_json || {},
      privacy: typeof config.privacy_json === 'string'
        ? JSON.parse(config.privacy_json)
        : config.privacy_json || {},
      api: typeof config.api_json === 'string'
        ? JSON.parse(config.api_json)
        : config.api_json || {},
      features: typeof config.features_json === 'string'
        ? JSON.parse(config.features_json)
        : config.features_json || {},
      metadata: typeof config.metadata_json === 'string'
        ? JSON.parse(config.metadata_json)
        : config.metadata_json || {},
      version: config.version,
      createdAt: config.created_at,
      updatedAt: config.updated_at,
      lastAccessed: config.last_accessed,
      profile: {
        firstName: config.first_name,
        lastName: config.last_name,
        email: config.email,
        avatar: config.avatar,
        timezone: config.timezone,
        locale: config.locale,
        role: config.role,
        department: config.department
      }
    };
  }

  /**
   * Format user profile response
   * @private
   */
  formatUserProfileResponse(profile) {
    return {
      id: profile.id,
      userId: profile.user_id,
      tenantId: profile.tenant_id,
      firstName: profile.first_name,
      lastName: profile.last_name,
      email: profile.email,
      avatar: profile.avatar,
      timezone: profile.timezone,
      locale: profile.locale,
      role: profile.role,
      department: profile.department,
      metadata: typeof profile.metadata_json === 'string'
        ? JSON.parse(profile.metadata_json)
        : profile.metadata_json || {},
      createdAt: profile.created_at,
      updatedAt: profile.updated_at
    };
  }

  /**
   * Close database connection
   */
  async close() {
    await this.pool.end();
    this.logger.info('UserConfigManager database connection closed');
  }
}

module.exports = UserConfigManager;
