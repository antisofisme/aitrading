/**
 * TenantManager - Multi-tenant management service
 *
 * Provides enterprise-grade multi-tenancy with:
 * - Tenant isolation and data segregation
 * - Tenant-specific configuration management
 * - Resource quotas and limits
 * - Tenant lifecycle management
 * - Cross-tenant analytics and reporting
 */

const { Pool } = require('pg');
const { v4: uuidv4 } = require('uuid');
const winston = require('winston');
const Joi = require('joi');

// Tenant Status enumeration
const TenantStatus = {
  ACTIVE: 'active',
  SUSPENDED: 'suspended',
  INACTIVE: 'inactive',
  PENDING: 'pending',
  TERMINATED: 'terminated'
};

// Tenant Tier enumeration
const TenantTier = {
  FREE: 'free',
  BASIC: 'basic',
  PREMIUM: 'premium',
  ENTERPRISE: 'enterprise',
  CUSTOM: 'custom'
};

class TenantManager {
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
          filename: 'logs/tenant-manager.log',
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
    this.tenantCache = new Map();
    this.quotaCache = new Map();
    this.isInitialized = false;
    this.healthStatus = true;

    this.initializeValidationSchemas();
  }

  /**
   * Initialize validation schemas
   */
  initializeValidationSchemas() {
    // Tenant schema
    this.tenantSchema = Joi.object({
      id: Joi.string().optional(),
      name: Joi.string().min(1).max(255).required(),
      domain: Joi.string().hostname().optional(),
      tier: Joi.string().valid(...Object.values(TenantTier)).default(TenantTier.FREE),
      status: Joi.string().valid(...Object.values(TenantStatus)).default(TenantStatus.PENDING),
      description: Joi.string().max(1000).optional(),
      contactEmail: Joi.string().email().required(),
      contactName: Joi.string().max(255).optional(),
      settings: Joi.object().optional(),
      features: Joi.array().items(Joi.string()).optional(),
      quotas: Joi.object({
        maxUsers: Joi.number().min(1).default(10),
        maxConfigurations: Joi.number().min(1).default(100),
        maxCredentials: Joi.number().min(1).default(50),
        maxFlows: Joi.number().min(1).default(25),
        maxApiCalls: Joi.number().min(100).default(10000),
        storageLimit: Joi.number().min(1).default(1024) // MB
      }).optional(),
      metadata: Joi.object().optional()
    });

    // Tenant settings schema
    this.tenantSettingsSchema = Joi.object({
      branding: Joi.object({
        logo: Joi.string().uri().optional(),
        primaryColor: Joi.string().optional(),
        secondaryColor: Joi.string().optional(),
        customCSS: Joi.string().optional()
      }).optional(),
      security: Joi.object({
        enforceSSO: Joi.boolean().default(false),
        passwordPolicy: Joi.object().optional(),
        sessionTimeout: Joi.number().min(300).max(86400).default(3600), // seconds
        mfaRequired: Joi.boolean().default(false)
      }).optional(),
      notifications: Joi.object({
        emailEnabled: Joi.boolean().default(true),
        smsEnabled: Joi.boolean().default(false),
        webhookUrl: Joi.string().uri().optional()
      }).optional(),
      integration: Joi.object({
        allowedDomains: Joi.array().items(Joi.string().hostname()).optional(),
        apiRateLimit: Joi.number().min(10).max(100000).default(1000),
        webhookSecrets: Joi.object().optional()
      }).optional()
    });
  }

  /**
   * Initialize the tenant manager
   */
  async initialize() {
    try {
      await this.initializeDatabase();
      await this.loadTenantsIntoCache();
      this.isInitialized = true;
      this.healthStatus = true;

      this.logger.info('TenantManager initialized successfully', {
        cachedTenants: this.tenantCache.size
      });
    } catch (error) {
      this.logger.error('Failed to initialize TenantManager', {
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

      // Create tenants table
      await client.query(`
        CREATE TABLE IF NOT EXISTS tenants (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id VARCHAR(100) UNIQUE NOT NULL,
          name VARCHAR(255) NOT NULL,
          domain VARCHAR(255),
          tier VARCHAR(50) DEFAULT 'free',
          status VARCHAR(50) DEFAULT 'pending',
          description TEXT,
          contact_email VARCHAR(255) NOT NULL,
          contact_name VARCHAR(255),
          settings_json JSONB DEFAULT '{}',
          features TEXT[],
          quotas_json JSONB DEFAULT '{}',
          metadata_json JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          activated_at TIMESTAMP,
          suspended_at TIMESTAMP,
          created_by VARCHAR(100)
        );
      `);

      // Create tenant usage table
      await client.query(`
        CREATE TABLE IF NOT EXISTS tenant_usage (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id VARCHAR(100) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
          metric_name VARCHAR(100) NOT NULL,
          metric_value BIGINT NOT NULL,
          recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          period_start TIMESTAMP NOT NULL,
          period_end TIMESTAMP NOT NULL,
          metadata_json JSONB DEFAULT '{}'
        );
      `);

      // Create tenant activity log table
      await client.query(`
        CREATE TABLE IF NOT EXISTS tenant_activity_log (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id VARCHAR(100) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
          activity_type VARCHAR(100) NOT NULL,
          description TEXT,
          performed_by VARCHAR(100),
          performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          ip_address INET,
          user_agent TEXT,
          metadata_json JSONB DEFAULT '{}'
        );
      `);

      // Create tenant subscriptions table
      await client.query(`
        CREATE TABLE IF NOT EXISTS tenant_subscriptions (
          id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
          tenant_id VARCHAR(100) REFERENCES tenants(tenant_id) ON DELETE CASCADE,
          subscription_type VARCHAR(100) NOT NULL,
          status VARCHAR(50) NOT NULL,
          starts_at TIMESTAMP NOT NULL,
          ends_at TIMESTAMP,
          billing_cycle VARCHAR(20), -- 'monthly', 'yearly', 'custom'
          price_amount DECIMAL(10,2),
          currency VARCHAR(3) DEFAULT 'USD',
          features_json JSONB DEFAULT '{}',
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
      `);

      // Create indexes
      await client.query(`
        CREATE INDEX IF NOT EXISTS idx_tenants_tenant_id ON tenants(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_tenants_domain ON tenants(domain);
        CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);
        CREATE INDEX IF NOT EXISTS idx_tenants_tier ON tenants(tier);
        CREATE INDEX IF NOT EXISTS idx_tenants_contact_email ON tenants(contact_email);
        CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_tenant_usage_metric_name ON tenant_usage(metric_name);
        CREATE INDEX IF NOT EXISTS idx_tenant_usage_recorded_at ON tenant_usage(recorded_at);
        CREATE INDEX IF NOT EXISTS idx_tenant_activity_log_tenant_id ON tenant_activity_log(tenant_id);
        CREATE INDEX IF NOT EXISTS idx_tenant_activity_log_performed_at ON tenant_activity_log(performed_at);
        CREATE INDEX IF NOT EXISTS idx_tenant_subscriptions_tenant_id ON tenant_subscriptions(tenant_id);
      `);

      await client.query('COMMIT');
      this.logger.info('TenantManager database tables initialized successfully');
    } catch (error) {
      await client.query('ROLLBACK');
      this.logger.error('Failed to initialize TenantManager database tables', {
        error: error.message
      });
      throw error;
    } finally {
      client.release();
    }
  }

  /**
   * Load tenants into cache
   */
  async loadTenantsIntoCache() {
    try {
      const result = await this.pool.query(
        'SELECT * FROM tenants WHERE status IN ($1, $2) ORDER BY created_at DESC',
        [TenantStatus.ACTIVE, TenantStatus.SUSPENDED]
      );

      this.tenantCache.clear();
      for (const tenant of result.rows) {
        this.tenantCache.set(tenant.tenant_id, this.formatTenantResponse(tenant));
      }

      this.logger.info('Tenants loaded into cache', {
        count: result.rows.length
      });
    } catch (error) {
      this.logger.error('Failed to load tenants into cache', {
        error: error.message
      });
      throw error;
    }
  }

  /**
   * Create a new tenant
   */
  async createTenant(tenantData, options = {}) {
    try {
      const { createdBy = 'system' } = options;

      // Generate tenant ID if not provided
      if (!tenantData.id) {
        tenantData.id = `tenant_${uuidv4().replace(/-/g, '').substring(0, 16)}`;
      }

      // Validate tenant data
      const { error, value } = this.tenantSchema.validate(tenantData);
      if (error) {
        throw new Error(`Tenant validation failed: ${error.details.map(d => d.message).join(', ')}`);
      }

      const validatedTenant = value;

      // Check if tenant ID or domain already exists
      const existingResult = await this.pool.query(
        'SELECT tenant_id, domain FROM tenants WHERE tenant_id = $1 OR (domain = $2 AND domain IS NOT NULL)',
        [validatedTenant.id, validatedTenant.domain]
      );

      if (existingResult.rows.length > 0) {
        const existing = existingResult.rows[0];
        if (existing.tenant_id === validatedTenant.id) {
          throw new Error(`Tenant with ID '${validatedTenant.id}' already exists`);
        }
        if (existing.domain === validatedTenant.domain) {
          throw new Error(`Tenant with domain '${validatedTenant.domain}' already exists`);
        }
      }

      const client = await this.pool.connect();
      try {
        await client.query('BEGIN');

        // Insert tenant
        const tenantResult = await client.query(
          `INSERT INTO tenants 
           (tenant_id, name, domain, tier, status, description, contact_email, contact_name,
            settings_json, features, quotas_json, metadata_json, created_by)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
           RETURNING *`,
          [
            validatedTenant.id,
            validatedTenant.name,
            validatedTenant.domain,
            validatedTenant.tier,
            validatedTenant.status,
            validatedTenant.description,
            validatedTenant.contactEmail,
            validatedTenant.contactName,
            JSON.stringify(validatedTenant.settings || {}),
            validatedTenant.features || [],
            JSON.stringify(validatedTenant.quotas || {}),
            JSON.stringify(validatedTenant.metadata || {}),
            createdBy
          ]
        );

        const createdTenant = tenantResult.rows[0];

        // Log tenant creation
        await this.logTenantActivity(
          validatedTenant.id,
          'TENANT_CREATED',
          `Tenant '${validatedTenant.name}' created`,
          createdBy
        );

        await client.query('COMMIT');

        const formattedTenant = this.formatTenantResponse(createdTenant);

        // Update cache
        this.tenantCache.set(validatedTenant.id, formattedTenant);

        this.logger.info('Tenant created successfully', {
          tenantId: validatedTenant.id,
          name: validatedTenant.name,
          tier: validatedTenant.tier
        });

        return formattedTenant;
      } catch (error) {
        await client.query('ROLLBACK');
        throw error;
      } finally {
        client.release();
      }
    } catch (error) {
      this.logger.error('Failed to create tenant', {
        error: error.message,
        tenantData
      });
      throw error;
    }
  }

  /**
   * Get tenant by ID
   */
  async getTenant(tenantId, options = {}) {
    try {
      const { useCache = true, includeUsage = false } = options;

      // Check cache first
      if (useCache && this.tenantCache.has(tenantId)) {
        const tenant = this.tenantCache.get(tenantId);
        if (includeUsage) {
          tenant.usage = await this.getTenantUsage(tenantId);
        }
        return tenant;
      }

      // Query database
      const result = await this.pool.query(
        'SELECT * FROM tenants WHERE tenant_id = $1',
        [tenantId]
      );

      if (result.rows.length === 0) {
        return null;
      }

      const tenant = this.formatTenantResponse(result.rows[0]);

      if (includeUsage) {
        tenant.usage = await this.getTenantUsage(tenantId);
      }

      // Update cache
      if (useCache && tenant.status === TenantStatus.ACTIVE) {
        this.tenantCache.set(tenantId, tenant);
      }

      return tenant;
    } catch (error) {
      this.logger.error('Failed to get tenant', {
        error: error.message,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Update tenant
   */
  async updateTenant(tenantId, updates, options = {}) {
    try {
      const { updatedBy = 'system' } = options;

      const result = await this.pool.query(
        `UPDATE tenants 
         SET name = COALESCE($2, name),
             domain = COALESCE($3, domain),
             tier = COALESCE($4, tier),
             status = COALESCE($5, status),
             description = COALESCE($6, description),
             contact_email = COALESCE($7, contact_email),
             contact_name = COALESCE($8, contact_name),
             settings_json = COALESCE($9, settings_json),
             features = COALESCE($10, features),
             quotas_json = COALESCE($11, quotas_json),
             metadata_json = COALESCE($12, metadata_json),
             updated_at = CURRENT_TIMESTAMP,
             activated_at = CASE WHEN $5 = 'active' AND status != 'active' THEN CURRENT_TIMESTAMP ELSE activated_at END,
             suspended_at = CASE WHEN $5 = 'suspended' AND status != 'suspended' THEN CURRENT_TIMESTAMP ELSE suspended_at END
         WHERE tenant_id = $1
         RETURNING *`,
        [
          tenantId,
          updates.name,
          updates.domain,
          updates.tier,
          updates.status,
          updates.description,
          updates.contactEmail,
          updates.contactName,
          updates.settings ? JSON.stringify(updates.settings) : null,
          updates.features,
          updates.quotas ? JSON.stringify(updates.quotas) : null,
          updates.metadata ? JSON.stringify(updates.metadata) : null
        ]
      );

      if (result.rows.length === 0) {
        throw new Error(`Tenant with ID '${tenantId}' not found`);
      }

      const updatedTenant = result.rows[0];

      // Log tenant update
      await this.logTenantActivity(
        tenantId,
        'TENANT_UPDATED',
        `Tenant updated`,
        updatedBy,
        { updates }
      );

      const formattedTenant = this.formatTenantResponse(updatedTenant);

      // Update cache
      if (formattedTenant.status === TenantStatus.ACTIVE) {
        this.tenantCache.set(tenantId, formattedTenant);
      } else {
        this.tenantCache.delete(tenantId);
      }

      this.logger.info('Tenant updated successfully', {
        tenantId,
        updates: Object.keys(updates)
      });

      return formattedTenant;
    } catch (error) {
      this.logger.error('Failed to update tenant', {
        error: error.message,
        tenantId,
        updates
      });
      throw error;
    }
  }

  /**
   * List tenants with filtering
   */
  async listTenants(options = {}) {
    try {
      const {
        status,
        tier,
        domain,
        page = 1,
        limit = 20,
        sortBy = 'created_at',
        sortOrder = 'DESC'
      } = options;

      let whereClause = '';
      const params = [];
      let paramCount = 0;
      const conditions = [];

      if (status) {
        conditions.push(`status = $${++paramCount}`);
        params.push(status);
      }

      if (tier) {
        conditions.push(`tier = $${++paramCount}`);
        params.push(tier);
      }

      if (domain) {
        conditions.push(`domain ILIKE $${++paramCount}`);
        params.push(`%${domain}%`);
      }

      if (conditions.length > 0) {
        whereClause = 'WHERE ' + conditions.join(' AND ');
      }

      const offset = (page - 1) * limit;

      // Get total count
      const countResult = await this.pool.query(
        `SELECT COUNT(*) FROM tenants ${whereClause}`,
        params
      );
      const totalCount = parseInt(countResult.rows[0].count);

      // Get tenants
      const result = await this.pool.query(
        `SELECT * FROM tenants ${whereClause}
         ORDER BY ${sortBy} ${sortOrder}
         LIMIT $${++paramCount} OFFSET $${++paramCount}`,
        [...params, limit, offset]
      );

      const tenants = result.rows.map(tenant => this.formatTenantResponse(tenant));

      return {
        tenants,
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
      this.logger.error('Failed to list tenants', {
        error: error.message,
        options
      });
      throw error;
    }
  }

  /**
   * Record tenant usage metric
   */
  async recordUsage(tenantId, metricName, value, options = {}) {
    try {
      const {
        periodStart = new Date(),
        periodEnd = new Date(),
        metadata = {}
      } = options;

      await this.pool.query(
        `INSERT INTO tenant_usage 
         (tenant_id, metric_name, metric_value, period_start, period_end, metadata_json)
         VALUES ($1, $2, $3, $4, $5, $6)`,
        [
          tenantId,
          metricName,
          value,
          periodStart,
          periodEnd,
          JSON.stringify(metadata)
        ]
      );

      this.logger.debug('Tenant usage recorded', {
        tenantId,
        metricName,
        value
      });
    } catch (error) {
      this.logger.error('Failed to record tenant usage', {
        error: error.message,
        tenantId,
        metricName,
        value
      });
      // Don't throw - usage recording failures shouldn't break main operations
    }
  }

  /**
   * Get tenant usage metrics
   */
  async getTenantUsage(tenantId, options = {}) {
    try {
      const {
        metricName,
        startDate,
        endDate,
        limit = 100
      } = options;

      let whereClause = 'WHERE tenant_id = $1';
      const params = [tenantId];
      let paramCount = 1;

      if (metricName) {
        whereClause += ` AND metric_name = $${++paramCount}`;
        params.push(metricName);
      }

      if (startDate) {
        whereClause += ` AND recorded_at >= $${++paramCount}`;
        params.push(startDate);
      }

      if (endDate) {
        whereClause += ` AND recorded_at <= $${++paramCount}`;
        params.push(endDate);
      }

      const result = await this.pool.query(
        `SELECT * FROM tenant_usage ${whereClause}
         ORDER BY recorded_at DESC
         LIMIT $${++paramCount}`,
        [...params, limit]
      );

      return result.rows.map(usage => ({
        id: usage.id,
        tenantId: usage.tenant_id,
        metricName: usage.metric_name,
        metricValue: usage.metric_value,
        recordedAt: usage.recorded_at,
        periodStart: usage.period_start,
        periodEnd: usage.period_end,
        metadata: typeof usage.metadata_json === 'string'
          ? JSON.parse(usage.metadata_json)
          : usage.metadata_json || {}
      }));
    } catch (error) {
      this.logger.error('Failed to get tenant usage', {
        error: error.message,
        tenantId
      });
      throw error;
    }
  }

  /**
   * Check tenant quota
   */
  async checkQuota(tenantId, quotaType, currentValue) {
    try {
      const tenant = await this.getTenant(tenantId);
      if (!tenant) {
        throw new Error(`Tenant '${tenantId}' not found`);
      }

      const quotas = tenant.quotas || {};
      const quotaLimit = quotas[quotaType];

      if (quotaLimit === undefined) {
        // No quota defined, allow
        return {
          allowed: true,
          quotaType,
          currentValue,
          limit: null,
          remaining: null
        };
      }

      const allowed = currentValue < quotaLimit;
      const remaining = Math.max(0, quotaLimit - currentValue);

      return {
        allowed,
        quotaType,
        currentValue,
        limit: quotaLimit,
        remaining
      };
    } catch (error) {
      this.logger.error('Failed to check tenant quota', {
        error: error.message,
        tenantId,
        quotaType
      });
      throw error;
    }
  }

  /**
   * Log tenant activity
   * @private
   */
  async logTenantActivity(tenantId, activityType, description, performedBy, options = {}) {
    try {
      const {
        ipAddress,
        userAgent,
        metadata = {}
      } = options;

      await this.pool.query(
        `INSERT INTO tenant_activity_log 
         (tenant_id, activity_type, description, performed_by, ip_address, user_agent, metadata_json)
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [
          tenantId,
          activityType,
          description,
          performedBy,
          ipAddress || null,
          userAgent || null,
          JSON.stringify(metadata)
        ]
      );
    } catch (error) {
      // Don't throw - logging failures shouldn't break the main operation
      this.logger.error('Failed to log tenant activity', {
        error: error.message,
        tenantId,
        activityType
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
   * Format tenant response
   * @private
   */
  formatTenantResponse(tenant) {
    return {
      id: tenant.id,
      tenantId: tenant.tenant_id,
      name: tenant.name,
      domain: tenant.domain,
      tier: tenant.tier,
      status: tenant.status,
      description: tenant.description,
      contactEmail: tenant.contact_email,
      contactName: tenant.contact_name,
      settings: typeof tenant.settings_json === 'string'
        ? JSON.parse(tenant.settings_json)
        : tenant.settings_json || {},
      features: tenant.features || [],
      quotas: typeof tenant.quotas_json === 'string'
        ? JSON.parse(tenant.quotas_json)
        : tenant.quotas_json || {},
      metadata: typeof tenant.metadata_json === 'string'
        ? JSON.parse(tenant.metadata_json)
        : tenant.metadata_json || {},
      createdAt: tenant.created_at,
      updatedAt: tenant.updated_at,
      activatedAt: tenant.activated_at,
      suspendedAt: tenant.suspended_at,
      createdBy: tenant.created_by
    };
  }

  /**
   * Close database connection
   */
  async close() {
    await this.pool.end();
    this.logger.info('TenantManager database connection closed');
  }
}

// Export class and enums
module.exports = {
  TenantManager,
  TenantStatus,
  TenantTier
};
