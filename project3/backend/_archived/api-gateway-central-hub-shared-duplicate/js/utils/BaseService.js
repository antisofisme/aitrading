/**
 * JavaScript BaseService - Compatible dengan Python BaseService
 * Provides standard service patterns untuk JavaScript services
 * Matches interface dari utils/base_service.py
 */

const EventEmitter = require('events');

class ServiceConfig {
    constructor({
        service_name,
        version,
        port,
        environment = 'development',
        enable_tracing = true,
        enable_circuit_breaker = true,
        health_check_interval = 30,
        cache_ttl_default = 300,
        max_connections = 100
    }) {
        this.service_name = service_name;
        this.version = version;
        this.port = port;
        this.environment = environment;
        this.enable_tracing = enable_tracing;
        this.enable_circuit_breaker = enable_circuit_breaker;
        this.health_check_interval = health_check_interval;
        this.cache_ttl_default = cache_ttl_default;
        this.max_connections = max_connections;
    }
}

class StandardResponse {
    constructor({
        success,
        data = null,
        error_message = null,
        processing_time_ms = 0,
        correlation_id = null
    }) {
        this.success = success;
        this.data = data;
        this.error_message = error_message;
        this.processing_time_ms = processing_time_ms;
        this.correlation_id = correlation_id;
        this.timestamp = new Date().toISOString();
    }
}

class BaseService extends EventEmitter {
    constructor(config) {
        super();

        if (!(config instanceof ServiceConfig)) {
            throw new Error('Config must be instance of ServiceConfig');
        }

        this.config = config;
        this.service_name = config.service_name;
        this.version = config.version;
        this.start_time = new Date();

        // Service state
        this.is_healthy = true;
        this.active_connections = 0;
        this.request_count = 0;
        this.error_count = 0;

        // Initialize components
        this._initializeComponents();

        // Setup logging
        this.logger = this._setupLogging();

        // Performance tracking
        this.response_times = [];
        this.request_timestamps = [];

        // Health check scheduler
        this._health_check_timer = null;
    }

    _initializeComponents() {
        // Initialize standard components (akan di-implement)
        this.db = null;           // Database manager
        this.cache = null;        // Cache manager
        this.config_manager = null; // Config manager
        this.tracer = null;       // Request tracer
        this.circuit_breaker = null; // Circuit breaker

        // Placeholder implementations
        if (this.config.enable_tracing) {
            this.tracer = {
                trace: (operation_name, correlation_id) => {
                    return {
                        end: () => {},
                        addError: (error) => {}
                    };
                }
            };
        }

        if (this.config.enable_circuit_breaker) {
            this.circuit_breaker = {
                is_open: (service) => false,
                record_success: async (service) => {},
                record_failure: async (service) => {},
                get_status: async () => ({ status: 'closed' })
            };
        }
    }

    _setupLogging() {
        // Use existing log_utils or create structured logger
        const logger = {
            info: (message, extra = {}) => {
                console.log(JSON.stringify({
                    timestamp: new Date().toISOString(),
                    level: 'INFO',
                    service: this.service_name,
                    message,
                    ...extra
                }));
            },
            warn: (message, extra = {}) => {
                console.warn(JSON.stringify({
                    timestamp: new Date().toISOString(),
                    level: 'WARN',
                    service: this.service_name,
                    message,
                    ...extra
                }));
            },
            error: (message, extra = {}) => {
                console.error(JSON.stringify({
                    timestamp: new Date().toISOString(),
                    level: 'ERROR',
                    service: this.service_name,
                    message,
                    ...extra
                }));
            },
            debug: (message, extra = {}) => {
                if (process.env.NODE_ENV === 'development') {
                    console.debug(JSON.stringify({
                        timestamp: new Date().toISOString(),
                        level: 'DEBUG',
                        service: this.service_name,
                        message,
                        ...extra
                    }));
                }
            }
        };

        return logger;
    }

    async processWithTracing(operation_name, func, correlation_id = null, ...args) {
        const start_time = Date.now();

        try {
            this.active_connections++;
            this.request_count++;

            let result;

            // Start tracing if enabled
            if (this.tracer && correlation_id) {
                const span = this.tracer.trace(operation_name, correlation_id);
                try {
                    result = await func(...args);
                } finally {
                    span.end();
                }
            } else {
                result = await func(...args);
            }

            // Calculate processing time
            const processing_time_ms = Date.now() - start_time;
            this.response_times.push(processing_time_ms);
            this.request_timestamps.push(Date.now());

            // Log success
            this.logger.info(`${operation_name} completed`, {
                operation: operation_name,
                processing_time_ms,
                correlation_id,
                success: true
            });

            return new StandardResponse({
                success: true,
                data: result,
                processing_time_ms,
                correlation_id
            });

        } catch (error) {
            this.error_count++;
            const processing_time_ms = Date.now() - start_time;

            // Log error
            this.logger.error(`${operation_name} failed: ${error.message}`, {
                operation: operation_name,
                processing_time_ms,
                correlation_id,
                error: error.message,
                success: false
            });

            // Add error to trace if tracing enabled
            if (this.tracer && correlation_id) {
                this.tracer.addError(correlation_id, error.message);
            }

            return new StandardResponse({
                success: false,
                error_message: error.message,
                processing_time_ms,
                correlation_id
            });

        } finally {
            this.active_connections--;
        }
    }

    async getConfig(key, defaultValue = null) {
        if (this.config_manager) {
            return await this.config_manager.get(key, defaultValue);
        }
        return process.env[key] || defaultValue;
    }

    async cacheGet(key, defaultValue = null) {
        if (this.cache) {
            return await this.cache.get(key, defaultValue);
        }
        return defaultValue;
    }

    async cacheSet(key, value, ttl = null) {
        if (this.cache) {
            return await this.cache.set(key, value, ttl);
        }
        return false;
    }

    async dbExecute(query, params = null) {
        if (this.db) {
            return await this.db.execute(query, params);
        }
        throw new Error('Database manager not initialized');
    }

    async checkCircuitBreaker(external_service) {
        if (this.circuit_breaker) {
            return this.circuit_breaker.is_open(external_service);
        }
        return false;
    }

    async recordExternalSuccess(external_service) {
        if (this.circuit_breaker) {
            await this.circuit_breaker.record_success(external_service);
        }
    }

    async recordExternalFailure(external_service) {
        if (this.circuit_breaker) {
            await this.circuit_breaker.record_failure(external_service);
        }
    }

    async healthCheck() {
        const uptime_seconds = Math.floor((Date.now() - this.start_time.getTime()) / 1000);

        const health_status = {
            service: this.service_name,
            status: this.is_healthy ? 'healthy' : 'unhealthy',
            version: this.version,
            timestamp: new Date().toISOString(),
            uptime_seconds,
            active_connections: this.active_connections,
            total_requests: this.request_count,
            error_rate: this.request_count > 0 ? this.error_count / this.request_count : 0,
            avg_response_time_ms: this._getAverageResponseTime()
        };

        try {
            // Check database connection
            if (this.db && typeof this.db.health_check === 'function') {
                health_status.database = await this.db.health_check();
            }

            // Check cache connection
            if (this.cache && typeof this.cache.health_check === 'function') {
                health_status.cache = await this.cache.health_check();
            }

            // Check circuit breaker status
            if (this.circuit_breaker) {
                health_status.circuit_breakers = await this.circuit_breaker.get_status();
            }

            // Add service-specific health checks
            const custom_health = await this.customHealthChecks();
            if (custom_health) {
                Object.assign(health_status, custom_health);
            }

        } catch (error) {
            this.logger.error(`Health check failed: ${error.message}`);
            health_status.status = 'degraded';
            health_status.error = error.message;
            this.is_healthy = false;
        }

        return health_status;
    }

    _getAverageResponseTime() {
        if (this.response_times.length === 0) return 0;
        const sum = this.response_times.reduce((a, b) => a + b, 0);
        return Math.round(sum / this.response_times.length);
    }

    async customHealthChecks() {
        // Override in child classes
        return {};
    }

    async start() {
        this.logger.info(`Starting ${this.service_name} v${this.version}`);

        try {
            // Initialize connections
            if (this.db && typeof this.db.connect === 'function') {
                await this.db.connect();
            }

            if (this.cache && typeof this.cache.connect === 'function') {
                await this.cache.connect();
            }

            if (this.config_manager && typeof this.config_manager.load_config === 'function') {
                await this.config_manager.load_config();
            }

            // Start health check scheduler
            if (this.config.health_check_interval > 0) {
                this._startHealthCheckScheduler();
            }

            // Custom startup logic
            await this.onStartup();

            this.logger.info(`${this.service_name} started successfully`);
            this.emit('started');

        } catch (error) {
            this.logger.error(`Failed to start ${this.service_name}: ${error.message}`);
            throw error;
        }
    }

    async stop() {
        this.logger.info(`Stopping ${this.service_name}`);

        try {
            // Stop health check scheduler
            if (this._health_check_timer) {
                clearInterval(this._health_check_timer);
                this._health_check_timer = null;
            }

            // Custom shutdown logic
            await this.onShutdown();

            // Close connections
            if (this.db && typeof this.db.disconnect === 'function') {
                await this.db.disconnect();
            }

            if (this.cache && typeof this.cache.disconnect === 'function') {
                await this.cache.disconnect();
            }

            this.logger.info(`${this.service_name} stopped`);
            this.emit('stopped');

        } catch (error) {
            this.logger.error(`Error during shutdown: ${error.message}`);
        }
    }

    _startHealthCheckScheduler() {
        this._health_check_timer = setInterval(async () => {
            try {
                await this.healthCheck();
            } catch (error) {
                this.logger.error(`Health check scheduler error: ${error.message}`);
            }
        }, this.config.health_check_interval * 1000);
    }

    // Abstract methods - implement in child classes
    async onStartup() {
        // Custom startup logic
    }

    async onShutdown() {
        // Custom shutdown logic
    }

    generateCorrelationId() {
        return `${this.service_name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}

module.exports = {
    BaseService,
    ServiceConfig,
    StandardResponse
};