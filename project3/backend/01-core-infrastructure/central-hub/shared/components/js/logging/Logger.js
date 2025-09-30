/**
 * JavaScript Logger - Structured logging compatible dengan Python logging
 * Creates service-specific loggers dengan consistent format
 */

const fs = require('fs');
const path = require('path');

const LogLevel = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARN: 'WARN',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL'
};

const LogLevelValues = {
    [LogLevel.DEBUG]: 10,
    [LogLevel.INFO]: 20,
    [LogLevel.WARN]: 30,
    [LogLevel.ERROR]: 40,
    [LogLevel.CRITICAL]: 50
};

class StructuredLogger {
    constructor(service_name, options = {}) {
        this.service_name = service_name;
        this.config = {
            level: options.level || LogLevel.INFO,
            format: options.format || 'json',
            output: options.output || 'console',
            file_path: options.file_path || null,
            max_file_size: options.max_file_size || 10 * 1024 * 1024, // 10MB
            max_files: options.max_files || 5,
            include_trace: options.include_trace || false,
            ...options
        };

        this.current_level = LogLevelValues[this.config.level];

        // File handles for file logging
        this.file_handles = new Map();

        // Setup file logging if configured
        if (this.config.output === 'file' || this.config.output === 'both') {
            this._setupFileLogging();
        }
    }

    _setupFileLogging() {
        if (!this.config.file_path) {
            this.config.file_path = path.join(process.cwd(), 'logs', `${this.service_name}.log`);
        }

        // Ensure log directory exists
        const log_dir = path.dirname(this.config.file_path);
        if (!fs.existsSync(log_dir)) {
            fs.mkdirSync(log_dir, { recursive: true });
        }
    }

    _shouldLog(level) {
        return LogLevelValues[level] >= this.current_level;
    }

    _formatMessage(level, message, extra = {}) {
        const log_entry = {
            timestamp: new Date().toISOString(),
            level: level,
            service: this.service_name,
            message: message,
            ...extra
        };

        // Add process information
        log_entry.process = {
            pid: process.pid,
            memory_usage: process.memoryUsage(),
            uptime: process.uptime()
        };

        // Add stack trace for errors
        if (level === LogLevel.ERROR || level === LogLevel.CRITICAL || this.config.include_trace) {
            const stack = new Error().stack;
            const stack_lines = stack.split('\n').slice(2); // Remove Error and _formatMessage lines
            log_entry.stack_trace = stack_lines;
        }

        if (this.config.format === 'json') {
            return JSON.stringify(log_entry, null, this.config.pretty_print ? 2 : 0);
        } else {
            // Simple text format
            const extra_str = Object.keys(extra).length > 0 ?
                ` | ${JSON.stringify(extra)}` : '';
            return `${log_entry.timestamp} - ${level} - ${this.service_name} - ${message}${extra_str}`;
        }
    }

    _writeToOutput(formatted_message, level) {
        // Console output
        if (this.config.output === 'console' || this.config.output === 'both') {
            switch (level) {
                case LogLevel.DEBUG:
                    if (process.env.NODE_ENV === 'development') {
                        console.debug(formatted_message);
                    }
                    break;
                case LogLevel.INFO:
                    console.log(formatted_message);
                    break;
                case LogLevel.WARN:
                    console.warn(formatted_message);
                    break;
                case LogLevel.ERROR:
                case LogLevel.CRITICAL:
                    console.error(formatted_message);
                    break;
            }
        }

        // File output
        if (this.config.output === 'file' || this.config.output === 'both') {
            this._writeToFile(formatted_message);
        }
    }

    _writeToFile(message) {
        try {
            // Check file size and rotate if needed
            this._rotateLogFileIfNeeded();

            fs.appendFileSync(this.config.file_path, message + '\n');
        } catch (error) {
            console.error(`Failed to write to log file: ${error.message}`);
        }
    }

    _rotateLogFileIfNeeded() {
        if (!fs.existsSync(this.config.file_path)) {
            return;
        }

        const stats = fs.statSync(this.config.file_path);
        if (stats.size >= this.config.max_file_size) {
            this._rotateLogFiles();
        }
    }

    _rotateLogFiles() {
        const base_path = this.config.file_path.replace('.log', '');
        const extension = '.log';

        try {
            // Remove oldest log file
            const oldest_log = `${base_path}.${this.config.max_files}${extension}`;
            if (fs.existsSync(oldest_log)) {
                fs.unlinkSync(oldest_log);
            }

            // Rotate existing log files
            for (let i = this.config.max_files - 1; i >= 1; i--) {
                const current_log = i === 1 ?
                    this.config.file_path :
                    `${base_path}.${i}${extension}`;
                const next_log = `${base_path}.${i + 1}${extension}`;

                if (fs.existsSync(current_log)) {
                    fs.renameSync(current_log, next_log);
                }
            }

        } catch (error) {
            console.error(`Log rotation failed: ${error.message}`);
        }
    }

    debug(message, extra = {}) {
        if (!this._shouldLog(LogLevel.DEBUG)) return;

        const formatted = this._formatMessage(LogLevel.DEBUG, message, extra);
        this._writeToOutput(formatted, LogLevel.DEBUG);
    }

    info(message, extra = {}) {
        if (!this._shouldLog(LogLevel.INFO)) return;

        const formatted = this._formatMessage(LogLevel.INFO, message, extra);
        this._writeToOutput(formatted, LogLevel.INFO);
    }

    warn(message, extra = {}) {
        if (!this._shouldLog(LogLevel.WARN)) return;

        const formatted = this._formatMessage(LogLevel.WARN, message, extra);
        this._writeToOutput(formatted, LogLevel.WARN);
    }

    error(message, extra = {}) {
        if (!this._shouldLog(LogLevel.ERROR)) return;

        const formatted = this._formatMessage(LogLevel.ERROR, message, extra);
        this._writeToOutput(formatted, LogLevel.ERROR);
    }

    critical(message, extra = {}) {
        if (!this._shouldLog(LogLevel.CRITICAL)) return;

        const formatted = this._formatMessage(LogLevel.CRITICAL, message, extra);
        this._writeToOutput(formatted, LogLevel.CRITICAL);
    }

    // Convenience methods
    log(level, message, extra = {}) {
        if (!Object.values(LogLevel).includes(level)) {
            throw new Error(`Invalid log level: ${level}`);
        }

        switch (level) {
            case LogLevel.DEBUG:
                this.debug(message, extra);
                break;
            case LogLevel.INFO:
                this.info(message, extra);
                break;
            case LogLevel.WARN:
                this.warn(message, extra);
                break;
            case LogLevel.ERROR:
                this.error(message, extra);
                break;
            case LogLevel.CRITICAL:
                this.critical(message, extra);
                break;
        }
    }

    // Performance logging
    async logPerformance(operation_name, func, extra = {}) {
        const start_time = Date.now();
        const correlation_id = extra.correlation_id || this._generateCorrelationId();

        this.info(`Starting ${operation_name}`, {
            operation: operation_name,
            correlation_id,
            ...extra
        });

        try {
            const result = await func();
            const processing_time = Date.now() - start_time;

            this.info(`Completed ${operation_name}`, {
                operation: operation_name,
                correlation_id,
                processing_time_ms: processing_time,
                success: true,
                ...extra
            });

            return result;

        } catch (error) {
            const processing_time = Date.now() - start_time;

            this.error(`Failed ${operation_name}`, {
                operation: operation_name,
                correlation_id,
                processing_time_ms: processing_time,
                error: error.message,
                success: false,
                ...extra
            });

            throw error;
        }
    }

    // Request logging middleware
    createRequestLogger() {
        return (req, res, next) => {
            const start_time = Date.now();
            const correlation_id = req.headers['x-correlation-id'] || this._generateCorrelationId();

            // Add correlation ID to request
            req.correlation_id = correlation_id;

            this.info('Incoming request', {
                method: req.method,
                url: req.url,
                user_agent: req.headers['user-agent'],
                ip: req.ip,
                correlation_id
            });

            // Log response
            const original_send = res.send;
            res.send = function(data) {
                const processing_time = Date.now() - start_time;

                const log_data = {
                    method: req.method,
                    url: req.url,
                    status_code: res.statusCode,
                    processing_time_ms: processing_time,
                    correlation_id
                };

                if (res.statusCode >= 400) {
                    this.error('Request completed with error', log_data);
                } else {
                    this.info('Request completed successfully', log_data);
                }

                return original_send.call(this, data);
            }.bind(this);

            next();
        };
    }

    _generateCorrelationId() {
        return `${this.service_name}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Configuration methods
    setLevel(level) {
        if (!Object.values(LogLevel).includes(level)) {
            throw new Error(`Invalid log level: ${level}`);
        }
        this.config.level = level;
        this.current_level = LogLevelValues[level];
        this.info(`Log level changed to ${level}`);
    }

    getLevel() {
        return this.config.level;
    }

    // Health check
    healthCheck() {
        return {
            service: 'Logger',
            status: 'healthy',
            config: {
                level: this.config.level,
                output: this.config.output,
                file_path: this.config.file_path
            },
            stats: {
                current_level: this.current_level,
                file_exists: this.config.file_path ? fs.existsSync(this.config.file_path) : false
            }
        };
    }

    // Cleanup
    close() {
        // Close any open file handles
        for (const handle of this.file_handles.values()) {
            if (handle && typeof handle.close === 'function') {
                handle.close();
            }
        }
        this.file_handles.clear();
    }
}

// Factory function to create service loggers
function createServiceLogger(service_name, options = {}) {
    // Set environment-specific defaults
    const env_defaults = {
        development: {
            level: LogLevel.DEBUG,
            output: 'console',
            format: 'json',
            pretty_print: true
        },
        production: {
            level: LogLevel.INFO,
            output: 'both',
            format: 'json',
            pretty_print: false
        },
        test: {
            level: LogLevel.WARN,
            output: 'console',
            format: 'json'
        }
    };

    const environment = process.env.NODE_ENV || 'development';
    const env_config = env_defaults[environment] || env_defaults.development;

    const final_options = {
        ...env_config,
        ...options
    };

    return new StructuredLogger(service_name, final_options);
}

module.exports = {
    StructuredLogger,
    createServiceLogger,
    LogLevel,
    LogLevelValues
};