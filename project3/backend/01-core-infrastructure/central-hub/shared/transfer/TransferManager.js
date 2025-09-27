/**
 * Universal Transfer Manager - Shared across all services
 *
 * Provides unified interface for 3 transport methods:
 * 1. NATS+Kafka Hybrid (High Volume + Mission Critical)
 * 2. gRPC (Medium Volume + Important)
 * 3. HTTP REST (Low Volume + Standard)
 *
 * Usage:
 * const transfer = new TransferManager(config);
 * await transfer.send(data, 'target-service', 'nats-kafka');
 */

const EventEmitter = require('events');
const logger = require('../logging/logger');

class TransferManager extends EventEmitter {
    constructor(config = {}) {
        super();

        this.config = {
            service_name: config.service_name || 'unknown-service',
            auto_method_selection: config.auto_method_selection !== false,
            fallback_enabled: config.fallback_enabled !== false,
            max_retries: config.max_retries || 3,
            timeout_ms: config.timeout_ms || 30000,
            ...config
        };

        // Transport adapters
        this.adapters = {
            'nats-kafka': null,
            'grpc': null,
            'http': null
        };

        // Performance metrics
        this.metrics = {
            'nats-kafka': { sent: 0, failed: 0, avgLatency: 0 },
            'grpc': { sent: 0, failed: 0, avgLatency: 0 },
            'http': { sent: 0, failed: 0, avgLatency: 0 }
        };

        // Method selection rules
        this.methodRules = {
            // High volume data types → NATS+Kafka
            high_volume: ['price_stream', 'trading_command', 'execution_confirm', 'tick_data'],
            // Medium volume → gRPC
            medium_volume: ['trading_signal', 'ml_prediction', 'analytics_output'],
            // Low volume → HTTP
            low_volume: ['account_profile', 'heartbeat', 'notification', 'config_update']
        };

        this.initializeAdapters();
    }

    /**
     * Initialize transport adapters
     */
    async initializeAdapters() {
        try {
            // Lazy load adapters to avoid circular dependencies
            const NATSKafkaAdapter = require('./adapters/NATSKafkaAdapter');
            const GRPCAdapter = require('./adapters/GRPCAdapter');
            const HTTPAdapter = require('./adapters/HTTPAdapter');

            this.adapters['nats-kafka'] = new NATSKafkaAdapter(this.config.natsKafka);
            this.adapters['grpc'] = new GRPCAdapter(this.config.grpc);
            this.adapters['http'] = new HTTPAdapter(this.config.http);

            // Initialize each adapter
            await Promise.all([
                this.adapters['nats-kafka'].initialize(),
                this.adapters['grpc'].initialize(),
                this.adapters['http'].initialize()
            ]);

            logger.info('TransferManager initialized', {
                service: this.config.service_name,
                adapters: Object.keys(this.adapters)
            });

        } catch (error) {
            logger.error('Failed to initialize TransferManager', { error });
            throw error;
        }
    }

    /**
     * Universal send method
     * @param {Object} data - Data to send (binary or protobuf)
     * @param {string} destination - Target service name
     * @param {string} method - Transport method ('auto', 'nats-kafka', 'grpc', 'http')
     * @param {Object} options - Additional options
     */
    async send(data, destination, method = 'auto', options = {}) {
        const startTime = Date.now();

        try {
            // Auto-select method if not specified
            if (method === 'auto') {
                method = this.selectMethod(data, destination, options);
            }

            // Validate method
            if (!this.adapters[method]) {
                throw new Error(`Unsupported transport method: ${method}`);
            }

            // Add transfer metadata
            const transferMetadata = {
                source_service: this.config.service_name,
                destination_service: destination,
                transport_method: method,
                timestamp: Date.now(),
                correlation_id: options.correlationId || this.generateCorrelationId(),
                ...options.metadata
            };

            // Send via selected method
            const result = await this.adapters[method].send(data, destination, {
                ...options,
                metadata: transferMetadata
            });

            // Update metrics
            const latency = Date.now() - startTime;
            this.updateMetrics(method, 'success', latency);

            logger.debug('Transfer successful', {
                method,
                destination,
                latency,
                dataSize: this.getDataSize(data)
            });

            return {
                success: true,
                method,
                latency,
                result
            };

        } catch (error) {
            // Update metrics
            const latency = Date.now() - startTime;
            this.updateMetrics(method, 'failed', latency);

            // Try fallback if enabled
            if (this.config.fallback_enabled && method !== 'http') {
                logger.warn('Primary transport failed, trying fallback', {
                    primary_method: method,
                    error: error.message
                });

                try {
                    return await this.send(data, destination, 'http', {
                        ...options,
                        is_fallback: true
                    });
                } catch (fallbackError) {
                    logger.error('Fallback transport also failed', {
                        fallback_error: fallbackError.message
                    });
                    throw fallbackError;
                }
            }

            logger.error('Transfer failed', {
                method,
                destination,
                error: error.message,
                latency
            });

            throw error;
        }
    }

    /**
     * Auto-select best transport method
     * @param {Object} data - Data to send
     * @param {string} destination - Target service
     * @param {Object} options - Send options
     * @returns {string} Selected method
     */
    selectMethod(data, destination, options) {
        // Check explicit priority
        if (options.priority) {
            switch (options.priority) {
                case 'high': return 'nats-kafka';
                case 'medium': return 'grpc';
                case 'low': return 'http';
            }
        }

        // Check data type
        const dataType = this.getDataType(data);

        // High volume data → NATS+Kafka
        if (this.methodRules.high_volume.includes(dataType)) {
            return 'nats-kafka';
        }

        // Medium volume data → gRPC
        if (this.methodRules.medium_volume.includes(dataType)) {
            return 'grpc';
        }

        // Low volume data → HTTP
        if (this.methodRules.low_volume.includes(dataType)) {
            return 'http';
        }

        // Default based on data size
        const dataSize = this.getDataSize(data);
        if (dataSize > 10240) { // > 10KB
            return 'nats-kafka';
        } else if (dataSize > 1024) { // > 1KB
            return 'grpc';
        } else {
            return 'http';
        }
    }

    /**
     * Get data type from message
     * @param {Object} data - Data object
     * @returns {string} Data type
     */
    getDataType(data) {
        // Check protobuf message type
        if (data.constructor && data.constructor.name) {
            const className = data.constructor.name.toLowerCase();
            if (className.includes('pricestream')) return 'price_stream';
            if (className.includes('tradingcommand')) return 'trading_command';
            if (className.includes('accountprofile')) return 'account_profile';
            if (className.includes('tradingsignal')) return 'trading_signal';
        }

        // Check message type property
        if (data.type) {
            return data.type;
        }

        // Check message_type property
        if (data.message_type) {
            return data.message_type;
        }

        // Fallback
        return 'unknown';
    }

    /**
     * Get data size in bytes
     * @param {Object} data - Data object
     * @returns {number} Size in bytes
     */
    getDataSize(data) {
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

    /**
     * Update performance metrics
     * @param {string} method - Transport method
     * @param {string} result - 'success' or 'failed'
     * @param {number} latency - Latency in ms
     */
    updateMetrics(method, result, latency) {
        if (!this.metrics[method]) return;

        if (result === 'success') {
            this.metrics[method].sent++;
            // Exponential moving average
            this.metrics[method].avgLatency =
                (this.metrics[method].avgLatency * 0.9) + (latency * 0.1);
        } else {
            this.metrics[method].failed++;
        }
    }

    /**
     * Receive message (for services that need to listen)
     * @param {string} method - Transport method to listen on
     * @param {string} source - Source service pattern
     * @param {Function} handler - Message handler
     */
    async receive(method, source, handler) {
        if (!this.adapters[method]) {
            throw new Error(`Unsupported transport method: ${method}`);
        }

        return await this.adapters[method].receive(source, handler);
    }

    /**
     * Generate correlation ID
     * @returns {string} Correlation ID
     */
    generateCorrelationId() {
        return `transfer_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get performance metrics
     * @returns {Object} Metrics
     */
    getMetrics() {
        return {
            service: this.config.service_name,
            metrics: this.metrics,
            uptime: Date.now() - this.startTime
        };
    }

    /**
     * Health check
     * @returns {Object} Health status
     */
    async healthCheck() {
        const health = {
            overall: 'healthy',
            adapters: {},
            timestamp: Date.now()
        };

        for (const [method, adapter] of Object.entries(this.adapters)) {
            try {
                health.adapters[method] = await adapter.healthCheck();
            } catch (error) {
                health.adapters[method] = {
                    status: 'unhealthy',
                    error: error.message
                };
                health.overall = 'degraded';
            }
        }

        return health;
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        logger.info('Shutting down TransferManager', {
            service: this.config.service_name
        });

        try {
            await Promise.all(
                Object.values(this.adapters).map(adapter => adapter.shutdown())
            );
            logger.info('TransferManager shutdown complete');
        } catch (error) {
            logger.error('Error during TransferManager shutdown', { error });
        }
    }
}

module.exports = TransferManager;