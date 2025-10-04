/**
 * Central Hub HTTP Client
 *
 * Replaces direct shared component dependencies with HTTP calls
 * to Central Hub service endpoints.
 */

const axios = require('axios');
const logger = require('../utils/logger');

class CentralHubClient {
    constructor(config = {}) {
        this.baseURL = config.centralHubURL || process.env.CENTRAL_HUB_URL || 'http://suho-central-hub:7000';
        this.serviceName = config.serviceName || 'api-gateway';
        this.timeout = config.timeout || 5000;

        // Create axios instance with default config
        this.client = axios.create({
            baseURL: this.baseURL,
            timeout: this.timeout,
            headers: {
                'Content-Type': 'application/json',
                'User-Agent': `${this.serviceName}/1.0.0`
            }
        });

        // Setup request/response interceptors
        this.setupInterceptors();
    }

    setupInterceptors() {
        // Request interceptor
        this.client.interceptors.request.use(
            (config) => {
                logger.debug(`Central Hub API: ${config.method?.toUpperCase()} ${config.url}`);
                return config;
            },
            (error) => {
                logger.error('Central Hub request error:', error.message);
                return Promise.reject(error);
            }
        );

        // Response interceptor
        this.client.interceptors.response.use(
            (response) => {
                logger.debug(`Central Hub response: ${response.status} ${response.config.url}`);
                return response;
            },
            (error) => {
                logger.error('Central Hub response error:', {
                    url: error.config?.url,
                    status: error.response?.status,
                    message: error.message
                });
                return Promise.reject(error);
            }
        );
    }

    // Replace shared.TransferManager functionality
    async sendMessage(targetService, data, options = {}) {
        try {
            const payload = {
                target_service: targetService,
                data: data,
                transport_method: options.transportMethod || 'auto',
                options: {
                    correlation_id: options.correlationId,
                    timeout: options.timeout,
                    critical_path: options.criticalPath || false,
                    volume: options.volume || 'medium'
                }
            };

            const response = await this.client.post('/coordination/send-message', payload);
            return response.data;
        } catch (error) {
            logger.error(`Failed to send message to ${targetService}:`, error.message);
            throw error;
        }
    }

    // Service Discovery
    async discoverService(serviceName) {
        try {
            const response = await this.client.get(`/discovery/services/${serviceName}`);
            return response.data;
        } catch (error) {
            logger.error(`Failed to discover service ${serviceName}:`, error.message);
            throw error;
        }
    }

    async registerService(serviceInfo) {
        try {
            const response = await this.client.post('/discovery/register', serviceInfo);
            return response.data;
        } catch (error) {
            logger.error('Failed to register service:', error.message);
            throw error;
        }
    }

    async getServices() {
        try {
            const response = await this.client.get('/discovery/services');
            return response.data.services;
        } catch (error) {
            logger.error('Failed to get services:', error.message);
            throw error;
        }
    }

    // Configuration Management
    async getConfig(serviceName = null) {
        try {
            const endpoint = serviceName
                ? `/config/service/${serviceName}`
                : '/config/services';

            const response = await this.client.get(endpoint);
            return response.data;
        } catch (error) {
            logger.error('Failed to get config:', error.message);
            throw error;
        }
    }

    // Health and Monitoring
    async getHealth() {
        try {
            const response = await this.client.get('/health');
            return response.data;
        } catch (error) {
            logger.error('Failed to get health:', error.message);
            throw error;
        }
    }

    async getDetailedHealth() {
        try {
            const response = await this.client.get('/health/detailed');
            return response.data;
        } catch (error) {
            logger.error('Failed to get detailed health:', error.message);
            throw error;
        }
    }

    async getMetrics() {
        try {
            const response = await this.client.get('/metrics');
            return response.data;
        } catch (error) {
            logger.error('Failed to get metrics:', error.message);
            throw error;
        }
    }

    // Circuit Breaker functionality
    async checkCircuitBreaker(serviceName, operation) {
        try {
            const response = await this.client.post('/coordination/circuit-breaker-check', {
                service_name: serviceName,
                operation_name: operation,
                context: { source: this.serviceName }
            });
            return response.data;
        } catch (error) {
            logger.error(`Failed to check circuit breaker for ${serviceName}:`, error.message);
            throw error;
        }
    }

    // Error Analysis (replaces ErrorDNA)
    async analyzeError(error, context = {}) {
        try {
            const response = await this.client.post('/shared/error-analysis', {
                error: {
                    message: error.message,
                    type: error.constructor.name,
                    stack: error.stack
                },
                context: {
                    service: this.serviceName,
                    ...context
                }
            });
            return response.data;
        } catch (analysisError) {
            logger.error('Failed to analyze error:', analysisError.message);
            // Return basic analysis if Central Hub is not available
            return {
                error_type: 'unknown_error',
                severity: 'medium',
                retryable: false,
                suggested_actions: ['log_and_escalate']
            };
        }
    }

    // Utility methods
    async ping() {
        try {
            const response = await this.client.get('/health');
            return response.status === 200;
        } catch (error) {
            return false;
        }
    }

    isConnected() {
        return this.ping();
    }
}

// Factory function for easy instantiation
function createCentralHubClient(config = {}) {
    return new CentralHubClient(config);
}

module.exports = {
    CentralHubClient,
    createCentralHubClient
};