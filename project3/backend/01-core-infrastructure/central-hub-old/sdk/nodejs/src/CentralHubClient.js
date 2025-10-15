/**
 * Central Hub Client - API Gateway Integration
 *
 * Handles communication with Central Hub service for:
 * - Service registration and discovery
 * - Configuration management (static & hot-reload)
 * - Health monitoring and reporting
 * - Contract validation
 *
 * Following ChainFlow pattern: coordination, not proxy
 */

const axios = require('axios');
const EventEmitter = require('events');

class CentralHubClient extends EventEmitter {
    constructor(options = {}) {
        super();

        this.baseURL = options.baseURL || 'http://suho-central-hub:7000';
        this.serviceName = options.serviceName || 'api-gateway';
        this.retryAttempts = options.retryAttempts || 5;
        this.retryDelay = options.retryDelay || 2000;
        this.timeout = options.timeout || 10000;

        this.serviceId = null;
        this.isConnected = false;
        this.retryCount = 0;
        this.heartbeatInterval = null;

        // HTTP client with retry and timeout
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': `${this.serviceName}/2.0.0`
            }
        });

        // Request interceptor for authentication
        this.client.interceptors.request.use(config => {
            if (this.serviceId) {
                config.headers['X-Service-ID'] = this.serviceId;
            }
            return config;
        });

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => this.handleError(error)
        );
    }

    /**
     * Register service with Central Hub
     */
    async register(serviceInfo) {
        try {
            console.log(`📡 Registering ${this.serviceName} with Central Hub...`);

            const response = await this.retryRequest(() =>
                this.client.post('/discovery/register', serviceInfo)
            );

            this.serviceId = response.data.service_id;
            this.isConnected = true;
            this.retryCount = 0;

            // Start heartbeat
            this.startHeartbeat();

            this.emit('registered', response.data);
            console.log(`✅ Service registered with ID: ${this.serviceId}`);

            return response.data;
        } catch (error) {
            console.error('❌ Failed to register with Central Hub:', error.message);
            this.emit('registration_failed', error);
            throw error;
        }
    }

    /**
     * Unregister service from Central Hub
     */
    async unregister() {
        if (!this.serviceId) return;

        try {
            console.log('📡 Unregistering from Central Hub...');

            await this.client.delete(`/discovery/services/${this.serviceId}`);

            this.stopHeartbeat();
            this.isConnected = false;
            this.serviceId = null;

            this.emit('unregistered');
            console.log('✅ Service unregistered successfully');
        } catch (error) {
            console.error('❌ Failed to unregister from Central Hub:', error.message);
        }
    }

    /**
     * Get service configuration from Central Hub
     */
    async getConfiguration(serviceName = null) {
        try {
            const target = serviceName || this.serviceName;
            console.log(`⚙️  Fetching configuration for ${target}...`);

            const response = await this.retryRequest(() =>
                this.client.get(`/config/${target}`)
            );

            console.log(`✅ Configuration loaded for ${target}`);
            this.emit('config_loaded', response.data);

            return response.data;
        } catch (error) {
            console.error(`❌ Failed to load configuration for ${target}:`, error.message);
            this.emit('config_failed', error);
            throw error;
        }
    }

    /**
     * Discover other services
     */
    async discoverService(serviceName) {
        try {
            console.log(`🔍 Discovering service: ${serviceName}`);

            const response = await this.retryRequest(() =>
                this.client.get(`/discovery/services/${serviceName}`)
            );

            return response.data;
        } catch (error) {
            console.error(`❌ Failed to discover service ${serviceName}:`, error.message);
            throw error;
        }
    }

    /**
     * Get all registered services
     */
    async getAllServices() {
        try {
            const response = await this.retryRequest(() =>
                this.client.get('/discovery/services')
            );

            return response.data;
        } catch (error) {
            console.error('❌ Failed to get service list:', error.message);
            throw error;
        }
    }

    /**
     * Report health status to Central Hub
     */
    async reportHealth(healthData = {}) {
        if (!this.serviceId) return;

        try {
            const healthReport = {
                service_id: this.serviceId,
                status: 'healthy',
                timestamp: Date.now(),
                ...healthData
            };

            await this.client.post('/discovery/health', healthReport);

            this.emit('health_reported', healthReport);
        } catch (error) {
            console.error('❌ Failed to report health:', error.message);
            this.emit('health_report_failed', error);
        }
    }

    /**
     * Validate configuration against contracts
     */
    async validateConfiguration(config) {
        try {
            const response = await this.client.post(
                `/config/${this.serviceName}/validate`,
                config
            );

            return response.data;
        } catch (error) {
            console.error('❌ Configuration validation failed:', error.message);
            throw error;
        }
    }

    /**
     * Check Central Hub health
     */
    async checkHealth() {
        try {
            const response = await this.client.get('/health');
            return response.data;
        } catch (error) {
            console.error('❌ Central Hub health check failed:', error.message);
            throw error;
        }
    }

    /**
     * Get database configuration from Central Hub
     * @param {string} dbName - Database name (postgresql, clickhouse, dragonflydb, arangodb, weaviate)
     * @returns {Promise<Object>} Database configuration
     */
    async getDatabaseConfig(dbName) {
        try {
            console.log(`⚙️  Fetching database config for ${dbName}...`);

            const response = await this.retryRequest(() =>
                this.client.get(`/config/database/${dbName}`)
            );

            console.log(`✅ Database config loaded for ${dbName}`);
            this.emit('database_config_loaded', response.data);

            return response.data.config;
        } catch (error) {
            console.error(`❌ Failed to load database config for ${dbName}:`, error.message);
            this.emit('database_config_failed', error);
            throw error;
        }
    }

    /**
     * Get messaging configuration from Central Hub
     * @param {string} msgName - Messaging system name (nats, kafka, zookeeper)
     * @returns {Promise<Object>} Messaging configuration
     */
    async getMessagingConfig(msgName) {
        try {
            console.log(`⚙️  Fetching messaging config for ${msgName}...`);

            const response = await this.retryRequest(() =>
                this.client.get(`/config/messaging/${msgName}`)
            );

            console.log(`✅ Messaging config loaded for ${msgName}`);
            this.emit('messaging_config_loaded', response.data);

            return response.data.config;
        } catch (error) {
            console.error(`❌ Failed to load messaging config for ${msgName}:`, error.message);
            this.emit('messaging_config_failed', error);
            throw error;
        }
    }

    /**
     * Start periodic health reporting (heartbeat)
     */
    startHeartbeat() {
        if (this.heartbeatInterval) return;

        this.heartbeatInterval = setInterval(async () => {
            await this.reportHealth({
                uptime: process.uptime(),
                memory_usage: process.memoryUsage(),
                cpu_usage: process.cpuUsage()
            });
        }, 30000); // Every 30 seconds

        console.log('💓 Health monitoring started');
    }

    /**
     * Stop health reporting
     */
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
            console.log('💓 Health monitoring stopped');
        }
    }

    /**
     * Retry mechanism for requests
     */
    async retryRequest(requestFn) {
        let lastError;

        for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
            try {
                return await requestFn();
            } catch (error) {
                lastError = error;

                if (attempt === this.retryAttempts) {
                    break;
                }

                const delay = this.retryDelay * Math.pow(2, attempt - 1); // Exponential backoff
                console.warn(`⚠️  Request failed (attempt ${attempt}/${this.retryAttempts}), retrying in ${delay}ms...`);

                await this.sleep(delay);
            }
        }

        throw lastError;
    }

    /**
     * Error handler for axios interceptor
     */
    handleError(error) {
        if (error.response) {
            // Server responded with error status
            const { status, data } = error.response;
            console.error(`❌ Central Hub error [${status}]:`, data?.message || data);

            if (status === 401) {
                this.emit('unauthorized');
            } else if (status === 503) {
                this.emit('service_unavailable');
            }
        } else if (error.request) {
            // Network error
            console.error('❌ Network error connecting to Central Hub:', error.message);
            this.isConnected = false;
            this.emit('connection_lost');
        } else {
            // Other error
            console.error('❌ Central Hub client error:', error.message);
        }

        return Promise.reject(error);
    }

    /**
     * Utility: Sleep function
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Get connection status
     */
    isHealthy() {
        return this.isConnected && this.serviceId !== null;
    }

    /**
     * Get service information
     */
    getServiceInfo() {
        return {
            serviceId: this.serviceId,
            serviceName: this.serviceName,
            baseURL: this.baseURL,
            isConnected: this.isConnected,
            retryCount: this.retryCount
        };
    }
}

module.exports = CentralHubClient;