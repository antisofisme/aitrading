/**
 * Service Port Coordinator
 * Manages port allocations, service discovery, and backend integration fixes
 */

const fs = require('fs').promises;
const path = require('path');

class ServicePortCoordinator {
    constructor(options = {}) {
        this.logger = options.logger || console;
        this.backendPath = options.backendPath || '/mnt/f/WINDSURF/neliti_code/aitrading/project/backend';

        // Centralized port allocation registry
        this.portRegistry = {
            // Core Foundation Services (3000-3999)
            'api-gateway': {
                port: 3001,
                protocol: 'http',
                description: 'External API Gateway - Main entry point',
                critical: true,
                health: '/health',
                configFile: 'api-gateway/config/gateway.config.js'
            },

            // Data Services (5000-5999)
            'data-bridge': {
                port: 5001,
                protocol: 'http+ws',
                description: 'Market Data Bridge - Real-time data ingestion',
                critical: false,
                health: '/health',
                configFile: 'data-bridge/config/config.js'
            },

            // Central Hub Services (7000-7999)
            'central-hub': {
                port: 7000,
                protocol: 'http',
                description: 'Service Discovery & Registration Hub',
                critical: true,
                health: '/health',
                configFile: 'central-hub/config/hub.config.js'
            },

            // Database Services (8000-8999)
            'database-service': {
                port: 8008,
                protocol: 'http',
                description: 'Database Access Layer',
                critical: true,
                health: '/health',
                configFile: 'database-service/config/database.config.js'
            },
            'ai-orchestrator': {
                port: 8020,
                protocol: 'http',
                description: 'Level 4 Intelligence Orchestrator',
                critical: true,
                health: '/health',
                configFile: 'ai-orchestrator/config/orchestrator.config.js'
            },
            'ml-automl': {
                port: 8021,
                protocol: 'http',
                description: 'AutoML Service',
                critical: false,
                health: '/health',
                configFile: 'ml-automl/config/automl.config.js'
            },
            'realtime-inference-engine': {
                port: 8022,
                protocol: 'http',
                description: 'Real-time ML Inference',
                critical: false,
                health: '/health',
                configFile: 'realtime-inference-engine/config/inference.config.js'
            },

            // Trading Services (9000-9999)
            'trading-engine': {
                port: 9000,
                protocol: 'http',
                description: 'Core Trading Engine',
                critical: true,
                health: '/health',
                configFile: 'trading-engine/config/trading.config.js'
            },
            'billing-service': {
                port: 9001,
                protocol: 'http',
                description: 'Subscription & Billing Management',
                critical: false,
                health: '/health',
                configFile: 'billing-service/config/billing.config.js'
            },
            'payment-service': {
                port: 9002,
                protocol: 'http',
                description: 'Payment Processing (Midtrans)',
                critical: false,
                health: '/health',
                configFile: 'payment-service/config/payment.config.js'
            },
            'notification-service': {
                port: 9003,
                protocol: 'http',
                description: 'Alerts & Notifications',
                critical: false,
                health: '/health',
                configFile: 'notification-service/config/notification.config.js'
            },

            // Analytics & Monitoring (9100-9199)
            'performance-analytics': {
                port: 9100,
                protocol: 'http',
                description: 'Performance Tracking & Analytics',
                critical: false,
                health: '/health',
                configFile: 'performance-analytics/config/analytics.config.js'
            },
            'usage-monitoring': {
                port: 9101,
                protocol: 'http',
                description: 'Usage Analytics & Monitoring',
                critical: false,
                health: '/health',
                configFile: 'usage-monitoring/config/monitoring.config.js'
            },
            'compliance-monitor': {
                port: 9102,
                protocol: 'http',
                description: 'Regulatory Compliance Monitoring',
                critical: false,
                health: '/health',
                configFile: 'compliance-monitor/config/compliance.config.js'
            }
        };

        this.serviceStatus = new Map();
        this.integrationFixes = [];
    }

    /**
     * Initialize service port coordination
     */
    async initialize() {
        this.logger.info('Initializing Service Port Coordinator...');

        try {
            // Validate port allocations
            await this.validatePortAllocations();

            // Apply backend integration fixes
            await this.applyBackendFixes();

            // Update service configurations
            await this.updateServiceConfigurations();

            // Generate service registry
            await this.generateServiceRegistry();

            this.logger.info('Service Port Coordinator initialization complete');
            return true;

        } catch (error) {
            this.logger.error('Failed to initialize Service Port Coordinator:', error);
            throw error;
        }
    }

    /**
     * Validate port allocations for conflicts
     */
    async validatePortAllocations() {
        const usedPorts = new Set();
        const conflicts = [];

        for (const [serviceName, config] of Object.entries(this.portRegistry)) {
            if (usedPorts.has(config.port)) {
                conflicts.push({
                    service: serviceName,
                    port: config.port,
                    type: 'duplicate'
                });
            } else {
                usedPorts.add(config.port);
            }

            // Validate port range appropriateness
            if (!this.isPortInValidRange(config.port, serviceName)) {
                conflicts.push({
                    service: serviceName,
                    port: config.port,
                    type: 'invalid_range'
                });
            }
        }

        if (conflicts.length > 0) {
            this.logger.warn('Port allocation conflicts detected:', conflicts);
            await this.resolvePortConflicts(conflicts);
        }

        return usedPorts.size;
    }

    /**
     * Check if port is in valid range for service type
     */
    isPortInValidRange(port, serviceName) {
        if (serviceName.includes('api-gateway')) return port >= 3000 && port < 4000;
        if (serviceName.includes('data')) return port >= 5000 && port < 6000;
        if (serviceName.includes('hub')) return port >= 7000 && port < 8000;
        if (serviceName.includes('database') || serviceName.includes('ai-') || serviceName.includes('ml-')) {
            return port >= 8000 && port < 9000;
        }
        if (serviceName.includes('trading') || serviceName.includes('billing') || serviceName.includes('payment') || serviceName.includes('notification')) {
            return port >= 9000 && port < 9100;
        }
        if (serviceName.includes('analytics') || serviceName.includes('monitoring') || serviceName.includes('compliance')) {
            return port >= 9100 && port < 9200;
        }
        return port >= 3000 && port < 10000;
    }

    /**
     * Resolve port allocation conflicts
     */
    async resolvePortConflicts(conflicts) {
        for (const conflict of conflicts) {
            if (conflict.type === 'duplicate') {
                const newPort = await this.findAvailablePort(conflict.port);
                this.logger.info(`Resolving port conflict for ${conflict.service}: ${conflict.port} -> ${newPort}`);
                this.portRegistry[conflict.service].port = newPort;
            }
        }
    }

    /**
     * Find next available port in valid range
     */
    async findAvailablePort(startPort) {
        const usedPorts = new Set(
            Object.values(this.portRegistry).map(config => config.port)
        );

        let port = startPort + 1;
        while (usedPorts.has(port) && port < 65535) {
            port++;
        }

        return port;
    }

    /**
     * Apply backend integration fixes
     */
    async applyBackendFixes() {
        this.logger.info('Applying backend integration fixes...');

        const fixes = [
            {
                name: 'Environment Variable Standardization',
                apply: () => this.standardizeEnvironmentVariables()
            },
            {
                name: 'Database Connection Pooling',
                apply: () => this.fixDatabaseConnections()
            },
            {
                name: 'Service Discovery Configuration',
                apply: () => this.configureServiceDiscovery()
            },
            {
                name: 'CORS and Security Headers',
                apply: () => this.applySecurity()
            },
            {
                name: 'Error Handling Standardization',
                apply: () => this.standardizeErrorHandling()
            },
            {
                name: 'Health Check Endpoints',
                apply: () => this.addHealthChecks()
            },
            {
                name: 'Logging Configuration',
                apply: () => this.standardizeLogging()
            }
        ];

        for (const fix of fixes) {
            try {
                await fix.apply();
                this.integrationFixes.push({
                    name: fix.name,
                    status: 'applied',
                    timestamp: new Date().toISOString()
                });
                this.logger.info(`✓ Applied fix: ${fix.name}`);
            } catch (error) {
                this.integrationFixes.push({
                    name: fix.name,
                    status: 'failed',
                    error: error.message,
                    timestamp: new Date().toISOString()
                });
                this.logger.error(`✗ Failed to apply fix: ${fix.name}`, error);
            }
        }
    }

    /**
     * Standardize environment variables across services
     */
    async standardizeEnvironmentVariables() {
        const standardEnvTemplate = `# AI Trading Platform - Service Environment Configuration
# Generated by Service Port Coordinator

# Core Service Configuration
NODE_ENV=\${NODE_ENV:-development}
LOG_LEVEL=\${LOG_LEVEL:-info}

# Service Discovery
CENTRAL_HUB_URL=\${CENTRAL_HUB_URL:-http://localhost:7000}
SERVICE_REGISTRY_ENABLED=\${SERVICE_REGISTRY_ENABLED:-true}

# Database Configuration
DB_HOST=\${DB_HOST:-localhost}
DB_PORT=\${DB_PORT:-5432}
DB_NAME=\${DB_NAME:-aitrading_main}
DB_USER=\${DB_USER:-postgres}
DB_PASSWORD=\${DB_PASSWORD:-postgres}
DB_POOL_SIZE=\${DB_POOL_SIZE:-10}
DB_CONNECTION_TIMEOUT=\${DB_CONNECTION_TIMEOUT:-30000}

# Redis Configuration
REDIS_HOST=\${REDIS_HOST:-localhost}
REDIS_PORT=\${REDIS_PORT:-6379}
REDIS_PASSWORD=\${REDIS_PASSWORD:-}

# Security Configuration
JWT_SECRET=\${JWT_SECRET:-your-super-secret-jwt-key-change-in-production}
JWT_EXPIRES_IN=\${JWT_EXPIRES_IN:-24h}
CORS_ORIGIN=\${CORS_ORIGIN:-http://localhost:3000}

# AI Provider Configuration
OPENAI_API_KEY=\${OPENAI_API_KEY:-}
ANTHROPIC_API_KEY=\${ANTHROPIC_API_KEY:-}
GOOGLE_AI_API_KEY=\${GOOGLE_AI_API_KEY:-}

# Trading Configuration
TRADING_MODE=\${TRADING_MODE:-simulation}
MAX_POSITION_SIZE=\${MAX_POSITION_SIZE:-10000}
RISK_LIMIT=\${RISK_LIMIT:-0.02}

# External Services
MT5_SERVER=\${MT5_SERVER:-}
MT5_LOGIN=\${MT5_LOGIN:-}
MT5_PASSWORD=\${MT5_PASSWORD:-}

# Payment Integration (Midtrans)
MIDTRANS_SERVER_KEY=\${MIDTRANS_SERVER_KEY:-}
MIDTRANS_CLIENT_KEY=\${MIDTRANS_CLIENT_KEY:-}
MIDTRANS_ENVIRONMENT=\${MIDTRANS_ENVIRONMENT:-sandbox}

# Monitoring & Analytics
METRICS_ENABLED=\${METRICS_ENABLED:-true}
PERFORMANCE_TRACKING=\${PERFORMANCE_TRACKING:-true}
ERROR_REPORTING_ENABLED=\${ERROR_REPORTING_ENABLED:-true}
`;

        const envPath = path.join(this.backendPath, '.env.template');
        await fs.writeFile(envPath, standardEnvTemplate);

        return true;
    }

    /**
     * Fix database connection configurations
     */
    async fixDatabaseConnections() {
        const dbConfigTemplate = `/**
 * Database Configuration - Standardized Connection Settings
 * Generated by Service Port Coordinator
 */

const { Pool } = require('pg');

const dbConfig = {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT) || 5432,
    database: process.env.DB_NAME || 'aitrading_main',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres',

    // Connection Pool Settings
    max: parseInt(process.env.DB_POOL_SIZE) || 10,
    min: 2,
    idle: 10000,
    evict: 1000,
    acquire: 30000,

    // Connection Settings
    connectionTimeoutMillis: parseInt(process.env.DB_CONNECTION_TIMEOUT) || 30000,
    idleTimeoutMillis: 30000,

    // SSL Configuration
    ssl: process.env.NODE_ENV === 'production' ? {
        rejectUnauthorized: false
    } : false,

    // Error Handling
    keepAlive: true,
    keepAliveInitialDelayMillis: 10000,
};

// Create connection pool
const pool = new Pool(dbConfig);

// Handle pool errors
pool.on('error', (err) => {
    console.error('Database pool error:', err);
});

// Health check function
const healthCheck = async () => {
    try {
        const client = await pool.connect();
        await client.query('SELECT 1');
        client.release();
        return { healthy: true, timestamp: new Date().toISOString() };
    } catch (error) {
        return {
            healthy: false,
            error: error.message,
            timestamp: new Date().toISOString()
        };
    }
};

module.exports = {
    pool,
    config: dbConfig,
    healthCheck
};`;

        // Apply to all services that need database connections
        const dbServices = [
            'api-gateway',
            'database-service',
            'trading-engine',
            'billing-service',
            'user-management'
        ];

        for (const service of dbServices) {
            const configPath = path.join(this.backendPath, service, 'config', 'database.js');
            try {
                await fs.mkdir(path.dirname(configPath), { recursive: true });
                await fs.writeFile(configPath, dbConfigTemplate);
            } catch (error) {
                this.logger.warn(`Could not write database config for ${service}:`, error.message);
            }
        }

        return true;
    }

    /**
     * Configure service discovery
     */
    async configureServiceDiscovery() {
        const serviceDiscoveryConfig = `/**
 * Service Discovery Configuration
 * Generated by Service Port Coordinator
 */

const axios = require('axios');

class ServiceDiscovery {
    constructor(serviceName, port) {
        this.serviceName = serviceName;
        this.port = port;
        this.centralHubUrl = process.env.CENTRAL_HUB_URL || 'http://localhost:7000';
        this.registrationInterval = 30000; // 30 seconds
        this.healthCheckInterval = 15000; // 15 seconds
        this.registered = false;
    }

    async register() {
        try {
            const registration = {
                name: this.serviceName,
                port: this.port,
                host: process.env.SERVICE_HOST || 'localhost',
                protocol: 'http',
                health: \`http://localhost:\${this.port}/health\`,
                timestamp: new Date().toISOString()
            };

            await axios.post(\`\${this.centralHubUrl}/api/services/register\`, registration);
            this.registered = true;
            console.log(\`Service \${this.serviceName} registered with Central Hub\`);

            // Start periodic re-registration
            setInterval(() => this.register(), this.registrationInterval);

        } catch (error) {
            console.error(\`Failed to register service \${this.serviceName}:\`, error.message);
            // Retry registration after delay
            setTimeout(() => this.register(), 5000);
        }
    }

    async discover(serviceName) {
        try {
            const response = await axios.get(
                \`\${this.centralHubUrl}/api/services/discovery?name=\${serviceName}\`
            );
            return response.data;
        } catch (error) {
            console.error(\`Failed to discover service \${serviceName}:\`, error.message);
            return null;
        }
    }

    async getServiceUrl(serviceName) {
        const service = await this.discover(serviceName);
        if (service) {
            return \`\${service.protocol}://\${service.host}:\${service.port}\`;
        }
        return null;
    }

    async healthCheck() {
        return {
            service: this.serviceName,
            port: this.port,
            registered: this.registered,
            centralHub: this.centralHubUrl,
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = ServiceDiscovery;`;

        // Apply to all services
        for (const serviceName of Object.keys(this.portRegistry)) {
            const configPath = path.join(this.backendPath, serviceName, 'config', 'service-discovery.js');
            try {
                await fs.mkdir(path.dirname(configPath), { recursive: true });
                await fs.writeFile(configPath, serviceDiscoveryConfig);
            } catch (error) {
                this.logger.warn(`Could not write service discovery config for ${serviceName}:`, error.message);
            }
        }

        return true;
    }

    /**
     * Apply security configurations
     */
    async applySecurity() {
        const securityMiddleware = `/**
 * Security Middleware Configuration
 * Generated by Service Port Coordinator
 */

const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');

const securityConfig = {
    // CORS Configuration
    cors: {
        origin: process.env.CORS_ORIGIN?.split(',') || ['http://localhost:3000'],
        credentials: true,
        methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowedHeaders: ['Content-Type', 'Authorization', 'X-Tenant-ID']
    },

    // Rate Limiting
    rateLimit: {
        windowMs: 15 * 60 * 1000, // 15 minutes
        max: process.env.NODE_ENV === 'production' ? 100 : 1000,
        message: 'Too many requests from this IP',
        standardHeaders: true,
        legacyHeaders: false
    },

    // Helmet Security Headers
    helmet: {
        contentSecurityPolicy: {
            directives: {
                defaultSrc: ["'self'"],
                styleSrc: ["'self'", "'unsafe-inline'"],
                scriptSrc: ["'self'"],
                imgSrc: ["'self'", "data:", "https:"],
                connectSrc: ["'self'"],
                fontSrc: ["'self'"],
                objectSrc: ["'none'"],
                mediaSrc: ["'self'"],
                frameSrc: ["'none'"]
            }
        },
        crossOriginEmbedderPolicy: false
    }
};

const applySecurity = (app) => {
    // Apply Helmet
    app.use(helmet(securityConfig.helmet));

    // Apply CORS
    app.use(cors(securityConfig.cors));

    // Apply Rate Limiting
    app.use('/api/', rateLimit(securityConfig.rateLimit));

    // Security Headers
    app.use((req, res, next) => {
        res.set('X-Content-Type-Options', 'nosniff');
        res.set('X-Frame-Options', 'DENY');
        res.set('X-XSS-Protection', '1; mode=block');
        next();
    });

    // Request logging middleware
    app.use((req, res, next) => {
        console.log(\`\${new Date().toISOString()} - \${req.method} \${req.path} - \${req.ip}\`);
        next();
    });
};

module.exports = { securityConfig, applySecurity };`;

        // Apply to all services
        for (const serviceName of Object.keys(this.portRegistry)) {
            const configPath = path.join(this.backendPath, serviceName, 'config', 'security.js');
            try {
                await fs.mkdir(path.dirname(configPath), { recursive: true });
                await fs.writeFile(configPath, securityMiddleware);
            } catch (error) {
                this.logger.warn(`Could not write security config for ${serviceName}:`, error.message);
            }
        }

        return true;
    }

    /**
     * Standardize error handling
     */
    async standardizeErrorHandling() {
        const errorHandler = `/**
 * Standardized Error Handling
 * Generated by Service Port Coordinator
 */

class ErrorHandler {
    static handle(err, req, res, next) {
        console.error('Error:', err);

        // Default error response
        const errorResponse = {
            success: false,
            error: {
                message: err.message || 'Internal Server Error',
                type: err.name || 'Error',
                timestamp: new Date().toISOString(),
                path: req.path,
                method: req.method
            }
        };

        // Add error code if available
        if (err.code) {
            errorResponse.error.code = err.code;
        }

        // Add stack trace in development
        if (process.env.NODE_ENV === 'development') {
            errorResponse.error.stack = err.stack;
        }

        // Determine status code
        let statusCode = 500;

        if (err.name === 'ValidationError') statusCode = 400;
        if (err.name === 'UnauthorizedError') statusCode = 401;
        if (err.name === 'ForbiddenError') statusCode = 403;
        if (err.name === 'NotFoundError') statusCode = 404;
        if (err.name === 'ConflictError') statusCode = 409;
        if (err.name === 'TooManyRequestsError') statusCode = 429;
        if (err.statusCode) statusCode = err.statusCode;

        res.status(statusCode).json(errorResponse);
    }

    static notFound(req, res) {
        res.status(404).json({
            success: false,
            error: {
                message: 'Route not found',
                type: 'NotFoundError',
                path: req.path,
                method: req.method,
                timestamp: new Date().toISOString()
            }
        });
    }

    static createError(message, type = 'Error', statusCode = 500) {
        const error = new Error(message);
        error.name = type;
        error.statusCode = statusCode;
        return error;
    }
}

module.exports = ErrorHandler;`;

        // Apply to all services
        for (const serviceName of Object.keys(this.portRegistry)) {
            const configPath = path.join(this.backendPath, serviceName, 'middleware', 'errorHandler.js');
            try {
                await fs.mkdir(path.dirname(configPath), { recursive: true });
                await fs.writeFile(configPath, errorHandler);
            } catch (error) {
                this.logger.warn(`Could not write error handler for ${serviceName}:`, error.message);
            }
        }

        return true;
    }

    /**
     * Add standardized health check endpoints
     */
    async addHealthChecks() {
        const healthCheckRoute = `/**
 * Health Check Route
 * Generated by Service Port Coordinator
 */

const express = require('express');
const router = express.Router();

// Health check endpoint
router.get('/health', async (req, res) => {
    try {
        const health = {
            status: 'healthy',
            timestamp: new Date().toISOString(),
            service: process.env.SERVICE_NAME || 'unknown',
            port: process.env.PORT || 'unknown',
            environment: process.env.NODE_ENV || 'development',
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            version: process.env.npm_package_version || '1.0.0'
        };

        // Add database health if applicable
        if (global.dbPool) {
            try {
                const dbHealth = await global.dbPool.healthCheck();
                health.database = dbHealth;
            } catch (error) {
                health.database = { healthy: false, error: error.message };
                health.status = 'degraded';
            }
        }

        // Add Redis health if applicable
        if (global.redisClient) {
            try {
                await global.redisClient.ping();
                health.redis = { healthy: true };
            } catch (error) {
                health.redis = { healthy: false, error: error.message };
                health.status = 'degraded';
            }
        }

        res.json(health);
    } catch (error) {
        res.status(500).json({
            status: 'unhealthy',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// Readiness check
router.get('/ready', async (req, res) => {
    try {
        const readiness = {
            ready: true,
            timestamp: new Date().toISOString(),
            checks: []
        };

        // Database readiness
        if (global.dbPool) {
            try {
                await global.dbPool.healthCheck();
                readiness.checks.push({ name: 'database', ready: true });
            } catch (error) {
                readiness.checks.push({ name: 'database', ready: false, error: error.message });
                readiness.ready = false;
            }
        }

        res.json(readiness);
    } catch (error) {
        res.status(503).json({
            ready: false,
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

module.exports = router;`;

        // Apply to all services
        for (const serviceName of Object.keys(this.portRegistry)) {
            const routePath = path.join(this.backendPath, serviceName, 'routes', 'health.js');
            try {
                await fs.mkdir(path.dirname(routePath), { recursive: true });
                await fs.writeFile(routePath, healthCheckRoute);
            } catch (error) {
                this.logger.warn(`Could not write health check route for ${serviceName}:`, error.message);
            }
        }

        return true;
    }

    /**
     * Standardize logging configuration
     */
    async standardizeLogging() {
        const loggingConfig = `/**
 * Logging Configuration
 * Generated by Service Port Coordinator
 */

const winston = require('winston');

const createLogger = (serviceName) => {
    return winston.createLogger({
        level: process.env.LOG_LEVEL || 'info',
        format: winston.format.combine(
            winston.format.timestamp(),
            winston.format.errors({ stack: true }),
            winston.format.json(),
            winston.format.metadata({ fillExcept: ['message', 'level', 'timestamp'] })
        ),
        defaultMeta: {
            service: serviceName,
            environment: process.env.NODE_ENV || 'development'
        },
        transports: [
            new winston.transports.Console({
                format: winston.format.combine(
                    winston.format.colorize(),
                    winston.format.simple()
                )
            })
        ]
    });
};

// Add file transport in production
if (process.env.NODE_ENV === 'production') {
    const fileTransport = new winston.transports.File({
        filename: 'logs/error.log',
        level: 'error'
    });

    const combinedTransport = new winston.transports.File({
        filename: 'logs/combined.log'
    });
}

module.exports = { createLogger };`;

        // Apply to all services
        for (const serviceName of Object.keys(this.portRegistry)) {
            const configPath = path.join(this.backendPath, serviceName, 'config', 'logging.js');
            try {
                await fs.mkdir(path.dirname(configPath), { recursive: true });
                await fs.writeFile(configPath, loggingConfig);
            } catch (error) {
                this.logger.warn(`Could not write logging config for ${serviceName}:`, error.message);
            }
        }

        return true;
    }

    /**
     * Update service configurations with new port allocations
     */
    async updateServiceConfigurations() {
        for (const [serviceName, config] of Object.entries(this.portRegistry)) {
            try {
                await this.updateServiceConfig(serviceName, config);
            } catch (error) {
                this.logger.error(`Failed to update config for ${serviceName}:`, error);
            }
        }
    }

    /**
     * Update individual service configuration
     */
    async updateServiceConfig(serviceName, config) {
        const configContent = `/**
 * ${serviceName} Configuration
 * Generated by Service Port Coordinator
 */

module.exports = {
    service: {
        name: '${serviceName}',
        port: ${config.port},
        protocol: '${config.protocol}',
        description: '${config.description}',
        critical: ${config.critical}
    },

    server: {
        host: process.env.SERVICE_HOST || 'localhost',
        port: process.env.PORT || ${config.port},
        timeout: 30000
    },

    centralHub: {
        url: process.env.CENTRAL_HUB_URL || 'http://localhost:7000',
        registerOnStart: true,
        heartbeatInterval: 30000
    },

    health: {
        endpoint: '${config.health}',
        interval: 15000
    },

    security: {
        corsEnabled: true,
        rateLimitEnabled: true,
        helmetEnabled: true
    },

    monitoring: {
        metricsEnabled: true,
        loggingEnabled: true,
        performanceTracking: true
    }
};`;

        const configPath = path.join(this.backendPath, serviceName, 'config', 'index.js');
        await fs.mkdir(path.dirname(configPath), { recursive: true });
        await fs.writeFile(configPath, configContent);
    }

    /**
     * Generate comprehensive service registry
     */
    async generateServiceRegistry() {
        const serviceRegistry = {
            version: '1.0.0',
            generatedAt: new Date().toISOString(),
            coordinator: 'ServicePortCoordinator',

            services: this.portRegistry,

            portRanges: {
                'core-services': '3000-3999',
                'data-services': '5000-5999',
                'hub-services': '7000-7999',
                'database-ai-services': '8000-8999',
                'trading-business': '9000-9099',
                'analytics-monitoring': '9100-9199'
            },

            criticalServices: Object.entries(this.portRegistry)
                .filter(([, config]) => config.critical)
                .map(([name]) => name),

            serviceGroups: {
                foundation: ['api-gateway', 'database-service', 'data-bridge', 'central-hub'],
                intelligence: ['ai-orchestrator', 'ml-automl', 'realtime-inference-engine'],
                trading: ['trading-engine', 'billing-service', 'payment-service'],
                monitoring: ['performance-analytics', 'usage-monitoring', 'compliance-monitor']
            },

            integrationFixes: this.integrationFixes,

            deployment: {
                docker: {
                    networkName: 'aitrading-network',
                    composeFile: 'docker-compose.yml'
                },
                kubernetes: {
                    namespace: 'aitrading',
                    configMapName: 'service-registry'
                }
            }
        };

        const registryPath = path.join(this.backendPath, 'config', 'service-registry.json');
        await fs.mkdir(path.dirname(registryPath), { recursive: true });
        await fs.writeFile(registryPath, JSON.stringify(serviceRegistry, null, 2));

        return serviceRegistry;
    }

    /**
     * Get service by name
     */
    getService(serviceName) {
        return this.portRegistry[serviceName];
    }

    /**
     * List all services
     */
    listServices(filter = {}) {
        const services = Object.entries(this.portRegistry);

        if (filter.critical !== undefined) {
            return services.filter(([, config]) => config.critical === filter.critical);
        }

        if (filter.protocol) {
            return services.filter(([, config]) => config.protocol.includes(filter.protocol));
        }

        return services;
    }

    /**
     * Check service health
     */
    async checkServiceHealth(serviceName) {
        const service = this.getService(serviceName);
        if (!service) {
            throw new Error(`Service ${serviceName} not found`);
        }

        try {
            const axios = require('axios');
            const response = await axios.get(
                `http://localhost:${service.port}${service.health}`,
                { timeout: 5000 }
            );

            return {
                service: serviceName,
                healthy: true,
                status: response.status,
                data: response.data,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                service: serviceName,
                healthy: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    /**
     * Get coordinator status
     */
    getStatus() {
        return {
            initialized: true,
            totalServices: Object.keys(this.portRegistry).length,
            criticalServices: Object.values(this.portRegistry).filter(s => s.critical).length,
            integrationFixes: this.integrationFixes.length,
            portRange: {
                min: Math.min(...Object.values(this.portRegistry).map(s => s.port)),
                max: Math.max(...Object.values(this.portRegistry).map(s => s.port))
            },
            timestamp: new Date().toISOString()
        };
    }
}

module.exports = ServicePortCoordinator;