/**
 * Service Configuration Module - API Gateway
 *
 * Manages configuration loading and validation following Central Hub patterns:
 * - Static configurations (infrastructure)
 * - Hot-reload configurations (business rules)
 * - Fallback configurations (standalone mode)
 * - Environment variable overrides
 */

const path = require('path');
const fs = require('fs');

class ServiceConfig {
    constructor() {
        this.config = null;
        this.environment = process.env.NODE_ENV || 'development';
    }

    /**
     * Get default configuration for standalone mode
     */
    static getDefaultConfig() {
        return {
            service_info: {
                name: 'api-gateway',
                version: '2.0.0',
                environment: process.env.NODE_ENV || 'development',
                description: 'Suho AI Trading Platform API Gateway'
            },

            // API Gateway specific configurations
            api_gateway: {
                // CORS configuration
                cors: {
                    origin: process.env.CORS_ORIGIN?.split(',') || ['*'],
                    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'HEAD'],
                    allowedHeaders: ['*'],
                    credentials: true,
                    maxAge: 86400
                },

                // Suho Binary Protocol settings
                suho_binary_protocol: {
                    enabled: true,
                    packet_size: 144,
                    compression: false,
                    validation: true,
                    timeout_ms: 5000
                },

                // WebSocket configuration
                websocket: {
                    trading_port: 8001,
                    price_stream_port: 8002,
                    ping_interval: 30000,
                    pong_timeout: 5000,
                    max_connections: 1000
                },

                // HTTP server settings
                http: {
                    port: parseInt(process.env.PORT || '8000'),
                    host: '0.0.0.0',
                    keep_alive_timeout: 5000,
                    headers_timeout: 60000,
                    max_request_size_mb: 10
                }
            },

            // Business rules and validation
            business_rules: {
                validation_rules: {
                    require_authentication: process.env.REQUIRE_AUTH === 'true',
                    max_request_size_mb: parseInt(process.env.MAX_REQUEST_SIZE || '10'),
                    validate_contracts: true,
                    strict_type_checking: true
                },

                rate_limiting: {
                    enabled: process.env.RATE_LIMIT_ENABLED !== 'false',
                    requests_per_minute: parseInt(process.env.RATE_LIMIT_RPM || '1000'),
                    burst_limit: parseInt(process.env.RATE_LIMIT_BURST || '100'),
                    window_ms: 60000,
                    store: 'memory' // 'memory' or 'redis'
                },

                timeouts: {
                    request_timeout_ms: parseInt(process.env.REQUEST_TIMEOUT || '30000'),
                    connection_timeout_ms: parseInt(process.env.CONNECTION_TIMEOUT || '5000'),
                    socket_timeout_ms: parseInt(process.env.SOCKET_TIMEOUT || '120000')
                },

                retry_policy: {
                    max_attempts: parseInt(process.env.RETRY_ATTEMPTS || '3'),
                    backoff_multiplier: parseFloat(process.env.RETRY_BACKOFF || '2'),
                    initial_delay_ms: parseInt(process.env.RETRY_DELAY || '1000')
                }
            },

            // Performance and monitoring
            performance: {
                enable_compression: process.env.ENABLE_COMPRESSION !== 'false',
                enable_caching: process.env.ENABLE_CACHING !== 'false',
                cache_ttl_seconds: parseInt(process.env.CACHE_TTL || '300'),
                enable_metrics: process.env.ENABLE_METRICS !== 'false',
                metrics_interval_ms: parseInt(process.env.METRICS_INTERVAL || '30000')
            },

            // Security settings
            security: {
                helmet_enabled: true,
                content_security_policy: false,
                cross_origin_embedder_policy: false,
                jwt_secret: process.env.JWT_SECRET || 'suho-dev-secret-change-in-production',
                session_timeout_hours: parseInt(process.env.SESSION_TIMEOUT || '24')
            },

            // Logging configuration
            logging: {
                level: process.env.LOG_LEVEL || 'info',
                format: process.env.LOG_FORMAT || 'json',
                enable_request_logging: true,
                enable_error_stack: process.env.NODE_ENV === 'development'
            },

            // Central Hub integration
            central_hub: {
                url: process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000',
                retry_attempts: parseInt(process.env.HUB_RETRY_ATTEMPTS || '5'),
                retry_delay_ms: parseInt(process.env.HUB_RETRY_DELAY || '2000'),
                health_report_interval_ms: parseInt(process.env.HUB_HEALTH_INTERVAL || '30000'),
                enable_fallback_mode: process.env.HUB_FALLBACK !== 'false'
            },

            // Database connections (static, loaded from Central Hub)
            databases: {
                postgresql: {
                    enabled: true,
                    connection_timeout_ms: 5000
                },
                dragonflydb: {
                    enabled: true,
                    connection_timeout_ms: 3000
                }
            },

            // Message brokers (static, loaded from Central Hub)
            messaging: {
                nats: {
                    enabled: true,
                    subjects: {
                        api_events: 'suho.api.events',
                        trade_commands: 'suho.trade.commands',
                        price_updates: 'suho.price.updates'
                    }
                },
                kafka: {
                    enabled: true,
                    topics: {
                        market_data: 'suho.market.data',
                        trade_events: 'suho.trade.events'
                    }
                }
            }
        };
    }

    /**
     * Load configuration from Central Hub or fallback to defaults
     */
    static async loadConfiguration(centralHubClient = null) {
        const config = new ServiceConfig();

        try {
            if (centralHubClient && centralHubClient.isHealthy()) {
                // Load from Central Hub
                console.log('⚙️  Loading configuration from Central Hub...');
                const hubConfig = await centralHubClient.getConfiguration('api-gateway');

                // Merge with defaults
                config.config = config.mergeConfigurations(
                    ServiceConfig.getDefaultConfig(),
                    hubConfig
                );

                console.log('✅ Configuration loaded from Central Hub');
            } else {
                // Fallback to default configuration
                console.log('⚠️  Using default configuration (Central Hub unavailable)');
                config.config = ServiceConfig.getDefaultConfig();
            }

            // Apply environment variable overrides
            config.applyEnvironmentOverrides();

            // Validate configuration
            config.validateConfiguration();

            return config.config;
        } catch (error) {
            console.error('❌ Failed to load configuration:', error.message);
            console.log('⚠️  Falling back to default configuration');

            config.config = ServiceConfig.getDefaultConfig();
            config.applyEnvironmentOverrides();

            return config.config;
        }
    }

    /**
     * Merge configurations with deep merge
     */
    mergeConfigurations(defaultConfig, hubConfig) {
        return this.deepMerge(defaultConfig, hubConfig);
    }

    /**
     * Apply environment variable overrides
     */
    applyEnvironmentOverrides() {
        if (!this.config) return;

        // Override critical settings from environment
        if (process.env.PORT) {
            this.config.api_gateway.http.port = parseInt(process.env.PORT);
        }

        if (process.env.API_GATEWAY_HOST) {
            this.config.api_gateway.http.host = process.env.API_GATEWAY_HOST;
        }

        if (process.env.CENTRAL_HUB_URL) {
            this.config.central_hub.url = process.env.CENTRAL_HUB_URL;
        }

        if (process.env.LOG_LEVEL) {
            this.config.logging.level = process.env.LOG_LEVEL;
        }

        // Security: Always use environment JWT secret if provided
        if (process.env.JWT_SECRET) {
            this.config.security.jwt_secret = process.env.JWT_SECRET;
        }

        console.log('✅ Environment overrides applied');
    }

    /**
     * Validate configuration for required fields and types
     */
    validateConfiguration() {
        if (!this.config) {
            throw new Error('Configuration is null or undefined');
        }

        // Validate required sections
        const requiredSections = [
            'service_info',
            'api_gateway',
            'business_rules',
            'performance',
            'security',
            'central_hub'
        ];

        for (const section of requiredSections) {
            if (!this.config[section]) {
                throw new Error(`Missing required configuration section: ${section}`);
            }
        }

        // Validate port numbers
        const port = this.config.api_gateway.http.port;
        if (!port || port < 1 || port > 65535) {
            throw new Error(`Invalid port number: ${port}`);
        }

        // Validate rate limiting
        const rateLimit = this.config.business_rules.rate_limiting;
        if (rateLimit.enabled && rateLimit.requests_per_minute <= 0) {
            throw new Error('Rate limiting requests_per_minute must be positive');
        }

        // Validate timeouts
        const timeouts = this.config.business_rules.timeouts;
        if (timeouts.request_timeout_ms <= 0 || timeouts.connection_timeout_ms <= 0) {
            throw new Error('Timeout values must be positive');
        }

        console.log('✅ Configuration validation passed');
    }

    /**
     * Get configuration value by path (dot notation)
     */
    static getConfigValue(config, path, defaultValue = null) {
        const keys = path.split('.');
        let current = config;

        for (const key of keys) {
            if (current && typeof current === 'object' && key in current) {
                current = current[key];
            } else {
                return defaultValue;
            }
        }

        return current;
    }

    /**
     * Check if running in development mode
     */
    static isDevelopment() {
        return process.env.NODE_ENV === 'development';
    }

    /**
     * Check if running in production mode
     */
    static isProduction() {
        return process.env.NODE_ENV === 'production';
    }

    /**
     * Deep merge utility function
     */
    deepMerge(target, source) {
        const result = { ...target };

        for (const key in source) {
            if (source.hasOwnProperty(key)) {
                if (
                    typeof source[key] === 'object' &&
                    source[key] !== null &&
                    !Array.isArray(source[key]) &&
                    typeof target[key] === 'object' &&
                    target[key] !== null &&
                    !Array.isArray(target[key])
                ) {
                    result[key] = this.deepMerge(target[key], source[key]);
                } else {
                    result[key] = source[key];
                }
            }
        }

        return result;
    }

    /**
     * Get service metadata for Central Hub registration
     */
    static getServiceMetadata(config) {
        return {
            name: config.service_info.name,
            version: config.service_info.version,
            environment: config.service_info.environment,
            host: process.env.API_GATEWAY_HOST || 'suho-api-gateway',
            port: config.api_gateway.http.port,
            protocol: 'http',
            health_endpoint: '/health',
            metadata: {
                type: 'api-gateway',
                capabilities: [
                    'http',
                    'websocket',
                    'trading',
                    'suho-binary-protocol',
                    'client-mt5-integration'
                ],
                max_connections: config.api_gateway.websocket.max_connections,
                load_balancing_weight: 10,
                suho_protocol_version: '2.0.0'
            },
            transport_config: {
                preferred_inbound: ['http', 'websocket'],
                preferred_outbound: ['http', 'nats-kafka'],
                supports_streaming: true,
                max_message_size: config.api_gateway.http.max_request_size_mb * 1024 * 1024
            }
        };
    }
}

module.exports = ServiceConfig;