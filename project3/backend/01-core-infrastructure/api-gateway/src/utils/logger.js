/**
 * Logger for API Gateway - Updated to use shared logger from Central Hub
 * Falls back to Winston if shared logger not available
 */

const winston = require('winston');
const path = require('path');

// Try to use shared logger from Central Hub
let shared;
try {
    shared = require('../../../../01-core-infrastructure/central-hub/shared');
} catch (error) {
    console.warn('Shared logger not available, falling back to Winston:', error.message);
}

// Define custom log format
const logFormat = winston.format.combine(
    winston.format.timestamp({
        format: 'YYYY-MM-DD HH:mm:ss.SSS'
    }),
    winston.format.errors({ stack: true }),
    winston.format.printf(({ timestamp, level, message, service, correlationId, ...meta }) => {
        let logMessage = `${timestamp} [${level.toUpperCase()}]`;

        if (service) {
            logMessage += ` [${service}]`;
        }

        if (correlationId) {
            logMessage += ` [${correlationId}]`;
        }

        logMessage += `: ${message}`;

        // Add metadata if present
        if (Object.keys(meta).length > 0) {
            logMessage += ` ${JSON.stringify(meta)}`;
        }

        return logMessage;
    })
);

// Create logger instance - prefer shared logger
let logger;

if (shared && shared.createServiceLogger) {
    // ✅ Use shared logger from Central Hub
    logger = shared.createServiceLogger('api-gateway');
    console.log('✅ Using shared logger from Central Hub');
} else {
    // ❌ Fallback to Winston logger
    logger = winston.createLogger({
        level: process.env.LOG_LEVEL || 'info',
        format: logFormat,
        defaultMeta: {
            service: 'api-gateway'
        },
        transports: [
            // Console output
            new winston.transports.Console({
                format: winston.format.combine(
                    winston.format.colorize(),
                    logFormat
                )
            }),

            // File output for errors
            new winston.transports.File({
                filename: path.join(__dirname, '../../logs/error.log'),
                level: 'error',
                maxsize: 5242880, // 5MB
                maxFiles: 5
            }),

            // File output for all logs
            new winston.transports.File({
                filename: path.join(__dirname, '../../logs/combined.log'),
                maxsize: 5242880, // 5MB
                maxFiles: 5
            })
        ],

        // Handle uncaught exceptions
        exceptionHandlers: [
            new winston.transports.File({
                filename: path.join(__dirname, '../../logs/exceptions.log')
            })
        ],

        // Handle unhandled rejections
        rejectionHandlers: [
            new winston.transports.File({
                filename: path.join(__dirname, '../../logs/rejections.log')
            })
        ]
    });
    console.log('⚠️  Using fallback Winston logger');
}

// Add request logging helper - works with both shared and Winston logger
if (!logger.logRequest) {
    logger.logRequest = (req, res, correlationId) => {
        const start = Date.now();

        res.on('finish', () => {
            const duration = Date.now() - start;
            logger.info('HTTP Request', {
                method: req.method,
                url: req.url,
                statusCode: res.statusCode,
                duration,
                correlationId,
                userAgent: req.get('User-Agent'),
                ip: req.ip
            });
        });
    };
}

// Add WebSocket logging helper - works with both shared and Winston logger
if (!logger.logWebSocket) {
    logger.logWebSocket = (event, data) => {
        logger.info(`WebSocket ${event}`, {
            ...data,
            timestamp: Date.now()
        });
    };
}

// Add performance logging helper - works with both shared and Winston logger
if (!logger.logPerformance) {
    logger.logPerformance = (operation, duration, metadata = {}) => {
        const level = duration > 1000 ? 'warn' : 'debug';

        if (logger.log) {
            logger.log(level, `Performance: ${operation}`, {
                duration,
                ...metadata
            });
        } else {
            // Fallback for shared logger
            logger[level](`Performance: ${operation}`, {
                duration,
                ...metadata
            });
        }
    };
}

module.exports = logger;