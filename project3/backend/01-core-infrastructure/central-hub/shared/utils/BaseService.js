/**
 * Base Service - JavaScript Implementation
 *
 * Standard base class untuk semua backend services dengan patterns:
 * - Database access management
 * - Caching strategies
 * - Configuration management
 * - Request tracing
 * - Circuit breaker protection
 * - Error handling with ErrorDNA
 * - Performance monitoring
 */

const ErrorDNA = require('./ErrorDNA');

/**
 * Service Configuration Interface
 */
class ServiceConfig {
    constructor(options = {}) {
        this.service_name = options.service_name || 'unknown-service';
        this.version = options.version || '1.0.0';
        this.port = options.port || 3000;
        this.environment = options.environment || 'development';
        this.enable_tracing = options.enable_tracing !== false;
        this.enable_circuit_breaker = options.enable_circuit_breaker !== false;
        this.health_check_interval = options.health_check_interval || 30000;
        this.cache_ttl_default = options.cache_ttl_default || 300000;
        this.max_connections = options.max_connections || 100;
        this.enable_metrics = options.enable_metrics !== false;
        this.log_level = options.log_level || 'info';

        // Database configuration
        this.database = options.database || {};

        // Cache configuration
        this.cache = options.cache || {
            type: 'memory',
            ttl: this.cache_ttl_default
        };

        // Transfer configuration
        this.transfer = options.transfer || {};
    }
}

/**
 * Standard Response Format
 */
class StandardResponse {
    static success(data, metadata = {}) {
        return {
            success: true,
            data,
            metadata: {
                timestamp: new Date().toISOString(),
                ...metadata
            }
        };
    }

    static error(error, metadata = {}) {
        return {
            success: false,
            error: {
                message: error.message || error,
                type: error.name || 'Error',
                code: error.code,
                statusCode: error.statusCode || 500
            },
            metadata: {
                timestamp: new Date().toISOString(),
                ...metadata
            }
        };
    }

    static paginated(data, pagination, metadata = {}) {
        return {
            success: true,
            data,
            pagination: {
                page: pagination.page || 1,
                limit: pagination.limit || 10,
                total: pagination.total || 0,
                hasNext: pagination.hasNext || false,
                hasPrev: pagination.hasPrev || false
            },
            metadata: {
                timestamp: new Date().toISOString(),
                ...metadata
            }
        };
    }
}

/**
 * Circuit Breaker Implementation
 */
class CircuitBreaker {
    constructor(name, options = {}) {
        this.name = name;
        this.failureThreshold = options.failureThreshold || 5;
        this.resetTimeout = options.resetTimeout || 60000;
        this.monitoringPeriod = options.monitoringPeriod || 30000;

        this.state = 'CLOSED'; // CLOSED, OPEN, HALF_OPEN
        this.failureCount = 0;
        this.nextAttempt = Date.now();
        this.successCount = 0;

        this.requests = [];
    }

    async execute(operation) {
        if (this.state === 'OPEN') {
            if (Date.now() < this.nextAttempt) {
                throw new Error(`Circuit breaker is OPEN for ${this.name}`);
            }
            this.state = 'HALF_OPEN';
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
        this.failureCount = 0;
        if (this.state === 'HALF_OPEN') {
            this.successCount++;
            if (this.successCount >= 3) {
                this.state = 'CLOSED';
                this.successCount = 0;
            }
        }

        this.recordRequest(true);
    }

    onFailure() {
        this.failureCount++;
        this.successCount = 0;

        if (this.failureCount >= this.failureThreshold) {
            this.state = 'OPEN';
            this.nextAttempt = Date.now() + this.resetTimeout;
        }

        this.recordRequest(false);
    }

    recordRequest(success) {
        const now = Date.now();
        this.requests.push({ timestamp: now, success });

        // Clean old requests
        const cutoff = now - this.monitoringPeriod;
        this.requests = this.requests.filter(req => req.timestamp > cutoff);
    }

    getStatus() {
        const now = Date.now();
        const cutoff = now - this.monitoringPeriod;
        const recentRequests = this.requests.filter(req => req.timestamp > cutoff);
        const successCount = recentRequests.filter(req => req.success).length;

        return {
            name: this.name,
            state: this.state,
            failureCount: this.failureCount,
            successRate: recentRequests.length > 0 ? successCount / recentRequests.length : 1,
            nextAttempt: this.state === 'OPEN' ? new Date(this.nextAttempt).toISOString() : null
        };
    }
}

/**
 * Request Tracer for distributed tracing
 */
class RequestTracer {
    constructor(serviceName) {
        this.serviceName = serviceName;
        this.activeTraces = new Map();
    }

    startTrace(correlationId = null) {
        const traceId = correlationId || this.generateTraceId();
        const trace = {
            traceId,
            serviceName: this.serviceName,
            startTime: Date.now(),
            spans: [],
            metadata: {}
        };

        this.activeTraces.set(traceId, trace);
        return traceId;
    }

    addSpan(traceId, operation, startTime = Date.now()) {
        const trace = this.activeTraces.get(traceId);
        if (!trace) return null;

        const spanId = this.generateSpanId();
        const span = {
            spanId,
            operation,
            startTime,
            endTime: null,
            duration: null,
            metadata: {}
        };

        trace.spans.push(span);
        return spanId;
    }

    endSpan(traceId, spanId, metadata = {}) {
        const trace = this.activeTraces.get(traceId);
        if (!trace) return;

        const span = trace.spans.find(s => s.spanId === spanId);
        if (!span) return;

        span.endTime = Date.now();
        span.duration = span.endTime - span.startTime;
        span.metadata = { ...span.metadata, ...metadata };
    }

    endTrace(traceId, metadata = {}) {
        const trace = this.activeTraces.get(traceId);
        if (!trace) return null;

        trace.endTime = Date.now();
        trace.duration = trace.endTime - trace.startTime;
        trace.metadata = { ...trace.metadata, ...metadata };

        this.activeTraces.delete(traceId);
        return trace;
    }

    generateTraceId() {
        return `trace_${this.serviceName}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    generateSpanId() {
        return `span_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
    }
}

/**
 * Base Service Class
 */
class BaseService {
    constructor(config) {
        this.config = config instanceof ServiceConfig ? config : new ServiceConfig(config);

        // Core components
        this.errorDNA = new ErrorDNA(this.config.service_name);
        this.tracer = new RequestTracer(this.config.service_name);
        this.circuitBreakers = new Map();

        // State management
        this.isHealthy = true;
        this.startTime = Date.now();
        this.metrics = {
            requestCount: 0,
            errorCount: 0,
            responseTime: [],
            activeConnections: 0
        };

        // Initialize components
        this.initializeComponents();
    }

    /**
     * Initialize base service components
     */
    async initializeComponents() {
        try {
            // Initialize shared components if available
            await this.initializeSharedComponents();

            // Initialize service-specific components
            await this.initializeServiceComponents();

            // Start health monitoring
            if (this.config.health_check_interval > 0) {
                this.startHealthMonitoring();
            }

        } catch (error) {
            this.logError('Failed to initialize base service components', error);
            throw error;
        }
    }

    /**
     * Initialize shared components (override in child classes)
     */
    async initializeSharedComponents() {
        // To be implemented by child classes using shared components
        // Example:
        // this.logger = shared.createServiceLogger(this.config.service_name);
        // this.transfer = new shared.TransferManager(this.config.transfer);
        // this.cache = new shared.CacheManager(this.config.cache);
    }

    /**
     * Initialize service-specific components (override in child classes)
     */
    async initializeServiceComponents() {
        // To be implemented by child classes
    }

    /**
     * Get or create circuit breaker for operation
     */
    getCircuitBreaker(operationName, options = {}) {
        if (!this.circuitBreakers.has(operationName)) {
            this.circuitBreakers.set(operationName, new CircuitBreaker(operationName, {
                failureThreshold: options.failureThreshold || 5,
                resetTimeout: options.resetTimeout || 60000,
                ...options
            }));
        }
        return this.circuitBreakers.get(operationName);
    }

    /**
     * Execute operation with circuit breaker protection
     */
    async executeWithCircuitBreaker(operationName, operation, options = {}) {
        if (!this.config.enable_circuit_breaker) {
            return await operation();
        }

        const circuitBreaker = this.getCircuitBreaker(operationName, options);
        return await circuitBreaker.execute(operation);
    }

    /**
     * Start distributed trace
     */
    startTrace(correlationId = null) {
        if (!this.config.enable_tracing) {
            return null;
        }
        return this.tracer.startTrace(correlationId);
    }

    /**
     * Add span to trace
     */
    addSpan(traceId, operation) {
        if (!this.config.enable_tracing || !traceId) {
            return null;
        }
        return this.tracer.addSpan(traceId, operation);
    }

    /**
     * End span
     */
    endSpan(traceId, spanId, metadata = {}) {
        if (!this.config.enable_tracing || !traceId || !spanId) {
            return;
        }
        this.tracer.endSpan(traceId, spanId, metadata);
    }

    /**
     * End trace
     */
    endTrace(traceId, metadata = {}) {
        if (!this.config.enable_tracing || !traceId) {
            return null;
        }
        return this.tracer.endTrace(traceId, metadata);
    }

    /**
     * Handle error using ErrorDNA
     */
    async handleError(error, context = {}) {
        this.metrics.errorCount++;

        const analysis = this.errorDNA.analyze(error, context);
        const recovery = await this.errorDNA.executeRecovery(analysis, context);

        // Log error based on severity
        const logLevel = recovery.escalate ? 'error' : 'warn';
        this.log(logLevel, 'Error handled by ErrorDNA', {
            errorId: analysis.errorId,
            classification: analysis.classification.type,
            action: recovery.action,
            shouldRetry: recovery.shouldRetry,
            correlationId: context.correlationId
        });

        return {
            analysis,
            recovery,
            userMessage: recovery.userMessage || 'An error occurred'
        };
    }

    /**
     * Record metrics
     */
    recordMetrics(operation, startTime, success = true) {
        if (!this.config.enable_metrics) return;

        const duration = Date.now() - startTime;
        this.metrics.requestCount++;
        this.metrics.responseTime.push(duration);

        // Keep only last 1000 response times
        if (this.metrics.responseTime.length > 1000) {
            this.metrics.responseTime = this.metrics.responseTime.slice(-1000);
        }

        if (!success) {
            this.metrics.errorCount++;
        }
    }

    /**
     * Get service metrics
     */
    getMetrics() {
        const responseTime = this.metrics.responseTime;
        const avgResponseTime = responseTime.length > 0
            ? responseTime.reduce((a, b) => a + b, 0) / responseTime.length
            : 0;

        const uptime = Date.now() - this.startTime;
        const errorRate = this.metrics.requestCount > 0
            ? this.metrics.errorCount / this.metrics.requestCount
            : 0;

        return {
            service: this.config.service_name,
            version: this.config.version,
            uptime,
            totalRequests: this.metrics.requestCount,
            totalErrors: this.metrics.errorCount,
            errorRate,
            avgResponseTime,
            activeConnections: this.metrics.activeConnections,
            circuitBreakers: Array.from(this.circuitBreakers.values()).map(cb => cb.getStatus()),
            errorDNA: this.errorDNA.getStatistics()
        };
    }

    /**
     * Health check
     */
    async healthCheck() {
        const health = {
            service: this.config.service_name,
            status: this.isHealthy ? 'healthy' : 'unhealthy',
            timestamp: new Date().toISOString(),
            uptime: Date.now() - this.startTime,
            metrics: this.getMetrics()
        };

        // Check circuit breakers
        const openCircuitBreakers = Array.from(this.circuitBreakers.values())
            .filter(cb => cb.getStatus().state === 'OPEN');

        if (openCircuitBreakers.length > 0) {
            health.status = 'degraded';
            health.issues = [`${openCircuitBreakers.length} circuit breakers are OPEN`];
        }

        // Check error rate
        const metrics = this.getMetrics();
        if (metrics.errorRate > 0.1) { // 10% error rate threshold
            health.status = 'degraded';
            health.issues = health.issues || [];
            health.issues.push(`High error rate: ${(metrics.errorRate * 100).toFixed(2)}%`);
        }

        return health;
    }

    /**
     * Start health monitoring
     */
    startHealthMonitoring() {
        setInterval(async () => {
            try {
                const health = await this.healthCheck();

                if (health.status !== 'healthy') {
                    this.log('warn', 'Service health degraded', health);
                }

                // Update healthy status
                this.isHealthy = health.status === 'healthy';

            } catch (error) {
                this.logError('Health check failed', error);
                this.isHealthy = false;
            }
        }, this.config.health_check_interval);
    }

    /**
     * Graceful shutdown
     */
    async shutdown() {
        this.log('info', `Shutting down ${this.config.service_name}`);

        try {
            // Stop accepting new requests
            this.isHealthy = false;

            // Wait for active connections to finish
            const maxWait = 30000; // 30 seconds
            const start = Date.now();

            while (this.metrics.activeConnections > 0 && (Date.now() - start) < maxWait) {
                this.log('info', `Waiting for ${this.metrics.activeConnections} active connections`);
                await this.sleep(1000);
            }

            // Shutdown service-specific components
            await this.shutdownServiceComponents();

            // Shutdown shared components
            await this.shutdownSharedComponents();

            this.log('info', `${this.config.service_name} shutdown complete`);

        } catch (error) {
            this.logError('Error during shutdown', error);
        }
    }

    /**
     * Shutdown service-specific components (override in child classes)
     */
    async shutdownServiceComponents() {
        // To be implemented by child classes
    }

    /**
     * Shutdown shared components (override in child classes)
     */
    async shutdownSharedComponents() {
        // To be implemented by child classes
        // Example:
        // if (this.transfer) await this.transfer.shutdown();
        // if (this.cache) await this.cache.close();
    }

    /**
     * Logging methods (fallback implementation)
     */
    log(level, message, metadata = {}) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level: level.toUpperCase(),
            service: this.config.service_name,
            message,
            ...metadata
        };

        console.log(JSON.stringify(logEntry));
    }

    logError(message, error, metadata = {}) {
        this.log('error', message, {
            error: {
                message: error.message,
                name: error.name,
                stack: error.stack
            },
            ...metadata
        });
    }

    /**
     * Utility method
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Generate correlation ID
     */
    generateCorrelationId() {
        return `${this.config.service_name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

module.exports = {
    BaseService,
    ServiceConfig,
    StandardResponse,
    CircuitBreaker,
    RequestTracer
};