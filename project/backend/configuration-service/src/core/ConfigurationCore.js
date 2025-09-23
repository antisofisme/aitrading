/**
 * ConfigurationCore - Core configuration management system
 *
 * Provides centralized configuration management with:
 * - Multi-tenant configuration isolation
 * - Configuration validation and schemas
 * - Hot-reload capabilities
 * - Configuration versioning
 * - Environment-specific configurations
 */

const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');
const crypto = require('crypto');

class ConfigurationCore {
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
          filename: 'logs/configuration-core.log',
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
    this.configCache = new Map();
    this.schemaRegistry = new Map();
    this.isInitialized = false;
    this.healthStatus = true;

    this.initializeValidationSchemas();
  }

  /**
   * Initialize configuration validation schemas
   */
  initializeValidationSchemas() {
    // Configuration schema
    this.configSchema = Joi.object({
      key: Joi.string().required(),
      value: Joi.any().required(),
      type: Joi.string().valid('string', 'number', 'boolean', 'object', 'array').required(),
      environment: Joi.string().valid('development', 'staging', 'production', 'global').default('global'),
      tenantId: Joi.string().optional(),
      userId: Joi.string().optional(),
      isSecret: Joi.boolean().default(false),
      version: Joi.string().default('1.0.0'),
      description: Joi.string().optional(),
      tags: Joi.array().items(Joi.string()).optional(),
      metadata: Joi.object().optional()
    });

    // Configuration template schema
    this.templateSchema = Joi.object({
      name: Joi.string().required(),
      description: Joi.string().optional(),
      configurations: Joi.array().items(this.configSchema).required(),
      environment: Joi.string().valid('development', 'staging', 'production', 'global').default('global'),
      tags: Joi.array().items(Joi.string()).optional(),
      metadata: Joi.object().optional()
    });
  }

  /**
   * Initialize the configuration core system
   */
  async initialize() {
    try {
      await this.initializeDatabase();
      await this.loadConfigurationsIntoCache();
      this.isInitialized = true;
      this.healthStatus = true;

      this.logger.info('ConfigurationCore initialized successfully', {
        cacheSize: this.configCache.size,
        schemaCount: this.schemaRegistry.size
      });
    } catch (error) {
      this.logger.error('Failed to initialize ConfigurationCore', {
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

      // Create configurations table
      await client.query(`
        CREATE TABLE IF NOT EXISTS configurations (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          key VARCHAR(255) NOT NULL,
          value_json JSONB NOT NULL,
          type VARCHAR(50) NOT NULL,
          environment VARCHAR(50) DEFAULT 'global',
          tenant_id VARCHAR(100),
          user_id VARCHAR(100),
          is_secret BOOLEAN DEFAULT false,
          version VARCHAR(20) DEFAULT '1.0.0',
          description TEXT,
          tags TEXT[],
          metadata_json JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          created_by VARCHAR(100),
          UNIQUE(key, environment, tenant_id, user_id)
        );
      `);

      // Create configuration templates table
      await client.query(`
        CREATE TABLE IF NOT EXISTS configuration_templates (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          name VARCHAR(255) UNIQUE NOT NULL,
          description TEXT,
          template_json JSONB NOT NULL,
          environment VARCHAR(50) DEFAULT 'global',
          tags TEXT[],
          metadata_json JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          created_by VARCHAR(100)
        );
      `);

      // Create configuration history table
      await client.query(`
        CREATE TABLE IF NOT EXISTS configuration_history (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          configuration_id UUID REFERENCES configurations(id) ON DELETE CASCADE,
          old_value_json JSONB,
          new_value_json JSONB,
          change_type VARCHAR(50) NOT NULL,
          changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          changed_by VARCHAR(100),
          reason TEXT
        );
      `);

      // Create indexes
      await client.query(`
        CREATE INDEX IF NOT EXISTS idx_configurations_key ON configurations(key);
        CREATE INDEX IF NOT EXISTS idx_configurations_environment ON configurations(environment);
        CREATE INDEX IF NOT EXISTS idx_configurations_tenant_id ON configurations(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_configurations_user_id ON configurations(user_id);
        CREATE INDEX IF NOT EXISTS idx_configurations_tags ON configurations USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_configuration_templates_name ON configuration_templates(name);
        CREATE INDEX IF NOT EXISTS idx_configuration_history_config_id ON configuration_history(configuration_id);
      `);

      await client.query('COMMIT');
      this.logger.info('ConfigurationCore database tables initialized successfully');
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Failed to initialize ConfigurationCore database tables', {
        error: error.message
      });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Load configurations into cache
   */
  async loadConfigurationsIntoCache() {
    try {
      const result = await this.pool.query(
        'SELECT * FROM configurations ORDER BY created_at DESC'
      );

      this.configCache.clear();
      for (const config of result.rows) {
        const cacheKey = this.generateCacheKey(
          config.key,
          config.environment,
          config.tenant_id,
          config.user_id
        );
        this.configCache.set(cacheKey, this.formatConfigurationResponse(config));
      }

      this.logger.info('Configurations loaded into cache', {
        count: result.rows.length
      });
    } catch (error) {
      this.logger.error('Failed to load configurations into cache', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Get configuration value
   */
  async getConfiguration(key, options = {}) {
    try {
      const {
        environment = 'global',
        tenantId = null,
        userId = null,
        useCache = true
      } = options;

      const cacheKey = this.generateCacheKey(key, environment, tenantId, userId);

      // Check cache first
      if (useCache && this.configCache.has(cacheKey)) {
        return this.configCache.get(cacheKey);
      }

      // Query database
      const result = await this.pool.query(
        `SELECT * FROM configurations 
         WHERE key = $1 AND environment = $2 
         AND (tenant_id = $3 OR tenant_id IS NULL)
         AND (user_id = $4 OR user_id IS NULL)
         ORDER BY 
           CASE WHEN tenant_id IS NOT NULL THEN 1 ELSE 2 END,
           CASE WHEN user_id IS NOT NULL THEN 1 ELSE 2 END
         LIMIT 1`,
        [key, environment, tenantId, userId]
      );

      if (result.rows.length === 0) {
        return null;
      }

      const config = this.formatConfigurationResponse(result.rows[0]);

      // Update cache
      if (useCache) {
        this.configCache.set(cacheKey, config);
      }

      return config;
    } catch (error) {
      this.logger.error('Failed to get configuration', {
        error: error.message,
        key,
        options
      });
      throw error;
    }
  }

  /**
   * Set configuration value
   */
  async setConfiguration(configData, options = {}) {
    try {
      const { changedBy = 'system', reason = 'Configuration update' } = options;

      // Validate configuration
      const { error, value } = this.configSchema.validate(configData);
      if (error) {
        throw new Error(`Configuration validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const validatedConfig = value;

      // Encrypt value if it's a secret
      let processedValue = validatedConfig.value;
      if (validatedConfig.isSecret && typeof processedValue === 'string') {
        processedValue = this.encryptValue(processedValue);
      }

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Check if configuration exists
        const existingResult = await client.query(
          `SELECT * FROM configurations 
           WHERE key = $1 AND environment = $2 
           AND (tenant_id = $3 OR (tenant_id IS NULL AND $3 IS NULL))
           AND (user_id = $4 OR (user_id IS NULL AND $4 IS NULL))`,
          [validatedConfig.key, validatedConfig.environment, validatedConfig.tenantId, validatedConfig.userId]
        );

        let configResult;
        if (existingResult.rows.length > 0) {
          // Update existing configuration
          const existingConfig = existingResult.rows[0];

          // Store history
          await client.query(
            `INSERT INTO configuration_history 
             (configuration_id, old_value_json, new_value_json, change_type, changed_by, reason)
             VALUES ($1, $2, $3, $4, $5, $6)`,
            [
              existingConfig.id,
              existingConfig.value_json,
              JSON.stringify(processedValue),
              'UPDATE',
              changedBy,
              reason
            ]
          );

          // Update configuration
          configResult = await client.query(
            `UPDATE configurations 
             SET value_json = $1, type = $2, is_secret = $3, version = $4,
                 description = $5, tags = $6, metadata_json = $7, updated_at = CURRENT_TIMESTAMP
             WHERE id = $8
             RETURNING *`,
            [
              JSON.stringify(processedValue),
              validatedConfig.type,
              validatedConfig.isSecret,
              validatedConfig.version,
              validatedConfig.description,
              validatedConfig.tags || [],
              JSON.stringify(validatedConfig.metadata || {}),
              existingConfig.id
            ]
          );
        } else {
          // Insert new configuration
          configResult = await client.query(
            `INSERT INTO configurations 
             (key, value_json, type, environment, tenant_id, user_id, is_secret, version, description, tags, metadata_json, created_by)
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
             RETURNING *`,
            [
              validatedConfig.key,
              JSON.stringify(processedValue),
              validatedConfig.type,
              validatedConfig.environment,
              validatedConfig.tenantId,
              validatedConfig.userId,
              validatedConfig.isSecret,
              validatedConfig.version,
              validatedConfig.description,
              validatedConfig.tags || [],
              JSON.stringify(validatedConfig.metadata || {}),
              changedBy
            ]
          );

          // Store creation history
          await client.query(
            `INSERT INTO configuration_history 
             (configuration_id, new_value_json, change_type, changed_by, reason)
             VALUES ($1, $2, $3, $4, $5)`,
            [
              configResult.rows[0].id,
              JSON.stringify(processedValue),
              'CREATE',
              changedBy,
              reason
            ]
          );
        }

        await client.query('COMMIT');

        const savedConfig = this.formatConfigurationResponse(configResult.rows[0]);

        // Update cache
        const cacheKey = this.generateCacheKey(
          validatedConfig.key,
          validatedConfig.environment,
          validatedConfig.tenantId,
          validatedConfig.userId
        );
        this.configCache.set(cacheKey, savedConfig);

        this.logger.info('Configuration saved successfully', {
          key: validatedConfig.key,
          environment: validatedConfig.environment,
          tenantId: validatedConfig.tenantId,
          userId: validatedConfig.userId
        });

        return savedConfig;
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to set configuration', {
        error: error.message,
        configData
      });
      throw error;
    }
  }

  /**
   * Delete configuration
   */
  async deleteConfiguration(key, options = {}) {
    try {
      const {
        environment = 'global',
        tenantId = null,
        userId = null,
        changedBy = 'system',
        reason = 'Configuration deletion'
      } = options;

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Get existing configuration
        const existingResult = await client.query(
          `SELECT * FROM configurations 
           WHERE key = $1 AND environment = $2 
           AND (tenant_id = $3 OR (tenant_id IS NULL AND $3 IS NULL))
           AND (user_id = $4 OR (user_id IS NULL AND $4 IS NULL))`,
          [key, environment, tenantId, userId]
        );

        if (existingResult.rows.length === 0) {
          throw new Error(`Configuration not found: ${key}`);
        }

        const existingConfig = existingResult.rows[0];

        // Store deletion history
        await client.query(
          `INSERT INTO configuration_history 
           (configuration_id, old_value_json, change_type, changed_by, reason)
           VALUES ($1, $2, $3, $4, $5)`,
          [
            existingConfig.id,
            existingConfig.value_json,
            'DELETE',
            changedBy,
            reason
          ]
        );

        // Delete configuration
        await client.query(
          'DELETE FROM configurations WHERE id = $1',
          [existingConfig.id]
        );

        await client.query('COMMIT');

        // Remove from cache
        const cacheKey = this.generateCacheKey(key, environment, tenantId, userId);
        this.configCache.delete(cacheKey);

        this.logger.info('Configuration deleted successfully', {
          key,
          environment,
          tenantId,
          userId
        });

        return true;
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to delete configuration', {
        error: error.message,
        key,
        options
      });
      throw error;
    }
  }

  /**
   * List configurations with filtering
   */
  async listConfigurations(options = {}) {
    try {
      const {
        environment,
        tenantId,
        userId,
        tags,
        keyPattern,
        page = 1,
        limit = 50,
        sortBy = 'created_at',
        sortOrder = 'DESC'
      } = options;

      let whereClause = '';
      const params = [];
      let paramCount = 0;
      const conditions = [];

      if (environment) {
        conditions.push(`environment = $${++paramCount}`);
        params.push(environment);
      }

      if (tenantId) {
        conditions.push(`tenant_id = $${++paramCount}`);
        params.push(tenantId);
      }

      if (userId) {
        conditions.push(`user_id = $${++paramCount}`);
        params.push(userId);
      }

      if (tags && tags.length > 0) {
        conditions.push(`tags && $${++paramCount}`);
        params.push(tags);
      }

      if (keyPattern) {
        conditions.push(`key ILIKE $${++paramCount}`);
        params.push(`%${keyPattern}%`);
      }

      if (conditions.length > 0) {
        whereClause = 'WHERE ' + conditions.join(' AND ');
      }

      const offset = (page - 1) * limit;

      // Get total count
      const countResult = await this.pool.query(
        `SELECT COUNT(*) FROM configurations ${whereClause}`,
        params
      );
      const totalCount = parseInt(countResult.rows[0].count);

      // Get configurations
      const result = await this.pool.query(
        `SELECT * FROM configurations ${whereClause}
         ORDER BY ${sortBy} ${sortOrder}
         LIMIT $${++paramCount} OFFSET $${++paramCount}`,
        [...params, limit, offset]
      );

      const configurations = result.rows.map(config => this.formatConfigurationResponse(config));

      return {
        configurations,
        pagination: {
          page,
          limit,
          totalCount,
          totalPages: Math.ceil(totalCount / limit),
          hasNext: page < Math.ceil(totalCount / limit),
          hasPrev: page > 1
        }
      };
    } catch (error) {
      this.logger.error('Failed to list configurations', {
        error: error.message,
        options
      });
      throw error;
    }
  }

  /**
   * Get configuration history
   */
  async getConfigurationHistory(configurationId, options = {}) {
    try {
      const { limit = 20, offset = 0 } = options;

      const result = await this.pool.query(
        `SELECT ch.*, c.key, c.environment, c.tenant_id, c.user_id
         FROM configuration_history ch
         JOIN configurations c ON ch.configuration_id = c.id
         WHERE ch.configuration_id = $1
         ORDER BY ch.changed_at DESC
         LIMIT $2 OFFSET $3`,
        [configurationId, limit, offset]
      );

      return result.rows.map(history => ({
        id: history.id,
        configurationId: history.configuration_id,
        key: history.key,
        environment: history.environment,
        tenantId: history.tenant_id,
        userId: history.user_id,
        oldValue: history.old_value_json ? JSON.parse(history.old_value_json) : null,
        newValue: history.new_value_json ? JSON.parse(history.new_value_json) : null,
        changeType: history.change_type,
        changedAt: history.changed_at,
        changedBy: history.changed_by,
        reason: history.reason
      }));
    } catch (error) {
      this.logger.error('Failed to get configuration history', {
        error: error.message,
        configurationId
      });
      throw error;
    }
  }

  /**
   * Check if the system is healthy
   */
  isHealthy() {
    return this.isInitialized && this.healthStatus;
  }

  /**
   * Generate cache key
   * @private
   */
  generateCacheKey(key, environment, tenantId, userId) {
    return `${key}:${environment}:${tenantId || 'null'}:${userId || 'null'}`;
  }

  /**
   * Encrypt sensitive values
   * @private
   */
  encryptValue(value) {
    const algorithm = 'aes-256-gcm';
    const secretKey = process.env.CONFIG_ENCRYPTION_KEY || 'default-key-change-in-production';
    const key = crypto.scryptSync(secretKey, 'salt', 32);
    const iv = crypto.randomBytes(16);
    
    const cipher = crypto.createCipher(algorithm, key);
    cipher.setAAD(Buffer.from('config-encryption', 'utf8'));
    
    let encrypted = cipher.update(value, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      encrypted: true,
      data: encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }

  /**
   * Decrypt sensitive values
   * @private
   */
  decryptValue(encryptedData) {
    if (!encryptedData.encrypted) {
      return encryptedData;
    }

    const algorithm = 'aes-256-gcm';
    const secretKey = process.env.CONFIG_ENCRYPTION_KEY || 'default-key-change-in-production';
    const key = crypto.scryptSync(secretKey, 'salt', 32);
    
    const decipher = crypto.createDecipher(algorithm, key);
    decipher.setAAD(Buffer.from('config-encryption', 'utf8'));
    decipher.setAuthTag(Buffer.from(encryptedData.authTag, 'hex'));
    
    let decrypted = decipher.update(encryptedData.data, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return decrypted;
  }

  /**
   * Format configuration response
   * @private
   */
  formatConfigurationResponse(config) {
    let value = typeof config.value_json === 'string' 
      ? JSON.parse(config.value_json) 
      : config.value_json;

    // Decrypt if it's a secret
    if (config.is_secret && typeof value === 'object' && value.encrypted) {
      try {
        value = this.decryptValue(value);
      } catch (error) {
        this.logger.warn('Failed to decrypt configuration value', {
          configId: config.id,
          key: config.key
        });
        value = '[ENCRYPTED]';
      }
    }

    return {
      id: config.id,
      key: config.key,
      value,
      type: config.type,
      environment: config.environment,
      tenantId: config.tenant_id,
      userId: config.user_id,
      isSecret: config.is_secret,
      version: config.version,
      description: config.description,
      tags: config.tags || [],
      metadata: typeof config.metadata_json === 'string'
        ? JSON.parse(config.metadata_json)
        : config.metadata_json || {},
      createdAt: config.created_at,
      updatedAt: config.updated_at,
      createdBy: config.created_by
    };
  }

  /**
   * Close database connection
   */
  async close() {
    await this.pool.end();
    this.logger.info('ConfigurationCore database connection closed');
  }
}

module.exports = ConfigurationCore;
