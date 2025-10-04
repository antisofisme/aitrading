/**
 * JavaScript ErrorDNA - Compatible dengan Python ErrorDNA
 * Intelligent error pattern analysis dan classification
 * Matches interface dari log_utils/error_dna/analyzer.py
 */

const crypto = require('crypto');

const ErrorSeverity = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
};

const ErrorCategory = {
    DATABASE: 'database',
    NETWORK: 'network',
    AUTHENTICATION: 'authentication',
    VALIDATION: 'validation',
    EXTERNAL_SERVICE: 'external_service',
    BUSINESS_LOGIC: 'business_logic',
    SYSTEM_RESOURCE: 'system_resource',
    CONFIGURATION: 'configuration',
    UNKNOWN: 'unknown'
};

class ErrorPattern {
    constructor({
        pattern_id,
        error_signature,
        category,
        severity,
        regex_patterns = [],
        keywords = new Set(),
        stack_trace_patterns = [],
        frequency = 0,
        first_seen = null,
        last_seen = null,
        affected_services = new Set(),
        correlation_patterns = []
    }) {
        this.pattern_id = pattern_id;
        this.error_signature = error_signature;
        this.category = category;
        this.severity = severity;
        this.regex_patterns = regex_patterns;
        this.keywords = keywords;
        this.stack_trace_patterns = stack_trace_patterns;
        this.frequency = frequency;
        this.first_seen = first_seen;
        this.last_seen = last_seen;
        this.affected_services = affected_services;
        this.correlation_patterns = correlation_patterns;
    }
}

class ErrorOccurrence {
    constructor({
        error_id,
        service_name,
        timestamp = new Date(),
        error_message,
        stack_trace = null,
        error_type = null,
        context = {},
        user_id = null,
        correlation_id = null,
        pattern_id = null,
        severity = ErrorSeverity.MEDIUM,
        category = ErrorCategory.UNKNOWN
    }) {
        this.error_id = error_id;
        this.service_name = service_name;
        this.timestamp = timestamp;
        this.error_message = error_message;
        this.stack_trace = stack_trace;
        this.error_type = error_type;
        this.context = context;
        this.user_id = user_id;
        this.correlation_id = correlation_id;
        this.pattern_id = pattern_id;
        this.severity = severity;
        this.category = category;
    }
}

class ErrorAnalysis {
    constructor({
        error_occurrence,
        matched_patterns,
        confidence_score,
        suggested_actions = [],
        related_errors = [],
        trend_analysis = {}
    }) {
        this.error_occurrence = error_occurrence;
        this.matched_patterns = matched_patterns;
        this.confidence_score = confidence_score;
        this.suggested_actions = suggested_actions;
        this.related_errors = related_errors;
        this.trend_analysis = trend_analysis;
    }
}

class ErrorDNAAnalyzer {
    constructor(service_name) {
        this.service_name = service_name;

        // Error storage (limited array instead of deque)
        this.error_occurrences = [];
        this.max_errors = 10000;
        this.error_patterns = new Map();

        // Analysis caches
        this.pattern_cache = new Map();
        this.trend_cache = new Map();

        // Load built-in patterns
        this._loadBuiltinPatterns();
    }

    _loadBuiltinPatterns() {
        const builtin_patterns = [
            // Database errors
            {
                pattern_id: 'db_connection_timeout',
                error_signature: 'database_connection_timeout',
                category: ErrorCategory.DATABASE,
                severity: ErrorSeverity.HIGH,
                regex_patterns: [
                    'connection.*timeout',
                    'database.*timeout',
                    'pool.*timeout'
                ],
                keywords: new Set(['connection', 'timeout', 'database', 'pool']),
                stack_trace_patterns: ['pg', 'mysql', 'mongodb', 'sequelize']
            },
            {
                pattern_id: 'db_connection_refused',
                error_signature: 'database_connection_refused',
                category: ErrorCategory.DATABASE,
                severity: ErrorSeverity.CRITICAL,
                regex_patterns: [
                    'connection.*refused',
                    'could not connect',
                    'database.*unavailable'
                ],
                keywords: new Set(['connection', 'refused', 'database', 'unavailable'])
            },

            // Network errors
            {
                pattern_id: 'network_timeout',
                error_signature: 'network_request_timeout',
                category: ErrorCategory.NETWORK,
                severity: ErrorSeverity.MEDIUM,
                regex_patterns: [
                    'request.*timeout',
                    'http.*timeout',
                    'connection.*timeout'
                ],
                keywords: new Set(['request', 'timeout', 'http', 'network'])
            },
            {
                pattern_id: 'network_connection_error',
                error_signature: 'network_connection_error',
                category: ErrorCategory.NETWORK,
                severity: ErrorSeverity.HIGH,
                regex_patterns: [
                    'connection.*error',
                    'network.*unreachable',
                    'host.*unreachable'
                ],
                keywords: new Set(['connection', 'error', 'network', 'unreachable', 'host'])
            },

            // Authentication errors
            {
                pattern_id: 'auth_token_invalid',
                error_signature: 'authentication_token_invalid',
                category: ErrorCategory.AUTHENTICATION,
                severity: ErrorSeverity.MEDIUM,
                regex_patterns: [
                    'token.*invalid',
                    'token.*expired',
                    'authentication.*failed'
                ],
                keywords: new Set(['token', 'invalid', 'expired', 'authentication', 'failed'])
            },
            {
                pattern_id: 'auth_unauthorized',
                error_signature: 'authorization_failed',
                category: ErrorCategory.AUTHENTICATION,
                severity: ErrorSeverity.MEDIUM,
                regex_patterns: [
                    'unauthorized',
                    'access.*denied',
                    'permission.*denied'
                ],
                keywords: new Set(['unauthorized', 'access', 'denied', 'permission'])
            },

            // Validation errors
            {
                pattern_id: 'validation_schema',
                error_signature: 'schema_validation_error',
                category: ErrorCategory.VALIDATION,
                severity: ErrorSeverity.LOW,
                regex_patterns: [
                    'validation.*error',
                    'schema.*error',
                    'invalid.*format'
                ],
                keywords: new Set(['validation', 'schema', 'invalid', 'format'])
            },

            // External service errors
            {
                pattern_id: 'external_api_error',
                error_signature: 'external_service_error',
                category: ErrorCategory.EXTERNAL_SERVICE,
                severity: ErrorSeverity.MEDIUM,
                regex_patterns: [
                    'external.*api.*error',
                    'service.*unavailable',
                    'api.*error'
                ],
                keywords: new Set(['external', 'api', 'service', 'unavailable'])
            },

            // System resource errors
            {
                pattern_id: 'memory_error',
                error_signature: 'memory_exhaustion',
                category: ErrorCategory.SYSTEM_RESOURCE,
                severity: ErrorSeverity.CRITICAL,
                regex_patterns: [
                    'out of memory',
                    'memory.*error',
                    'allocation.*failed'
                ],
                keywords: new Set(['memory', 'allocation', 'failed', 'exhaustion'])
            }
        ];

        for (const pattern_data of builtin_patterns) {
            const pattern = new ErrorPattern(pattern_data);
            this.error_patterns.set(pattern.pattern_id, pattern);
        }
    }

    async analyzeError({
        error_message,
        stack_trace = null,
        error_type = null,
        context = null,
        user_id = null,
        correlation_id = null
    }) {
        // Create error occurrence
        const error_occurrence = new ErrorOccurrence({
            error_id: this._generateErrorId(error_message, stack_trace),
            service_name: this.service_name,
            timestamp: new Date(),
            error_message,
            stack_trace,
            error_type,
            context: context || {},
            user_id,
            correlation_id
        });

        // Find matching patterns
        const matched_patterns = this._findMatchingPatterns(error_occurrence);

        // Calculate confidence score
        const confidence_score = this._calculateConfidenceScore(error_occurrence, matched_patterns);

        // Update pattern frequencies
        this._updatePatternFrequencies(matched_patterns);

        // Set category and severity based on best match
        if (matched_patterns.length > 0) {
            const best_match = matched_patterns[0];
            error_occurrence.pattern_id = best_match.pattern_id;
            error_occurrence.category = best_match.category;
            error_occurrence.severity = best_match.severity;
        }

        // Store error occurrence
        this._storeErrorOccurrence(error_occurrence);

        // Generate suggested actions
        const suggested_actions = this._generateSuggestedActions(error_occurrence, matched_patterns);

        // Find related errors
        const related_errors = this._findRelatedErrors(error_occurrence);

        // Perform trend analysis
        const trend_analysis = this._performTrendAnalysis(error_occurrence);

        // Create analysis result
        const analysis = new ErrorAnalysis({
            error_occurrence,
            matched_patterns,
            confidence_score,
            suggested_actions,
            related_errors,
            trend_analysis
        });

        console.log(`Analyzed error ${error_occurrence.error_id} with confidence ${confidence_score.toFixed(2)}`);
        return analysis;
    }

    _generateErrorId(error_message, stack_trace = null) {
        const content = error_message + (stack_trace || '');
        return crypto.createHash('md5').update(content).digest('hex').substring(0, 12);
    }

    _findMatchingPatterns(error_occurrence) {
        const matched_patterns = [];

        const error_text = error_occurrence.error_message.toLowerCase();
        const stack_text = (error_occurrence.stack_trace || '').toLowerCase();
        const full_text = error_text + ' ' + stack_text;

        for (const pattern of this.error_patterns.values()) {
            let match_score = 0;

            // Check regex patterns
            for (const regex_pattern of pattern.regex_patterns) {
                const regex = new RegExp(regex_pattern, 'i');
                if (regex.test(full_text)) {
                    match_score += 2;
                }
            }

            // Check keywords
            const words = new Set(full_text.split(/\s+/));
            const keyword_matches = [...pattern.keywords].filter(keyword => words.has(keyword)).length;
            match_score += keyword_matches;

            // Check stack trace patterns
            for (const stack_pattern of pattern.stack_trace_patterns) {
                if (stack_text.includes(stack_pattern.toLowerCase())) {
                    match_score += 1;
                }
            }

            // If we have a match, add to results
            if (match_score > 0) {
                pattern.match_score = match_score;
                matched_patterns.push(pattern);
            }
        }

        // Sort by match score (highest first)
        matched_patterns.sort((a, b) => (b.match_score || 0) - (a.match_score || 0));

        return matched_patterns;
    }

    _calculateConfidenceScore(error_occurrence, matched_patterns) {
        if (matched_patterns.length === 0) {
            return 0.0;
        }

        const best_pattern = matched_patterns[0];
        const match_score = best_pattern.match_score || 0;

        // Base confidence from match score
        const base_confidence = Math.min(match_score / 5.0, 1.0);

        // Boost confidence if multiple patterns match
        const pattern_boost = Math.min(matched_patterns.length * 0.1, 0.3);

        // Boost confidence if we've seen this pattern before
        const frequency_boost = Math.min(best_pattern.frequency * 0.01, 0.2);

        // Final confidence score
        const confidence = Math.min(base_confidence + pattern_boost + frequency_boost, 1.0);

        return confidence;
    }

    _updatePatternFrequencies(matched_patterns) {
        const current_time = new Date();

        for (const pattern of matched_patterns) {
            pattern.frequency += 1;
            pattern.last_seen = current_time;
            pattern.affected_services.add(this.service_name);

            if (pattern.first_seen === null) {
                pattern.first_seen = current_time;
            }
        }
    }

    _storeErrorOccurrence(error_occurrence) {
        this.error_occurrences.push(error_occurrence);

        // Maintain max size
        if (this.error_occurrences.length > this.max_errors) {
            this.error_occurrences.shift();
        }
    }

    _generateSuggestedActions(error_occurrence, matched_patterns) {
        const suggestions = [];

        if (matched_patterns.length === 0) {
            suggestions.push('Investigate error message and stack trace for clues');
            suggestions.push('Check service logs for related errors');
            return suggestions;
        }

        const best_pattern = matched_patterns[0];

        // Category-specific suggestions
        switch (best_pattern.category) {
            case ErrorCategory.DATABASE:
                suggestions.push(
                    'Check database connection pool status',
                    'Verify database server availability',
                    'Review database query performance',
                    'Check for database locks or deadlocks'
                );
                break;

            case ErrorCategory.NETWORK:
                suggestions.push(
                    'Verify network connectivity to external services',
                    'Check DNS resolution',
                    'Review network timeouts configuration',
                    'Test external service availability'
                );
                break;

            case ErrorCategory.AUTHENTICATION:
                suggestions.push(
                    'Verify authentication token validity',
                    'Check user permissions',
                    'Review authentication configuration',
                    'Validate token expiration settings'
                );
                break;

            case ErrorCategory.EXTERNAL_SERVICE:
                suggestions.push(
                    'Check external service status',
                    'Review API rate limits',
                    'Verify service credentials',
                    'Implement circuit breaker if not present'
                );
                break;

            case ErrorCategory.SYSTEM_RESOURCE:
                suggestions.push(
                    'Monitor system resource usage',
                    'Check memory/disk space availability',
                    'Review resource allocation',
                    'Consider scaling resources'
                );
                break;
        }

        // Severity-specific suggestions
        if (best_pattern.severity === ErrorSeverity.CRITICAL) {
            suggestions.unshift('⚠️ CRITICAL: Immediate attention required');
            suggestions.push('Consider alerting on-call team');
        } else if (best_pattern.severity === ErrorSeverity.HIGH) {
            suggestions.unshift('🔥 HIGH PRIORITY: Address as soon as possible');
        }

        return suggestions;
    }

    _findRelatedErrors(error_occurrence) {
        const related_errors = [];

        // Look for errors with same correlation ID
        if (error_occurrence.correlation_id) {
            for (const other_error of this.error_occurrences) {
                if (other_error.correlation_id === error_occurrence.correlation_id &&
                    other_error.error_id !== error_occurrence.error_id) {
                    related_errors.push(other_error.error_id);
                }
            }
        }

        // Look for errors from same user within 5 minutes
        if (error_occurrence.user_id && related_errors.length < 5) {
            for (const other_error of this.error_occurrences) {
                if (other_error.user_id === error_occurrence.user_id &&
                    other_error.error_id !== error_occurrence.error_id &&
                    !related_errors.includes(other_error.error_id)) {
                    const time_diff = Math.abs(other_error.timestamp.getTime() - error_occurrence.timestamp.getTime()) / 1000;
                    if (time_diff < 300) { // Within 5 minutes
                        related_errors.push(other_error.error_id);
                    }
                }
            }
        }

        return related_errors.slice(0, 5); // Limit to 5 related errors
    }

    _performTrendAnalysis(error_occurrence) {
        if (!error_occurrence.pattern_id) {
            return { trend: 'insufficient_data' };
        }

        const pattern_id = error_occurrence.pattern_id;
        const current_time = new Date();
        const day_ago = new Date(current_time.getTime() - 24 * 60 * 60 * 1000);

        // Get errors for this pattern in last 24 hours
        const recent_errors = this.error_occurrences.filter(err =>
            err.pattern_id === pattern_id && err.timestamp >= day_ago
        );

        if (recent_errors.length < 2) {
            return { trend: 'insufficient_data' };
        }

        // Calculate hourly error counts
        const hourly_counts = new Map();
        for (const error of recent_errors) {
            const hour = new Date(error.timestamp);
            hour.setMinutes(0, 0, 0);
            const hour_key = hour.toISOString();
            hourly_counts.set(hour_key, (hourly_counts.get(hour_key) || 0) + 1);
        }

        // Analyze trend
        const counts = Array.from(hourly_counts.values());
        if (counts.length >= 3) {
            const recent_avg = counts.slice(-3).reduce((a, b) => a + b, 0) / 3;
            const earlier_avg = counts.slice(0, -3).reduce((a, b) => a + b, 0) / Math.max(counts.length - 3, 1);

            let trend, severity;
            if (recent_avg > earlier_avg * 1.5) {
                trend = 'increasing';
                severity = recent_avg > earlier_avg * 2 ? 'high' : 'medium';
            } else if (recent_avg < earlier_avg * 0.5) {
                trend = 'decreasing';
                severity = 'low';
            } else {
                trend = 'stable';
                severity = 'low';
            }

            return {
                trend,
                severity,
                count_24h: recent_errors.length,
                avg_per_hour: recent_errors.length / 24,
                peak_hour_count: Math.max(...counts)
            };
        }

        return {
            trend: 'stable',
            severity: 'low',
            count_24h: recent_errors.length,
            avg_per_hour: recent_errors.length / 24,
            peak_hour_count: 0
        };
    }

    async getErrorStatistics(time_window_hours = 24) {
        const current_time = new Date();
        const cutoff_time = new Date(current_time.getTime() - time_window_hours * 60 * 60 * 1000);

        const recent_errors = this.error_occurrences.filter(err =>
            err.timestamp >= cutoff_time
        );

        // Category and severity statistics
        const category_counts = {};
        const severity_counts = {};
        const pattern_counts = {};

        for (const error of recent_errors) {
            category_counts[error.category] = (category_counts[error.category] || 0) + 1;
            severity_counts[error.severity] = (severity_counts[error.severity] || 0) + 1;
            if (error.pattern_id) {
                pattern_counts[error.pattern_id] = (pattern_counts[error.pattern_id] || 0) + 1;
            }
        }

        // Top error patterns
        const top_patterns = Object.entries(pattern_counts)
            .sort(([,a], [,b]) => b - a)
            .slice(0, 10)
            .map(([pattern_id, count]) => ({ pattern_id, count }));

        return {
            time_window_hours,
            total_errors: recent_errors.length,
            unique_patterns: Object.keys(pattern_counts).length,
            category_breakdown: category_counts,
            severity_breakdown: severity_counts,
            top_error_patterns: top_patterns,
            error_rate_per_hour: recent_errors.length / time_window_hours
        };
    }

    getPatternDetails(pattern_id) {
        const pattern = this.error_patterns.get(pattern_id);
        if (!pattern) {
            return null;
        }

        // Get recent occurrences
        const recent_occurrences = this.error_occurrences
            .filter(err => err.pattern_id === pattern_id)
            .slice(-10)
            .map(err => ({
                error_id: err.error_id,
                timestamp: err.timestamp.toISOString(),
                service: err.service_name,
                message: err.error_message.length > 100 ?
                    err.error_message.substring(0, 100) + '...' :
                    err.error_message
            }));

        return {
            pattern_id: pattern.pattern_id,
            category: pattern.category,
            severity: pattern.severity,
            frequency: pattern.frequency,
            first_seen: pattern.first_seen ? pattern.first_seen.toISOString() : null,
            last_seen: pattern.last_seen ? pattern.last_seen.toISOString() : null,
            affected_services: Array.from(pattern.affected_services),
            recent_occurrences
        };
    }

    clearOldErrors(older_than_days = 7) {
        const cutoff_time = new Date(Date.now() - older_than_days * 24 * 60 * 60 * 1000);

        const initial_count = this.error_occurrences.length;
        this.error_occurrences = this.error_occurrences.filter(err =>
            err.timestamp >= cutoff_time
        );

        console.log(`Cleared ${initial_count - this.error_occurrences.length} errors older than ${older_than_days} days`);
    }

    exportErrorData(format = 'json') {
        if (format.toLowerCase() === 'json') {
            const patterns = {};
            for (const [pid, pattern] of this.error_patterns) {
                patterns[pid] = {
                    category: pattern.category,
                    severity: pattern.severity,
                    frequency: pattern.frequency,
                    first_seen: pattern.first_seen ? pattern.first_seen.toISOString() : null,
                    last_seen: pattern.last_seen ? pattern.last_seen.toISOString() : null
                };
            }

            return {
                service_name: this.service_name,
                export_timestamp: new Date().toISOString(),
                total_patterns: this.error_patterns.size,
                total_errors: this.error_occurrences.length,
                patterns,
                statistics: this.getErrorStatistics()
            };
        } else {
            throw new Error(`Unsupported export format: ${format}`);
        }
    }
}

// Convenience class for easy import
class ErrorDNA extends ErrorDNAAnalyzer {}

module.exports = {
    ErrorDNA,
    ErrorDNAAnalyzer,
    ErrorPattern,
    ErrorOccurrence,
    ErrorAnalysis,
    ErrorSeverity,
    ErrorCategory
};