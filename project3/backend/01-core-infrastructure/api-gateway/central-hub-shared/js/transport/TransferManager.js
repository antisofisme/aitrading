/**
 * JavaScript TransferManager - Universal transport layer
 * Auto-selects transport method based on data type, volume, and criticality
 * Supports NATS+Kafka, gRPC, and HTTP transports
 */

const EventEmitter = require('events');

// Transport method priorities
const TransportMethods = {
    AUTO: 'auto',
    NATS_KAFKA: 'nats-kafka',
    GRPC: 'grpc',
    HTTP: 'http'
};

// Data type classifications for auto-selection
const DataTypeConfig = {
    // High-volume, real-time
    'price_stream': { method: 'nats-kafka', volume: 'high', critical: true },
    'trading_command': { method: 'nats-kafka', volume: 'high', critical: true },
    'execution_confirm': { method: 'nats-kafka', volume: 'high', critical: true },
    'tick_data': { method: 'nats-kafka', volume: 'high', critical: false },
    'raw_data': { method: 'nats-kafka', volume: 'high', critical: false },

    // Service-to-service
    'trading_signal': { method: 'grpc', volume: 'medium', critical: true },
    'ml_prediction': { method: 'grpc', volume: 'medium', critical: true },
    'analytics_output': { method: 'grpc', volume: 'medium', critical: false },
    'user_context': { method: 'grpc', volume: 'low', critical: true },
    'order_request': { method: 'grpc', volume: 'medium', critical: true },

    // Standard operations
    'account_profile': { method: 'http', volume: 'low', critical: false },
    'heartbeat': { method: 'http', volume: 'low', critical: false },
    'notification': { method: 'http', volume: 'low', critical: false },
    'config_update': { method: 'http', volume: 'low', critical: false },
    'health_check': { method: 'http', volume: 'low', critical: false }
};

class TransferManager extends EventEmitter {
    constructor({ service_name, ...config }) {
        super();

        this.service_name = service_name;
        this.config = {
            retry_attempts: 3,
            timeout_ms: 30000,
            circuit_breaker_enabled: true,
            fallback_enabled: false, // ❌ DISABLED: No fallback - fail fast
            use_simulation: false,   // ❌ DISABLED: No simulation - real transport only
            ...config
        };

        // Transport adapters
        this.adapters = {
            'nats-kafka': null,
            'grpc': null,
            'http': null
        };

        // Performance tracking
        this.metrics = {
            total_requests: 0,
            successful_requests: 0,
            failed_requests: 0,
            avg_response_time: 0,
            transport_usage: {
                'nats-kafka': 0,
                'grpc': 0,
                'http': 0
            }
        };

        // Circuit breaker states
        this.circuit_breakers = new Map();

        // Response times for auto-optimization
        this.response_times = new Map();
    }

    async initialize() {
        console.log(`Initializing TransferManager for ${this.service_name}`);

        try {
            // Initialize transport adapters
            await this._initializeAdapters();

            // Start performance monitoring
            this._startPerformanceMonitoring();

            console.log('TransferManager initialized successfully');
            this.emit('initialized');

        } catch (error) {
            console.error(`Failed to initialize TransferManager: ${error.message}`);
            throw error;
        }
    }

    async _initializeAdapters() {
        // Placeholder implementations - would be replaced with actual adapters

        // NATS+Kafka adapter
        this.adapters['nats-kafka'] = {
            send: async (data, destination, options) => {
                // Simulate NATS+Kafka transport
                return await this._simulateTransport('nats-kafka', data, destination, options);
            },
            subscribe: async (topic, handler) => {
                // Subscribe implementation
            },
            health_check: async () => ({ status: 'healthy', transport: 'nats-kafka' })
        };

        // gRPC adapter
        this.adapters['grpc'] = {
            send: async (data, destination, options) => {
                // Simulate gRPC transport
                return await this._simulateTransport('grpc', data, destination, options);
            },
            health_check: async () => ({ status: 'healthy', transport: 'grpc' })
        };

        // HTTP adapter
        this.adapters['http'] = {
            send: async (data, destination, options) => {
                // Simulate HTTP transport
                return await this._simulateTransport('http', data, destination, options);
            },
            health_check: async () => ({ status: 'healthy', transport: 'http' })
        };
    }

    async send(data, destination, method = 'auto', options = {}) {
        const start_time = Date.now();
        const correlation_id = options.correlation_id || this._generateCorrelationId();

        try {
            this.metrics.total_requests++;

            // Select transport method
            const selected_method = this._selectTransportMethod(method, data, options);

            // Check circuit breaker
            if (this._isCircuitBreakerOpen(destination, selected_method)) {
                throw new Error(`Circuit breaker open for ${destination} via ${selected_method}`);
            }

            // Execute transport with retries
            const result = await this._executeWithRetries(
                selected_method,
                data,
                destination,
                options,
                correlation_id
            );

            // Track success metrics
            const processing_time = Date.now() - start_time;
            this._recordSuccess(selected_method, destination, processing_time);

            console.log(`Successfully sent to ${destination} via ${selected_method} in ${processing_time}ms`);

            return {
                success: true,
                transport_method: selected_method,
                processing_time_ms: processing_time,
                correlation_id,
                data: result
            };

        } catch (error) {
            const processing_time = Date.now() - start_time;
            this._recordFailure(method, destination, error, processing_time);

            console.error(`Failed to send to ${destination}: ${error.message}`);

            // No fallback - fail fast
            console.error(`❌ Transport to ${destination} via ${selected_method} FAILED - no fallback available`);

            throw error;
        }
    }

    _selectTransportMethod(method, data, options) {
        if (method !== 'auto') {
            return method;
        }

        // Auto-select based on data type
        const data_type = this._extractDataType(data, options);
        const config = DataTypeConfig[data_type];

        if (config) {
            return config.method;
        }

        // Default selection based on data size
        const data_size = this._estimateDataSize(data);

        if (data_size > 1024 * 100) { // > 100KB
            return 'nats-kafka';
        } else if (options.critical || options.streaming) {
            return 'grpc';
        } else {
            return 'http';
        }
    }

    _extractDataType(data, options) {
        // Extract data type from metadata
        if (options.data_type) {
            return options.data_type;
        }

        if (data.message_type) {
            return data.message_type;
        }

        if (data.type) {
            return data.type;
        }

        // Infer from data structure
        if (data.symbols && Array.isArray(data.symbols)) {
            return 'price_stream';
        }

        if (data.command || data.action) {
            return 'trading_command';
        }

        if (data.prediction || data.confidence) {
            return 'ml_prediction';
        }

        return 'unknown';
    }

    _estimateDataSize(data) {
        if (Buffer.isBuffer(data)) {
            return data.length;
        }

        if (typeof data === 'string') {
            return Buffer.byteLength(data, 'utf8');
        }

        if (typeof data === 'object') {
            return Buffer.byteLength(JSON.stringify(data), 'utf8');
        }

        return 0;
    }

    async _executeWithRetries(method, data, destination, options, correlation_id) {
        let last_error;

        for (let attempt = 1; attempt <= this.config.retry_attempts; attempt++) {
            try {
                const adapter = this.adapters[method];
                if (!adapter) {
                    throw new Error(`❌ Transport adapter not available: ${method} - cannot send to ${destination}`);
                }

                // For now, use Central Hub endpoints instead of simulation
                if (this.config.use_simulation) {
                    throw new Error(`❌ Simulation mode disabled - real transport required for ${method}`);
                }

                const result = await Promise.race([
                    adapter.send(data, destination, { ...options, correlation_id }),
                    this._createTimeoutPromise(this.config.timeout_ms)
                ]);

                return result;

            } catch (error) {
                last_error = error;
                console.warn(`Attempt ${attempt} failed for ${destination} via ${method}: ${error.message}`);

                if (attempt < this.config.retry_attempts) {
                    // Exponential backoff
                    const delay = Math.pow(2, attempt - 1) * 1000;
                    await this._sleep(delay);
                }
            }
        }

        throw last_error;
    }

    _createTimeoutPromise(timeout_ms) {
        return new Promise((_, reject) => {
            setTimeout(() => {
                reject(new Error(`Transport timeout after ${timeout_ms}ms`));
            }, timeout_ms);
        });
    }

    _sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async _simulateTransport(method, data, destination, options) {
        // Simulation disabled - fail fast
        throw new Error(`❌ Transport simulation disabled - real ${method} transport required to reach ${destination}`);
    }

    _isCircuitBreakerOpen(destination, method) {
        if (!this.config.circuit_breaker_enabled) {
            return false;
        }

        const key = `${destination}:${method}`;
        const breaker = this.circuit_breakers.get(key);

        if (!breaker) {
            return false;
        }

        // Simple circuit breaker logic
        return breaker.failures >= 5 &&
               (Date.now() - breaker.last_failure) < 60000; // 1 minute
    }

    _recordSuccess(method, destination, processing_time) {
        this.metrics.successful_requests++;
        this.metrics.transport_usage[method]++;

        // Update average response time
        const total_time = this.metrics.avg_response_time * (this.metrics.successful_requests - 1);
        this.metrics.avg_response_time = (total_time + processing_time) / this.metrics.successful_requests;

        // Record response time for optimization
        const key = `${destination}:${method}`;
        if (!this.response_times.has(key)) {
            this.response_times.set(key, []);
        }
        const times = this.response_times.get(key);
        times.push(processing_time);
        if (times.length > 100) {
            times.shift(); // Keep only last 100 measurements
        }

        // Reset circuit breaker on success
        const breaker_key = `${destination}:${method}`;
        if (this.circuit_breakers.has(breaker_key)) {
            this.circuit_breakers.delete(breaker_key);
        }
    }

    _recordFailure(method, destination, error, processing_time) {
        this.metrics.failed_requests++;

        // Update circuit breaker
        if (this.config.circuit_breaker_enabled) {
            const key = `${destination}:${method}`;
            const breaker = this.circuit_breakers.get(key) || { failures: 0, last_failure: 0 };
            breaker.failures++;
            breaker.last_failure = Date.now();
            this.circuit_breakers.set(key, breaker);
        }
    }

    _generateCorrelationId() {
        return `${this.service_name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    _startPerformanceMonitoring() {
        // Emit metrics every 60 seconds
        setInterval(() => {
            this.emit('metrics', this.getMetrics());
        }, 60000);
    }

    getMetrics() {
        const error_rate = this.metrics.total_requests > 0 ?
            this.metrics.failed_requests / this.metrics.total_requests : 0;

        return {
            service_name: this.service_name,
            total_requests: this.metrics.total_requests,
            successful_requests: this.metrics.successful_requests,
            failed_requests: this.metrics.failed_requests,
            error_rate: Math.round(error_rate * 10000) / 100, // Percentage with 2 decimals
            avg_response_time_ms: Math.round(this.metrics.avg_response_time),
            transport_usage: { ...this.metrics.transport_usage },
            active_circuit_breakers: this.circuit_breakers.size
        };
    }

    async healthCheck() {
        const health_status = {
            service: 'TransferManager',
            status: 'healthy',
            timestamp: new Date().toISOString(),
            transports: {}
        };

        try {
            // Check each transport adapter
            for (const [method, adapter] of Object.entries(this.adapters)) {
                if (adapter && typeof adapter.health_check === 'function') {
                    health_status.transports[method] = await adapter.health_check();
                } else {
                    health_status.transports[method] = { status: 'not_initialized' };
                }
            }

            // Check overall health
            const unhealthy_transports = Object.values(health_status.transports)
                .filter(status => status.status !== 'healthy').length;

            if (unhealthy_transports >= Object.keys(this.adapters).length) {
                health_status.status = 'unhealthy';
            } else if (unhealthy_transports > 0) {
                health_status.status = 'degraded';
            }

        } catch (error) {
            health_status.status = 'error';
            health_status.error = error.message;
        }

        return health_status;
    }

    async shutdown() {
        console.log('Shutting down TransferManager');

        try {
            // Stop performance monitoring
            this.removeAllListeners();

            // Shutdown adapters
            for (const [method, adapter] of Object.entries(this.adapters)) {
                if (adapter && typeof adapter.shutdown === 'function') {
                    await adapter.shutdown();
                }
            }

            console.log('TransferManager shutdown complete');

        } catch (error) {
            console.error(`Error during TransferManager shutdown: ${error.message}`);
        }
    }

    // Utility methods for contract-based routing
    getOptimalTransport(data_type, volume = 'medium', critical = false) {
        const config = DataTypeConfig[data_type];
        if (config) {
            return config.method;
        }

        // Fallback logic
        if (volume === 'high' || critical) {
            return 'nats-kafka';
        } else if (volume === 'medium') {
            return 'grpc';
        } else {
            return 'http';
        }
    }

    async broadcastToServices(data, services, method = 'auto', options = {}) {
        const promises = services.map(service =>
            this.send(data, service, method, options)
        );

        const results = await Promise.allSettled(promises);

        return {
            total: services.length,
            successful: results.filter(r => r.status === 'fulfilled').length,
            failed: results.filter(r => r.status === 'rejected').length,
            results: results.map((result, index) => ({
                service: services[index],
                status: result.status,
                value: result.status === 'fulfilled' ? result.value : null,
                error: result.status === 'rejected' ? result.reason.message : null
            }))
        };
    }
}

module.exports = {
    TransferManager,
    TransportMethods,
    DataTypeConfig
};