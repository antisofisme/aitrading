/**
 * Configuration Service - Get configs from Central Hub
 * Replaces all hardcoded configurations with centralized management
 */

const axios = require('axios');

class ConfigService {
    constructor() {
        this.config = null;
        this.lastFetched = null;
        this.cacheTimeout = 5 * 60 * 1000; // 5 minutes cache
        this.centralHubUrl = process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000';
    }

    async getConfig(forceRefresh = false) {
        const now = Date.now();

        // Use cache if available and not expired
        if (!forceRefresh && this.config && this.lastFetched &&
            (now - this.lastFetched < this.cacheTimeout)) {
            return this.config;
        }

        try {
            console.log(`🔄 Fetching configuration from Central Hub: ${this.centralHubUrl}`);

            const response = await axios.post(`${this.centralHubUrl}/config`, {
                service_name: 'api-gateway',
                config_keys: [], // Get all configs
                environment: process.env.NODE_ENV || 'development'
            }, {
                timeout: 10000,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (response.data && response.data.direct_response) {
                this.config = response.data.direct_response.data.configuration;
                this.lastFetched = now;

                console.log('✅ Configuration loaded from Central Hub');
                return this.config;
            } else {
                throw new Error('Invalid response format from Central Hub');
            }

        } catch (error) {
            console.warn(`⚠️ Failed to fetch config from Central Hub: ${error.message}`);

            // Return fallback configuration if Central Hub is not available
            return this.getFallbackConfig();
        }
    }

    getFallbackConfig() {
        console.log('📦 Using fallback configuration');

        return {
            database: {
                postgresql: process.env.DATABASE_URL || 'postgresql://suho_admin:suho_secure_password_2024@suho-postgresql:5432/suho_trading',
                dragonflydb: process.env.CACHE_URL || 'redis://:dragonfly_secure_2024@suho-dragonflydb:6379'
            },
            messaging: {
                nats: process.env.NATS_URL || 'nats://suho-nats-server:4222',
                kafka: process.env.KAFKA_BROKERS || 'suho-kafka:9092'
            },
            jwt: {
                secret: process.env.JWT_SECRET || 'your-super-secret-jwt-key-change-in-production',
                expiresIn: process.env.JWT_EXPIRES_IN || '24h',
                issuer: process.env.JWT_ISSUER || 'suho-api-gateway',
                audience: process.env.JWT_AUDIENCE || 'suho-trading'
            },
            api: {
                port: parseInt(process.env.PORT) || 8000,
                trading_ws_port: 8001,
                price_stream_ws_port: 8002,
                cors_origins: process.env.ALLOWED_ORIGINS?.split(',') || ['*'],
                rate_limit: {
                    window_ms: 15 * 60 * 1000, // 15 minutes
                    max_requests: 1000
                }
            },
            services: {
                central_hub: process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000'
            },
            hot_reload: {
                enabled: process.env.HOT_RELOAD_ENABLED !== 'false'
            }
        };
    }

    // Get specific configuration value with fallback
    get(keyPath, fallback = null) {
        if (!this.config) {
            console.warn('⚠️ Configuration not loaded, using fallback');
            return fallback;
        }

        const keys = keyPath.split('.');
        let value = this.config;

        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                return fallback;
            }
        }

        return value !== undefined ? value : fallback;
    }

    // Get database configuration
    getDatabase(dbName) {
        return this.get(`database.${dbName}`, null);
    }

    // Get messaging configuration
    getMessaging(service) {
        return this.get(`messaging.${service}`, null);
    }

    // Get JWT configuration
    getJWT() {
        return {
            secret: this.get('jwt.secret', 'fallback-secret'),
            expiresIn: this.get('jwt.expiresIn', '24h'),
            issuer: this.get('jwt.issuer', 'api-gateway'),
            audience: this.get('jwt.audience', 'suho-trading')
        };
    }

    // Get API configuration
    getAPI() {
        return {
            port: this.get('api.port', 8000),
            trading_ws_port: this.get('api.trading_ws_port', 8001),
            price_stream_ws_port: this.get('api.price_stream_ws_port', 8002),
            cors_origins: this.get('api.cors_origins', ['*']),
            rate_limit: this.get('api.rate_limit', {
                window_ms: 15 * 60 * 1000,
                max_requests: 1000
            })
        };
    }

    // Get service URLs
    getServiceURL(serviceName) {
        return this.get(`services.${serviceName}`, null);
    }

    // Check if hot reload is enabled
    isHotReloadEnabled() {
        return this.get('hot_reload.enabled', false);
    }

    // Force refresh configuration
    async refresh() {
        return await this.getConfig(true);
    }
}

// Export singleton instance
const configService = new ConfigService();

module.exports = {
    ConfigService,
    configService
};