/**
 * Central Hub Client for Node.js Services
 * Consistent with Python SDK (central_hub_sdk/client.py)
 *
 * Features:
 * - Service registration with multi-instance support
 * - Periodic heartbeat with auto re-registration on 404
 * - Instance ID auto-detection from hostname
 * - Graceful deregistration
 */

const axios = require('axios');
const os = require('os');

class CentralHubClient {
    constructor(options = {}) {
        this.serviceName = options.serviceName || 'unknown-service';
        this.serviceType = options.serviceType || 'generic';
        this.version = options.version || '1.0.0';
        this.capabilities = options.capabilities || [];
        this.metadata = options.metadata || {};

        // Central Hub configuration
        this.centralHubUrl = options.centralHubUrl ||
            process.env.CENTRAL_HUB_URL ||
            'http://suho-central-hub:7000';
        this.heartbeatInterval = options.heartbeatInterval ||
            parseInt(process.env.HEARTBEAT_INTERVAL || '30') * 1000; // Convert to ms

        // Auto-detect instance_id from hostname (consistent with Python SDK)
        const envInstanceId = process.env.INSTANCE_ID?.trim() || '';
        this.instanceId = envInstanceId || os.hostname();

        // State
        this.registered = false;
        this.heartbeatTimer = null;
        this.isRunning = false;

        // HTTP client configuration
        this.httpClient = axios.create({
            baseURL: this.centralHubUrl,
            timeout: 10000,
            headers: {
                'Content-Type': 'application/json'
            }
        });

        console.log(`Central Hub Client initialized for ${this.serviceName}`);
        console.log(`Central Hub URL: ${this.centralHubUrl}`);
        console.log(`Instance ID: ${this.instanceId}`);
    }

    /**
     * Register service with Central Hub
     * @returns {Promise<boolean>} True if registration successful
     */
    async register() {
        try {
            const registrationData = {
                name: this.serviceName,
                host: process.env.HOSTNAME || this.serviceName,
                port: parseInt(process.env.SERVICE_PORT || process.env.PORT || '8080'),
                protocol: 'http',
                health_endpoint: '/health',
                version: this.version,
                metadata: {
                    ...this.metadata,
                    type: this.serviceType,
                    instance_id: this.instanceId,
                    start_time: Date.now()
                },
                capabilities: this.capabilities
            };

            const response = await this.httpClient.post(
                '/api/discovery/register',
                registrationData
            );

            if (response.status === 200) {
                this.registered = true;
                console.log(`✅ Registered with Central Hub: ${this.serviceName}`);
                console.log(`Registration response:`, response.data);
                return true;
            } else {
                console.error(`❌ Registration failed: HTTP ${response.status}`);
                console.error(`Response:`, response.data);
                return false;
            }

        } catch (error) {
            if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
                console.warn(`⚠️  Cannot connect to Central Hub at ${this.centralHubUrl}`);
                console.warn(`Service ${this.serviceName} will run without Central Hub integration`);
            } else {
                console.error(`❌ Registration error:`, error.message);
            }
            return false;
        }
    }

    /**
     * Send heartbeat to Central Hub with optional metrics
     * Implements auto re-registration on 404 (consistent with Python SDK)
     *
     * @param {Object} metrics - Service-specific metrics to report
     * @returns {Promise<boolean>} True if heartbeat sent successfully
     */
    async sendHeartbeat(metrics = {}) {
        if (!this.registered) {
            console.debug('Not registered, skipping heartbeat');
            return false;
        }

        try {
            const heartbeatData = {
                service_name: this.serviceName,
                instance_id: this.instanceId,  // Include instance_id for multi-instance support
                status: 'healthy',
                timestamp: Date.now(),
                metrics: metrics
            };

            const response = await this.httpClient.post(
                '/api/discovery/heartbeat',
                heartbeatData
            );

            if (response.status === 200) {
                console.debug(`Heartbeat sent for ${this.serviceName}`);
                return true;
            } else if (response.status === 404) {
                // Service not found in registry - auto re-register (consistent with Python SDK)
                console.warn(`⚠️  Service not found in Central Hub (404) - attempting re-registration...`);
                this.registered = false;  // Mark as not registered
                const success = await this.register();
                if (success) {
                    console.log(`✅ Successfully re-registered with Central Hub`);
                    return true;
                } else {
                    console.error(`❌ Re-registration failed`);
                    return false;
                }
            } else {
                console.warn(`Heartbeat failed: HTTP ${response.status}`);
                return false;
            }

        } catch (error) {
            if (error.response?.status === 404) {
                // Handle 404 from error response
                console.warn(`⚠️  Service not found in Central Hub (404) - attempting re-registration...`);
                this.registered = false;
                const success = await this.register();
                if (success) {
                    console.log(`✅ Successfully re-registered with Central Hub`);
                    return true;
                }
            }
            console.warn(`Heartbeat error: ${error.message}`);
            return false;
        }
    }

    /**
     * Start Central Hub integration
     * @param {Function} metricsCallback - Optional async function that returns metrics dict
     */
    async start(metricsCallback = null) {
        // Register with Central Hub
        await this.register();

        // Start heartbeat loop if registered
        if (this.registered) {
            this.isRunning = true;

            const heartbeatLoop = async () => {
                while (this.isRunning) {
                    try {
                        await new Promise(resolve => setTimeout(resolve, this.heartbeatInterval));

                        // Get metrics if callback provided
                        let metrics = {};
                        if (metricsCallback) {
                            metrics = typeof metricsCallback === 'function'
                                ? await Promise.resolve(metricsCallback())
                                : metricsCallback;
                        }

                        await this.sendHeartbeat(metrics);

                    } catch (error) {
                        if (error.name === 'AbortError') break;
                        console.error(`Heartbeat loop error: ${error.message}`);
                    }
                }
            };

            // Start heartbeat loop (non-blocking)
            heartbeatLoop().catch(error => {
                console.error(`Heartbeat loop crashed: ${error.message}`);
            });

            console.log(`Started heartbeat loop (interval: ${this.heartbeatInterval / 1000}s)`);
        }
    }

    /**
     * Deregister service from Central Hub (graceful shutdown)
     */
    async deregister() {
        if (!this.registered) {
            return;
        }

        try {
            // Stop heartbeat
            this.isRunning = false;
            if (this.heartbeatTimer) {
                clearInterval(this.heartbeatTimer);
                this.heartbeatTimer = null;
            }

            // Send deregistration
            await this.httpClient.post('/api/discovery/deregister', {
                service_name: this.serviceName
            });

            console.log(`✅ Deregistered ${this.serviceName} from Central Hub`);
            this.registered = false;

        } catch (error) {
            console.warn(`Deregistration error: ${error.message}`);
        }
    }

    /**
     * Stop Central Hub integration
     */
    async stop() {
        await this.deregister();
    }

    /**
     * Get database configuration from Central Hub
     * @param {string} dbName - Database name (postgresql, clickhouse, dragonflydb, arangodb, weaviate)
     * @returns {Promise<Object>} Database configuration
     */
    async getDatabaseConfig(dbName) {
        try {
            const response = await this.httpClient.get(
                `/api/config/database/${dbName}`
            );

            console.log(`✅ Retrieved database config for ${dbName}`);
            return response.data.config;

        } catch (error) {
            if (error.response?.status === 404) {
                console.error(`❌ Database config not found: ${dbName}`);
                throw new Error(`Database '${dbName}' not found in Central Hub configuration`);
            } else {
                console.error(`❌ Failed to get database config: ${error.message}`);
                throw error;
            }
        }
    }

    /**
     * Get messaging configuration from Central Hub
     * @param {string} msgName - Messaging system name (nats, kafka, zookeeper)
     * @returns {Promise<Object>} Messaging configuration
     */
    async getMessagingConfig(msgName) {
        try {
            const response = await this.httpClient.get(
                `/api/config/messaging/${msgName}`
            );

            console.log(`✅ Retrieved messaging config for ${msgName}`);
            return response.data.config;

        } catch (error) {
            if (error.response?.status === 404) {
                console.error(`❌ Messaging config not found: ${msgName}`);
                throw new Error(`Messaging system '${msgName}' not found in Central Hub configuration`);
            } else {
                console.error(`❌ Failed to get messaging config: ${error.message}`);
                throw error;
            }
        }
    }

    /**
     * Check if client is registered
     * @returns {boolean}
     */
    isRegistered() {
        return this.registered;
    }

    /**
     * Get instance ID
     * @returns {string}
     */
    getInstanceId() {
        return this.instanceId;
    }
}

module.exports = CentralHubClient;
