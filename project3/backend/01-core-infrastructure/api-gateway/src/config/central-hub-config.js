/**
 * Central Hub Configuration Loader
 * Uses Central Hub Client for Node.js services
 */

const CentralHubClient = require('./central-hub-client');

class CentralHubConfigLoader {
    constructor() {
        this.centralHub = new CentralHubClient({
            serviceName: 'api-gateway',
            serviceType: 'gateway',
            version: '2.0.0',
            centralHubUrl: process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000',
            capabilities: [
                'http-api',
                'websocket',
                'bidirectional-routing',
                'binary-protocol',
                'nats-messaging',
                'kafka-messaging',
                'client-mt5-support'
            ],
            metadata: {
                websocket_port: process.env.WS_PORT || 8001
            }
        });

        this.config = {
            database: {},
            messaging: {},
            service: {}
        };

        this.isInitialized = false;
    }

    /**
     * Initialize Central Hub connection and fetch all configs
     * Also starts heartbeat mechanism
     */
    async initialize() {
        try {
            console.log('🚀 Initializing Central Hub integration...');

            // 1. Register service with Central Hub and start heartbeat
            await this.centralHub.start(() => this.getServiceMetrics());

            // 2. Fetch database configurations
            await this.fetchDatabaseConfigs();

            // 3. Fetch messaging configurations
            await this.fetchMessagingConfigs();

            this.isInitialized = true;
            console.log('✅ Central Hub integration initialized successfully');

            return this.config;
        } catch (error) {
            console.warn(`⚠️  Central Hub initialization failed: ${error.message}`);
            console.warn('⚠️  Using fallback configuration...');
            return this.getFallbackConfig();
        }
    }

    /**
     * Get service metrics for heartbeat
     * @returns {Object} Service metrics
     */
    getServiceMetrics() {
        return {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            connections: 0  // Will be updated by actual service
        };
    }

    /**
     * Fetch database configurations from Central Hub
     */
    async fetchDatabaseConfigs() {
        try {
            // Fetch PostgreSQL config
            const postgresConfig = await this.centralHub.getDatabaseConfig('postgresql');
            this.config.database.postgresql = this.buildPostgresUrl(postgresConfig);

            // Fetch DragonflyDB config
            const dragonflyConfig = await this.centralHub.getDatabaseConfig('dragonflydb');
            this.config.database.dragonflydb = this.buildRedisUrl(dragonflyConfig);

            console.log('✅ Database configurations loaded from Central Hub');
        } catch (error) {
            console.warn(`⚠️  Failed to fetch database configs: ${error.message}`);
            throw error;
        }
    }

    /**
     * Fetch messaging configurations from Central Hub
     */
    async fetchMessagingConfigs() {
        try {
            // Fetch NATS config
            const natsConfig = await this.centralHub.getMessagingConfig('nats');
            this.config.messaging.nats = this.buildNatsUrl(natsConfig);

            // Fetch Kafka config
            const kafkaConfig = await this.centralHub.getMessagingConfig('kafka');
            this.config.messaging.kafka = this.buildKafkaConfig(kafkaConfig);

            console.log('✅ Messaging configurations loaded from Central Hub');
        } catch (error) {
            console.warn(`⚠️  Failed to fetch messaging configs: ${error.message}`);
            throw error;
        }
    }

    /**
     * Build PostgreSQL connection URL
     */
    buildPostgresUrl(config) {
        const conn = config.connection;
        const auth = config.credentials;
        return `postgresql://${auth.username}:${auth.password}@${conn.host}:${conn.port}/${conn.database}`;
    }

    /**
     * Build Redis/DragonflyDB connection URL
     */
    buildRedisUrl(config) {
        const conn = config.connection;
        const auth = config.credentials;
        const password = auth.password ? `:${auth.password}` : '';
        return `redis://${password}@${conn.host}:${conn.port}`;
    }

    /**
     * Build NATS connection URLs (supports cluster)
     */
    buildNatsUrl(config) {
        const conn = config.connection;

        // Support cluster_urls for NATS cluster
        if (conn.cluster_urls && Array.isArray(conn.cluster_urls)) {
            return {
                servers: conn.cluster_urls,
                cluster: true
            };
        }

        // Fallback to single server
        return {
            servers: [`nats://${conn.host}:${conn.port}`],
            cluster: false
        };
    }

    /**
     * Build Kafka configuration object
     */
    buildKafkaConfig(config) {
        const conn = config.connection;
        return {
            brokers: Array.isArray(conn.bootstrap_servers)
                ? conn.bootstrap_servers
                : [conn.bootstrap_servers],
            clientId: 'api-gateway',
            connectionTimeout: 10000,
            requestTimeout: 30000
        };
    }

    /**
     * Get current configuration
     */
    getConfig() {
        if (!this.isInitialized) {
            throw new Error('CentralHubConfigLoader not initialized. Call initialize() first.');
        }
        return this.config;
    }

    /**
     * Fallback configuration if Central Hub is unavailable
     */
    getFallbackConfig() {
        console.log('📦 Using fallback configuration (environment variables)');

        return {
            database: {
                postgresql: process.env.DATABASE_URL ||
                    'postgresql://suho_admin:suho_secure_password_2024@suho-postgresql:5432/suho_trading',
                dragonflydb: process.env.CACHE_URL ||
                    'redis://:dragonfly_secure_2024@suho-dragonflydb:6379'
            },
            messaging: {
                nats: process.env.NATS_URL || 'nats://suho-nats-server:4222',
                kafka: {
                    brokers: (process.env.KAFKA_BROKERS || 'suho-kafka:9092').split(','),
                    clientId: 'api-gateway'
                }
            },
            service: {
                registered: false,
                fallback_mode: true
            }
        };
    }

    /**
     * Report health to Central Hub (via heartbeat)
     */
    async reportHealth(healthData) {
        if (this.centralHub.isRegistered()) {
            await this.centralHub.sendHeartbeat(healthData);
        }
    }

    /**
     * Get Central Hub client instance
     */
    getCentralHubClient() {
        return this.centralHub;
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        console.log('🛑 Shutting down Central Hub integration...');
        await this.centralHub.stop();
        console.log('✅ Central Hub integration shutdown complete');
    }
}

module.exports = CentralHubConfigLoader;
