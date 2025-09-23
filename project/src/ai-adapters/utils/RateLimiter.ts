/**
 * Rate limiting and quota management utilities
 */

export interface RateLimitConfig {
  /** Requests per minute limit */
  requestsPerMinute: number;
  /** Tokens per minute limit */
  tokensPerMinute?: number;
  /** Concurrent requests limit */
  concurrentRequests?: number;
  /** Burst allowance */
  burstSize?: number;
  /** Time window in milliseconds */
  windowMs?: number;
}

export interface QuotaConfig {
  /** Daily request quota */
  dailyRequests?: number;
  /** Daily token quota */
  dailyTokens?: number;
  /** Monthly request quota */
  monthlyRequests?: number;
  /** Monthly token quota */
  monthlyTokens?: number;
  /** Reset time (for custom quotas) */
  resetTime?: Date;
}

interface RequestRecord {
  timestamp: Date;
  tokens: number;
}

interface QuotaUsage {
  requests: number;
  tokens: number;
  resetTime: Date;
}

export class RateLimiter {
  private requestQueue: RequestRecord[] = [];
  private tokenQueue: RequestRecord[] = [];
  private concurrentRequests = 0;
  private dailyUsage: QuotaUsage;
  private monthlyUsage: QuotaUsage;

  constructor(
    private rateLimitConfig: RateLimitConfig,
    private quotaConfig?: QuotaConfig
  ) {
    this.dailyUsage = this.initializeQuotaUsage('daily');
    this.monthlyUsage = this.initializeQuotaUsage('monthly');
  }

  /**
   * Check if request is allowed under rate limits and quotas
   */
  async checkLimit(estimatedTokens: number = 0): Promise<{
    allowed: boolean;
    waitTime?: number;
    reason?: string;
  }> {
    const now = Date.now();

    // Check quota limits first
    const quotaCheck = this.checkQuotas(estimatedTokens);
    if (!quotaCheck.allowed) {
      return quotaCheck;
    }

    // Check concurrent requests limit
    if (this.rateLimitConfig.concurrentRequests) {
      if (this.concurrentRequests >= this.rateLimitConfig.concurrentRequests) {
        return {
          allowed: false,
          reason: 'Concurrent request limit exceeded'
        };
      }
    }

    // Clean old requests from queues
    this.cleanupOldRequests(now);

    // Check requests per minute limit
    const windowMs = this.rateLimitConfig.windowMs || 60000; // 1 minute default
    const requestsInWindow = this.requestQueue.length;

    if (requestsInWindow >= this.rateLimitConfig.requestsPerMinute) {
      const oldestRequest = this.requestQueue[0];
      const waitTime = windowMs - (now - oldestRequest.timestamp.getTime());

      return {
        allowed: false,
        waitTime: Math.max(0, waitTime),
        reason: 'Request rate limit exceeded'
      };
    }

    // Check tokens per minute limit
    if (this.rateLimitConfig.tokensPerMinute && estimatedTokens > 0) {
      const tokensInWindow = this.tokenQueue.reduce((sum, req) => sum + req.tokens, 0);

      if (tokensInWindow + estimatedTokens > this.rateLimitConfig.tokensPerMinute) {
        // Find when enough tokens will be available
        let tokensNeeded = tokensInWindow + estimatedTokens - this.rateLimitConfig.tokensPerMinute;
        let waitTime = 0;

        for (const req of this.tokenQueue) {
          const reqAge = now - req.timestamp.getTime();
          if (reqAge < windowMs) {
            waitTime = Math.max(waitTime, windowMs - reqAge);
            tokensNeeded -= req.tokens;
            if (tokensNeeded <= 0) break;
          }
        }

        return {
          allowed: false,
          waitTime,
          reason: 'Token rate limit exceeded'
        };
      }
    }

    return { allowed: true };
  }

  /**
   * Record a request (call after successful request)
   */
  recordRequest(actualTokens: number = 0): void {
    const now = new Date();

    // Record in rate limit queues
    this.requestQueue.push({
      timestamp: now,
      tokens: actualTokens
    });

    if (actualTokens > 0) {
      this.tokenQueue.push({
        timestamp: now,
        tokens: actualTokens
      });
    }

    // Update quota usage
    this.updateQuotaUsage(actualTokens);
  }

  /**
   * Increment concurrent request counter
   */
  startRequest(): void {
    this.concurrentRequests++;
  }

  /**
   * Decrement concurrent request counter
   */
  endRequest(): void {
    this.concurrentRequests = Math.max(0, this.concurrentRequests - 1);
  }

  /**
   * Get current rate limit status
   */
  getStatus(): {
    requestsPerMinute: {
      used: number;
      limit: number;
      remaining: number;
      resetTime: Date;
    };
    tokensPerMinute?: {
      used: number;
      limit: number;
      remaining: number;
      resetTime: Date;
    };
    concurrentRequests: {
      active: number;
      limit: number;
    };
    quotas: {
      daily?: {
        requests: { used: number; limit: number; remaining: number };
        tokens?: { used: number; limit: number; remaining: number };
        resetTime: Date;
      };
      monthly?: {
        requests: { used: number; limit: number; remaining: number };
        tokens?: { used: number; limit: number; remaining: number };
        resetTime: Date;
      };
    };
  } {
    const now = Date.now();
    const windowMs = this.rateLimitConfig.windowMs || 60000;

    // Clean old requests
    this.cleanupOldRequests(now);

    const requestsUsed = this.requestQueue.length;
    const tokensUsed = this.tokenQueue.reduce((sum, req) => sum + req.tokens, 0);

    const status: any = {
      requestsPerMinute: {
        used: requestsUsed,
        limit: this.rateLimitConfig.requestsPerMinute,
        remaining: Math.max(0, this.rateLimitConfig.requestsPerMinute - requestsUsed),
        resetTime: new Date(now + windowMs)
      },
      concurrentRequests: {
        active: this.concurrentRequests,
        limit: this.rateLimitConfig.concurrentRequests || Infinity
      },
      quotas: {}
    };

    if (this.rateLimitConfig.tokensPerMinute) {
      status.tokensPerMinute = {
        used: tokensUsed,
        limit: this.rateLimitConfig.tokensPerMinute,
        remaining: Math.max(0, this.rateLimitConfig.tokensPerMinute - tokensUsed),
        resetTime: new Date(now + windowMs)
      };
    }

    // Add quota information
    if (this.quotaConfig?.dailyRequests || this.quotaConfig?.dailyTokens) {
      status.quotas.daily = {
        requests: {
          used: this.dailyUsage.requests,
          limit: this.quotaConfig.dailyRequests || Infinity,
          remaining: Math.max(0, (this.quotaConfig.dailyRequests || Infinity) - this.dailyUsage.requests)
        },
        resetTime: this.dailyUsage.resetTime
      };

      if (this.quotaConfig.dailyTokens) {
        status.quotas.daily.tokens = {
          used: this.dailyUsage.tokens,
          limit: this.quotaConfig.dailyTokens,
          remaining: Math.max(0, this.quotaConfig.dailyTokens - this.dailyUsage.tokens)
        };
      }
    }

    if (this.quotaConfig?.monthlyRequests || this.quotaConfig?.monthlyTokens) {
      status.quotas.monthly = {
        requests: {
          used: this.monthlyUsage.requests,
          limit: this.quotaConfig.monthlyRequests || Infinity,
          remaining: Math.max(0, (this.quotaConfig.monthlyRequests || Infinity) - this.monthlyUsage.requests)
        },
        resetTime: this.monthlyUsage.resetTime
      };

      if (this.quotaConfig.monthlyTokens) {
        status.quotas.monthly.tokens = {
          used: this.monthlyUsage.tokens,
          limit: this.quotaConfig.monthlyTokens,
          remaining: Math.max(0, this.quotaConfig.monthlyTokens - this.monthlyUsage.tokens)
        };
      }
    }

    return status;
  }

  /**
   * Reset rate limits (useful for testing)
   */
  reset(): void {
    this.requestQueue = [];
    this.tokenQueue = [];
    this.concurrentRequests = 0;
  }

  /**
   * Reset quotas (useful for manual resets)
   */
  resetQuotas(): void {
    this.dailyUsage = this.initializeQuotaUsage('daily');
    this.monthlyUsage = this.initializeQuotaUsage('monthly');
  }

  /**
   * Wait for rate limit to allow request
   */
  async waitForAvailability(estimatedTokens: number = 0): Promise<void> {
    while (true) {
      const check = await this.checkLimit(estimatedTokens);

      if (check.allowed) {
        return;
      }

      if (check.waitTime && check.waitTime > 0) {
        await this.sleep(check.waitTime);
      } else {
        // If no wait time specified, wait a default amount
        await this.sleep(1000);
      }
    }
  }

  /**
   * Check quota limits
   */
  private checkQuotas(estimatedTokens: number): {
    allowed: boolean;
    reason?: string;
  } {
    // Check if quotas need to be reset
    this.checkQuotaResets();

    // Check daily quotas
    if (this.quotaConfig?.dailyRequests) {
      if (this.dailyUsage.requests >= this.quotaConfig.dailyRequests) {
        return {
          allowed: false,
          reason: 'Daily request quota exceeded'
        };
      }
    }

    if (this.quotaConfig?.dailyTokens && estimatedTokens > 0) {
      if (this.dailyUsage.tokens + estimatedTokens > this.quotaConfig.dailyTokens) {
        return {
          allowed: false,
          reason: 'Daily token quota exceeded'
        };
      }
    }

    // Check monthly quotas
    if (this.quotaConfig?.monthlyRequests) {
      if (this.monthlyUsage.requests >= this.quotaConfig.monthlyRequests) {
        return {
          allowed: false,
          reason: 'Monthly request quota exceeded'
        };
      }
    }

    if (this.quotaConfig?.monthlyTokens && estimatedTokens > 0) {
      if (this.monthlyUsage.tokens + estimatedTokens > this.quotaConfig.monthlyTokens) {
        return {
          allowed: false,
          reason: 'Monthly token quota exceeded'
        };
      }
    }

    return { allowed: true };
  }

  /**
   * Clean up old requests from queues
   */
  private cleanupOldRequests(now: number): void {
    const windowMs = this.rateLimitConfig.windowMs || 60000;
    const cutoff = now - windowMs;

    this.requestQueue = this.requestQueue.filter(req =>
      req.timestamp.getTime() > cutoff
    );

    this.tokenQueue = this.tokenQueue.filter(req =>
      req.timestamp.getTime() > cutoff
    );
  }

  /**
   * Update quota usage
   */
  private updateQuotaUsage(tokens: number): void {
    this.checkQuotaResets();

    this.dailyUsage.requests++;
    this.dailyUsage.tokens += tokens;

    this.monthlyUsage.requests++;
    this.monthlyUsage.tokens += tokens;
  }

  /**
   * Check if quotas need to be reset
   */
  private checkQuotaResets(): void {
    const now = new Date();

    // Check daily reset
    if (now >= this.dailyUsage.resetTime) {
      this.dailyUsage = this.initializeQuotaUsage('daily');
    }

    // Check monthly reset
    if (now >= this.monthlyUsage.resetTime) {
      this.monthlyUsage = this.initializeQuotaUsage('monthly');
    }
  }

  /**
   * Initialize quota usage structure
   */
  private initializeQuotaUsage(period: 'daily' | 'monthly'): QuotaUsage {
    const now = new Date();
    let resetTime: Date;

    if (period === 'daily') {
      resetTime = new Date(now);
      resetTime.setDate(resetTime.getDate() + 1);
      resetTime.setHours(0, 0, 0, 0);
    } else {
      resetTime = new Date(now);
      resetTime.setMonth(resetTime.getMonth() + 1);
      resetTime.setDate(1);
      resetTime.setHours(0, 0, 0, 0);
    }

    return {
      requests: 0,
      tokens: 0,
      resetTime
    };
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}