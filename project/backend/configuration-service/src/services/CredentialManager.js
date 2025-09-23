/**
 * CredentialManager - Secure credential storage and management service
 *
 * Provides enterprise-grade credential management with:
 * - AES-256 encryption for sensitive data
 * - Multi-tenant credential isolation
 * - Credential versioning and rotation
 * - Audit logging for credential access
 * - Support for various credential types (API keys, tokens, secrets, OAuth)
 */

const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');
const crypto = require('crypto');

// Credential Types enumeration
const CredentialType = {
  API_KEY: 'api_key',
  TOKEN: 'token',
  SECRET: 'secret',
  OAUTH: 'oauth',
  DATABASE: 'database',
  CERTIFICATE: 'certificate',
  SSH_KEY: 'ssh_key',
  WEBHOOK: 'webhook'
};

// Credential Status enumeration
const CredentialStatus = {
  ACTIVE: 'active',
  EXPIRED: 'expired',
  REVOKED: 'revoked',
  SUSPENDED: 'suspended'
};

class CredentialManager {
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
          filename: 'logs/credential-manager.log',
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
    this.encryptionKey = this.deriveEncryptionKey();
    this.credentialCache = new Map();
    this.isInitialized = false;
    this.healthStatus = true;

    this.initializeValidationSchemas();
  }

  /**
   * Derive encryption key from environment or generate one
   * @private
   */
  deriveEncryptionKey() {
    const masterKey = process.env.CREDENTIAL_ENCRYPTION_KEY || 'default-master-key-change-in-production';
    const salt = process.env.CREDENTIAL_ENCRYPTION_SALT || 'credential-salt';
    return crypto.scryptSync(masterKey, salt, 32);
  }

  /**
   * Initialize validation schemas
   */
  initializeValidationSchemas() {
    // Credential schema
    this.credentialSchema = Joi.object({
      userId: Joi.string().required(),
      tenantId: Joi.string().optional(),
      name: Joi.string().min(1).max(255).required(),
      type: Joi.string().valid(...Object.values(CredentialType)).required(),
      description: Joi.string().max(1000).optional(),
      credentials: Joi.object().required(),
      scope: Joi.array().items(Joi.string()).optional(),
      tags: Joi.array().items(Joi.string()).optional(),
      expiresAt: Joi.date().optional(),
      rotationPolicy: Joi.object({
        enabled: Joi.boolean().default(false),
        intervalDays: Joi.number().min(1).max(365).optional(),
        autoRotate: Joi.boolean().default(false)
      }).optional(),
      metadata: Joi.object().optional()
    });

    // OAuth credential schema
    this.oauthCredentialSchema = Joi.object({
      clientId: Joi.string().required(),
      clientSecret: Joi.string().required(),
      accessToken: Joi.string().optional(),
      refreshToken: Joi.string().optional(),
      tokenType: Joi.string().default('Bearer'),
      expiresIn: Joi.number().optional(),
      scope: Joi.array().items(Joi.string()).optional(),
      redirectUri: Joi.string().uri().optional(),
      authUrl: Joi.string().uri().optional(),
      tokenUrl: Joi.string().uri().optional()
    });

    // Database credential schema
    this.databaseCredentialSchema = Joi.object({
      host: Joi.string().required(),
      port: Joi.number().min(1).max(65535).required(),
      database: Joi.string().required(),
      username: Joi.string().required(),
      password: Joi.string().required(),
      ssl: Joi.boolean().default(false),
      connectionString: Joi.string().optional()
    });
  }

  /**
   * Initialize the credential manager
   */
  async initialize() {
    try {
      await this.initializeDatabase();
      this.isInitialized = true;
      this.healthStatus = true;

      this.logger.info('CredentialManager initialized successfully');
    } catch (error) {
      this.logger.error('Failed to initialize CredentialManager', {
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

      // Create credentials table
      await client.query(`
        CREATE TABLE IF NOT EXISTS credentials (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          user_id VARCHAR(100) NOT NULL,
          tenant_id VARCHAR(100),
          name VARCHAR(255) NOT NULL,
          type VARCHAR(50) NOT NULL,
          description TEXT,
          encrypted_credentials TEXT NOT NULL,
          encryption_iv VARCHAR(32) NOT NULL,
          encryption_auth_tag VARCHAR(32) NOT NULL,
          scope TEXT[],
          tags TEXT[],
          status VARCHAR(20) DEFAULT 'active',
          expires_at TIMESTAMP,
          rotation_policy_json JSONB DEFAULT '{}',
          metadata_json JSONB DEFAULT '{}',
          version INTEGER DEFAULT 1,
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          created_by VARCHAR(100),
          last_accessed TIMESTAMP,
          access_count INTEGER DEFAULT 0,
          UNIQUE(user_id, tenant_id, name)
        );
      `);

      // Create credential access log table
      await client.query(`
        CREATE TABLE IF NOT EXISTS credential_access_log (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          credential_id UUID REFERENCES credentials(id) ON DELETE CASCADE,
          accessed_by VARCHAR(100) NOT NULL,
          access_type VARCHAR(50) NOT NULL, -- 'READ', 'UPDATE', 'DELETE'
          accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          ip_address INET,
          user_agent TEXT,
          success BOOLEAN DEFAULT true,
          error_message TEXT
        );
      `);

      // Create credential rotation history table
      await client.query(`
        CREATE TABLE IF NOT EXISTS credential_rotation_history (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          credential_id UUID REFERENCES credentials(id) ON DELETE CASCADE,
          old_version INTEGER NOT NULL,
          new_version INTEGER NOT NULL,
          rotated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          rotated_by VARCHAR(100),
          rotation_type VARCHAR(50) NOT NULL, -- 'MANUAL', 'AUTOMATIC', 'POLICY'
          reason TEXT
        );
      `);

      // Create indexes
      await client.query(`
        CREATE INDEX IF NOT EXISTS idx_credentials_user_id ON credentials(user_id);
        CREATE INDEX IF NOT EXISTS idx_credentials_tenant_id ON credentials(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_credentials_type ON credentials(type);
        CREATE INDEX IF NOT EXISTS idx_credentials_status ON credentials(status);
        CREATE INDEX IF NOT EXISTS idx_credentials_expires_at ON credentials(expires_at);
        CREATE INDEX IF NOT EXISTS idx_credentials_tags ON credentials USING GIN(tags);
        CREATE INDEX IF NOT EXISTS idx_credential_access_log_credential_id ON credential_access_log(credential_id);
        CREATE INDEX IF NOT EXISTS idx_credential_access_log_accessed_at ON credential_access_log(accessed_at);
        CREATE INDEX IF NOT EXISTS idx_credential_rotation_history_credential_id ON credential_rotation_history(credential_id);
      `);

      await client.query('COMMIT');
      this.logger.info('CredentialManager database tables initialized successfully');
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Failed to initialize CredentialManager database tables', {
        error: error.message
      });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Store encrypted credentials
   */
  async storeCredentials(userId, credentialType, credentials, tenantId = null, options = {}) {
    try {
      const {
        name,
        description,
        scope = [],
        tags = [],
        expiresAt,
        rotationPolicy = {},
        metadata = {},
        createdBy = userId
      } = options;

      if (!name) {
        throw new Error('Credential name is required');
      }

      // Validate credential data based on type
      await this.validateCredentialsByType(credentialType, credentials);

      // Validate the full credential object
      const { error, value } = this.credentialSchema.validate({
        userId,
        tenantId,
        name,
        type: credentialType,
        description,
        credentials,
        scope,
        tags,
        expiresAt,
        rotationPolicy,
        metadata
      });

      if (error) {
        throw new Error(`Credential validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const validatedCredential = value;

      // Encrypt the credentials
      const { encryptedData, iv, authTag } = this.encryptCredentials(validatedCredential.credentials);

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Check if credential with same name exists
        const existingResult = await client.query(
          `SELECT id FROM credentials 
           WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL)) AND name = $3`,
          [userId, tenantId, name]
        );

        if (existingResult.rows.length > 0) {
          throw new Error(`Credential with name '${name}' already exists for this user`);
        }

        // Insert credential
        const result = await client.query(
          `INSERT INTO credentials 
           (user_id, tenant_id, name, type, description, encrypted_credentials, 
            encryption_iv, encryption_auth_tag, scope, tags, expires_at, 
            rotation_policy_json, metadata_json, created_by)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
           RETURNING *`,
          [
            userId,
            tenantId,
            name,
            credentialType,
            description,
            encryptedData,
            iv,
            authTag,
            scope,
            tags,
            expiresAt,
            JSON.stringify(rotationPolicy),
            JSON.stringify(metadata),
            createdBy
          ]
        );

        const storedCredential = result.rows[0];

        // Log the creation
        await this.logCredentialAccess(
          storedCredential.id,
          createdBy,
          'CREATE',
          { success: true }
        );

        await client.query('COMMIT');

        this.logger.info('Credentials stored successfully', {
          credentialId: storedCredential.id,
          userId,
          tenantId,
          name,
          type: credentialType
        });

        return this.formatCredentialResponse(storedCredential, false); // Don't include actual credentials
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to store credentials', {
        error: error.message,
        userId,
        tenantId,
        credentialType
      });
      throw error;
    }
  }

  /**
   * Retrieve and decrypt credentials
   */
  async getCredentials(userId, credentialName, tenantId = null, options = {}) {
    try {
      const {
        accessedBy = userId,
        includeCredentials = true,
        ipAddress,
        userAgent
      } = options;

      const result = await this.pool.query(
        `SELECT * FROM credentials 
         WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL)) 
         AND name = $3 AND status = 'active'`,
        [userId, tenantId, credentialName]
      );

      if (result.rows.length === 0) {
        await this.logCredentialAccess(
          null,
          accessedBy,
          'READ',
          {
            success: false,
            error: 'Credential not found',
            ipAddress,
            userAgent
          }
        );
        return null;
      }

      const credential = result.rows[0];

      // Check if credential is expired
      if (credential.expires_at && new Date(credential.expires_at) < new Date()) {
        await this.logCredentialAccess(
          credential.id,
          accessedBy,
          'READ',
          {
            success: false,
            error: 'Credential expired',
            ipAddress,
            userAgent
          }
        );
        throw new Error('Credential has expired');
      }

      // Update access statistics
      await this.pool.query(
        'UPDATE credentials SET last_accessed = CURRENT_TIMESTAMP, access_count = access_count + 1 WHERE id = $1',
        [credential.id]
      );

      // Log successful access
      await this.logCredentialAccess(
        credential.id,
        accessedBy,
        'READ',
        {
          success: true,
          ipAddress,
          userAgent
        }
      );

      const response = this.formatCredentialResponse(credential, includeCredentials);

      // Decrypt credentials if requested
      if (includeCredentials) {
        try {
          response.credentials = this.decryptCredentials(
            credential.encrypted_credentials,
            credential.encryption_iv,
            credential.encryption_auth_tag
          );
        } catch (decryptError) {
          this.logger.error('Failed to decrypt credentials', {
            error: decryptError.message,
            credentialId: credential.id
          });
          throw new Error('Failed to decrypt credentials');
        }
      }

      return response;
    } catch (error) {
      this.logger.error('Failed to get credentials', {
        error: error.message,
        userId,
        tenantId,
        credentialName
      });
      throw error;
    }
  }

  /**
   * List user credentials (without sensitive data)
   */
  async listCredentials(userId, tenantId = null, options = {}) {
    try {
      const {
        type,
        status = 'active',
        tags,
        page = 1,
        limit = 20,
        sortBy = 'created_at',
        sortOrder = 'DESC'
      } = options;

      let whereClause = 'WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL))';
      const params = [userId, tenantId];
      let paramCount = 2;

      if (type) {
        whereClause += ` AND type = $${++paramCount}`;
        params.push(type);
      }

      if (status) {
        whereClause += ` AND status = $${++paramCount}`;
        params.push(status);
      }

      if (tags && tags.length > 0) {
        whereClause += ` AND tags && $${++paramCount}`;
        params.push(tags);
      }

      const offset = (page - 1) * limit;

      // Get total count
      const countResult = await this.pool.query(
        `SELECT COUNT(*) FROM credentials ${whereClause}`,
        params
      );
      const totalCount = parseInt(countResult.rows[0].count);

      // Get credentials
      const result = await this.pool.query(
        `SELECT * FROM credentials ${whereClause}
         ORDER BY ${sortBy} ${sortOrder}
         LIMIT $${++paramCount} OFFSET $${++paramCount}`,
        [...params, limit, offset]
      );

      const credentials = result.rows.map(cred => this.formatCredentialResponse(cred, false));

      return {
        credentials,
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
      this.logger.error('Failed to list credentials', {
        error: error.message,
        userId,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Update credential metadata (not the actual credentials)
   */
  async updateCredentialMetadata(userId, credentialName, updates, tenantId = null, options = {}) {
    try {
      const { updatedBy = userId } = options;

      const result = await this.pool.query(
        `UPDATE credentials 
         SET description = COALESCE($4, description),
             scope = COALESCE($5, scope),
             tags = COALESCE($6, tags),
             expires_at = COALESCE($7, expires_at),
             rotation_policy_json = COALESCE($8, rotation_policy_json),
             metadata_json = COALESCE($9, metadata_json),
             updated_at = CURRENT_TIMESTAMP
         WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL)) AND name = $3
         RETURNING *`,
        [
          userId,
          tenantId,
          credentialName,
          updates.description,
          updates.scope,
          updates.tags,
          updates.expiresAt,
          updates.rotationPolicy ? JSON.stringify(updates.rotationPolicy) : null,
          updates.metadata ? JSON.stringify(updates.metadata) : null
        ]
      );

      if (result.rows.length === 0) {
        throw new Error(`Credential '${credentialName}' not found`);
      }

      const updatedCredential = result.rows[0];

      // Log the update
      await this.logCredentialAccess(
        updatedCredential.id,
        updatedBy,
        'UPDATE',
        { success: true }
      );

      this.logger.info('Credential metadata updated successfully', {
        credentialId: updatedCredential.id,
        userId,
        tenantId,
        credentialName
      });

      return this.formatCredentialResponse(updatedCredential, false);
    } catch (error) {
      this.logger.error('Failed to update credential metadata', {
        error: error.message,
        userId,
        tenantId,
        credentialName
      });
      throw error;
    }
  }

  /**
   * Rotate credentials
   */
  async rotateCredentials(userId, credentialName, newCredentials, tenantId = null, options = {}) {
    try {
      const {
        rotatedBy = userId,
        rotationType = 'MANUAL',
        reason = 'Manual credential rotation'
      } = options;

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Get existing credential
        const existingResult = await client.query(
          `SELECT * FROM credentials 
           WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL)) AND name = $3`,
          [userId, tenantId, credentialName]
        );

        if (existingResult.rows.length === 0) {
          throw new Error(`Credential '${credentialName}' not found`);
        }

        const existingCredential = existingResult.rows[0];

        // Validate new credentials
        await this.validateCredentialsByType(existingCredential.type, newCredentials);

        // Encrypt new credentials
        const { encryptedData, iv, authTag } = this.encryptCredentials(newCredentials);

        // Update credential with new encrypted data
        const updateResult = await client.query(
          `UPDATE credentials 
           SET encrypted_credentials = $1, encryption_iv = $2, encryption_auth_tag = $3,
               version = version + 1, updated_at = CURRENT_TIMESTAMP
           WHERE id = $4
           RETURNING *`,
          [encryptedData, iv, authTag, existingCredential.id]
        );

        const updatedCredential = updateResult.rows[0];

        // Record rotation history
        await client.query(
          `INSERT INTO credential_rotation_history 
           (credential_id, old_version, new_version, rotated_by, rotation_type, reason)
           VALUES ($1, $2, $3, $4, $5, $6)`,
          [
            existingCredential.id,
            existingCredential.version,
            updatedCredential.version,
            rotatedBy,
            rotationType,
            reason
          ]
        );

        // Log the rotation
        await this.logCredentialAccess(
          existingCredential.id,
          rotatedBy,
          'ROTATE',
          { success: true }
        );

        await client.query('COMMIT');

        this.logger.info('Credentials rotated successfully', {
          credentialId: existingCredential.id,
          userId,
          tenantId,
          credentialName,
          oldVersion: existingCredential.version,
          newVersion: updatedCredential.version
        });

        return this.formatCredentialResponse(updatedCredential, false);
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to rotate credentials', {
        error: error.message,
        userId,
        tenantId,
        credentialName
      });
      throw error;
    }
  }

  /**
   * Delete credentials
   */
  async deleteCredentials(userId, credentialName, tenantId = null, options = {}) {
    try {
      const { deletedBy = userId, reason = 'User requested deletion' } = options;

      const result = await this.pool.query(
        `UPDATE credentials 
         SET status = 'revoked', updated_at = CURRENT_TIMESTAMP
         WHERE user_id = $1 AND (tenant_id = $2 OR (tenant_id IS NULL AND $2 IS NULL)) AND name = $3
         RETURNING *`,
        [userId, tenantId, credentialName]
      );

      if (result.rows.length === 0) {
        throw new Error(`Credential '${credentialName}' not found`);
      }

      const deletedCredential = result.rows[0];

      // Log the deletion
      await this.logCredentialAccess(
        deletedCredential.id,
        deletedBy,
        'DELETE',
        { success: true, reason }
      );

      this.logger.info('Credentials deleted successfully', {
        credentialId: deletedCredential.id,
        userId,
        tenantId,
        credentialName
      });

      return true;
    } catch (error) {
      this.logger.error('Failed to delete credentials', {
        error: error.message,
        userId,
        tenantId,
        credentialName
      });
      throw error;
    }
  }

  /**
   * Encrypt credentials using AES-256-GCM
   * @private
   */
  encryptCredentials(credentials) {
    const algorithm = 'aes-256-gcm';
    const iv = crypto.randomBytes(16);
    
    const cipher = crypto.createCipher(algorithm, this.encryptionKey);
    cipher.setAAD(Buffer.from('credential-encryption', 'utf8'));
    
    let encrypted = cipher.update(JSON.stringify(credentials), 'utf8', 'hex');
    encrypted += cipher.final('hex');
    
    const authTag = cipher.getAuthTag();
    
    return {
      encryptedData: encrypted,
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex')
    };
  }

  /**
   * Decrypt credentials using AES-256-GCM
   * @private
   */
  decryptCredentials(encryptedData, iv, authTag) {
    const algorithm = 'aes-256-gcm';
    
    const decipher = crypto.createDecipher(algorithm, this.encryptionKey);
    decipher.setAAD(Buffer.from('credential-encryption', 'utf8'));
    decipher.setAuthTag(Buffer.from(authTag, 'hex'));
    
    let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
    decrypted += decipher.final('utf8');
    
    return JSON.parse(decrypted);
  }

  /**
   * Validate credentials based on type
   * @private
   */
  async validateCredentialsByType(type, credentials) {
    switch (type) {
      case CredentialType.OAUTH:
        const oauthValidation = this.oauthCredentialSchema.validate(credentials);
        if (oauthValidation.error) {
          throw new Error(`OAuth credential validation failed: ${oauthValidation.error.details.map(d => d.message).join(', ')}`);
        }
        break;
      
      case CredentialType.DATABASE:
        const dbValidation = this.databaseCredentialSchema.validate(credentials);
        if (dbValidation.error) {
          throw new Error(`Database credential validation failed: ${dbValidation.error.details.map(d => d.message).join(', ')}`);
        }
        break;
      
      case CredentialType.API_KEY:
        if (!credentials.apiKey || typeof credentials.apiKey !== 'string') {
          throw new Error('API key credential must have an apiKey field');
        }
        break;
      
      case CredentialType.TOKEN:
        if (!credentials.token || typeof credentials.token !== 'string') {
          throw new Error('Token credential must have a token field');
        }
        break;
      
      case CredentialType.SECRET:
        if (!credentials.secret || typeof credentials.secret !== 'string') {
          throw new Error('Secret credential must have a secret field');
        }
        break;
      
      default:
        // For other types, just ensure it's an object
        if (typeof credentials !== 'object' || credentials === null) {
          throw new Error('Credentials must be an object');
        }
    }
  }

  /**
   * Log credential access
   * @private
   */
  async logCredentialAccess(credentialId, accessedBy, accessType, details = {}) {
    try {
      if (!credentialId) {
        // For failed access attempts where credential doesn't exist
        this.logger.warn('Credential access attempt failed', {
          accessedBy,
          accessType,
          ...details
        });
        return;
      }

      await this.pool.query(
        `INSERT INTO credential_access_log 
         (credential_id, accessed_by, access_type, ip_address, user_agent, success, error_message)
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [
          credentialId,
          accessedBy,
          accessType.toUpperCase(),
          details.ipAddress || null,
          details.userAgent || null,
          details.success || false,
          details.error || null
        ]
      );
    } catch (error) {
      // Don't throw - logging failures shouldn't break the main operation
      this.logger.error('Failed to log credential access', {
        error: error.message,
        credentialId,
        accessedBy,
        accessType
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
   * Format credential response
   * @private
   */
  formatCredentialResponse(credential, includeCredentials = false) {
    const response = {
      id: credential.id,
      userId: credential.user_id,
      tenantId: credential.tenant_id,
      name: credential.name,
      type: credential.type,
      description: credential.description,
      scope: credential.scope || [],
      tags: credential.tags || [],
      status: credential.status,
      expiresAt: credential.expires_at,
      rotationPolicy: typeof credential.rotation_policy_json === 'string'
        ? JSON.parse(credential.rotation_policy_json)
        : credential.rotation_policy_json || {},
      metadata: typeof credential.metadata_json === 'string'
        ? JSON.parse(credential.metadata_json)
        : credential.metadata_json || {},
      version: credential.version,
      createdAt: credential.created_at,
      updatedAt: credential.updated_at,
      createdBy: credential.created_by,
      lastAccessed: credential.last_accessed,
      accessCount: credential.access_count
    };

    if (!includeCredentials) {
      response.hasCredentials = true;
    }

    return response;
  }

  /**
   * Close database connection
   */
  async close() {
    await this.pool.end();
    this.logger.info('CredentialManager database connection closed');
  }
}

// Export class and enums
module.exports = {
  CredentialManager,
  CredentialType,
  CredentialStatus
};
