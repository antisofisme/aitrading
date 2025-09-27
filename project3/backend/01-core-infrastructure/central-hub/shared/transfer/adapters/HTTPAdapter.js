/**
 * HTTP REST Transport Adapter
 *
 * Implements HTTP transport for low volume, standard data
 * Features:
 * - RESTful API calls
 * - JSON and binary payload support
 * - Retry mechanism
 * - Circuit breaker pattern
 * - Connection pooling
 */

const axios = require('axios');
const EventEmitter = require('events');
const logger = require('../../logging/logger');

class HTTPAdapter extends EventEmitter {
    constructor(config = {}) {
        super();

        this.config = {
            timeout: config.timeout || 30000,
            max_retries: config.max_retries || 3,
            retry_delay: config.retry_delay || 1000,
            base_port: config.base_port || 8080,
            default_headers: {
                'Content-Type': 'application/json',
                'User-Agent': 'SuhoTransfer/1.0',
                ...config.default_headers
            },
            circuit_breaker: {
                failure_threshold: config.circuit_breaker?.failure_threshold || 5,
                reset_timeout: config.circuit_breaker?.reset_timeout || 60000,
                ...config.circuit_breaker
            },
            ...config
        };

        // HTTP clients with connection pooling
        this.clients = new Map(); // destination -> axios instance
        this.circuit_breakers = new Map(); // destination -> circuit breaker state

        // Status
        this.status = {
            active_connections: 0,
            total_requests: 0,
            failed_requests: 0
        };

        // Metrics
        this.metrics = {
            requests_sent: 0,
            requests_failed: 0,
            avg_latency: 0,
            circuit_breaker_trips: 0
        };
    }

    /**
     * Initialize HTTP adapter
     */
    async initialize() {
        logger.info('Initializing HTTP adapter');

        try {
            // Setup default axios configuration
            axios.defaults.timeout = this.config.timeout;
            axios.defaults.headers.common = {
                ...axios.defaults.headers.common,
                ...this.config.default_headers
            };

            logger.info('HTTP adapter initialized successfully');
            this.emit('ready');

        } catch (error) {
            logger.error('Failed to initialize HTTP adapter', { error });
            throw error;
        }
    }

    /**
     * Send message via HTTP
     */
    async send(data, destination, options = {}) {
        const startTime = Date.now();

        try {
            // Check circuit breaker
            if (this.isCircuitOpen(destination)) {
                throw new Error(`Circuit breaker open for ${destination}`);
            }

            // Get HTTP client for destination
            const client = this.getClient(destination);

            // Prepare request
            const requestConfig = this.prepareRequest(data, destination, options);

            // Send HTTP request with retries
            const response = await this.sendWithRetry(client, requestConfig);

            // Update metrics
            const latency = Date.now() - startTime;
            this.updateMetrics('success', latency);
            this.recordCircuitBreakerSuccess(destination);

            return {
                success: true,
                data: response.data,
                status: response.status,
                latency,
                transport: 'http'
            };

        } catch (error) {
            const latency = Date.now() - startTime;
            this.updateMetrics('failed', latency);
            this.recordCircuitBreakerFailure(destination);

            logger.error('HTTP send failed', { error: error.message, destination });
            throw error;
        }
    }

    /**
     * Get or create HTTP client for destination
     */
    getClient(destination) {
        if (this.clients.has(destination)) {
            return this.clients.get(destination);
        }

        // Create new axios instance with connection pooling
        const baseURL = this.getBaseURL(destination);

        const client = axios.create({
            baseURL,
            timeout: this.config.timeout,
            maxRedirects: 3,
            validateStatus: (status) => status < 500, // Don't throw on 4xx errors
            headers: this.config.default_headers,
            // Connection pooling
            httpAgent: new (require('http').Agent)({
                keepAlive: true,
                maxSockets: 10,
                maxFreeSockets: 10,
                timeout: 60000,
                freeSocketTimeout: 30000
            }),
            httpsAgent: new (require('https').Agent)({
                keepAlive: true,
                maxSockets: 10,
                maxFreeSockets: 10,
                timeout: 60000,
                freeSocketTimeout: 30000
            })
        });

        // Add request/response interceptors
        this.setupInterceptors(client, destination);

        this.clients.set(destination, client);
        return client;
    }

    /**
     * Setup axios interceptors
     */
    setupInterceptors(client, destination) {
        // Request interceptor
        client.interceptors.request.use(
            (config) => {
                this.status.active_connections++;
                logger.debug('HTTP request started', {
                    destination,
                    method: config.method,
                    url: config.url
                });
                return config;
            },
            (error) => {
                this.status.active_connections--;
                return Promise.reject(error);
            }
        );

        // Response interceptor
        client.interceptors.response.use(
            (response) => {
                this.status.active_connections--;
                this.status.total_requests++;
                return response;
            },
            (error) => {
                this.status.active_connections--;
                this.status.total_requests++;
                this.status.failed_requests++;
                return Promise.reject(error);
            }
        );
    }

    /**
     * Get base URL for destination service
     */
    getBaseURL(destination) {
        // Simple service discovery - in production this would query Central Hub
        return `http://${destination}:${this.config.base_port}`;
    }

    /**
     * Prepare HTTP request configuration
     */
    prepareRequest(data, destination, options) {
        const endpoint = options.endpoint || '/api/input';
        const method = options.method || 'POST';

        const config = {
            method,
            url: endpoint,
            headers: {
                'X-Source-Service': options.metadata?.source_service || 'unknown',
                'X-Destination-Service': destination,
                'X-Correlation-ID': options.correlationId || this.generateCorrelationId(),
                'X-Message-Type': options.messageType || this.getMessageType(data),
                ...options.headers
            },
            timeout: options.timeout || this.config.timeout
        };

        // Handle different data types
        if (Buffer.isBuffer(data)) {
            config.data = data;
            config.headers['Content-Type'] = 'application/octet-stream';
        } else if (options.isBinary) {
            config.data = data;
            config.headers['Content-Type'] = 'application/octet-stream';
            config.headers['X-Protocol'] = 'suho-binary';
        } else {
            config.data = data;
            config.headers['Content-Type'] = 'application/json';
        }

        return config;
    }

    /**
     * Send HTTP request with retry mechanism
     */
    async sendWithRetry(client, requestConfig) {
        let lastError;

        for (let attempt = 1; attempt <= this.config.max_retries; attempt++) {
            try {
                const response = await client.request(requestConfig);

                // Check if response indicates success
                if (response.status >= 200 && response.status < 300) {
                    return response;
                }

                // Handle non-2xx responses
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);

            } catch (error) {
                lastError = error;

                logger.warn('HTTP request attempt failed', {
                    attempt,
                    max_retries: this.config.max_retries,
                    error: error.message,
                    url: requestConfig.url
                });

                // Don't retry on 4xx errors (client errors)
                if (error.response && error.response.status >= 400 && error.response.status < 500) {
                    break;
                }

                // Wait before retry (exponential backoff)
                if (attempt < this.config.max_retries) {
                    const delay = this.config.retry_delay * Math.pow(2, attempt - 1);
                    await this.sleep(delay);
                }
            }
        }

        throw lastError;
    }

    /**
     * Receive messages (webhook/polling)
     */
    async receive(source, handler) {
        // For HTTP, we typically set up webhook endpoints or polling
        logger.info('HTTP receive not implemented - use webhook endpoints instead');

        // Return a mock subscription object for consistency
        return {
            type: 'http',
            source,
            unsubscribe: () => {
                logger.info('HTTP subscription unsubscribed', { source });
            }
        };
    }

    /**
     * Circuit breaker implementation
     */
    isCircuitOpen(destination) {
        const breaker = this.circuit_breakers.get(destination);
        if (!breaker) return false;

        if (breaker.state === 'OPEN') {
            // Check if reset timeout has passed
            if (Date.now() - breaker.lastFailureTime > this.config.circuit_breaker.reset_timeout) {
                breaker.state = 'HALF_OPEN';
                breaker.consecutiveFailures = 0;
                logger.info('Circuit breaker reset to HALF_OPEN', { destination });
                return false;
            }
            return true;
        }

        return false;
    }

    /**
     * Record circuit breaker success
     */
    recordCircuitBreakerSuccess(destination) {
        const breaker = this.circuit_breakers.get(destination);
        if (breaker) {
            breaker.consecutiveFailures = 0;
            if (breaker.state === 'HALF_OPEN') {
                breaker.state = 'CLOSED';
                logger.info('Circuit breaker closed', { destination });
            }
        }
    }

    /**
     * Record circuit breaker failure
     */
    recordCircuitBreakerFailure(destination) {
        let breaker = this.circuit_breakers.get(destination);
        if (!breaker) {
            breaker = {
                state: 'CLOSED',
                consecutiveFailures: 0,
                lastFailureTime: 0
            };
            this.circuit_breakers.set(destination, breaker);
        }

        breaker.consecutiveFailures++;
        breaker.lastFailureTime = Date.now();

        if (breaker.consecutiveFailures >= this.config.circuit_breaker.failure_threshold) {
            breaker.state = 'OPEN';
            this.metrics.circuit_breaker_trips++;
            logger.warn('Circuit breaker opened', {
                destination,
                consecutive_failures: breaker.consecutiveFailures
            });
        }
    }

    /**
     * Get message type from data
     */
    getMessageType(data) {
        if (data && typeof data === 'object') {
            if (data.message_type) return data.message_type;
            if (data.type) return data.type;
            if (data.constructor?.name) return data.constructor.name;
        }
        return 'unknown';
    }

    /**
     * Update metrics
     */
    updateMetrics(result, latency) {
        if (result === 'success') {
            this.metrics.requests_sent++;
            this.metrics.avg_latency = (this.metrics.avg_latency * 0.9) + (latency * 0.1);
        } else {
            this.metrics.requests_failed++;
        }
    }

    /**
     * Sleep utility
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Generate correlation ID
     */
    generateCorrelationId() {
        return `http_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Health check
     */
    async healthCheck() {
        return {
            status: 'healthy',
            active_connections: this.status.active_connections,
            total_requests: this.status.total_requests,
            failed_requests: this.status.failed_requests,
            circuit_breakers: Array.from(this.circuit_breakers.entries()).map(([dest, breaker]) => ({
                destination: dest,
                state: breaker.state,
                consecutive_failures: breaker.consecutiveFailures
            })),
            metrics: this.metrics
        };
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        logger.info('Shutting down HTTP adapter');

        try {
            // Close all HTTP clients
            for (const client of this.clients.values()) {
                // Axios doesn't have explicit close, but we can clear the clients
                client.defaults.timeout = 1; // Force quick timeout for pending requests
            }

            this.clients.clear();
            this.circuit_breakers.clear();

            logger.info('HTTP adapter shutdown complete');

        } catch (error) {
            logger.error('Error during HTTP adapter shutdown', { error });
        }
    }
}

module.exports = HTTPAdapter;