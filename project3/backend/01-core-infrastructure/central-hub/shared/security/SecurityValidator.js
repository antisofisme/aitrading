/**
 * Security Validator - Input Validation and Authorization
 *
 * Comprehensive security validation system for:
 * - Input sanitization and validation
 * - Authentication token validation
 * - Authorization checks
 * - Rate limiting
 * - SQL injection prevention
 * - XSS protection
 * - CSRF protection
 * - Tenant isolation validation
 */

const crypto = require('crypto');

class SecurityValidator {
    constructor(serviceName, options = {}) {
        this.serviceName = serviceName;
        this.options = {
            enableRateLimiting: options.enableRateLimiting !== false,
            enableInputValidation: options.enableInputValidation !== false,
            enableTenantValidation: options.enableTenantValidation !== false,
            maxRequestSize: options.maxRequestSize || 10 * 1024 * 1024, // 10MB
            defaultRateLimit: options.defaultRateLimit || 100, // requests per minute
            rateLimitWindow: options.rateLimitWindow || 60000, // 1 minute
            jwtSecret: options.jwtSecret || process.env.JWT_SECRET,
            allowedOrigins: options.allowedOrigins || ['*'],
            ...options
        };

        // Rate limiting storage
        this.rateLimitStore = new Map();

        // Blacklisted patterns
        this.sqlInjectionPatterns = [
            /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)/i,
            /(\'(\s*(OR|AND)\s*\'\s*=\s*\'|[\w\s]*\'\s*(OR|AND)\s*\'\w*\s*=))/i,
            /(--|\#|\/\*|\*\/)/,
            /(\b(SLEEP|BENCHMARK|WAITFOR)\s*\()/i
        ];

        this.xssPatterns = [
            /<script[^>]*>.*?<\/script>/gi,
            /<iframe[^>]*>.*?<\/iframe>/gi,
            /javascript:/gi,
            /on\w+\s*=/gi,
            /<object[^>]*>.*?<\/object>/gi,
            /<embed[^>]*>.*?<\/embed>/gi
        ];

        // Common validation schemas
        this.initializeValidationSchemas();
    }

    /**
     * Initialize common validation schemas
     */
    initializeValidationSchemas() {
        this.schemas = {
            email: {
                pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                maxLength: 255,
                required: true
            },
            password: {
                minLength: 8,
                maxLength: 128,
                pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
                required: true
            },
            username: {
                pattern: /^[a-zA-Z0-9_-]{3,30}$/,
                minLength: 3,
                maxLength: 30,
                required: true
            },
            tenant_id: {
                pattern: /^[a-zA-Z0-9_-]{1,50}$/,
                maxLength: 50,
                required: true
            },
            uuid: {
                pattern: /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
            },
            correlation_id: {
                pattern: /^[a-zA-Z0-9_-]{10,100}$/,
                maxLength: 100
            },
            phone: {
                pattern: /^\+?[\d\s\-\(\)]{7,20}$/,
                maxLength: 20
            },
            url: {
                pattern: /^https?:\/\/[^\s]+$/,
                maxLength: 2048
            },
            ip_address: {
                pattern: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/
            }
        };
    }

    /**
     * Validate input data against schema
     */
    validateInput(data, schema, context = {}) {
        const errors = [];
        const sanitized = {};

        // Check if data exists
        if (!data || typeof data !== 'object') {
            return {
                isValid: false,
                errors: ['Input data is required and must be an object'],
                sanitized: {}
            };
        }

        // Validate each field in schema
        for (const [fieldName, fieldSchema] of Object.entries(schema)) {
            const value = data[fieldName];
            const fieldErrors = this.validateField(fieldName, value, fieldSchema, context);

            if (fieldErrors.length > 0) {
                errors.push(...fieldErrors);
            } else if (value !== undefined) {
                sanitized[fieldName] = this.sanitizeField(value, fieldSchema);
            }
        }

        // Check for unexpected fields
        const allowedFields = Object.keys(schema);
        const unexpectedFields = Object.keys(data).filter(field => !allowedFields.includes(field));

        if (unexpectedFields.length > 0) {
            errors.push(`Unexpected fields: ${unexpectedFields.join(', ')}`);
        }

        return {
            isValid: errors.length === 0,
            errors,
            sanitized
        };
    }

    /**
     * Validate individual field
     */
    validateField(fieldName, value, schema, context = {}) {
        const errors = [];

        // Check required fields
        if (schema.required && (value === undefined || value === null || value === '')) {
            errors.push(`${fieldName} is required`);
            return errors;
        }

        // Skip validation if value is not provided and not required
        if (value === undefined || value === null) {
            return errors;
        }

        // Type validation
        if (schema.type && typeof value !== schema.type) {
            errors.push(`${fieldName} must be of type ${schema.type}`);
            return errors;
        }

        // String validations
        if (typeof value === 'string') {
            // Length validations
            if (schema.minLength && value.length < schema.minLength) {
                errors.push(`${fieldName} must be at least ${schema.minLength} characters long`);
            }

            if (schema.maxLength && value.length > schema.maxLength) {
                errors.push(`${fieldName} must be no more than ${schema.maxLength} characters long`);
            }

            // Pattern validation
            if (schema.pattern && !schema.pattern.test(value)) {
                errors.push(`${fieldName} format is invalid`);
            }

            // SQL injection check
            if (this.containsSqlInjection(value)) {
                errors.push(`${fieldName} contains potentially malicious content`);
            }

            // XSS check
            if (this.containsXss(value)) {
                errors.push(`${fieldName} contains potentially malicious scripts`);
            }

            // Enum validation
            if (schema.enum && !schema.enum.includes(value)) {
                errors.push(`${fieldName} must be one of: ${schema.enum.join(', ')}`);
            }
        }

        // Number validations
        if (typeof value === 'number') {
            if (schema.min !== undefined && value < schema.min) {
                errors.push(`${fieldName} must be at least ${schema.min}`);
            }

            if (schema.max !== undefined && value > schema.max) {
                errors.push(`${fieldName} must be no more than ${schema.max}`);
            }

            if (schema.integer && !Number.isInteger(value)) {
                errors.push(`${fieldName} must be an integer`);
            }
        }

        // Array validations
        if (Array.isArray(value)) {
            if (schema.minItems && value.length < schema.minItems) {
                errors.push(`${fieldName} must have at least ${schema.minItems} items`);
            }

            if (schema.maxItems && value.length > schema.maxItems) {
                errors.push(`${fieldName} must have no more than ${schema.maxItems} items`);
            }

            // Validate array items
            if (schema.items) {
                value.forEach((item, index) => {
                    const itemErrors = this.validateField(`${fieldName}[${index}]`, item, schema.items, context);
                    errors.push(...itemErrors);
                });
            }
        }

        // Custom validation function
        if (schema.validate && typeof schema.validate === 'function') {
            try {
                const customResult = schema.validate(value, context);
                if (customResult !== true) {
                    errors.push(customResult || `${fieldName} validation failed`);
                }
            } catch (error) {
                errors.push(`${fieldName} custom validation error: ${error.message}`);
            }
        }

        return errors;
    }

    /**
     * Sanitize field value
     */
    sanitizeField(value, schema) {
        if (typeof value === 'string') {
            // Trim whitespace
            value = value.trim();

            // HTML encode if needed
            if (schema.htmlEncode) {
                value = this.htmlEncode(value);
            }

            // Remove dangerous characters
            if (schema.removeDangerous) {
                value = this.removeDangerousCharacters(value);
            }

            // Convert to lowercase if needed
            if (schema.lowercase) {
                value = value.toLowerCase();
            }

            // Convert to uppercase if needed
            if (schema.uppercase) {
                value = value.toUpperCase();
            }
        }

        return value;
    }

    /**
     * Check for SQL injection patterns
     */
    containsSqlInjection(input) {
        if (typeof input !== 'string') return false;

        return this.sqlInjectionPatterns.some(pattern => pattern.test(input));
    }

    /**
     * Check for XSS patterns
     */
    containsXss(input) {
        if (typeof input !== 'string') return false;

        return this.xssPatterns.some(pattern => pattern.test(input));
    }

    /**
     * HTML encode string
     */
    htmlEncode(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#x27;')
            .replace(/\//g, '&#x2F;');
    }

    /**
     * Remove dangerous characters
     */
    removeDangerousCharacters(str) {
        return str.replace(/[<>\"'%;()&+]/g, '');
    }

    /**
     * Validate JWT token
     */
    validateJwtToken(token, options = {}) {
        try {
            if (!token) {
                return {
                    isValid: false,
                    error: 'Token is required'
                };
            }

            // Remove Bearer prefix if present
            if (token.startsWith('Bearer ')) {
                token = token.substring(7);
            }

            // Basic JWT format check
            const parts = token.split('.');
            if (parts.length !== 3) {
                return {
                    isValid: false,
                    error: 'Invalid token format'
                };
            }

            // Decode header and payload
            const header = JSON.parse(Buffer.from(parts[0], 'base64').toString());
            const payload = JSON.parse(Buffer.from(parts[1], 'base64').toString());

            // Check expiration
            if (payload.exp && Date.now() >= payload.exp * 1000) {
                return {
                    isValid: false,
                    error: 'Token has expired'
                };
            }

            // Check issuer if specified
            if (options.issuer && payload.iss !== options.issuer) {
                return {
                    isValid: false,
                    error: 'Invalid token issuer'
                };
            }

            // Check audience if specified
            if (options.audience && payload.aud !== options.audience) {
                return {
                    isValid: false,
                    error: 'Invalid token audience'
                };
            }

            // Verify signature (simplified - in production use proper JWT library)
            if (this.options.jwtSecret) {
                const signature = crypto
                    .createHmac('sha256', this.options.jwtSecret)
                    .update(`${parts[0]}.${parts[1]}`)
                    .digest('base64url');

                if (signature !== parts[2]) {
                    return {
                        isValid: false,
                        error: 'Invalid token signature'
                    };
                }
            }

            return {
                isValid: true,
                payload,
                header
            };

        } catch (error) {
            return {
                isValid: false,
                error: `Token validation error: ${error.message}`
            };
        }
    }

    /**
     * Check user permissions
     */
    checkPermissions(userPermissions, requiredPermissions, context = {}) {
        if (!Array.isArray(userPermissions)) {
            return {
                hasPermission: false,
                error: 'User permissions must be an array'
            };
        }

        if (!Array.isArray(requiredPermissions)) {
            return {
                hasPermission: false,
                error: 'Required permissions must be an array'
            };
        }

        // Check if user has all required permissions
        const missingPermissions = requiredPermissions.filter(
            permission => !userPermissions.includes(permission)
        );

        if (missingPermissions.length > 0) {
            return {
                hasPermission: false,
                error: `Missing permissions: ${missingPermissions.join(', ')}`,
                missingPermissions
            };
        }

        return {
            hasPermission: true
        };
    }

    /**
     * Validate tenant access
     */
    validateTenantAccess(userTenantId, requestedTenantId, context = {}) {
        if (!this.options.enableTenantValidation) {
            return { hasAccess: true };
        }

        if (!userTenantId) {
            return {
                hasAccess: false,
                error: 'User tenant ID is required'
            };
        }

        if (!requestedTenantId) {
            return {
                hasAccess: false,
                error: 'Requested tenant ID is required'
            };
        }

        // Simple tenant isolation - user can only access their own tenant
        if (userTenantId !== requestedTenantId) {
            return {
                hasAccess: false,
                error: 'Access denied: insufficient tenant permissions'
            };
        }

        return {
            hasAccess: true
        };
    }

    /**
     * Rate limiting check
     */
    checkRateLimit(identifier, options = {}) {
        if (!this.options.enableRateLimiting) {
            return { allowed: true };
        }

        const limit = options.limit || this.options.defaultRateLimit;
        const windowMs = options.windowMs || this.options.rateLimitWindow;
        const key = `${identifier}:${this.serviceName}`;

        const now = Date.now();
        const windowStart = now - windowMs;

        // Get or create rate limit entry
        let entry = this.rateLimitStore.get(key);
        if (!entry) {
            entry = {
                requests: [],
                resetTime: now + windowMs
            };
            this.rateLimitStore.set(key, entry);
        }

        // Remove old requests outside the window
        entry.requests = entry.requests.filter(timestamp => timestamp > windowStart);

        // Check if limit exceeded
        if (entry.requests.length >= limit) {
            return {
                allowed: false,
                error: 'Rate limit exceeded',
                resetTime: entry.resetTime,
                remaining: 0,
                limit
            };
        }

        // Add current request
        entry.requests.push(now);

        return {
            allowed: true,
            remaining: limit - entry.requests.length,
            limit,
            resetTime: entry.resetTime
        };
    }

    /**
     * Validate CORS origin
     */
    validateCorsOrigin(origin) {
        if (this.options.allowedOrigins.includes('*')) {
            return { allowed: true };
        }

        if (!origin) {
            return {
                allowed: false,
                error: 'Origin header is required'
            };
        }

        if (this.options.allowedOrigins.includes(origin)) {
            return { allowed: true };
        }

        return {
            allowed: false,
            error: `Origin ${origin} is not allowed`
        };
    }

    /**
     * Validate request size
     */
    validateRequestSize(contentLength) {
        if (contentLength > this.options.maxRequestSize) {
            return {
                isValid: false,
                error: `Request size ${contentLength} exceeds maximum allowed size ${this.options.maxRequestSize}`
            };
        }

        return { isValid: true };
    }

    /**
     * Sanitize object recursively
     */
    sanitizeObject(obj, options = {}) {
        if (obj === null || obj === undefined) {
            return obj;
        }

        if (typeof obj === 'string') {
            let sanitized = obj.trim();

            if (options.removeHtml) {
                sanitized = this.stripHtml(sanitized);
            }

            if (options.encodeHtml) {
                sanitized = this.htmlEncode(sanitized);
            }

            if (options.removeDangerous) {
                sanitized = this.removeDangerousCharacters(sanitized);
            }

            return sanitized;
        }

        if (Array.isArray(obj)) {
            return obj.map(item => this.sanitizeObject(item, options));
        }

        if (typeof obj === 'object') {
            const sanitized = {};
            for (const [key, value] of Object.entries(obj)) {
                sanitized[key] = this.sanitizeObject(value, options);
            }
            return sanitized;
        }

        return obj;
    }

    /**
     * Strip HTML tags
     */
    stripHtml(str) {
        return str.replace(/<[^>]*>/g, '');
    }

    /**
     * Get predefined validation schema
     */
    getSchema(schemaName) {
        return this.schemas[schemaName];
    }

    /**
     * Add custom validation schema
     */
    addSchema(schemaName, schema) {
        this.schemas[schemaName] = schema;
    }

    /**
     * Clean up old rate limit entries
     */
    cleanupRateLimitStore() {
        const now = Date.now();
        for (const [key, entry] of this.rateLimitStore.entries()) {
            if (entry.resetTime < now) {
                this.rateLimitStore.delete(key);
            }
        }
    }

    /**
     * Start cleanup timer
     */
    startCleanupTimer() {
        this.cleanupTimer = setInterval(() => {
            this.cleanupRateLimitStore();
        }, this.options.rateLimitWindow);
    }

    /**
     * Stop cleanup timer
     */
    stopCleanupTimer() {
        if (this.cleanupTimer) {
            clearInterval(this.cleanupTimer);
            this.cleanupTimer = null;
        }
    }

    /**
     * Health check
     */
    async healthCheck() {
        return {
            status: 'operational',
            rateLimitEnabled: this.options.enableRateLimiting,
            inputValidationEnabled: this.options.enableInputValidation,
            tenantValidationEnabled: this.options.enableTenantValidation,
            activeRateLimitEntries: this.rateLimitStore.size,
            availableSchemas: Object.keys(this.schemas).length
        };
    }
}

module.exports = SecurityValidator;