/**
 * Shared Logger Utility - Used across all services
 *
 * Provides structured logging with different levels and formats
 * Aligned with Winston logger but simplified for shared usage
 */

class SharedLogger {
    constructor(serviceName = 'unknown-service') {
        this.serviceName = serviceName;
        this.logLevel = process.env.LOG_LEVEL || 'info';

        // Log levels
        this.levels = {
            error: 0,
            warn: 1,
            info: 2,
            debug: 3
        };

        this.currentLevel = this.levels[this.logLevel] || this.levels.info;
    }

    /**
     * Format log message
     */
    formatMessage(level, message, meta = {}) {
        const timestamp = new Date().toISOString();

        let logMessage = `${timestamp} [${level.toUpperCase()}] [${this.serviceName}]`;

        if (meta.correlationId) {
            logMessage += ` [${meta.correlationId}]`;
        }

        logMessage += `: ${message}`;

        // Add metadata if present
        const metaCopy = { ...meta };
        delete metaCopy.correlationId; // Already included above

        if (Object.keys(metaCopy).length > 0) {
            logMessage += ` ${JSON.stringify(metaCopy)}`;
        }

        return logMessage;
    }

    /**
     * Check if level should be logged
     */
    shouldLog(level) {
        return this.levels[level] <= this.currentLevel;
    }

    /**
     * Output log message
     */
    output(level, formattedMessage) {
        if (level === 'error') {
            console.error(formattedMessage);
        } else if (level === 'warn') {
            console.warn(formattedMessage);
        } else {
            console.log(formattedMessage);
        }
    }

    /**
     * Error logging
     */
    error(message, meta = {}) {
        if (this.shouldLog('error')) {
            const formatted = this.formatMessage('error', message, meta);
            this.output('error', formatted);
        }
    }

    /**
     * Warning logging
     */
    warn(message, meta = {}) {
        if (this.shouldLog('warn')) {
            const formatted = this.formatMessage('warn', message, meta);
            this.output('warn', formatted);
        }
    }

    /**
     * Info logging
     */
    info(message, meta = {}) {
        if (this.shouldLog('info')) {
            const formatted = this.formatMessage('info', message, meta);
            this.output('info', formatted);
        }
    }

    /**
     * Debug logging
     */
    debug(message, meta = {}) {
        if (this.shouldLog('debug')) {
            const formatted = this.formatMessage('debug', message, meta);
            this.output('debug', formatted);
        }
    }

    /**
     * Log request (for HTTP/WebSocket)
     */
    logRequest(req, res, correlationId) {
        const start = Date.now();

        if (res && res.on) {
            res.on('finish', () => {
                const duration = Date.now() - start;
                this.info('Request completed', {
                    method: req.method,
                    url: req.url || req.path,
                    statusCode: res.statusCode,
                    duration,
                    correlationId,
                    userAgent: req.get ? req.get('User-Agent') : req.headers?.['user-agent'],
                    ip: req.ip || req.connection?.remoteAddress
                });
            });
        } else {
            // For requests without response object
            this.info('Request received', {
                method: req.method,
                url: req.url || req.path,
                correlationId,
                userAgent: req.get ? req.get('User-Agent') : req.headers?.['user-agent'],
                ip: req.ip || req.connection?.remoteAddress
            });
        }
    }

    /**
     * Log WebSocket events
     */
    logWebSocket(event, data = {}) {
        this.info(`WebSocket ${event}`, {
            ...data,
            timestamp: Date.now()
        });
    }

    /**
     * Log performance metrics
     */
    logPerformance(operation, duration, metadata = {}) {
        const level = duration > 1000 ? 'warn' : 'debug';
        this[level](`Performance: ${operation}`, {
            duration,
            ...metadata
        });
    }

    /**
     * Log transfer operations
     */
    logTransfer(operation, method, destination, metadata = {}) {
        this.info(`Transfer ${operation}`, {
            method,
            destination,
            ...metadata
        });
    }

    /**
     * Change log level
     */
    setLevel(level) {
        if (this.levels[level] !== undefined) {
            this.logLevel = level;
            this.currentLevel = this.levels[level];
            this.info('Log level changed', { newLevel: level });
        } else {
            this.warn('Invalid log level', { level, validLevels: Object.keys(this.levels) });
        }
    }

    /**
     * Set service name
     */
    setServiceName(serviceName) {
        this.serviceName = serviceName;
    }
}

// Create default logger instance
let defaultLogger = null;

/**
 * Get or create logger instance
 */
function getLogger(serviceName) {
    if (!serviceName && defaultLogger) {
        return defaultLogger;
    }

    const logger = new SharedLogger(serviceName);

    if (!defaultLogger) {
        defaultLogger = logger;
    }

    return logger;
}

/**
 * Create logger for service
 */
function createLogger(serviceName) {
    return new SharedLogger(serviceName);
}

// Export default logger and factory functions
module.exports = getLogger();
module.exports.getLogger = getLogger;
module.exports.createLogger = createLogger;
module.exports.SharedLogger = SharedLogger;