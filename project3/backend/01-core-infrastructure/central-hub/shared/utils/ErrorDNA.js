/**
 * Error DNA - JavaScript Implementation
 *
 * Provides intelligent error classification, handling, and recovery strategies
 * Based on the Python version but optimized for JavaScript/Node.js services
 */

class ErrorDNA {
    constructor(serviceName = 'unknown-service') {
        this.serviceName = serviceName;
        this.errorPatterns = new Map();
        this.errorHistory = [];
        this.recoveryStrategies = new Map();

        // Initialize default error patterns
        this.initializeDefaultPatterns();
        this.initializeRecoveryStrategies();
    }

    /**
     * Initialize default error classification patterns
     */
    initializeDefaultPatterns() {
        // Business Logic Errors
        this.addPattern('BUSINESS_ERROR', {
            keywords: ['validation', 'invalid', 'missing', 'required', 'format', 'duplicate'],
            statusCodes: [400, 409, 422],
            severity: 'medium',
            userFacing: true,
            retryable: false
        });

        // Technical/System Errors
        this.addPattern('TECHNICAL_ERROR', {
            keywords: ['database', 'connection', 'timeout', 'unavailable', 'internal'],
            statusCodes: [500, 502, 503, 504],
            severity: 'high',
            userFacing: false,
            retryable: true,
            maxRetries: 3
        });

        // Network/Transport Errors
        this.addPattern('NETWORK_ERROR', {
            keywords: ['network', 'socket', 'refused', 'unreachable', 'dns'],
            statusCodes: [502, 503, 504],
            severity: 'high',
            userFacing: false,
            retryable: true,
            maxRetries: 5,
            backoffMultiplier: 2
        });

        // Authentication/Authorization Errors
        this.addPattern('AUTH_ERROR', {
            keywords: ['unauthorized', 'forbidden', 'token', 'expired', 'permission'],
            statusCodes: [401, 403],
            severity: 'medium',
            userFacing: true,
            retryable: false
        });

        // Rate Limiting Errors
        this.addPattern('RATE_LIMIT_ERROR', {
            keywords: ['rate', 'limit', 'quota', 'throttle'],
            statusCodes: [429],
            severity: 'medium',
            userFacing: false,
            retryable: true,
            retryDelay: 60000 // 1 minute
        });

        // Client/Input Errors
        this.addPattern('CLIENT_ERROR', {
            keywords: ['bad request', 'malformed', 'syntax', 'parse'],
            statusCodes: [400, 415],
            severity: 'low',
            userFacing: true,
            retryable: false
        });
    }

    /**
     * Initialize recovery strategies
     */
    initializeRecoveryStrategies() {
        this.recoveryStrategies.set('BUSINESS_ERROR', {
            action: 'NOTIFY_USER',
            escalate: false,
            logLevel: 'warn'
        });

        this.recoveryStrategies.set('TECHNICAL_ERROR', {
            action: 'RETRY_WITH_BACKOFF',
            escalate: true,
            logLevel: 'error',
            fallbackAction: 'CIRCUIT_BREAKER'
        });

        this.recoveryStrategies.set('NETWORK_ERROR', {
            action: 'RETRY_WITH_EXPONENTIAL_BACKOFF',
            escalate: true,
            logLevel: 'error',
            fallbackAction: 'FAILOVER_TRANSPORT'
        });

        this.recoveryStrategies.set('AUTH_ERROR', {
            action: 'REFRESH_TOKEN',
            escalate: false,
            logLevel: 'warn',
            fallbackAction: 'REDIRECT_LOGIN'
        });

        this.recoveryStrategies.set('RATE_LIMIT_ERROR', {
            action: 'EXPONENTIAL_BACKOFF',
            escalate: false,
            logLevel: 'warn'
        });

        this.recoveryStrategies.set('CLIENT_ERROR', {
            action: 'VALIDATE_AND_REJECT',
            escalate: false,
            logLevel: 'info'
        });
    }

    /**
     * Add custom error pattern
     */
    addPattern(type, pattern) {
        this.errorPatterns.set(type, {
            ...pattern,
            type,
            createdAt: Date.now()
        });
    }

    /**
     * Analyze error and classify it
     */
    analyze(error, context = {}) {
        const errorInfo = this.extractErrorInfo(error);
        const classification = this.classifyError(errorInfo);
        const errorId = this.generateErrorId();

        const analysis = {
            errorId,
            classification,
            originalError: errorInfo,
            context,
            timestamp: Date.now(),
            serviceName: this.serviceName,
            severity: classification.severity || 'medium',
            userFacing: classification.userFacing || false,
            retryable: classification.retryable || false
        };

        // Store in history for pattern learning
        this.errorHistory.push(analysis);
        this.maintainHistorySize();

        return analysis;
    }

    /**
     * Extract error information from various error types
     */
    extractErrorInfo(error) {
        if (error instanceof Error) {
            return {
                message: error.message,
                name: error.name,
                stack: error.stack,
                code: error.code,
                statusCode: error.statusCode || error.status
            };
        }

        if (typeof error === 'string') {
            return {
                message: error,
                name: 'StringError'
            };
        }

        if (typeof error === 'object' && error !== null) {
            return {
                message: error.message || error.msg || 'Unknown error',
                name: error.name || 'ObjectError',
                code: error.code,
                statusCode: error.statusCode || error.status,
                ...error
            };
        }

        return {
            message: String(error),
            name: 'UnknownError'
        };
    }

    /**
     * Classify error based on patterns
     */
    classifyError(errorInfo) {
        const message = (errorInfo.message || '').toLowerCase();
        const statusCode = errorInfo.statusCode;

        // Check each pattern
        for (const [type, pattern] of this.errorPatterns.entries()) {
            let matches = 0;
            let total = 0;

            // Check keywords
            if (pattern.keywords) {
                total++;
                if (pattern.keywords.some(keyword => message.includes(keyword.toLowerCase()))) {
                    matches++;
                }
            }

            // Check status codes
            if (pattern.statusCodes && statusCode) {
                total++;
                if (pattern.statusCodes.includes(statusCode)) {
                    matches++;
                }
            }

            // If we have a match, return this classification
            if (matches > 0 && matches / total >= 0.5) {
                return {
                    type,
                    confidence: matches / total,
                    ...pattern
                };
            }
        }

        // Default classification for unmatched errors
        return {
            type: 'UNKNOWN_ERROR',
            confidence: 0,
            severity: 'medium',
            userFacing: false,
            retryable: false
        };
    }

    /**
     * Get recovery strategy for error classification
     */
    getRecoveryStrategy(classification) {
        const strategy = this.recoveryStrategies.get(classification.type);

        if (!strategy) {
            return {
                action: 'LOG_AND_ESCALATE',
                escalate: true,
                logLevel: 'error'
            };
        }

        return {
            ...strategy,
            errorType: classification.type,
            severity: classification.severity
        };
    }

    /**
     * Execute recovery strategy
     */
    async executeRecovery(analysis, options = {}) {
        const strategy = this.getRecoveryStrategy(analysis.classification);
        const context = {
            ...analysis.context,
            ...options,
            errorId: analysis.errorId,
            attempt: options.attempt || 1
        };

        switch (strategy.action) {
            case 'RETRY_WITH_BACKOFF':
                return this.handleRetryWithBackoff(analysis, context);

            case 'RETRY_WITH_EXPONENTIAL_BACKOFF':
                return this.handleExponentialBackoff(analysis, context);

            case 'EXPONENTIAL_BACKOFF':
                return this.handleExponentialBackoff(analysis, context);

            case 'CIRCUIT_BREAKER':
                return this.handleCircuitBreaker(analysis, context);

            case 'FAILOVER_TRANSPORT':
                return this.handleFailoverTransport(analysis, context);

            case 'REFRESH_TOKEN':
                return this.handleRefreshToken(analysis, context);

            case 'NOTIFY_USER':
                return this.handleNotifyUser(analysis, context);

            case 'VALIDATE_AND_REJECT':
                return this.handleValidateAndReject(analysis, context);

            case 'LOG_AND_ESCALATE':
            default:
                return this.handleLogAndEscalate(analysis, context);
        }
    }

    /**
     * Handle retry with linear backoff
     */
    async handleRetryWithBackoff(analysis, context) {
        const maxRetries = analysis.classification.maxRetries || 3;
        const baseDelay = analysis.classification.retryDelay || 1000;

        if (context.attempt > maxRetries) {
            return {
                action: 'MAX_RETRIES_EXCEEDED',
                shouldRetry: false,
                escalate: true
            };
        }

        const delay = baseDelay * context.attempt;

        return {
            action: 'RETRY',
            shouldRetry: true,
            delay,
            nextAttempt: context.attempt + 1,
            maxRetries
        };
    }

    /**
     * Handle retry with exponential backoff
     */
    async handleExponentialBackoff(analysis, context) {
        const maxRetries = analysis.classification.maxRetries || 5;
        const baseDelay = analysis.classification.retryDelay || 1000;
        const multiplier = analysis.classification.backoffMultiplier || 2;

        if (context.attempt > maxRetries) {
            return {
                action: 'MAX_RETRIES_EXCEEDED',
                shouldRetry: false,
                escalate: true
            };
        }

        const delay = baseDelay * Math.pow(multiplier, context.attempt - 1);

        return {
            action: 'RETRY',
            shouldRetry: true,
            delay: Math.min(delay, 60000), // Cap at 1 minute
            nextAttempt: context.attempt + 1,
            maxRetries
        };
    }

    /**
     * Handle circuit breaker activation
     */
    async handleCircuitBreaker(analysis, context) {
        return {
            action: 'CIRCUIT_BREAKER_OPEN',
            shouldRetry: false,
            circuitOpen: true,
            resetAfter: 60000 // 1 minute
        };
    }

    /**
     * Handle transport failover
     */
    async handleFailoverTransport(analysis, context) {
        const availableTransports = ['http', 'grpc', 'nats-kafka'];
        const currentTransport = context.transport || 'http';
        const currentIndex = availableTransports.indexOf(currentTransport);
        const nextTransport = availableTransports[(currentIndex + 1) % availableTransports.length];

        return {
            action: 'FAILOVER',
            shouldRetry: true,
            newTransport: nextTransport,
            delay: 0
        };
    }

    /**
     * Handle token refresh
     */
    async handleRefreshToken(analysis, context) {
        return {
            action: 'REFRESH_TOKEN',
            shouldRetry: true,
            requiresAuth: true,
            delay: 0
        };
    }

    /**
     * Handle user notification
     */
    async handleNotifyUser(analysis, context) {
        return {
            action: 'NOTIFY_USER',
            shouldRetry: false,
            userMessage: this.formatUserMessage(analysis),
            statusCode: 400
        };
    }

    /**
     * Handle validation and rejection
     */
    async handleValidateAndReject(analysis, context) {
        return {
            action: 'REJECT',
            shouldRetry: false,
            userMessage: this.formatValidationMessage(analysis),
            statusCode: 400
        };
    }

    /**
     * Handle log and escalate
     */
    async handleLogAndEscalate(analysis, context) {
        return {
            action: 'ESCALATE',
            shouldRetry: false,
            escalate: true,
            severity: 'high'
        };
    }

    /**
     * Format user-friendly error message
     */
    formatUserMessage(analysis) {
        const errorType = analysis.classification.type;

        switch (errorType) {
            case 'BUSINESS_ERROR':
                return 'Invalid request. Please check your input and try again.';
            case 'AUTH_ERROR':
                return 'Authentication required. Please log in and try again.';
            case 'RATE_LIMIT_ERROR':
                return 'Too many requests. Please wait a moment and try again.';
            case 'CLIENT_ERROR':
                return 'Invalid request format. Please check your request and try again.';
            default:
                return 'An error occurred. Please try again later.';
        }
    }

    /**
     * Format validation error message
     */
    formatValidationMessage(analysis) {
        const message = analysis.originalError.message || '';

        // Extract field name if possible
        const fieldMatch = message.match(/(\w+)\s+(is|must|should)/);
        const field = fieldMatch ? fieldMatch[1] : 'input';

        return `Invalid ${field}: ${message}`;
    }

    /**
     * Generate unique error ID
     */
    generateErrorId() {
        const timestamp = Date.now();
        const random = Math.random().toString(36).substr(2, 9);
        return `err_${this.serviceName}_${timestamp}_${random}`;
    }

    /**
     * Maintain error history size
     */
    maintainHistorySize(maxSize = 1000) {
        if (this.errorHistory.length > maxSize) {
            this.errorHistory = this.errorHistory.slice(-maxSize);
        }
    }

    /**
     * Get error statistics
     */
    getStatistics(timeWindow = 3600000) { // 1 hour default
        const cutoff = Date.now() - timeWindow;
        const recentErrors = this.errorHistory.filter(err => err.timestamp > cutoff);

        const stats = {
            total: recentErrors.length,
            byType: {},
            bySeverity: {},
            retryableCount: 0,
            userFacingCount: 0
        };

        recentErrors.forEach(error => {
            const type = error.classification.type;
            const severity = error.classification.severity;

            stats.byType[type] = (stats.byType[type] || 0) + 1;
            stats.bySeverity[severity] = (stats.bySeverity[severity] || 0) + 1;

            if (error.classification.retryable) stats.retryableCount++;
            if (error.classification.userFacing) stats.userFacingCount++;
        });

        return stats;
    }

    /**
     * Health check for ErrorDNA
     */
    async healthCheck() {
        const stats = this.getStatistics();

        return {
            status: 'operational',
            patternsLoaded: this.errorPatterns.size,
            strategiesLoaded: this.recoveryStrategies.size,
            recentErrors: stats.total,
            errorTypes: Object.keys(stats.byType).length
        };
    }
}

module.exports = ErrorDNA;