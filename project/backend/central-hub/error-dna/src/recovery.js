class ErrorRecovery {
  constructor(config = {}) {
    this.config = {
      enabled: config.enabled !== false,
      strategies: {
        retry: {
          enabled: true,
          maxAttempts: 3,
          backoffMultiplier: 2,
          initialDelay: 1000,
          ...config.strategies?.retry
        },
        fallback: {
          enabled: true,
          timeout: 30000,
          ...config.strategies?.fallback
        },
        circuit_breaker: {
          enabled: true,
          threshold: 5,
          timeout: 60000,
          resetTimeout: 300000,
          ...config.strategies?.circuit_breaker
        },
        ...config.strategies
      },
      ...config
    };

    this.circuitBreakers = new Map();
    this.retryAttempts = new Map();
    this.recoveryStats = {
      attempts: 0,
      successes: 0,
      failures: 0,
      byStrategy: {}
    };
  }

  /**
   * Attempt to recover from an error
   * @param {Object} errorData - Error data with categorization
   * @param {Object} context - Recovery context (operation, parameters, etc.)
   * @returns {Promise<Object>} - Recovery result
   */
  async attemptRecovery(errorData, context = {}) {
    if (!this.config.enabled) {
      return { success: false, reason: 'Recovery disabled' };
    }

    const recoveryId = this._generateRecoveryId();
    const startTime = Date.now();

    try {
      this.recoveryStats.attempts++;

      // Determine recovery strategy based on error type
      const strategy = this._selectRecoveryStrategy(errorData, context);

      if (!strategy) {
        return {
          success: false,
          reason: 'No suitable recovery strategy found',
          recoveryId,
          duration: Date.now() - startTime
        };
      }

      // Execute recovery strategy
      const result = await this._executeRecoveryStrategy(strategy, errorData, context);

      // Update statistics
      if (result.success) {
        this.recoveryStats.successes++;
      } else {
        this.recoveryStats.failures++;
      }

      this._updateStrategyStats(strategy, result.success);

      return {
        ...result,
        recoveryId,
        strategy,
        duration: Date.now() - startTime
      };

    } catch (recoveryError) {
      this.recoveryStats.failures++;

      return {
        success: false,
        reason: 'Recovery strategy execution failed',
        error: recoveryError.message,
        recoveryId,
        duration: Date.now() - startTime
      };
    }
  }

  /**
   * Select appropriate recovery strategy
   * @private
   */
  _selectRecoveryStrategy(errorData, context) {
    const { category, subcategory, severity } = errorData.categorization || {};

    // Critical errors get immediate fallback
    if (severity === 'CRITICAL') {
      return this.config.strategies.fallback?.enabled ? 'fallback' : null;
    }

    // Network/API errors get retry with circuit breaker
    if (category === 'API' || category === 'SYSTEM') {
      if (subcategory === 'NETWORK' || subcategory === 'TIMEOUT') {
        return this._isCircuitBreakerOpen(context.operation) ? 'fallback' : 'retry';
      }
    }

    // Trading errors get careful handling
    if (category === 'TRADING') {
      // Don't retry order placement errors automatically
      if (subcategory === 'ORDER') {
        return 'fallback';
      }
      return 'retry';
    }

    // User errors typically don't need recovery
    if (category === 'USER') {
      return null;
    }

    // Default to retry for other cases
    return this.config.strategies.retry?.enabled ? 'retry' : 'fallback';
  }

  /**
   * Execute specific recovery strategy
   * @private
   */
  async _executeRecoveryStrategy(strategy, errorData, context) {
    switch (strategy) {
      case 'retry':
        return await this._executeRetryStrategy(errorData, context);
      case 'fallback':
        return await this._executeFallbackStrategy(errorData, context);
      case 'circuit_breaker':
        return await this._executeCircuitBreakerStrategy(errorData, context);
      default:
        throw new Error(`Unknown recovery strategy: ${strategy}`);
    }
  }

  /**
   * Execute retry recovery strategy
   * @private
   */
  async _executeRetryStrategy(errorData, context) {
    const retryConfig = this.config.strategies.retry;
    const operationKey = context.operation || 'default';

    // Get current retry count
    const retryCount = this.retryAttempts.get(operationKey) || 0;

    if (retryCount >= retryConfig.maxAttempts) {
      // Max retries reached, clear counter and try fallback
      this.retryAttempts.delete(operationKey);

      if (this.config.strategies.fallback?.enabled) {
        return await this._executeFallbackStrategy(errorData, context);
      }

      return {
        success: false,
        reason: `Max retry attempts reached (${retryConfig.maxAttempts})`,
        attempts: retryCount
      };
    }

    // Calculate delay with exponential backoff
    const delay = retryConfig.initialDelay * Math.pow(retryConfig.backoffMultiplier, retryCount);

    // Wait before retry
    await this._delay(delay);

    // Increment retry count
    this.retryAttempts.set(operationKey, retryCount + 1);

    // Attempt to execute the original operation
    try {
      if (context.retryFunction && typeof context.retryFunction === 'function') {
        const result = await context.retryFunction();

        // Success - clear retry counter
        this.retryAttempts.delete(operationKey);

        return {
          success: true,
          reason: 'Retry successful',
          attempts: retryCount + 1,
          delay,
          result
        };
      } else {
        return {
          success: false,
          reason: 'No retry function provided',
          attempts: retryCount + 1
        };
      }
    } catch (retryError) {
      // Retry failed, will try again on next call (if within limits)
      return {
        success: false,
        reason: 'Retry attempt failed',
        attempts: retryCount + 1,
        delay,
        error: retryError.message
      };
    }
  }

  /**
   * Execute fallback recovery strategy
   * @private
   */
  async _executeFallbackStrategy(errorData, context) {
    const fallbackConfig = this.config.strategies.fallback;

    try {
      if (context.fallbackFunction && typeof context.fallbackFunction === 'function') {
        // Execute with timeout
        const result = await Promise.race([
          context.fallbackFunction(),
          this._timeoutPromise(fallbackConfig.timeout)
        ]);

        return {
          success: true,
          reason: 'Fallback successful',
          result
        };
      } else if (context.fallbackValue !== undefined) {
        // Use fallback value
        return {
          success: true,
          reason: 'Fallback value used',
          result: context.fallbackValue
        };
      } else {
        // Generate category-specific fallback
        const fallbackResult = this._generateCategoryFallback(errorData, context);

        return {
          success: fallbackResult !== null,
          reason: fallbackResult ? 'Generated fallback' : 'No fallback available',
          result: fallbackResult
        };
      }
    } catch (fallbackError) {
      return {
        success: false,
        reason: 'Fallback execution failed',
        error: fallbackError.message
      };
    }
  }

  /**
   * Execute circuit breaker strategy
   * @private
   */
  async _executeCircuitBreakerStrategy(errorData, context) {
    const cbConfig = this.config.strategies.circuit_breaker;
    const operationKey = context.operation || 'default';

    let circuitBreaker = this.circuitBreakers.get(operationKey);

    if (!circuitBreaker) {
      circuitBreaker = {
        failures: 0,
        lastFailure: null,
        state: 'CLOSED', // CLOSED, OPEN, HALF_OPEN
        nextRetry: null
      };
      this.circuitBreakers.set(operationKey, circuitBreaker);
    }

    const now = Date.now();

    // Check circuit breaker state
    if (circuitBreaker.state === 'OPEN') {
      if (now < circuitBreaker.nextRetry) {
        // Circuit is open, use fallback
        return await this._executeFallbackStrategy(errorData, {
          ...context,
          reason: 'Circuit breaker is open'
        });
      } else {
        // Try to half-open the circuit
        circuitBreaker.state = 'HALF_OPEN';
      }
    }

    // Try the operation
    try {
      if (context.retryFunction && typeof context.retryFunction === 'function') {
        const result = await context.retryFunction();

        // Success - reset circuit breaker
        circuitBreaker.failures = 0;
        circuitBreaker.state = 'CLOSED';
        circuitBreaker.lastFailure = null;
        circuitBreaker.nextRetry = null;

        return {
          success: true,
          reason: 'Circuit breaker operation successful',
          circuitState: 'CLOSED',
          result
        };
      } else {
        throw new Error('No retry function provided');
      }
    } catch (operationError) {
      // Operation failed
      circuitBreaker.failures++;
      circuitBreaker.lastFailure = now;

      if (circuitBreaker.failures >= cbConfig.threshold) {
        // Open the circuit
        circuitBreaker.state = 'OPEN';
        circuitBreaker.nextRetry = now + cbConfig.resetTimeout;
      }

      // Use fallback
      const fallbackResult = await this._executeFallbackStrategy(errorData, {
        ...context,
        reason: 'Circuit breaker triggered fallback'
      });

      return {
        ...fallbackResult,
        circuitState: circuitBreaker.state,
        failures: circuitBreaker.failures
      };
    }
  }

  /**
   * Generate category-specific fallback values
   * @private
   */
  _generateCategoryFallback(errorData, context) {
    const { category, subcategory } = errorData.categorization || {};

    switch (category) {
      case 'API':
        if (subcategory === 'TIMEOUT') {
          return { status: 'timeout', retry: true };
        }
        return { status: 'error', message: 'API temporarily unavailable' };

      case 'TRADING':
        // Never generate fallback trading data - too risky
        return null;

      case 'AI_ML':
        if (subcategory === 'PREDICTION') {
          return { confidence: 0, prediction: null, fallback: true };
        }
        return { status: 'model_unavailable', fallback: true };

      case 'SYSTEM':
        if (subcategory === 'DATABASE') {
          return { cached: true, data: null };
        }
        return { status: 'degraded', fallback: true };

      default:
        return { error: true, message: 'Service temporarily unavailable' };
    }
  }

  /**
   * Check if circuit breaker is open for operation
   * @private
   */
  _isCircuitBreakerOpen(operation) {
    if (!this.config.strategies.circuit_breaker?.enabled) {
      return false;
    }

    const circuitBreaker = this.circuitBreakers.get(operation || 'default');

    if (!circuitBreaker) {
      return false;
    }

    if (circuitBreaker.state === 'OPEN') {
      return Date.now() < circuitBreaker.nextRetry;
    }

    return false;
  }

  /**
   * Update strategy statistics
   * @private
   */
  _updateStrategyStats(strategy, success) {
    if (!this.recoveryStats.byStrategy[strategy]) {
      this.recoveryStats.byStrategy[strategy] = {
        attempts: 0,
        successes: 0,
        failures: 0
      };
    }

    const stats = this.recoveryStats.byStrategy[strategy];
    stats.attempts++;

    if (success) {
      stats.successes++;
    } else {
      stats.failures++;
    }
  }

  /**
   * Create timeout promise
   * @private
   */
  _timeoutPromise(timeout) {
    return new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Operation timeout')), timeout);
    });
  }

  /**
   * Simple delay utility
   * @private
   */
  _delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Generate unique recovery ID
   * @private
   */
  _generateRecoveryId() {
    return `recovery_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get recovery statistics
   */
  getStats() {
    return {
      ...this.recoveryStats,
      circuitBreakers: Object.fromEntries(
        Array.from(this.circuitBreakers.entries()).map(([key, cb]) => [
          key,
          {
            state: cb.state,
            failures: cb.failures,
            lastFailure: cb.lastFailure
          }
        ])
      ),
      retryAttempts: Object.fromEntries(this.retryAttempts)
    };
  }

  /**
   * Reset circuit breaker for operation
   */
  resetCircuitBreaker(operation) {
    const key = operation || 'default';

    if (this.circuitBreakers.has(key)) {
      this.circuitBreakers.get(key).state = 'CLOSED';
      this.circuitBreakers.get(key).failures = 0;
      this.circuitBreakers.get(key).nextRetry = null;
      return true;
    }

    return false;
  }

  /**
   * Clear retry attempts for operation
   */
  clearRetryAttempts(operation) {
    const key = operation || 'default';
    return this.retryAttempts.delete(key);
  }

  /**
   * Reset all recovery state
   */
  reset() {
    this.circuitBreakers.clear();
    this.retryAttempts.clear();
    this.recoveryStats = {
      attempts: 0,
      successes: 0,
      failures: 0,
      byStrategy: {}
    };
  }
}

module.exports = ErrorRecovery;