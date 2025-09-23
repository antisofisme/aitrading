/**
 * RateLimiter - Token bucket rate limiting for AI providers
 */

class RateLimiter {
    constructor(options = {}) {
        this.buckets = new Map(); // provider:tenant -> bucket
        this.globalLimits = new Map(); // provider -> global limits
        this.tenantLimits = new Map(); // tenant -> per-tenant limits
        this.cleanupInterval = options.cleanupInterval || 60000; // 1 minute
        this.maxBucketAge = options.maxBucketAge || 300000; // 5 minutes

        // Default limits
        this.defaultLimits = {
            requestsPerSecond: 10,
            requestsPerMinute: 300,
            requestsPerHour: 1000,
            tokensPerSecond: 1000,
            tokensPerMinute: 30000,
            tokensPerHour: 100000,
            concurrentRequests: 5
        };

        this.startCleanup();
    }

    /**
     * Set rate limits for a provider
     */
    setProviderLimits(provider, limits) {
        this.globalLimits.set(provider, {
            ...this.defaultLimits,
            ...limits
        });
    }

    /**
     * Set rate limits for a tenant
     */
    setTenantLimits(tenant, limits) {
        this.tenantLimits.set(tenant, {
            ...this.defaultLimits,
            ...limits
        });
    }

    /**
     * Check if request is allowed and consume tokens
     */
    async checkLimit(provider, tenant = 'default', tokens = 1, type = 'request') {
        const bucketKey = `${provider}:${tenant}`;
        let bucket = this.buckets.get(bucketKey);

        if (!bucket) {
            bucket = this.createBucket(provider, tenant);
            this.buckets.set(bucketKey, bucket);
        }

        const limits = this.getEffectiveLimits(provider, tenant);
        const now = Date.now();

        // Update bucket tokens
        this.refillBucket(bucket, limits, now);

        // Check limits
        const checks = [
            this.checkRateLimit(bucket, limits, 'second', tokens, type, now),
            this.checkRateLimit(bucket, limits, 'minute', tokens, type, now),
            this.checkRateLimit(bucket, limits, 'hour', tokens, type, now)
        ];

        // Check concurrent requests for request type
        if (type === 'request') {
            checks.push(this.checkConcurrentLimit(bucket, limits));
        }

        const results = await Promise.all(checks);
        const allowed = results.every(result => result.allowed);

        if (allowed) {
            // Consume tokens
            this.consumeTokens(bucket, tokens, type, now);
            bucket.lastAccess = now;

            return {
                allowed: true,
                remaining: this.getRemainingTokens(bucket, limits, type),
                resetTime: this.getResetTime(bucket, limits),
                retryAfter: null
            };
        } else {
            // Find the most restrictive limit
            const blockedResult = results.find(r => !r.allowed);

            return {
                allowed: false,
                remaining: 0,
                resetTime: blockedResult.resetTime,
                retryAfter: blockedResult.retryAfter,
                reason: blockedResult.reason
            };
        }
    }

    /**
     * Create a new token bucket
     */
    createBucket(provider, tenant) {
        const now = Date.now();

        return {
            provider,
            tenant,
            created: now,
            lastAccess: now,
            lastRefill: now,
            concurrentRequests: 0,
            tokens: {
                request: {
                    second: { count: 0, resetTime: now + 1000 },
                    minute: { count: 0, resetTime: now + 60000 },
                    hour: { count: 0, resetTime: now + 3600000 }
                },
                token: {
                    second: { count: 0, resetTime: now + 1000 },
                    minute: { count: 0, resetTime: now + 60000 },
                    hour: { count: 0, resetTime: now + 3600000 }
                }
            }
        };
    }

    /**
     * Get effective limits for provider/tenant combination
     */
    getEffectiveLimits(provider, tenant) {
        const providerLimits = this.globalLimits.get(provider) || this.defaultLimits;
        const tenantLimits = this.tenantLimits.get(tenant) || {};

        // Tenant limits override provider limits (use the more restrictive)
        return {
            requestsPerSecond: Math.min(
                providerLimits.requestsPerSecond,
                tenantLimits.requestsPerSecond || providerLimits.requestsPerSecond
            ),
            requestsPerMinute: Math.min(
                providerLimits.requestsPerMinute,
                tenantLimits.requestsPerMinute || providerLimits.requestsPerMinute
            ),
            requestsPerHour: Math.min(
                providerLimits.requestsPerHour,
                tenantLimits.requestsPerHour || providerLimits.requestsPerHour
            ),
            tokensPerSecond: Math.min(
                providerLimits.tokensPerSecond,
                tenantLimits.tokensPerSecond || providerLimits.tokensPerSecond
            ),
            tokensPerMinute: Math.min(
                providerLimits.tokensPerMinute,
                tenantLimits.tokensPerMinute || providerLimits.tokensPerMinute
            ),
            tokensPerHour: Math.min(
                providerLimits.tokensPerHour,
                tenantLimits.tokensPerHour || providerLimits.tokensPerHour
            ),
            concurrentRequests: Math.min(
                providerLimits.concurrentRequests,
                tenantLimits.concurrentRequests || providerLimits.concurrentRequests
            )
        };
    }

    /**
     * Refill bucket tokens based on time elapsed
     */
    refillBucket(bucket, limits, now) {
        const timeSinceRefill = now - bucket.lastRefill;

        // Refill tokens for each time window
        ['second', 'minute', 'hour'].forEach(window => {
            const tokenData = bucket.tokens.request[window];

            // Reset if window has passed
            if (now >= tokenData.resetTime) {
                const windowMs = window === 'second' ? 1000 : window === 'minute' ? 60000 : 3600000;
                tokenData.count = 0;
                tokenData.resetTime = now + windowMs;
            }
        });

        // Also refill token buckets
        ['second', 'minute', 'hour'].forEach(window => {
            const tokenData = bucket.tokens.token[window];

            if (now >= tokenData.resetTime) {
                const windowMs = window === 'second' ? 1000 : window === 'minute' ? 60000 : 3600000;
                tokenData.count = 0;
                tokenData.resetTime = now + windowMs;
            }
        });

        bucket.lastRefill = now;
    }

    /**
     * Check rate limit for a specific time window
     */
    async checkRateLimit(bucket, limits, window, tokens, type, now) {
        const limitKey = type === 'request' ? `requestsPer${window.charAt(0).toUpperCase() + window.slice(1)}` : `tokensPer${window.charAt(0).toUpperCase() + window.slice(1)}`;
        const limit = limits[limitKey];
        const tokenData = bucket.tokens[type][window];

        if (tokenData.count + tokens > limit) {
            return {
                allowed: false,
                reason: `${type} rate limit exceeded for ${window}`,
                retryAfter: Math.ceil((tokenData.resetTime - now) / 1000),
                resetTime: tokenData.resetTime
            };
        }

        return {
            allowed: true,
            remaining: limit - tokenData.count - tokens,
            resetTime: tokenData.resetTime
        };
    }

    /**
     * Check concurrent request limit
     */
    async checkConcurrentLimit(bucket, limits) {
        if (bucket.concurrentRequests >= limits.concurrentRequests) {
            return {
                allowed: false,
                reason: 'Concurrent request limit exceeded',
                retryAfter: 1, // Retry in 1 second
                resetTime: Date.now() + 1000
            };
        }

        return {
            allowed: true,
            remaining: limits.concurrentRequests - bucket.concurrentRequests
        };
    }

    /**
     * Consume tokens from bucket
     */
    consumeTokens(bucket, tokens, type, now) {
        ['second', 'minute', 'hour'].forEach(window => {
            bucket.tokens[type][window].count += tokens;
        });

        if (type === 'request') {
            bucket.concurrentRequests++;
        }
    }

    /**
     * Release a concurrent request
     */
    releaseRequest(provider, tenant = 'default') {
        const bucketKey = `${provider}:${tenant}`;
        const bucket = this.buckets.get(bucketKey);

        if (bucket && bucket.concurrentRequests > 0) {
            bucket.concurrentRequests--;
        }
    }

    /**
     * Get remaining tokens for a bucket
     */
    getRemainingTokens(bucket, limits, type) {
        const limitKey = type === 'request' ? 'requestsPerSecond' : 'tokensPerSecond';
        const limit = limits[limitKey];
        const tokenData = bucket.tokens[type].second;

        return Math.max(0, limit - tokenData.count);
    }

    /**
     * Get reset time for the most restrictive limit
     */
    getResetTime(bucket, limits) {
        const resetTimes = [
            bucket.tokens.request.second.resetTime,
            bucket.tokens.request.minute.resetTime,
            bucket.tokens.request.hour.resetTime
        ];

        return Math.min(...resetTimes);
    }

    /**
     * Get rate limit status for a provider/tenant
     */
    getStatus(provider, tenant = 'default') {
        const bucketKey = `${provider}:${tenant}`;
        const bucket = this.buckets.get(bucketKey);
        const limits = this.getEffectiveLimits(provider, tenant);

        if (!bucket) {
            return {
                provider,
                tenant,
                limits,
                usage: {
                    request: { second: 0, minute: 0, hour: 0 },
                    token: { second: 0, minute: 0, hour: 0 }
                },
                concurrentRequests: 0,
                remaining: limits
            };
        }

        // Refill bucket to get current status
        this.refillBucket(bucket, limits, Date.now());

        return {
            provider,
            tenant,
            limits,
            usage: {
                request: {
                    second: bucket.tokens.request.second.count,
                    minute: bucket.tokens.request.minute.count,
                    hour: bucket.tokens.request.hour.count
                },
                token: {
                    second: bucket.tokens.token.second.count,
                    minute: bucket.tokens.token.minute.count,
                    hour: bucket.tokens.token.hour.count
                }
            },
            concurrentRequests: bucket.concurrentRequests,
            remaining: {
                requestsPerSecond: Math.max(0, limits.requestsPerSecond - bucket.tokens.request.second.count),
                requestsPerMinute: Math.max(0, limits.requestsPerMinute - bucket.tokens.request.minute.count),
                requestsPerHour: Math.max(0, limits.requestsPerHour - bucket.tokens.request.hour.count),
                tokensPerSecond: Math.max(0, limits.tokensPerSecond - bucket.tokens.token.second.count),
                tokensPerMinute: Math.max(0, limits.tokensPerMinute - bucket.tokens.token.minute.count),
                tokensPerHour: Math.max(0, limits.tokensPerHour - bucket.tokens.token.hour.count),
                concurrentRequests: Math.max(0, limits.concurrentRequests - bucket.concurrentRequests)
            },
            resetTimes: {
                second: Math.max(bucket.tokens.request.second.resetTime, bucket.tokens.token.second.resetTime),
                minute: Math.max(bucket.tokens.request.minute.resetTime, bucket.tokens.token.minute.resetTime),
                hour: Math.max(bucket.tokens.request.hour.resetTime, bucket.tokens.token.hour.resetTime)
            }
        };
    }

    /**
     * Get all rate limit statuses
     */
    getAllStatuses() {
        const statuses = {};

        for (const bucketKey of this.buckets.keys()) {
            const [provider, tenant] = bucketKey.split(':');
            if (!statuses[provider]) {
                statuses[provider] = {};
            }
            statuses[provider][tenant] = this.getStatus(provider, tenant);
        }

        return statuses;
    }

    /**
     * Reset rate limits for a provider/tenant
     */
    resetLimits(provider, tenant = 'default') {
        const bucketKey = `${provider}:${tenant}`;
        this.buckets.delete(bucketKey);
    }

    /**
     * Reset all rate limits
     */
    resetAllLimits() {
        this.buckets.clear();
    }

    /**
     * Start cleanup of old buckets
     */
    startCleanup() {
        this.cleanupIntervalId = setInterval(() => {
            this.cleanupOldBuckets();
        }, this.cleanupInterval);
    }

    /**
     * Stop cleanup
     */
    stopCleanup() {
        if (this.cleanupIntervalId) {
            clearInterval(this.cleanupIntervalId);
            this.cleanupIntervalId = null;
        }
    }

    /**
     * Cleanup old, unused buckets
     */
    cleanupOldBuckets() {
        const now = Date.now();
        const toDelete = [];

        for (const [key, bucket] of this.buckets) {
            if (now - bucket.lastAccess > this.maxBucketAge) {
                toDelete.push(key);
            }
        }

        toDelete.forEach(key => this.buckets.delete(key));

        if (toDelete.length > 0) {
            console.log(`Cleaned up ${toDelete.length} old rate limit buckets`);
        }
    }

    /**
     * Get configuration
     */
    getConfiguration() {
        return {
            defaultLimits: this.defaultLimits,
            globalLimits: Object.fromEntries(this.globalLimits),
            tenantLimits: Object.fromEntries(this.tenantLimits),
            cleanupInterval: this.cleanupInterval,
            maxBucketAge: this.maxBucketAge,
            activeBuckets: this.buckets.size
        };
    }

    /**
     * Update configuration
     */
    updateConfiguration(config) {
        if (config.defaultLimits) {
            this.defaultLimits = { ...this.defaultLimits, ...config.defaultLimits };
        }

        if (config.cleanupInterval) {
            this.cleanupInterval = config.cleanupInterval;
            this.stopCleanup();
            this.startCleanup();
        }

        if (config.maxBucketAge) {
            this.maxBucketAge = config.maxBucketAge;
        }
    }

    /**
     * Get statistics
     */
    getStatistics() {
        const stats = {
            totalBuckets: this.buckets.size,
            providerBreakdown: {},
            tenantBreakdown: {},
            concurrentRequests: 0,
            oldestBucket: null,
            newestBucket: null
        };

        let oldestTime = Date.now();
        let newestTime = 0;

        for (const [key, bucket] of this.buckets) {
            const [provider, tenant] = key.split(':');

            // Provider breakdown
            if (!stats.providerBreakdown[provider]) {
                stats.providerBreakdown[provider] = { buckets: 0, concurrentRequests: 0 };
            }
            stats.providerBreakdown[provider].buckets++;
            stats.providerBreakdown[provider].concurrentRequests += bucket.concurrentRequests;

            // Tenant breakdown
            if (!stats.tenantBreakdown[tenant]) {
                stats.tenantBreakdown[tenant] = { buckets: 0, concurrentRequests: 0 };
            }
            stats.tenantBreakdown[tenant].buckets++;
            stats.tenantBreakdown[tenant].concurrentRequests += bucket.concurrentRequests;

            // Total concurrent requests
            stats.concurrentRequests += bucket.concurrentRequests;

            // Oldest/newest buckets
            if (bucket.created < oldestTime) {
                oldestTime = bucket.created;
                stats.oldestBucket = { key, created: bucket.created };
            }

            if (bucket.created > newestTime) {
                newestTime = bucket.created;
                stats.newestBucket = { key, created: bucket.created };
            }
        }

        return stats;
    }
}

module.exports = RateLimiter;