/**
 * Central Hub Shared Components - Main Export
 * JavaScript wrappers untuk Python shared components
 * Compatible dengan SERVICE_ARCHITECTURE.md specifications
 */

// Core utilities
const { BaseService, ServiceConfig, StandardResponse } = require('./js/utils/BaseService');
const { ErrorDNA, ErrorDNAAnalyzer, ErrorPattern, ErrorOccurrence, ErrorAnalysis, ErrorSeverity, ErrorCategory } = require('./js/utils/ErrorDNA');

// Transport layer
const { TransferManager, TransportMethods, DataTypeConfig } = require('./js/transport/TransferManager');

// Logging
const { StructuredLogger, createServiceLogger, LogLevel } = require('./js/logging/Logger');

// Transport adapters
const NATSKafkaAdapter = require('./js/adapters/NATSKafkaAdapter');

// Legacy/existing components (Python-based, available for reference)
const suhoBinary = require('./suho-binary');

// Create convenience wrappers for common usage patterns
class ServiceTemplate extends BaseService {
    constructor(serviceName, config = {}) {
        const serviceConfig = new ServiceConfig({
            service_name: serviceName,
            version: config.version || '1.0.0',
            port: config.port || 3000,
            ...config
        });

        super(serviceConfig);

        // Initialize shared components
        this.transfer = new TransferManager({
            service_name: serviceName,
            ...config.transfer
        });

        this.errorDNA = new ErrorDNA(serviceName);

        // Enhanced logger with correlation support
        this.logger = createServiceLogger(serviceName, config.logging);
    }

    async initialize() {
        await super.start();

        // Initialize transfer manager
        if (this.transfer) {
            await this.transfer.initialize();
        }

        this.logger.info(`${this.service_name} initialized with shared components`);
    }

    async processInput(inputData, sourceService, inputType) {
        return await this.processWithTracing(
            `process_${inputType}`,
            async () => {
                // Default implementation - override in child classes
                return await this.handleInput(inputData, sourceService, inputType);
            },
            inputData.metadata?.correlation_id
        );
    }

    async handleInput(inputData, sourceService, inputType) {
        // Abstract method - implement in child classes
        throw new Error('handleInput must be implemented in child class');
    }

    async sendOutput(data, targetService, options = {}) {
        if (!this.transfer) {
            throw new Error('TransferManager not initialized');
        }

        return await this.transfer.send(data, targetService, options.method || 'auto', {
            correlation_id: options.correlation_id || this.generateCorrelationId(),
            source: this.service_name,
            ...options
        });
    }

    async analyzeError(error, context = {}) {
        if (!this.errorDNA) {
            this.logger.error(`Error occurred: ${error.message}`, context);
            return null;
        }

        return await this.errorDNA.analyzeError({
            error_message: error.message,
            stack_trace: error.stack,
            error_type: error.constructor.name,
            context,
            correlation_id: context.correlation_id
        });
    }
}

// Transport adapters collection
const adapters = {
    NATSKafkaAdapter,
    // Future adapters:
    // GRPCAdapter,
    // HTTPAdapter
};

// Utility functions
function createStandardService(serviceName, config = {}) {
    return new ServiceTemplate(serviceName, config);
}

function getTransportMethod(dataType, volume = 'medium', critical = false) {
    const config = DataTypeConfig[dataType];
    if (config) {
        return config.method;
    }

    // Fallback logic
    if (volume === 'high' || critical) {
        return TransportMethods.NATS_KAFKA;
    } else if (volume === 'medium') {
        return TransportMethods.GRPC;
    } else {
        return TransportMethods.HTTP;
    }
}

// Performance monitoring utilities
class PerformanceTracker {
    constructor(serviceName) {
        this.serviceName = serviceName;
        this.metrics = {
            requests: 0,
            responses: 0,
            errors: 0,
            totalTime: 0,
            avgResponseTime: 0
        };
    }

    trackRequest(processingTime, success = true) {
        this.metrics.requests++;
        this.metrics.totalTime += processingTime;
        this.metrics.avgResponseTime = this.metrics.totalTime / this.metrics.requests;

        if (success) {
            this.metrics.responses++;
        } else {
            this.metrics.errors++;
        }
    }

    getMetrics() {
        return {
            ...this.metrics,
            errorRate: this.metrics.requests > 0 ? this.metrics.errors / this.metrics.requests : 0,
            successRate: this.metrics.requests > 0 ? this.metrics.responses / this.metrics.requests : 0
        };
    }
}

// Circuit breaker utility
class CircuitBreaker {
    constructor(options = {}) {
        this.failureThreshold = options.failureThreshold || 5;
        this.timeout = options.timeout || 60000; // 1 minute
        this.failures = 0;
        this.lastFailureTime = null;
        this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
    }

    async call(operation) {
        if (this.state === 'OPEN') {
            if (Date.now() - this.lastFailureTime >= this.timeout) {
                this.state = 'HALF_OPEN';
            } else {
                throw new Error('Circuit breaker is OPEN');
            }
        }

        try {
            const result = await operation();
            this.onSuccess();
            return result;
        } catch (error) {
            this.onFailure();
            throw error;
        }
    }

    onSuccess() {
        this.failures = 0;
        this.state = 'CLOSED';
    }

    onFailure() {
        this.failures++;
        this.lastFailureTime = Date.now();

        if (this.failures >= this.failureThreshold) {
            this.state = 'OPEN';
        }
    }

    getState() {
        return {
            state: this.state,
            failures: this.failures,
            lastFailureTime: this.lastFailureTime
        };
    }
}

// Configuration manager
class ConfigManager {
    constructor(serviceName, environment = 'development') {
        this.serviceName = serviceName;
        this.environment = environment;
        this.config = new Map();
        this.watchers = new Map();
    }

    get(key, defaultValue = null) {
        return this.config.get(key) || process.env[key] || defaultValue;
    }

    set(key, value) {
        const oldValue = this.config.get(key);
        this.config.set(key, value);

        // Notify watchers
        const watchers = this.watchers.get(key) || [];
        watchers.forEach(callback => callback(value, oldValue));
    }

    watch(key, callback) {
        if (!this.watchers.has(key)) {
            this.watchers.set(key, []);
        }
        this.watchers.get(key).push(callback);
    }

    loadFromEnv(prefix = '') {
        const envPrefix = prefix || `${this.serviceName.toUpperCase()}_`;

        for (const [key, value] of Object.entries(process.env)) {
            if (key.startsWith(envPrefix)) {
                const configKey = key.substring(envPrefix.length).toLowerCase();
                this.config.set(configKey, value);
            }
        }
    }
}

// Main exports
module.exports = {
    // Core classes
    BaseService,
    ServiceTemplate,
    ServiceConfig,
    StandardResponse,

    // Error handling
    ErrorDNA,
    ErrorDNAAnalyzer,
    ErrorPattern,
    ErrorOccurrence,
    ErrorAnalysis,
    ErrorSeverity,
    ErrorCategory,

    // Transport
    TransferManager,
    TransportMethods,
    DataTypeConfig,

    // Logging
    StructuredLogger,
    createServiceLogger,
    LogLevel,

    // Adapters
    adapters,
    NATSKafkaAdapter,

    // Utilities
    PerformanceTracker,
    CircuitBreaker,
    ConfigManager,

    // Factory functions
    createStandardService,
    getTransportMethod,

    // Legacy components
    suhoBinary,

    // Constants
    TRANSPORT_METHODS: TransportMethods,
    LOG_LEVELS: LogLevel,
    ERROR_SEVERITIES: ErrorSeverity,
    ERROR_CATEGORIES: ErrorCategory
};

// Export individual components for ES6 imports
module.exports.default = module.exports;